# Ponderada CC08: do pipeline ao deadlock

**Autor: Luiz Felipe Paravatti Maciel Hinuy**

Análise da pulseira sensorial Tato: arquitetura, pipeline, concorrência e decisão de produção.

A [atividade](ponderada/ponderada-tato.md) contém as Partes A e B. O código da
A4 está em `ponderada/codigo` e os prints estão em `ponderada/img`.

## Executar A4

Requisito: Python 3.10 ou superior, sem dependências externas. Execute na raiz
do repositório. Cada comando processa 20.000 amostras com buffer de N = 3:

```bash
python3 ponderada/codigo/versao1.py
python3 ponderada/codigo/versao2.py
python3 ponderada/codigo/versao3.py
```

Para executar as três repetições de cada versão:

```bash
python3 ponderada/codigo/versao1.py --repeticoes 3
python3 ponderada/codigo/versao2.py --repeticoes 3
python3 ponderada/codigo/versao3.py --repeticoes 3
```

As versões 1 e 3 têm erros intencionais. Após 1 s sem consumo com alguma thread
pendente, a execução registra travamento e encerra. A versão 2 usa os semáforos
`vazio`, `cheio` e `mutex`. Nas três versões, o produtor inicia 20 ms antes do
consumidor para exercitar o buffer cheio. Os resultados da versão 1 podem variar
conforme o escalonamento.

Tag da entrega: `PONDERADA-CC08`.
