# ⚽ FIFA Data App

Data App que identifica as **10 melhores seleções da FIFA** e detalha os **11 jogadores
mais convocados** de cada uma desde a **Copa de 2018** (com pelo menos 1 goleiro por seleção).

Construído com **Python + Flask** (backend) e **Tailwind CSS** (frontend), seguindo
tipografia e cores inspiradas na identidade visual da FIFA (azul-marinho, azul elétrico
e dourado; fontes Oswald + Inter).

## ✨ Funcionalidades

- **Grid de fotos clicáveis** estilo carta FIFA, com avaliação geral, posição e bandeira.
- **Filtros** por país e por posição, **busca** por jogador/clube e **ordenação**
  (melhor avaliação, mais convocados, mais jovens, mais experientes, A–Z).
- **Página de perfil individual** com:
  - Foto, idade, clube atual, Copas do Mundo disputadas e nº de convocações desde 2018.
  - **Gráfico de radar** (Chart.js) com atributos de desempenho conforme a posição.
  - Métricas de desempenho da temporada atual (2025/26).
  - Últimas convocações em jogos pela seleção (com minutos jogados).
  - **Notícias em destaque**: 5 notícias **reais** por jogador (RSS do Google
    Notícias), com indicador de atualização (verifica a data da última coleta
    contra a data de hoje) e botão **"Leia mais"** que abre a busca no Google
    Notícias. As notícias são recuperadas/atualizadas no máximo uma vez por dia
    por jogador (cache em `news.json`).
- **Duelo 1 a 1**: na página do jogador, selecione um oponente para comparar
  atributo por atributo, com placar, veredito e **radar comparativo**.

## 🚀 Como rodar

```bash
pip install -r requirements.txt
python3 app.py
# abra http://127.0.0.1:5001
```

## 🗂️ Estrutura

```
app.py                  # Backend Flask (rotas web + API JSON)
data.py                 # Dataset: 10 seleções, 110 jogadores, stats e notícias
templates/
  base.html             # Layout + identidade visual FIFA
  index.html            # Grid + filtros + ordenação
  player.html           # Perfil + radar + métricas + notícias + duelo
  404.html
requirements.txt
```

## 🔌 API

| Rota | Descrição |
|------|-----------|
| `GET /api/players?team=&pos=&q=&sort=` | Lista filtrada de jogadores |
| `GET /api/player/<id\|slug>` | Dados de um jogador |
| `GET /api/compare/<a>/<b>` | Comparação/duelo entre dois jogadores |

## 📌 Sobre os dados

As seleções são o top 10 do ranking FIFA. Os elencos (nome, posição, idade, clube,
Copas e nº de convocações) são curados manualmente em `data.py`.

**Estatísticas de desempenho:** o radar e as barras de atributos usam **ratings reais
de referência do EA SPORTS FC** (Geral + 6 atributos por jogador). Jogadores de linha
têm Ritmo, Finalização, Passe, Drible, Defesa e Físico; goleiros têm Elasticidade,
Manejo, Chute, Reflexos, Velocidade e Posicionamento. Os 110 jogadores têm todos os
atributos preenchidos — **sem dados ausentes** (validado em `python3 data.py`). O resumo
(geral, média, atributo de destaque) é derivado desses valores.

### Dados de seleção (reais)

Cada perfil mostra agregados de carreira na seleção — **Atuações** (jogos) e **Gols** —
extraídos do infobox da Wikipédia (`fetch_caps.py` → `caps.json`), para os 110 jogadores:

```bash
python3 fetch_caps.py          # busca quem ainda não tem
python3 fetch_caps.py --force  # refaz todos
```

### Últimos jogos da seleção (reais, atualizados diariamente)

A seção "Últimos jogos de &lt;seleção&gt;" usa partidas **reais** da API do
**TheSportsDB** (`callups.py` → `callups.json`): adversário, placar, data, torneio e
resultado (Vitória/Empate/Derrota), além do próximo jogo agendado. O cache guarda a
data da coleta; a cada acesso compara-se com a data de hoje e recoleta se estiver
defasado (uma vez por dia) — mesmo mecanismo das notícias. O botão **"Mais convocações"**
abre uma busca com os dados de convocação do jogador.

```bash
python3 callups.py             # (re)coleta os jogos de todas as seleções
```

Observação: os jogos são reais e em nível de seleção (todos os 11 jogadores da seleção
compartilham os mesmos jogos); a participação individual minuto a minuto não é exibida
porque não há fonte aberta de escalações por jogador. Dados para fins de portfólio.

### Notícias (reais, atualizadas diariamente)

As notícias vêm do **RSS do Google Notícias** (`news.py`) — 5 manchetes reais por
jogador, com link direto para cada matéria. O cache fica em `news.json` com a data
da coleta; a cada acesso ao perfil compara-se essa data com a de hoje e, se estiver
defasada, busca-se de novo (no máximo uma vez por dia por jogador). O selo
"Atualizado hoje / em &lt;data&gt;" mostra o estado.

Para pré-aquecer/forçar a atualização de todos de uma vez (ex.: via cron diário):

```bash
python3 news.py            # atualiza só quem estiver defasado
python3 news.py --force    # força recoleta de todos
```

### Fotos dos jogadores

As **fotos são reais**, hospedadas no Wikimedia Commons (estáveis e com hotlink
permitido). Elas ficam mapeadas em `photos.json` (nome → URL) e são carregadas por
`data.py`. Para regerar/atualizar:

```bash
python3 fetch_photos.py        # busca todas as fotos na Wikipédia
python3 fetch_photos_retry.py  # re-tenta as que falharem (rate limit)
```

Se algum jogador ficar sem foto, o app cai automaticamente para um avatar com as
iniciais (fallback `onerror` nos templates).
# world-cup-claude
