T2 — Matching de Produtos (Aprendizado de Máquina)
Prof. Me. Otávio Parraga
====================================================

INTEGRANTES
-----------
- <NOME COMPLETO 1> — matrícula <XXXXXX>
- <NOME COMPLETO 2> — matrícula <XXXXXX>
(preencher com os integrantes do grupo)

DESCRIÇÃO
---------
Sistema de matching de produtos: dado um texto de consulta heterogêneo
(ex.: "FANTA LARANJA 2L C/6"), encontra o produto correspondente no
catálogo normalizado (Dados/catalog.csv, 14.206 produtos).

Duas abordagens implementadas:
  Abordagem 1 (NLP clássico) — TF-IDF (palavras e n-gramas de caracteres)
      com similaridade de cosseno e BM25 (implementação própria).
  Abordagem 2 (Deep Learning) — embeddings semânticos com o modelo
      sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2, nas
      variantes busca densa pura e híbrida (BM25 top-50 -> re-rank neural).

INSTALAÇÃO
----------
1. Python 3.10+ (testado com 3.11).
2. Instalar as dependências:

       pip install -r requirements.txt

3. Não é necessária NENHUMA chave de API: o modelo neural roda localmente
   na CPU. Na primeira execução, o modelo (~470 MB) é baixado
   automaticamente do Hugging Face Hub. Opcionalmente, defina a variável
   de ambiente HF_TOKEN com um token gratuito do Hugging Face para
   downloads mais rápidos (não é obrigatório):

       Windows (PowerShell):  $env:HF_TOKEN = "hf_..."
       Linux/macOS:           export HF_TOKEN="hf_..."

OBSERVAÇÃO (Windows): em algumas instalações, importar pandas antes de
torch causa erro de DLL (c10.dll). Os scripts já importam torch primeiro;
mantenha essa ordem se criar novos scripts.

COMO REPRODUZIR OS RESULTADOS
-----------------------------
Executar a partir da raiz do projeto (a pasta que contém src/ e Dados/):

1. Exploração dos dados:
       python src/explore.py

2. Abordagem 1 (clássica) — métricas na validação e no teste:
       python src/approach1_classic.py --split val
       python src/approach1_classic.py --split test

3. Abordagem 2 (deep learning) — métricas na validação e no teste:
       python src/approach2_deep.py --split val
       python src/approach2_deep.py --split test
   (a primeira execução codifica o catálogo e grava cache em cache/;
    as execuções seguintes reutilizam o cache)

   Ablação sem pré-processamento (apêndice do relatório):
       python src/approach2_deep.py --split val --raw-text

4. Análise qualitativa (gera results/analise_qualitativa_test.md):
       python src/qualitative.py --split test --classic tfidf_char --deep deep_hybrid

5. Comportamento em casos NO_MATCH (gera results/no_match.md):
       python src/run_no_match.py

ESTRUTURA DO CÓDIGO
-------------------
src/preprocess.py         pré-processamento textual (normalização)
src/bm25.py               implementação própria do BM25 (Okapi)
src/evaluate.py           métricas P@1, MRR@5 e R@5
src/approach1_classic.py  Abordagem 1: TF-IDF (cosseno) e BM25
src/approach2_deep.py     Abordagem 2: embeddings (dense e híbrido)
src/explore.py            exploração dos dados
src/qualitative.py        análise qualitativa (acertos/erros/ambíguos)
src/run_no_match.py       probe de casos NO_MATCH
results/                  saídas (top-5 por query, análises em Markdown)
relatorio.pdf             relatório completo do trabalho
relatorio.html            fonte do relatório; para regenerar o PDF após editar:
                          msedge --headless=new --no-pdf-header-footer
                            --print-to-pdf="relatorio.pdf" "relatorio.html"

MÉTRICAS FINAIS (queries_test.csv, 250 queries)
-----------------------------------------------
Abordagem 1 — TF-IDF char (3-5):  P@1=0.992  MRR@5=0.996  R@5=1.000
Abordagem 1 — BM25:               P@1=0.976  MRR@5=0.987  R@5=1.000
Abordagem 2 — híbrida (BM25+NN):  P@1=0.940  MRR@5=0.960  R@5=0.984
