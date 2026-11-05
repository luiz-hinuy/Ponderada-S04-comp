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

## Conferir a implementação e reproduzir os prints

Os testes conferem a contagem do nome, a integridade FIFO da versão 2 com
capacidades 1, 3 e 7, a contabilidade da versão 1 e o deadlock da versão 3:

```bash
python3 -m unittest discover -s ponderada/codigo -v
```

Para recriar as capturas a partir dos TXT já salvos, instale Chromium no PATH e
execute o utilitário opcional, que usa somente biblioteca padrão Python:

```bash
python3 ponderada/codigo/capturar_evidencias.py
```

Os prints são capturas de páginas locais com as saídas reais. A captura de
caches usa um recorte do `lscpu`, cuja saída integral também está em `img`.
Para atualizar medições e capturas, execute os três comandos com `--repeticoes 3`,
direcione cada saída para o respectivo `ponderada/img/versaoX.txt` e grave o JSON
no mesmo diretório antes de recriar os prints. Recalcule também a tabela do
relatório: os resultados novos podem diferir dos preservados nesta entrega.

## Estrutura da entrega

```text
README.md
.gitignore
ponderada/
  ponderada-tato.md     # Partes A e B; D1=4, D2=0, N=3
  codigo/              # Três versões, executor, testes e captura de evidências
  img/                 # Prints PNG, saídas TXT e resultados JSON reais
```

A tag da entrega é `PONDERADA-CC08`. O PDF de origem permanece fora do repositório.
