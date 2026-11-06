"""Acrescenta prints reais do terminal Foot sem sobrescrever a entrega anterior.

Executa três novas séries de A4 e lscpu, salva TXT/JSON próprios e captura apenas
a janela criada pelo utilitário. Requer uma sessão Wayland/Hyprland com Foot e
Grim. Não altera configurações do desktop nem o código dos experimentos.
"""

import argparse
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import time


RAIZ = Path(__file__).resolve().parents[2]
IMAGENS = RAIZ / "ponderada" / "img"


def consultar_janela(pid):
    """Recebe PID do Foot; retorna sua janela Hyprland, ou None enquanto não existe."""
    resposta = subprocess.run(["hyprctl", "-j", "clients"], check=True,
                              capture_output=True, text=True)
    return next((janela for janela in json.loads(resposta.stdout)
                 if janela["pid"] == pid), None)


def aguardar(condicao, timeout, processo):
    """Recebe função sem argumentos, prazo e processo; retorna seu valor verdadeiro.

    Consulta até a condição ser satisfeita. Lança erro se o terminal sair antes
    da conclusão ou se o prazo em segundos for ultrapassado.
    """
    limite = time.monotonic() + timeout
    while time.monotonic() < limite:
        valor = condicao()
        if valor:
            return valor
        if processo.poll() is not None:
            raise RuntimeError(f"Terminal encerrou antes da captura: {processo.returncode}")
        time.sleep(0.05)
    raise TimeoutError("O terminal não ficou pronto dentro do prazo")


def capturar(nome, comando, sobrescrever=False):
    """Recebe nome-base, comando local e opção de substituir somente o PNG novo.

    Recusa sobrescrita por padrão. O shell informa conclusão por arquivo; o Grim
    captura a região da janela identificada pelo PID, sem capturar outras janelas.
    Retorna None e fecha somente o terminal criado por esta função.
    """
    destino = IMAGENS / f"{nome}.png"
    if destino.exists() and not sobrescrever:
        raise FileExistsError(f"Captura já existe: {destino}")
    with tempfile.TemporaryDirectory(prefix="tato-terminal-") as diretorio:
        pasta = Path(diretorio)
        pronto, encerrar = pasta / "pronto", pasta / "encerrar"
        script = pasta / "executar.sh"
        script.write_text(
            "#!/usr/bin/env bash\nset -euo pipefail\n"
            f"cd {shlex.quote(str(RAIZ))}\n"
            "PS4='$ '\nset -x\ndate --iso-8601=seconds\n"
            f"{comando}\nset +x\n"
            "printf '\\nExecução concluída. Captura direta do terminal Foot.\\n'\n"
            f"touch {shlex.quote(str(pronto))}\n"
            f"while [ ! -f {shlex.quote(str(encerrar))} ]; do sleep 0.1; done\n",
            encoding="utf-8",
        )
        processo = subprocess.Popen([
            "foot", "--config=/dev/null", "--fullscreen", "--log-no-syslog",
            "--app-id=tato-evidencia-terminal", f"--title=Tato CC08 | {nome}",
            "--font=monospace:size=10",
            "bash", str(script),
        ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            aguardar(pronto.exists, 60, processo)
            janela = aguardar(lambda: consultar_janela(processo.pid), 5, processo)
            # Espera curta para o compositor apresentar o último frame do terminal.
            time.sleep(0.5)
            x, y = janela["at"]
            largura, altura = janela["size"]
            subprocess.run(["grim", "-g", f"{x},{y} {largura}x{altura}", str(destino)],
                           check=True, timeout=10)
            print(f"Captura direta salva: {destino.relative_to(RAIZ)}", flush=True)
        finally:
            encerrar.touch()
            try:
                processo.wait(timeout=5)
            except subprocess.TimeoutExpired:
                processo.terminate()
                processo.wait(timeout=5)
            if processo.stderr:
                erro = processo.stderr.read().decode(errors="replace")
                processo.stderr.close()
                if processo.returncode:
                    print(erro)


def principal():
    """Sem parâmetros/retorno; verifica dependências e acrescenta quatro capturas.

    Por padrão não substitui PNG, TXT ou JSON existentes. Cada versão roda três
    vezes com 20.000 amostras, em séries sequenciais. --reexibir permite refazer
    somente os novos PNGs de terminal exibindo seus TXT via cat, sem repetir
    medições e sem alterar os prints anteriores de navegador.
    """
    for programa in ("foot", "grim", "hyprctl", "bash"):
        if not shutil.which(programa):
            raise SystemExit(f"Dependência de captura ausente: {programa}")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reexibir", action="store_true")
    argumentos = parser.parse_args()
    nomes = [f"terminal-versao{versao}" for versao in (1, 2, 3)]
    if argumentos.reexibir:
        for nome in nomes + ["terminal-caches"]:
            if not (IMAGENS / f"{nome}.txt").is_file():
                raise SystemExit(f"Saída ainda não coletada: {nome}.txt")
        for nome in nomes + ["terminal-caches"]:
            capturar(nome, f"cat ponderada/img/{nome}.txt", sobrescrever=True)
        return
    arquivos = [IMAGENS / f"{nome}.{ext}" for nome in nomes for ext in ("png", "txt", "json")]
    arquivos += [IMAGENS / "terminal-caches.png", IMAGENS / "terminal-caches.txt"]
    if any(arquivo.exists() for arquivo in arquivos):
        raise SystemExit("Já existem evidências de terminal; preserve-as antes de uma nova coleta.")
    for versao, nome in enumerate(nomes, 1):
        capturar(nome, f"python3 ponderada/codigo/versao{versao}.py --repeticoes 3 "
                 f"--saida ponderada/img/{nome}.json | tee ponderada/img/{nome}.txt")
    capturar("terminal-caches", "lscpu --caches | tee ponderada/img/terminal-caches.txt")


if __name__ == "__main__":
    principal()
