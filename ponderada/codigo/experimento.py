"""A4: executa e mede buffers circulares com e sem sincronização.

Cada medição roda em um processo isolado com duas threads. O processo termina
também quando as threads de demonstração entram em deadlock; nenhum semáforo é
liberado artificialmente para esconder o defeito.
"""

import argparse
from collections import Counter
from datetime import datetime
import json
import multiprocessing as mp
from pathlib import Path
import platform
import threading
import time


NOME = "Luiz Felipe Paravatti Maciel Hinuy"
D1 = sum(letra.isalpha() for letra in NOME.split()[0]) % 10
D2 = sum(letra.isalpha() for letra in NOME) % 10
N = 3 + D2 % 5
AMOSTRAS = 20_000
LIMITE_SEM_CONSUMO = 1.0
ANTECEDENCIA_PRODUTOR = 0.02


def medir(versao, total, capacidade):
    """Mede uma execução com threads produtora e consumidora.

    Parâmetros: versao (1, 2 ou 3), total de amostras e capacidade do buffer,
    inteiros positivos. Retorna um dicionário de métricas e diagnóstico.
    O observador encerra após 1 s sem consumo, inclusive na versão incorreta.
    As threads daemon são descartadas ao encerrar o processo desta medição.
    """
    if versao not in (1, 2, 3) or total <= 0 or capacidade <= 0:
        raise ValueError("Versão inválida ou dimensões não positivas")
    buffer = [None] * capacidade
    escrita = leitura = ocupadas = produzidas = 0
    recebidas = []
    vazio = threading.Semaphore(capacidade)
    cheio = threading.Semaphore(0)
    mutex = threading.Semaphore(1)
    ultimo_recebimento = time.monotonic()
    estado_produtor = estado_consumidor = "iniciando"
    falhas = []

    def produtor():
        """Sem parâmetros/retorno; publica IDs crescentes usando a versão escolhida."""
        nonlocal escrita, ocupadas, produzidas, estado_produtor
        try:
            for amostra in range(total):
                if versao == 1:
                    estado_produtor = "polling: buffer cheio"
                    while ocupadas >= capacidade:
                        time.sleep(0)  # polling, sem bloqueio por notificação
                    buffer[escrita] = amostra
                    escrita = (escrita + 1) % capacidade
                    anterior = ocupadas
                    time.sleep(0)  # interrompe a operação ler-modificar-escrever
                    ocupadas = anterior + 1
                else:
                    if versao == 3:
                        estado_produtor = "aguarda mutex"
                        mutex.acquire()  # erro proposital: retém mutex ao esperar vaga
                        estado_produtor = "retém mutex e aguarda vazio"
                        vazio.acquire()
                    else:
                        estado_produtor = "aguarda vazio"
                        vazio.acquire()
                        estado_produtor = "aguarda mutex"
                        mutex.acquire()
                    buffer[escrita] = amostra
                    escrita = (escrita + 1) % capacidade
                    mutex.release()
                    cheio.release()
                produzidas += 1
            estado_produtor = "concluído"
        except Exception as erro:
            falhas.append(f"produtor: {erro!r}")

    def consumidor():
        """Sem parâmetros/retorno; registra cada leitura e seu instante para o observador."""
        nonlocal leitura, ocupadas, ultimo_recebimento, estado_consumidor
        try:
            for _ in range(total):
                if versao == 1:
                    estado_consumidor = "polling: buffer vazio"
                    while ocupadas <= 0:
                        time.sleep(0)
                    amostra = buffer[leitura]
                    leitura = (leitura + 1) % capacidade
                    anterior = ocupadas
                    time.sleep(0)  # mesma janela de corrida do produtor
                    ocupadas = anterior - 1
                else:
                    estado_consumidor = "aguarda cheio"
                    cheio.acquire()
                    estado_consumidor = "retém cheio e aguarda mutex"
                    mutex.acquire()
                    amostra = buffer[leitura]
                    leitura = (leitura + 1) % capacidade
                    mutex.release()
                    vazio.release()
                recebidas.append(amostra)
                ultimo_recebimento = time.monotonic()
            estado_consumidor = "concluído"
        except Exception as erro:
            falhas.append(f"consumidor: {erro!r}")

    inicio = time.monotonic()
    thread_produtor = threading.Thread(target=produtor, daemon=True)
    thread_consumidor = threading.Thread(target=consumidor, daemon=True)
    thread_produtor.start()
    # Mesmo escalonamento nas três versões: permite encher N=3 antes de consumir.
    # Não altera IDs, contadores, conteúdo ou permissões dos semáforos.
    time.sleep(ANTECEDENCIA_PRODUTOR)
    ultimo_recebimento = time.monotonic()
    thread_consumidor.start()
    travou = False
    while thread_produtor.is_alive() or thread_consumidor.is_alive():
        if falhas:
            raise RuntimeError("; ".join(falhas))
        if time.monotonic() - ultimo_recebimento >= LIMITE_SEM_CONSUMO:
            travou = True
            break
        time.sleep(0.001)
    if falhas:
        raise RuntimeError("; ".join(falhas))

    # Cópia única: todas as métricas descrevem o mesmo prefixo observado.
    observadas = recebidas.copy()
    validas = [valor for valor in observadas if isinstance(valor, int) and 0 <= valor < total]
    frequencias = Counter(validas)
    return {
        "versao": versao,
        "amostras_solicitadas": total,
        "capacidade": capacidade,
        "produzidas": produzidas,
        "consumidas": len(observadas),
        "unicas": len(frequencias),
        "perdidas": total - len(frequencias),
        "duplicadas": sum(contagem - 1 for contagem in frequencias.values()),
        "invalidas": len(observadas) - len(validas),
        "em_ordem": observadas == list(range(total)),
        "travou": travou,
        "duracao_s": round(time.monotonic() - inicio, 6),
        "estado_produtor": estado_produtor,
        "estado_consumidor": estado_consumidor,
        "inicio_sequencia": observadas[:12],
        "fim_sequencia": observadas[-12:],
    }


def executar_isolado(conexao, versao, total, capacidade):
    """Recebe Pipe e parâmetros de medir; envia resultado/erro, fecha Pipe e retorna None."""
    try:
        conexao.send({"resultado": medir(versao, total, capacidade)})
    except Exception as erro:
        conexao.send({"erro": repr(erro)})
    finally:
        conexao.close()


def executar(versao, total=AMOSTRAS, capacidade=N):
    """Recebe versão, total e capacidade; retorna métricas de um processo novo.

    Usa spawn para não herdar threads. Uma falha ou timeout externo de 60 s
    lança RuntimeError, sem ser confundida com o travamento medido de 1 s.
    """
    contexto = mp.get_context("spawn")
    receptor, emissor = contexto.Pipe(duplex=False)
    processo = contexto.Process(target=executar_isolado, args=(emissor, versao, total, capacidade))
    processo.start()
    emissor.close()
    try:
        if not receptor.poll(60):
            raise RuntimeError("Experimento excedeu o limite externo de 60 s")
        mensagem = receptor.recv()
        if "erro" in mensagem:
            raise RuntimeError(mensagem["erro"])
        return mensagem["resultado"]
    finally:
        receptor.close()
        processo.join(timeout=2)
        if processo.is_alive():
            processo.terminate()
            processo.join()


def principal(versao):
    """Recebe versão fixa do wrapper; lê CLI, imprime métricas e retorna None.

    --repeticoes define a quantidade de medições; --saida salva o JSON completo.
    As execuções oficiais sempre usam as 20.000 amostras e N calculado do nome.
    """
    parser = argparse.ArgumentParser(description=f"A4 - versão {versao}, N={N}")
    parser.add_argument("--repeticoes", type=int, default=1)
    parser.add_argument("--saida", type=Path)
    argumentos = parser.parse_args()
    if argumentos.repeticoes <= 0:
        parser.error("--repeticoes deve ser positivo")
    print(f"A4 | versão {versao} | {NOME}", flush=True)
    print(f"D1={D1} D2={D2} N={N} | {AMOSTRAS} amostras por execução", flush=True)
    print(f"Python {platform.python_version()} | {platform.system()} {platform.release()}", flush=True)
    print("Observador: encerra após 1 s sem consumo; produtor inicia 20 ms antes.", flush=True)
    resultados = []
    for indice in range(1, argumentos.repeticoes + 1):
        resultado = executar(versao)
        resultado["execucao"] = indice
        resultados.append(resultado)
        print(f"\nExecução {indice}: produzidas={resultado['produzidas']} "
              f"consumidas={resultado['consumidas']} únicas={resultado['unicas']}", flush=True)
        print(f"perdidas={resultado['perdidas']} duplicadas={resultado['duplicadas']} "
              f"inválidas={resultado['invalidas']} travou={'sim' if resultado['travou'] else 'não'} "
              f"FIFO completo={'sim' if resultado['em_ordem'] else 'não'}", flush=True)
        print(f"produtor: {resultado['estado_produtor']}; "
              f"consumidor: {resultado['estado_consumidor']}", flush=True)
        print(f"duração={resultado['duracao_s']:.6f} s", flush=True)
    if argumentos.saida:
        argumentos.saida.parent.mkdir(parents=True, exist_ok=True)
        argumentos.saida.write_text(json.dumps({
            "nome": NOME, "D1": D1, "D2": D2, "N": N,
            "data": datetime.now().astimezone().isoformat(),
            "python": platform.python_version(),
            "sistema": platform.platform(),
            "antecedencia_produtor_s": ANTECEDENCIA_PRODUTOR,
            "limite_sem_consumo_s": LIMITE_SEM_CONSUMO,
            "resultados": resultados,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit("Execute versao1.py, versao2.py ou versao3.py.")
