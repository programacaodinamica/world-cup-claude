"""
Busca dados REAIS de seleção (jogos/atuações e gols) no infobox da Wikipédia
e salva em caps.json (nome -> {caps, goals, team}).

Uso:
  python3 fetch_caps.py          # busca quem ainda não tem
  python3 fetch_caps.py --force  # refaz todos
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.parse

from data import ROSTERS, TEAMS

_CAPS_PATH = os.path.join(os.path.dirname(__file__), "caps.json")

# País (PT -> nome em inglês usado na Wikipédia para casar a seleção principal)
COUNTRY_EN = {
    "Argentina": "Argentina", "França": "France", "Espanha": "Spain",
    "Inglaterra": "England", "Brasil": "Brazil", "Portugal": "Portugal",
    "Holanda": "Netherlands", "Bélgica": "Belgium", "Itália": "Italy",
    "Croácia": "Croatia",
}

# Títulos da Wikipédia (EN) para nomes ambíguos
OVERRIDES = {
    "Danilo": "Danilo (footballer, born July 1991)",
    "Jorginho": "Jorginho (footballer, born December 1991)",
    "Fred": "Fred (footballer, born 1993)",
    "Pepe": "Pepe (footballer, born 1983)",
    "Rodri": "Rodrigo Hernández Cascante",
    "Raphinha": "Raphinha (footballer, born 1996)",
    "Marquinhos": "Marquinhos",
    "Gavi": "Gavi (footballer)",
    "Richarlison": "Richarlison",
    "Casemiro": "Casemiro",
    "Neymar": "Neymar",
}


def _wikitext(title):
    params = urllib.parse.urlencode({
        "action": "query", "prop": "revisions", "rvprop": "content",
        "rvslots": "main", "titles": title, "format": "json", "redirects": "1",
    })
    url = "https://en.wikipedia.org/w/api.php?" + params
    for attempt in range(4):
        try:
            out = subprocess.run(
                ["curl", "-s", "-m", "25", "-A", "FIFA-Data-App/1.0", url],
                capture_output=True, text=True, timeout=30,
            ).stdout
            if not out.strip():
                time.sleep(1.0 + attempt)
                continue
            pages = json.loads(out)["query"]["pages"]
        except Exception:
            time.sleep(1.0 + attempt)
            continue
        for _, p in pages.items():
            revs = p.get("revisions")
            if revs:
                return revs[0]["slots"]["main"]["*"]
        return None
    return None


def _num(s):
    """Extrai um inteiro de um valor de infobox (lida com [[link|123]], {{0}}, refs)."""
    if not s:
        return None
    s = re.sub(r"<ref.*?(/>|</ref>)", "", s, flags=re.DOTALL)   # refs
    s = re.sub(r"\{\{.*?\}\}", "", s)                            # templates ({{efn}}, {{0}})
    # em [[alvo|exibição]] o número fica na parte de exibição (após o último |)
    s = re.sub(r"\[\[(?:[^\]\|]*\|)*([^\]\|]+)\]\]", r"\1", s)
    s = s.replace("−", "-")
    m = re.search(r"-?\d+", s)
    return int(m.group()) if m else None


def _clean_team(team):
    t = re.sub(r"\{\{.*?\}\}", "", team)       # templates
    t = re.sub(r"\[\[|\]\]", "", t)            # colchetes de wikilink
    return t.split("|")[-1].strip()


def _is_senior(raw_team, country_en):
    t = _clean_team(raw_team).lower()
    if country_en.lower() not in t:
        return False
    for bad in ("u-1", "u-2", "u17", "u18", "u19", "u20", "u21", "u23",
                "under-", "olympic", "youth", "futsal", "beach", " b)", " b "):
        if bad in t:
            return False
    return True


def parse_national(txt, country_en):
    """Extrai (caps, goals) da seleção PRINCIPAL a partir do infobox."""
    teams, caps, goals = {}, {}, {}
    # Captura cada campo nationalX# = valor. O valor vai até o próximo separador
    # de campo " | <campo> " ou o fim da linha — assim funciona mesmo quando há
    # vários campos na mesma linha (e ignora os pipes internos de [[link|texto]]).
    pat = re.compile(r"national(team|caps|goals)(\d+)\s*=\s*(.*?)(?=\s+\|\s+\w|$)",
                     re.MULTILINE)
    for m in pat.finditer(txt):
        kind, idx, val = m.group(1), m.group(2), m.group(3).strip()
        if kind == "team":
            teams[idx] = val
        elif kind == "caps":
            caps[idx] = val
        else:
            goals[idx] = val

    if not teams:
        return None

    # candidatos: 1) nome exatamente == país; 2) seleção principal (contém país,
    # sem sufixo de base/U-xx); 3) qualquer linha. Escolhe a de mais jogos.
    exact = [i for i, t in teams.items() if _clean_team(t).lower() == country_en.lower()]
    senior = [i for i, t in teams.items() if _is_senior(t, country_en)]
    candidates = exact or senior or list(teams)
    best = max(candidates, key=lambda i: (_num(caps.get(i, "")) or -1))

    return {"caps": _num(caps.get(best, "")),
            "goals": _num(goals.get(best, "")),
            "team": _clean_team(teams.get(best, ""))}


def fetch_one(name, country_pt):
    title = OVERRIDES.get(name, name)
    txt = _wikitext(title)
    if not txt and name not in OVERRIDES:
        txt = _wikitext(f"{name} (footballer)")
    if not txt:
        return None
    return parse_national(txt, COUNTRY_EN[country_pt])


def main():
    force = "--force" in sys.argv
    try:
        with open(_CAPS_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}

    pairs = [(name, team) for team, roster in ROSTERS.items()
             for (name, *_rest) in roster]
    for i, (name, team) in enumerate(pairs, 1):
        if not force and name in data and data[name].get("caps") is not None:
            print(f"[{i:3}] cache  {name}")
            continue
        res = fetch_one(name, team)
        if res and res.get("caps") is not None:
            data[name] = res
            print(f"[{i:3}] {res['caps']:>3} jogos, {res['goals'] if res['goals'] is not None else '?'} gols  {name} ({res['team']})")
        else:
            print(f"[{i:3}] FALHOU  {name}")
        with open(_CAPS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        time.sleep(0.5)

    missing = [n for n, _ in pairs if data.get(n, {}).get("caps") is None]
    print(f"\nSalvo caps.json — {len(pairs) - len(missing)}/{len(pairs)} com dados.")
    if missing:
        print("Faltando:", missing)


if __name__ == "__main__":
    main()
