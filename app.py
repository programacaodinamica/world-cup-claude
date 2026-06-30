"""
FIFA Data App — Backend Flask.

Rotas:
  /                       Grid de jogadores com filtros (país, posição) e ordenação
  /jogador/<slug>         Perfil individual do jogador (radar, métricas, notícias, duelo)
  /api/players            JSON de todos os jogadores (com filtros via query string)
  /api/player/<id>        JSON de um jogador
  /api/compare/<a>/<b>    JSON de comparação entre dois jogadores (duelo)
"""

from datetime import date

from flask import Flask, render_template, jsonify, request, abort, url_for

import callups
import data
import news

app = Flask(__name__)

SORT_OPTIONS = {
    "overall":  ("Melhor avaliação",      lambda p: -p["overall"]),
    "caps":     ("Mais jogos pela seleção", lambda p: -p["nt"]["caps"]),
    "goals":    ("Mais gols na seleção",  lambda p: -p["nt"]["goals"]),
    "age_asc":  ("Mais jovens",           lambda p: p["age"]),
    "age_desc": ("Mais experientes",      lambda p: -p["age"]),
    "name":     ("Nome (A-Z)",            lambda p: p["name"]),
}


def _filter_sort(players):
    team = request.args.get("team", "").strip()
    pos = request.args.get("pos", "").strip()
    search = request.args.get("q", "").strip().lower()
    sort = request.args.get("sort", "overall")

    out = players
    if team:
        out = [p for p in out if p["team"] == team]
    if pos:
        out = [p for p in out if p["pos"] == pos]
    if search:
        out = [p for p in out if search in p["name"].lower()
               or search in p["club"].lower()]

    key = SORT_OPTIONS.get(sort, SORT_OPTIONS["overall"])[1]
    out = sorted(out, key=key)
    return out, team, pos, search, sort


@app.route("/")
def index():
    players, team, pos, search, sort = _filter_sort(data.PLAYERS)
    return render_template(
        "index.html",
        players=players,
        teams=data.TEAMS,
        positions=data.POSITION_LABEL,
        sort_options=SORT_OPTIONS,
        sel_team=team,
        sel_pos=pos,
        search=search,
        sel_sort=sort,
        total=len(data.PLAYERS),
    )


@app.route("/jogador/<slug>")
def player_profile(slug):
    player = data.get_player(slug)
    if not player:
        abort(404)
    # candidatos para o duelo (todos os outros jogadores)
    opponents = sorted(
        [p for p in data.PLAYERS if p["id"] != player["id"]],
        key=lambda p: p["name"],
    )
    # notícias reais (com verificação/atualização diária)
    player_news = news.get_news(player["name"])
    # jogos reais da seleção (com verificação/atualização diária)
    team_callups = callups.get_callups(player["team"])
    return render_template(
        "player.html",
        player=player,
        opponents=opponents,
        teams=data.TEAMS,
        news=player_news,
        callups=team_callups,
        callups_url=callups.player_callups_url(player["name"]),
        today=date.today().isoformat(),
    )


@app.route("/api/players")
def api_players():
    players, *_ = _filter_sort(data.PLAYERS)
    return jsonify(players)


@app.route("/api/player/<identifier>")
def api_player(identifier):
    player = data.get_player(identifier)
    if not player:
        abort(404)
    return jsonify(player)


@app.route("/api/compare/<a>/<b>")
def api_compare(a, b):
    pa, pb = data.get_player(a), data.get_player(b)
    if not pa or not pb:
        abort(404)
    # vencedor de cada eixo do radar (apenas se os eixos coincidirem)
    duel = None
    if pa["stats"]["axes"] == pb["stats"]["axes"]:
        rounds = []
        wins_a = wins_b = 0
        for axis, va, vb in zip(pa["stats"]["axes"], pa["stats"]["values"], pb["stats"]["values"]):
            if va > vb:
                winner = "a"; wins_a += 1
            elif vb > va:
                winner = "b"; wins_b += 1
            else:
                winner = "draw"
            rounds.append({"axis": axis, "a": va, "b": vb, "winner": winner})
        overall_winner = "a" if pa["overall"] > pb["overall"] else ("b" if pb["overall"] > pa["overall"] else "draw")
        duel = {"rounds": rounds, "wins_a": wins_a, "wins_b": wins_b, "overall_winner": overall_winner}
    return jsonify({"a": pa, "b": pb, "duel": duel})


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    import os
    app.run(debug=True, port=int(os.environ.get("PORT", 5001)))
