# Análise qualitativa — split: test


## Abordagem 1 (tfidf_char): 248 acertos, 2 erros (P@1=0.992)

### Exemplos de acertos

| Query | Produto encontrado | Score |
|---|---|---|
| Lava-Roupas Líquido Omo Lavagem Perfeita Sachê 900ml Refil | Lava-roupas líquido omo lavagem perfeita sachê refil 900ml | 1.000 |
| Sabonete Líquido Dove Nutrição Profunda Sachê 200ml Refil | Sabonete líquido dove nutrição profunda sachê refil 200ml | 1.000 |
| Mortadela Fatiada Defumada Sadia Soltíssimo 200g | Mortadela defumada fatiada soltíssimo sadia 200g | 1.000 |
| Macarrão Instantâneo Yakissoba Carne com Molho Japonês Nissin U.F.O. 97g | Macarrão instantâneo carne com molho japonês ufo yakissoba nissin 97g | 0.952 |
| Presunto Cozido Fatiado Sadia Soltíssimo 200g | Presunto cozido fatiado soltíssimo sadia 200g | 1.000 |

### Erros (todos) com diagnóstico

| Query | Esperado | Obtido (top-1) | Posição do correto | Diagnóstico |
|---|---|---|---|---|
| Fralda Pampers Confort Sec G 128 Unidades | Fralda pampers confort sec g 128 unidades | Fralda pampers confort sec g 60 unidades | 2 | variante/sabor/versão errada do mesmo produto |
| Espumante Casa Valduga Arte Tradicional Brut 750ml | Espumante brut branco arte tradicional casa valduga 750ml | Espumante brut rosé arte tradicional casa valduga 750ml | 2 | variante/sabor/versão errada do mesmo produto |

## Abordagem 2 (deep_hybrid): 236 acertos, 14 erros (P@1=0.944)

### Exemplos de acertos

| Query | Produto encontrado | Score |
|---|---|---|
| Lava-Roupas Líquido Omo Lavagem Perfeita Sachê 900ml Refil | Lava-roupas líquido omo lavagem perfeita sachê refil 900ml | 0.998 |
| Sabonete Líquido Dove Nutrição Profunda Sachê 200ml Refil | Sabonete líquido dove nutrição profunda sachê refil 200ml | 0.999 |
| Mortadela Fatiada Defumada Sadia Soltíssimo 200g | Mortadela defumada fatiada soltíssimo sadia 200g | 0.983 |
| Macarrão Instantâneo Yakissoba Carne com Molho Japonês Nissin U.F.O. 97g | Macarrão instantâneo carne com molho japonês ufo yakissoba nissin 97g | 0.957 |
| Presunto Cozido Fatiado Sadia Soltíssimo 200g | Presunto cozido fatiado soltíssimo sadia 200g | 0.976 |

### Erros (todos) com diagnóstico

| Query | Esperado | Obtido (top-1) | Posição do correto | Diagnóstico |
|---|---|---|---|---|
| Pipoca para Microondas Manteiga YOKI 100g | Pipoca para micro-ondas manteiga yoki 100g | Saco hermético para freezer e microondas 31x27cm conserv 8 unidades | >5 | produto diferente (similaridade lexical enganosa) |
| Fralda Pampers Confort Sec G 128 Unidades | Fralda pampers confort sec g 128 unidades | Fralda pampers confort sec g 60 unidades | 2 | variante/sabor/versão errada do mesmo produto |
| Vinho Argentino Tinto Cordero con Piel de Lobo 750ml | Cordero con piel de lobo tinto de tintas argentino vinho tinto 750ml | Cordero con piel de lobo malbec argentino vinho tinto 750ml | >5 | variante/sabor/versão errada do mesmo produto |
| Espumante Casa Valduga Arte Tradicional Brut 750ml | Espumante brut branco arte tradicional casa valduga 750ml | Espumante brut rosé arte tradicional casa valduga 750ml | 2 | variante/sabor/versão errada do mesmo produto |
| Biscoito Recheado Chocolícia 132g | Biscoito recheado chocolate chocolícia 132g | Biscoito recheado tortinha de limão trakinas 126g | >5 | tamanho/quantidade errada |
| Creme Dental Antitártaro Colgate Total 12 Caixa 180g | Creme dental colgate total 12 anti-tártaro 180g | Creme dental colgate total 12 gengiva reforçada 180g | 2 | variante/sabor/versão errada do mesmo produto |
| Refresco em Pó Laranja Docinha Tang Pacote 18g | Refresco em pó laranja docinha tang 18g | Refresco em pó laranja tang 18g | 2 | variante/sabor/versão errada do mesmo produto |
| Queijo Maasdam Président 160g | Queijo tipo maasdam président 160g | Queijo mussarela fatiado président 150g | 3 | tamanho/quantidade errada |
| Refresco em Pó Maracujá Tang Pacote 18g | Refresco em pó maracujá tang 18g | Refresco em pó manga tang 18g | 4 | variante/sabor/versão errada do mesmo produto |
| Pipoca para Microondas Sabor Natural YOKI com Sal 100g | Pipoca para micro-ondas natural com sal yoki 100g | Salgadinho tostitos sabor toque de sal marinho 110g | >5 | tamanho/quantidade errada |
| Aperitivo Lillet Blanc de Vinho Francês - 750 ml | Aperitivo francês lillet blanc 750ml | Bergerac francês vinho tinto 750ml | 3 | variante/sabor/versão errada do mesmo produto |
| Biscoito Salgado Piraquê Presuntinho 100g | Biscoito salgadinho presuntinho piraquê 100g | Biscoito de polvilho salgado plic-plac 100g | 2 | variante/sabor/versão errada do mesmo produto |
| Sal Grosso para Churrasco CISNE Pacote 1kg | Sal grosso para churrasco cisne 1kg | Sal grosso para churrasco iodado lebre 1kg | 2 | variante/sabor/versão errada do mesmo produto |
| Salsicha Viena Ceratti 500g | Salsicha viena ceratti 200g | Salsicha viena perdigão 500g | 2 | tamanho/quantidade errada |

## Comparação direta

- Erros só da Abordagem 1 (deep acertou): 0
- Erros só da Abordagem 2 (clássico acertou): 12
  - Biscoito Salgado Piraquê Presuntinho 100g
  - Biscoito Recheado Chocolícia 132g
  - Creme Dental Antitártaro Colgate Total 12 Caixa 180g
  - Sal Grosso para Churrasco CISNE Pacote 1kg
  - Refresco em Pó Laranja Docinha Tang Pacote 18g
  - Vinho Argentino Tinto Cordero con Piel de Lobo 750ml
- Erros em comum: 2

## Casos ambíguos

Queries cujo produto correto tem nome duplicado no catálogo (ids diferentes, mesmo nome) ou cujo top-2 tem scores quase idênticos:

| Query | Top-1 | Top-2 | Δ score | Observação |
|---|---|---|---|---|
| Refrigerante Laranja Fanta Lata 350ml | Refrigerante fanta laranja lata 350ml | Refrigerante fanta laranja lata 350ml 12 un | 0.0000 | scores quase empatados |
| Fralda Pampers Confort Sec G 128 Unidades | Fralda pampers confort sec g 60 unidades | Fralda pampers confort sec g 128 unidades | 0.0000 | scores quase empatados |
| Leite UHT Semidesnatado Parmalat Garrafa 1 Litro | Leite uht semidesnatado parmalat garrafa 1 litro | Leite uht semidesnatado parmalat garrafa 1 litro 6 un | 0.0000 | scores quase empatados |
| Espumante Casa Valduga Arte Tradicional Brut 750ml | Espumante brut rosé arte tradicional casa valduga 750ml | Espumante brut branco arte tradicional casa valduga 750ml | 0.0009 | scores quase empatados |
| CORONA CERO SUNBREW LONG NECK 330ML - C/24 | Cerveja corona cero sunbrew long neck 330ml | Cerveja corona cero sunbrew long neck 330ml 6 un | 0.0000 | scores quase empatados |

## Casos NO_MATCH

Os conjuntos val/test não contêm queries sem correspondência no catálogo (todos os matched_id existem). Para discutir o comportamento em NO_MATCH, analisamos os *scores* do top-1: um sistema em produção deve rejeitar matches com score abaixo de um limiar.

- Score top-1 quando o match está **correto**: média 0.964, p5 0.880, mín 0.786
- Score top-1 quando o match está **errado**: média 0.983, máx 1.000

Exemplos de queries reais de queries.csv sem produto no catálogo (verificadas manualmente) e o que cada abordagem devolve estão na seção de NO_MATCH do relatório (script run_no_match.py).