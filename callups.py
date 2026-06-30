"""
Jogos REAIS recentes das seleções via TheSportsDB (API gratuita, chave de teste).

Como nas notícias, há cache diário: callups.json guarda os jogos com a data da
coleta; a cada acesso compara-se com a data de HOJE e, se estiver defasado, busca
de novo (uma vez por dia). Os jogos são reais (adversário, placar, data, torneio).

Estratégia: o torneio atual (Copa do Mundo, liga 4429 no TheSportsDB) é varrido
dia a dia (eventsday) nas últimas semanas; os eventos são agrupados por seleção.
Também se mescla o último jogo de cada seleção (eventslast) como garantia.
"""

import json
import os
import subprocess
import time
import urllib.parse
from datetime import date, datetime, timedelta

_CACHE_PATH = os.path.join(os.path.dirname(__file__), "callups.json")
_KEY = "3"                      # chave pública de teste do TheSportsDB
_WC_LEAGUE = "4429"            # FIFA World Cup
_DAYS_BACK = 24                # janela de varredura
_MAX_MATCHES = 6

# IDs das seleções no TheSportsDB (nome PT -> idTeam)
TEAM_IDS = {
    "Argentina": "134509", "França": "133913", "Espanha": "133909",
    "Inglaterra": "133914", "Brasil": "134496", "Portugal": "133908",
    "Holanda": "133905", "Bélgica": "134515", "Itália": "133910",
    "Croácia": "133912",
}

_MESES = ["jan", "fev", "mar", "abr", "mai", "jun",
          "jul", "ago", "set", "out", "nov", "dez"]


def player_callups_url(name):
    """Link 'Mais convocações' -> dados/convocações do jogador (busca Google)."""
    q = urllib.parse.quote(f'"{name}" convocação seleção')
    return f"https://www.google.com/search?q={q}"


def _curl_json(url, retries=3):
    for attempt in range(retries):
        try:
            out = subprocess.run(
                ["curl", "-s", "-m", "25", "-A", "Mozilla/5.0 (FIFA-Data-App)", url],
                capture_output=True, text=True, timeout=30,
            ).stdout
            if out.strip():
                return json.loads(out)
        except Exception:
            pass
        time.sleep(0.8 + attempt)
    return None


def _fmt_date(s):
    try:
        dt = datetime.strptime(s, "%Y-%m-%d")
        return f"{dt.day} {_MESES[dt.month - 1]} {dt.year}"
    except Exception:
        return s or ""


def _to_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _build_match(e, team_id):
    """Monta o jogo na perspectiva da seleção (mando, adversário, resultado)."""
    hs, as_ = _to_int(e.get("intHomeScore")), _to_int(e.get("intAwayScore"))
    finished = hs is not None and as_ is not None
    is_home = e.get("idHomeTeam") == team_id
    opponent = e.get("strAwayTeam") if is_home else e.get("strHomeTeam")
    result = None
    if finished:
        gf, ga = (hs, as_) if is_home else (as_, hs)
        result = "V" if gf > ga else ("E" if gf == ga else "D")
    return {
        "date_iso": e.get("dateEvent") or "",
        "date": _fmt_date(e.get("dateEvent") or ""),
        "competition": e.get("strLeague") or "",
        "home_team": e.get("strHomeTeam") or "",
        "away_team": e.get("strAwayTeam") or "",
        "home_score": hs,
        "away_score": as_,
        "opponent": opponent,
        "is_home": is_home,
        "result": result,
        "finished": finished,
    }


def _collect_events():
    """Varre os últimos dias do Mundial e devolve {idEvent: evento}."""
    events = {}
    today = date.today()
    for i in range(_DAYS_BACK):
        d = (today - timedelta(days=i)).isoformat()
        data = _curl_json(f"https://www.thesportsdb.com/api/v1/json/{_KEY}/eventsday.php?d={d}&l={_WC_LEAGUE}")
        for e in (data or {}).get("events") or []:
            events[e.get("idEvent")] = e
    return events


def _latest_for_team(team_id):
    """Último(s) jogo(s) disputado(s) pela seleção (eventslast)."""
    data = _curl_json(f"https://www.thesportsdb.com/api/v1/json/{_KEY}/eventslast.php?id={team_id}")
    return (data or {}).get("results") or []


def _next_for_team(team_id):
    """Próximo(s) jogo(s) agendado(s) da seleção (eventsnext)."""
    data = _curl_json(f"https://www.thesportsdb.com/api/v1/json/{_KEY}/eventsnext.php?id={team_id}")
    return (data or {}).get("events") or []


def refresh_all():
    """(Re)coleta os jogos reais de todas as seleções e grava callups.json."""
    events = _collect_events()
    teams_out = {}
    for team_pt, tid in TEAM_IDS.items():
        # 1) histórico do Mundial (varredura por dia) + 2) último jogo + 3) próximo
        raw = [e for e in events.values()
               if e.get("idHomeTeam") == tid or e.get("idAwayTeam") == tid]
        raw += _latest_for_team(tid)
        raw += _next_for_team(tid)
        time.sleep(0.3)
        # dedup por idEvent
        seen, uniq = set(), []
        for e in raw:
            eid = e.get("idEvent")
            if eid and eid not in seen:
                seen.add(eid)
                uniq.append(e)
        # passados (mais recentes primeiro) + 1 próximo agendado
        played = sorted([e for e in uniq if _to_int(e.get("intHomeScore")) is not None],
                        key=lambda e: e.get("dateEvent") or "", reverse=True)
        upcoming = sorted([e for e in uniq if _to_int(e.get("intHomeScore")) is None],
                          key=lambda e: e.get("dateEvent") or "")
        ordered = upcoming[:1] + played[:_MAX_MATCHES - 1] if upcoming else played[:_MAX_MATCHES]
        matches = [_build_match(e, tid) for e in ordered]
        teams_out[team_pt] = matches
        print(f"  {team_pt:12} {len(matches)} jogo(s)")

    cache = {"date": date.today().isoformat(), "teams": teams_out}
    with open(_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    print(f"\nSalvo callups.json — {date.today().isoformat()}")
    return cache


def _load_cache():
    try:
        with open(_CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def get_callups(team_pt):
    """Retorna {matches, last_updated, is_fresh} para a seleção, com checagem diária."""
    today = date.today().isoformat()
    cache = _load_cache()

    if cache.get("date") == today and team_pt in cache.get("teams", {}):
        return {"matches": cache["teams"][team_pt], "last_updated": today, "is_fresh": True}

    # defasado/inexistente -> recoleta tudo (1x por dia)
    try:
        cache = refresh_all()
    except Exception:
        pass
    matches = (cache.get("teams") or {}).get(team_pt, [])
    fresh = cache.get("date") == today and bool(matches)
    return {"matches": matches, "last_updated": cache.get("date"), "is_fresh": fresh}


if __name__ == "__main__":
    print("Coletando jogos reais das seleções (Copa do Mundo)…")
    refresh_all()
