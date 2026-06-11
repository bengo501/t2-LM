# Comportamento em casos NO_MATCH

Referência (validação, tfidf_char): score top-1 dos matches corretos tem média 0.962 e percentil 5 = 0.891.


## Queries NO_MATCH (produto não existe no catálogo)


**MORMAII LATA BRANCO C/6**

| Abordagem | Top-3 | Scores |
|---|---|---|
| tfidf_char | Pão de ló branco rio branco 300g; Molho branco santa clara 250g; Molho branco elegê 200g | 0.407, 0.269, 0.268 |
| deep_hybrid | Pão de ló branco rio branco 300g; Cerveja patagonia weisse lata 473ml 6 un; Nozes pecan caramelizadas pecanita lata 100g | 0.447, 0.351, 0.339 |

**Limpador para Casa Perfumado QUALITÁ Lavanda 2 litros**

| Abordagem | Top-3 | Scores |
|---|---|---|
| tfidf_char | Limpador veja perfumes lavanda da frança 2 litros; Limpador veja perfumes lavanda da frança 1 litro; Limpador ajax perfume flores de lavanda 1 litro | 0.584, 0.546, 0.518 |
| deep_hybrid | Limpador casa & perfume agradable 1 litro; Limpador casa & perfume agradable 2 litros embalagem promocional; Limpador casa & perfume agradable leve 1 litro, pague 900ml | 0.902, 0.872, 0.822 |

**Farinha de Chia Taeq Pouch 150g**

| Abordagem | Top-3 | Scores |
|---|---|---|
| tfidf_char | Farinha de chia e linhaça chiaça orgânico ecobio 250g; Farinha de trigo farina 1kg; Iogurte de morango parmalat fit pouch 100g | 0.384, 0.372, 0.349 |
| deep_hybrid | Iogurte de morango parmalat fit pouch 100g; Farinha de aveia nestlé 170g; Farinha panko grano divino 200g | 0.681, 0.663, 0.655 |

**Rabo de Bovino Congelado SWIFT 2Kg**

| Abordagem | Top-3 | Scores |
|---|---|---|
| tfidf_char | Assado de tira bovino congelado las piedras; Assado de tira bovino congelado gran selezione; Hambúrguer bovino congelado sadia 672g | 0.366, 0.358, 0.349 |
| deep_hybrid | Assado de tira bovino congelado gran selezione; Entrecot bovino resfriado minerva; Mocotó bovino congelado rei do mocotó 720g | 0.833, 0.767, 0.762 |

**Ração para Cães Carnilove Adulto Fresh Chicken & Rabbit 1,5kg**

| Abordagem | Top-3 | Scores |
|---|---|---|
| tfidf_char | Ração úmida para cães champ adultos carne 85g; Ração para cães birbo premium adultos carne 1kg; Ração para cães bandit adultos ômega 6 5kg | 0.298, 0.282, 0.277 |
| deep_hybrid | Ração para cães birbo premium adultos frango 15kg; Ração para cães pedigree adultos carne, frango e cereais 900g; Ração para cães monello cães filhote premium especial frango 1kg | 0.823, 0.766, 0.764 |

**CACHACA COBICADA UMBURANA 250ml C/6**

| Abordagem | Top-3 | Scores |
|---|---|---|
| tfidf_char | Cachaça salinas umburana 700ml; Cachaça weber haus amburana 700ml; Cachaça 7 campos reserva ouro amburana 970ml | 0.683, 0.478, 0.438 |
| deep_hybrid | Cachaça salinas umburana 700ml; Cachaça com mel e limão 51 740ml; Cachaça salinas tradicional 670ml | 0.790, 0.695, 0.682 |

**CHICLETE BUZZY ROSA MORANGO**

| Abordagem | Top-3 | Scores |
|---|---|---|
| tfidf_char | Pirulito flopito chiclé tutti-frutti florestal 600g; Morango 250g; Suco de morango vigor 200ml | 0.239, 0.232, 0.229 |
| deep_hybrid | Chinelo ipanema glitter rosa 37/38; Estojo box rosa luxcel; Sabonete em barra francis brasilidades manga rosa 80g | 0.649, 0.559, 0.535 |

## Queries de controle (produto existe)


**Café Solúvel Granulado Forte Nescafé Tradição Sachê 40g**

| Abordagem | Top-3 | Scores |
|---|---|---|
| tfidf_char | Café solúvel tradição forte granulado nescafé sachê 40g; Café solúvel tradição forte granulado nescafé 160g; Café solúvel extraforte granulado nescafé sachê 40g | 1.000, 0.894, 0.824 |
| deep_hybrid | Café solúvel tradição forte granulado nescafé sachê 40g; Café solúvel tradição forte granulado nescafé 160g; Café solúvel extraforte granulado nescafé sachê 40g | 0.990, 0.967, 0.955 |

**Lava-Roupas Líquido Lavanda Omo Sachê 900ml Refil**

| Abordagem | Top-3 | Scores |
|---|---|---|
| tfidf_char | Lava-roupas líquido omo lavanda sachê refil 900ml; Lava-roupas líquido omo lavanda 3 litros; Lava-roupas líquido omo puro cuidado sachê refil 900ml | 1.000, 0.798, 0.771 |
| deep_hybrid | Lava-roupas líquido omo lavanda sachê refil 900ml; Lava-roupas líquido omo puro cuidado sachê refil 900ml; Lava-roupas líquido omo lavagem perfeita sachê refil 900ml | 0.994, 0.978, 0.970 |