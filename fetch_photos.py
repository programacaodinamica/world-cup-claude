"""
Busca fotos reais dos jogadores na Wikipédia (Wikimedia Commons) e salva em
photos.json (mapa nome -> URL da foto). As imagens ficam hospedadas em
upload.wikimedia.org, que é estável e permite hotlink.

Uso:  python3 fetch_photos.py
"""

import json
import subprocess
import time
import urllib.parse

from data import ROSTERS

# Títulos específicos da Wikipédia (EN) para nomes ambíguos / desambiguação
OVERRIDES = {
    "Fred": "Fred (footballer, born 1993)",
    "Danilo": "Danilo (footballer, born 1991)",
    "Pepe": "Pepe (footballer, born 1983)",
    "Rodri": "Rodri",
    "Raphinha": "Raphinha (footballer, born 1996)",
    "Jorginho": "Jorginho (footballer, born 1991)",
    "Marquinhos": "Marquinhos (footballer, born 1994)",
    "Gavi": "Gavi (footballer)",
    "Pedri": "Pedri",
    "Richarlison": "Richarlison",
    "Casemiro": "Casemiro",
    "Neymar": "Neymar",
    "Fred": "Fred (footballer, born 1993)",
    "Bruno Fernandes": "Bruno Fernandes",
    "Thorgan Hazard": "Thorgan Hazard",
    "Eden Hazard": "Eden Hazard",
    "Lucas Hernández": "Lucas Hernández",
    "Ángel Di María": "Ángel Di María",
    "Diogo Jota": "Diogo Jota",
    "Phil Foden": "Phil Foden",
    "Josip Brekalo": "Josip Brekalo",
}


def candidate_titles(name):
    """Lista de títulos a tentar, em ordem de preferência."""
    cands = []
    if name in OVERRIDES:
        cands.append(OVERRIDES[name])
    cands.append(name)
    cands.append(f"{name} (footballer)")
    cands.append(f"{name} (soccer)")
    # remove duplicados preservando ordem
    seen = set()
    out = []
    for c in cands:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def fetch_thumb(title):
    t = urllib.parse.quote(title.replace(" ", "_"))
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{t}?redirect=true"
    try:
        out = subprocess.run(
            ["curl", "-s", "-m", "20", "-A", "FIFA-Data-App/1.0 (educational)", url],
            capture_output=True, text=True, timeout=25,
        ).stdout
        d = json.loads(out)
    except Exception:
        return None
    if d.get("type") == "disambiguation":
        return None
    # prefere o thumbnail (menor/leve); cai para a imagem original
    thumb = (d.get("thumbnail") or d.get("originalimage") or {}).get("source")
    return thumb


def main():
    photos = {}
    names = [name for roster in ROSTERS.values() for (name, *_rest) in roster]
    total = len(names)
    for i, name in enumerate(names, 1):
        url = None
        for title in candidate_titles(name):
            url = fetch_thumb(title)
            if url:
                break
            time.sleep(0.15)
        photos[name] = url
        status = "OK " if url else "FALTOU"
        print(f"[{i:3}/{total}] {status} {name}")
        time.sleep(0.15)

    with open("photos.json", "w", encoding="utf-8") as f:
        json.dump(photos, f, ensure_ascii=False, indent=2)

    missing = [n for n, u in photos.items() if not u]
    print(f"\nSalvo photos.json — {total - len(missing)}/{total} com foto.")
    if missing:
        print("Sem foto:", missing)


if __name__ == "__main__":
    main()
