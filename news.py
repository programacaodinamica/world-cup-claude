"""
Notícias reais dos jogadores via RSS do Google Notícias (gratuito, sem chave).

Estratégia de atualização diária:
  - As notícias de cada jogador ficam em cache em news.json com a data da coleta.
  - Ao pedir as notícias (get_news), compara-se a data do cache com a data de HOJE.
  - Se o cache for de outro dia (ou não existir), busca-se de novo e regrava-se.
  Assim as manchetes se mantêm atualizadas, sendo recuperadas no máximo uma vez
  por dia por jogador (no primeiro acesso do dia).
"""

import json
import os
import subprocess
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import date, datetime
from email.utils import parsedate_to_datetime

_CACHE_PATH = os.path.join(os.path.dirname(__file__), "news.json")
_NUM_NEWS = 5

_MESES = ["jan", "fev", "mar", "abr", "mai", "jun",
          "jul", "ago", "set", "out", "nov", "dez"]


def search_url(name):
    """Link da BUSCA do Google Notícias (página legível) — usado no 'Leia mais'."""
    q = urllib.parse.quote(f'"{name}"')
    return f"https://news.google.com/search?q={q}&hl=pt-BR&gl=BR&ceid=BR:pt-419"


def _rss_url(name):
    q = urllib.parse.quote(f'"{name}"')
    return f"https://news.google.com/rss/search?q={q}&hl=pt-BR&gl=BR&ceid=BR:pt-419"


def _fmt_date(pub):
    """'Wed, 24 Jun 2026 10:59:00 GMT' -> ('2026-06-24', '24 jun 2026')."""
    try:
        dt = parsedate_to_datetime(pub)
        return dt.date().isoformat(), f"{dt.day} {_MESES[dt.month - 1]} {dt.year}"
    except Exception:
        return "", (pub or "")[:16]


def _clean_title(title, source):
    """Remove o sufixo ' - Fonte' que o Google costuma anexar ao título."""
    if source and title.endswith(f" - {source}"):
        return title[: -(len(source) + 3)].strip()
    return title.strip()


def fetch_player_news(name, n=_NUM_NEWS):
    """Busca as n notícias mais recentes do jogador no Google Notícias (RSS)."""
    url = _rss_url(name)
    try:
        out = subprocess.run(
            ["curl", "-s", "-m", "20", "-A", "Mozilla/5.0 (FIFA-Data-App)", url],
            capture_output=True, text=True, timeout=25,
        ).stdout
        root = ET.fromstring(out)
    except Exception:
        return []

    items = []
    for it in root.findall(".//item")[:n]:
        title = it.findtext("title") or ""
        link = it.findtext("link") or ""
        pub = it.findtext("pubDate") or ""
        src_el = it.find("{*}source")
        source = src_el.text if src_el is not None else "Google Notícias"
        date_iso, date_br = _fmt_date(pub)
        items.append({
            "title": _clean_title(title, source),
            "url": link,
            "source": source,
            "date": date_br,
            "date_iso": date_iso,
        })
    return items


# --------------------------- cache em disco -------------------------------
def _load_cache():
    try:
        with open(_CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _save_cache(cache):
    try:
        with open(_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def get_news(name):
    """Retorna {items, last_updated, is_fresh, search_url} para um jogador.

    Faz a verificação da última atualização em relação à data de hoje e
    recupera notícias novas quando o cache está defasado.
    """
    today = date.today().isoformat()
    cache = _load_cache()
    entry = cache.get(name)

    if entry and entry.get("date") == today and entry.get("items"):
        # cache do dia — não precisa buscar de novo
        return {
            "items": entry["items"],
            "last_updated": entry["date"],
            "is_fresh": True,
            "search_url": search_url(name),
        }

    # cache defasado ou inexistente -> busca nova
    items = fetch_player_news(name)
    if items:
        cache[name] = {"date": today, "items": items}
        _save_cache(cache)
        return {"items": items, "last_updated": today, "is_fresh": True,
                "search_url": search_url(name)}

    # falha na busca -> devolve o que houver em cache (defasado), se existir
    if entry and entry.get("items"):
        return {"items": entry["items"], "last_updated": entry.get("date", "?"),
                "is_fresh": False, "search_url": search_url(name)}

    return {"items": [], "last_updated": None, "is_fresh": False,
            "search_url": search_url(name)}


def refresh_all(names, force=False):
    """Pré-aquece o cache de todos os jogadores (uso opcional via CLI)."""
    today = date.today().isoformat()
    cache = _load_cache()
    updated = 0
    for i, name in enumerate(names, 1):
        entry = cache.get(name)
        if not force and entry and entry.get("date") == today and entry.get("items"):
            print(f"[{i:3}] cache OK  {name}")
            continue
        items = fetch_player_news(name)
        if items:
            cache[name] = {"date": today, "items": items}
            updated += 1
            print(f"[{i:3}] {len(items)} notícias  {name}")
        else:
            print(f"[{i:3}] FALHOU  {name}")
        _save_cache(cache)
    print(f"\nAtualizados {updated} jogadores. Cache: {_CACHE_PATH}")


if __name__ == "__main__":
    import sys
    from data import PLAYERS
    names = [p["name"] for p in PLAYERS]
    force = "--force" in sys.argv
    refresh_all(names, force=force)
