"""Re-tenta apenas os jogadores sem foto em photos.json, com retentativas e
delays maiores (a API da Wikipédia limita rajadas). Mescla no arquivo."""

import json
import subprocess
import time
import urllib.parse

from data import ROSTERS

# Títulos alternativos para quem não tem imagem no resumo padrão
ALT = {
    "Rodri": "Rodrigo Hernández Cascante",
}


def fetch_thumb(title):
    t = urllib.parse.quote(title.replace(" ", "_"))
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{t}?redirect=true"
    for attempt in range(4):
        try:
            out = subprocess.run(
                ["curl", "-s", "-m", "20", "-A", "FIFA-Data-App/1.0 (educational)", url],
                capture_output=True, text=True, timeout=25,
            ).stdout
            if not out.strip():
                time.sleep(1.0 + attempt)
                continue
            d = json.loads(out)
        except Exception:
            time.sleep(1.0 + attempt)
            continue
        if d.get("type") == "disambiguation":
            return None
        thumb = (d.get("thumbnail") or d.get("originalimage") or {}).get("source")
        if thumb:
            return thumb
        return None
    return None


def main():
    with open("photos.json", encoding="utf-8") as f:
        photos = json.load(f)

    names = [name for roster in ROSTERS.values() for (name, *_rest) in roster]
    missing = [n for n in names if not photos.get(n)]
    print(f"Re-tentando {len(missing)} jogadores…")

    for i, name in enumerate(missing, 1):
        title = ALT.get(name, name)
        url = fetch_thumb(title)
        if not url and name not in ALT:
            url = fetch_thumb(f"{name} (footballer)")
        photos[name] = url
        print(f"[{i:3}/{len(missing)}] {'OK ' if url else 'FALTOU'} {name}")
        time.sleep(0.6)

    with open("photos.json", "w", encoding="utf-8") as f:
        json.dump(photos, f, ensure_ascii=False, indent=2)

    still = [n for n in names if not photos.get(n)]
    ok = len(names) - len(still)
    print(f"\nphotos.json atualizado — {ok}/{len(names)} com foto.")
    if still:
        print("Ainda sem foto:", still)


if __name__ == "__main__":
    main()
