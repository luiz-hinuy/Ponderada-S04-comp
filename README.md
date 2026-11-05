# Ponderada CC08: do pipeline ao deadlock

**Autor: Luiz Felipe Paravatti Maciel Hinuy**

Análise da pulseira sensorial Tato e experimentos de concorrência com buffer circular.

Leia a [atividade completa](ponderada/ponderada-tato.md) para as contas de A1,
diagramas de A2/A3/A5, resultados de A4 e memorando da Parte B.

## Executar A4

Requisito: Python 3.10 ou superior, somente biblioteca padrão. Na raiz do
repositório, cada comando executa uma versão com **20.000 amostras e N = 3**:

```bash
python3 ponderada/codigo/versao1.py
python3 ponderada/codigo/versao2.py
python3 ponderada/codigo/versao3.py
```

As versões 1 e 3 têm erros intencionais. O observador encerra a medição após
1 segundo sem consumo, registra o travamento e descarta o processo experimental.
Isso não é uma correção do buffer. Nas três versões, o produtor inicia 20 ms
antes do consumidor para exercitar o buffer cheio. A versão 2 deve entregar a
sequência inteira em ordem, sem perda, duplicação ou travamento.

Para repetir as nove medições e salvar os resultados em outra pasta:

```bash
python3 ponderada/codigo/versao1.py --repeticoes 3 --saida /tmp/tato-v1.json
python3 ponderada/codigo/versao2.py --repeticoes 3 --saida /tmp/tato-v2.json
python3 ponderada/codigo/versao3.py --repeticoes 3 --saida /tmp/tato-v3.json
```

As saídas reais e os prints da entrega ficam em [ponderada/img](ponderada/img).
Os números da versão 1 dependem do escalonamento e podem variar entre execuções.
