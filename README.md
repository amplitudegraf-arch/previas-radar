# Radar Prévias

O que cada vereador faz, só com dados oficiais das Câmaras Municipais: presença nas sessões, propostas apresentadas e votos. Sem nota e sem opinião; cada número tem link para a fonte oficial.

No ar: **https://www.previas26.com.br/ap/santana/radar/**

Inspirado no manual *Como criar o Radar da sua cidade* (Radar PTlândia, Hortolândia-SP).

## Como funciona

```
coletor/sapl.py      baixa a API do SAPL da Câmara + as atas em PDF  → dados/bruto/<cidade>/
processar/sapl.py    presença, propostas, votos, Mesa Diretora        → dados/site/<cidade>.json
processar/lugares.py bairro, rua e tema de cada pedido; texto legível
verificar.py         confere tudo; se algo estiver errado, não publica
site/gerar.py        gera o site estático                              → publico/ap/<cidade>/radar/
```

O robô (`.github/workflows/atualizar.yml`) roda todo dia às 6h de Brasília e publica no GitHub Pages. O domínio previas26.com.br repassa o caminho `/ap/` para cá.

Rodar no computador:

```
python3 coletor/sapl.py santana
python3 processar/sapl.py santana
python3 verificar.py santana
RADAR_LOCAL=1 python3 site/gerar.py santana   # links com index.html, para abrir do disco
open publico/ap/santana/radar/index.html
```

Fotos: miniaturas centradas no rosto em `site/fotos/<cidade>/`, geradas no Mac com `sh site/fotos.sh santana`. Uma foto melhor colocada em `site/fotos/originais/<cidade>/<slug>.jpg` tem prioridade sobre a foto do SAPL.

## Regras

- Só dados oficiais, a mesma regra para todos, estimativas sempre identificadas.
- Contato: só o e-mail publicado pela Câmara. Número pessoal, nunca.
- Dado ausente não é falta: sessão sem registro de presença não entra na conta.
- Achou um erro? Avise pelo Instagram [@previas.ap](https://www.instagram.com/previas.ap).
