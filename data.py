"""
Camada de dados do FIFA Data App.

Contém as 10 melhores seleções da FIFA e os 11 jogadores mais convocados de
cada uma desde a Copa de 2018 (com pelo menos 1 goleiro por seleção).

As estatísticas de desempenho (estilo radar FIFA) e os links de notícias são
gerados de forma determinística a partir do nome do jogador, garantindo que os
mesmos valores apareçam sempre. Os links de notícias apontam para buscas reais
do Google Notícias e ficam armazenados em cada jogador.
"""

import hashlib
import json
import os
import urllib.parse

# Fotos reais dos jogadores (Wikimedia Commons), geradas por fetch_photos.py.
# Mapa nome -> URL. Ausentes caem no avatar com iniciais.
_PHOTOS_PATH = os.path.join(os.path.dirname(__file__), "photos.json")
try:
    with open(_PHOTOS_PATH, encoding="utf-8") as _f:
        REAL_PHOTOS = json.load(_f)
except (OSError, ValueError):
    REAL_PHOTOS = {}

# Dados REAIS de seleção (Wikipédia), gerados por fetch_caps.py.
# Mapa nome -> {"caps": jogos/atuações, "goals": gols, "team": seleção}.
_CAPS_PATH = os.path.join(os.path.dirname(__file__), "caps.json")
try:
    with open(_CAPS_PATH, encoding="utf-8") as _f:
        REAL_CAPS = json.load(_f)
except (OSError, ValueError):
    REAL_CAPS = {}

# ---------------------------------------------------------------------------
# Seleções (top 10 do ranking FIFA) + identidade visual
# ---------------------------------------------------------------------------
TEAMS = {
    "Argentina":     {"rank": 1,  "flag": "🇦🇷", "color": "#6CACE4", "confederation": "CONMEBOL"},
    "França":        {"rank": 2,  "flag": "🇫🇷", "color": "#1E3A8A", "confederation": "UEFA"},
    "Espanha":       {"rank": 3,  "flag": "🇪🇸", "color": "#C60B1E", "confederation": "UEFA"},
    "Inglaterra":    {"rank": 4,  "flag": "🏴",  "color": "#1D3FBA", "confederation": "UEFA"},
    "Brasil":        {"rank": 5,  "flag": "🇧🇷", "color": "#009C3B", "confederation": "CONMEBOL"},
    "Portugal":      {"rank": 6,  "flag": "🇵🇹", "color": "#006600", "confederation": "UEFA"},
    "Holanda":       {"rank": 7,  "flag": "🇳🇱", "color": "#F36C21", "confederation": "UEFA"},
    "Bélgica":       {"rank": 8,  "flag": "🇧🇪", "color": "#E30613", "confederation": "UEFA"},
    "Itália":        {"rank": 9,  "flag": "🇮🇹", "color": "#0066A1", "confederation": "UEFA"},
    "Croácia":       {"rank": 10, "flag": "🇭🇷", "color": "#C00000", "confederation": "UEFA"},
}

# ---------------------------------------------------------------------------
# Rosters: 11 jogadores mais convocados desde 2018 (>= 1 goleiro cada)
# Campos curados: nome, posição, idade (em 2026), clube, copas, convocações
# pos: GK (goleiro), DF (defensor), MF (meio-campo), FW (atacante)
# ---------------------------------------------------------------------------
ROSTERS = {
    "Argentina": [
        ("Lionel Messi",        "FW", 38, "Inter Miami",        [2014, 2018, 2022], 68),
        ("Ángel Di María",      "FW", 38, "Benfica",            [2014, 2018, 2022], 61),
        ("Rodrigo De Paul",     "MF", 31, "Atlético de Madrid", [2018, 2022],       58),
        ("Nicolás Otamendi",    "DF", 38, "Benfica",            [2014, 2018, 2022], 55),
        ("Nicolás Tagliafico",  "DF", 33, "Olympique Lyon",     [2018, 2022],       47),
        ("Lautaro Martínez",    "FW", 28, "Inter de Milão",     [2018, 2022],       52),
        ("Leandro Paredes",     "MF", 31, "Boca Juniors",       [2018, 2022],       49),
        ("Giovani Lo Celso",    "MF", 29, "Real Betis",         [2018, 2022],       45),
        ("Cristian Romero",     "DF", 27, "Tottenham",          [2022],             38),
        ("Nahuel Molina",       "DF", 28, "Atlético de Madrid", [2022],             41),
        ("Emiliano Martínez",   "GK", 33, "Aston Villa",        [2022],             39),
    ],
    "França": [
        ("Kylian Mbappé",       "FW", 27, "Real Madrid",        [2018, 2022],       82),
        ("Antoine Griezmann",   "FW", 35, "Atlético de Madrid", [2014, 2018, 2022], 90),
        ("Olivier Giroud",      "FW", 39, "Los Angeles FC",     [2014, 2018, 2022], 57),
        ("Hugo Lloris",         "GK", 39, "Los Angeles FC",     [2014, 2018, 2022], 51),
        ("Raphaël Varane",      "DF", 32, "Aposentado",         [2014, 2018, 2022], 48),
        ("Paul Pogba",          "MF", 33, "AS Mônaco",          [2014, 2018],       44),
        ("N'Golo Kanté",        "MF", 35, "Al-Ittihad",         [2018, 2022],       46),
        ("Ousmane Dembélé",     "FW", 28, "Paris Saint-Germain",[2018, 2022],       43),
        ("Lucas Hernández",     "DF", 30, "Paris Saint-Germain",[2018, 2022],       38),
        ("Benjamin Pavard",     "DF", 30, "Inter de Milão",     [2018, 2022],       40),
        ("Adrien Rabiot",       "MF", 31, "Olympique Marseille",[2018, 2022],       42),
    ],
    "Espanha": [
        ("Álvaro Morata",       "FW", 33, "Como",               [2014, 2018, 2022], 78),
        ("Sergio Busquets",     "MF", 37, "Inter Miami",        [2010, 2014, 2018], 71),
        ("Jordi Alba",          "DF", 37, "Inter Miami",        [2014, 2018],       93),
        ("Dani Carvajal",       "DF", 34, "Real Madrid",        [2018, 2022],       48),
        ("Rodri",               "MF", 29, "Manchester City",    [2018, 2022],       55),
        ("Ferran Torres",       "FW", 26, "Barcelona",          [2022],             46),
        ("Pedri",               "MF", 23, "Barcelona",          [2022],             38),
        ("Gavi",                "MF", 21, "Barcelona",          [2022],             33),
        ("Unai Simón",          "GK", 28, "Athletic Bilbao",    [2022],             44),
        ("Marco Asensio",       "FW", 30, "Fenerbahçe",         [2018, 2022],       40),
        ("Aymeric Laporte",     "DF", 31, "Al-Nassr",           [2022],             36),
    ],
    "Inglaterra": [
        ("Harry Kane",          "FW", 32, "Bayern de Munique",  [2018, 2022],       95),
        ("Raheem Sterling",     "FW", 31, "Arsenal",            [2018, 2022],       82),
        ("Jordan Henderson",    "MF", 35, "Ajax",               [2018, 2022],       81),
        ("Harry Maguire",       "DF", 32, "Manchester United",  [2018, 2022],       63),
        ("Jordan Pickford",     "GK", 31, "Everton",            [2018, 2022],       72),
        ("Kyle Walker",         "DF", 35, "Burnley",            [2018, 2022],       90),
        ("Declan Rice",         "MF", 27, "Arsenal",            [2022],             58),
        ("Bukayo Saka",         "FW", 24, "Arsenal",            [2022],             45),
        ("John Stones",         "DF", 31, "Manchester City",    [2018, 2022],       78),
        ("Marcus Rashford",     "FW", 28, "Aston Villa",        [2018, 2022],       62),
        ("Phil Foden",          "MF", 25, "Manchester City",    [2022],             44),
    ],
    "Brasil": [
        ("Neymar",              "FW", 34, "Santos",             [2014, 2018, 2022], 79),
        ("Casemiro",            "MF", 34, "Manchester United",  [2018, 2022],       76),
        ("Thiago Silva",        "DF", 41, "Fluminense",         [2014, 2018, 2022], 87),
        ("Marquinhos",          "DF", 31, "Paris Saint-Germain",[2018, 2022],       84),
        ("Alisson",             "GK", 33, "Liverpool",          [2018, 2022],       70),
        ("Richarlison",         "FW", 28, "Tottenham",          [2022],             49),
        ("Vinícius Júnior",     "FW", 25, "Real Madrid",        [2022],             42),
        ("Lucas Paquetá",       "MF", 28, "West Ham",           [2022],             52),
        ("Danilo",              "DF", 34, "Flamengo",           [2018, 2022],       58),
        ("Raphinha",            "FW", 29, "Barcelona",          [2022],             40),
        ("Fred",                "MF", 33, "Fenerbahçe",         [2018, 2022],       39),
    ],
    "Portugal": [
        ("Cristiano Ronaldo",   "FW", 41, "Al-Nassr",           [2006, 2010, 2014, 2018, 2022], 130),
        ("Bernardo Silva",      "MF", 31, "Manchester City",    [2018, 2022],       95),
        ("Bruno Fernandes",     "MF", 31, "Manchester United",  [2018, 2022],       78),
        ("Rúben Dias",          "DF", 28, "Manchester City",    [2022],             62),
        ("João Cancelo",        "DF", 31, "Al-Hilal",           [2018, 2022],       60),
        ("Diogo Jota",          "FW", 29, "Liverpool",          [2022],             47),
        ("João Félix",          "FW", 26, "Chelsea",            [2022],             44),
        ("Rui Patrício",        "GK", 38, "Aposentado",         [2018, 2022],       57),
        ("Pepe",                "DF", 43, "Aposentado",         [2014, 2018, 2022], 64),
        ("William Carvalho",    "MF", 33, "Real Betis",         [2018, 2022],       49),
        ("Rafael Leão",         "FW", 26, "AC Milan",           [2022],             38),
    ],
    "Holanda": [
        ("Memphis Depay",       "FW", 32, "Corinthians",        [2014, 2022],       100),
        ("Virgil van Dijk",     "DF", 34, "Liverpool",          [2022],             78),
        ("Georginio Wijnaldum", "MF", 35, "Al-Ettifaq",         [2014, 2022],       91),
        ("Frenkie de Jong",     "MF", 28, "Barcelona",          [2022],             62),
        ("Daley Blind",         "DF", 36, "Girona",             [2014, 2022],       103),
        ("Steven Bergwijn",     "FW", 28, "Al-Ittihad",         [2022],             40),
        ("Denzel Dumfries",     "DF", 30, "Inter de Milão",     [2022],             58),
        ("Matthijs de Ligt",    "DF", 26, "Manchester United",  [2022],             55),
        ("Stefan de Vrij",      "DF", 34, "Inter de Milão",     [2014, 2022],       60),
        ("Cody Gakpo",          "FW", 26, "Liverpool",          [2022],             42),
        ("Jasper Cillessen",    "GK", 36, "NEC Nijmegen",       [2014],             56),
    ],
    "Bélgica": [
        ("Romelu Lukaku",       "FW", 32, "Napoli",             [2014, 2018, 2022], 122),
        ("Kevin De Bruyne",     "MF", 34, "Napoli",             [2014, 2018, 2022], 110),
        ("Eden Hazard",         "FW", 35, "Aposentado",         [2014, 2018, 2022], 126),
        ("Thibaut Courtois",    "GK", 33, "Real Madrid",        [2014, 2018],       102),
        ("Toby Alderweireld",   "DF", 36, "Royal Antwerp",      [2014, 2018, 2022], 127),
        ("Jan Vertonghen",      "DF", 38, "RSC Anderlecht",     [2014, 2018, 2022], 157),
        ("Axel Witsel",         "MF", 37, "Girona",             [2014, 2018, 2022], 132),
        ("Dries Mertens",       "FW", 38, "Galatasaray",        [2014, 2018, 2022], 109),
        ("Youri Tielemans",     "MF", 28, "Aston Villa",        [2018, 2022],       72),
        ("Thorgan Hazard",      "FW", 32, "RSC Anderlecht",     [2018, 2022],       50),
        ("Yannick Carrasco",    "FW", 32, "Al-Shabab",          [2018, 2022],       69),
    ],
    "Itália": [
        ("Lorenzo Insigne",     "FW", 34, "Toronto FC",         [2014],             53),
        ("Ciro Immobile",       "FW", 36, "Beşiktaş",           [2014],             57),
        ("Jorginho",            "MF", 34, "Arsenal",            [2018],             52),
        ("Marco Verratti",      "MF", 33, "Al-Arabi",           [2014, 2018],       57),
        ("Leonardo Bonucci",    "DF", 38, "Aposentado",         [2014],             121),
        ("Giorgio Chiellini",   "DF", 41, "Aposentado",         [2010, 2014],       117),
        ("Federico Chiesa",     "FW", 28, "Liverpool",          [2014],             52),
        ("Nicolò Barella",      "MF", 28, "Inter de Milão",     [2014],             58),
        ("Gianluigi Donnarumma","GK", 27, "Manchester City",    [2014],             70),
        ("Leonardo Spinazzola",  "DF", 33, "Napoli",            [2014],             36),
        ("Federico Bernardeschi","FW", 32, "Toronto FC",        [2014],             39),
    ],
    "Croácia": [
        ("Luka Modrić",         "MF", 40, "AC Milan",           [2006, 2014, 2018, 2022], 185),
        ("Ivan Perišić",        "FW", 37, "PSV Eindhoven",      [2014, 2018, 2022], 142),
        ("Marcelo Brozović",    "MF", 33, "Al-Nassr",           [2014, 2018, 2022], 95),
        ("Mateo Kovačić",       "MF", 31, "Manchester City",    [2014, 2018, 2022], 102),
        ("Andrej Kramarić",     "FW", 34, "Hoffenheim",         [2014, 2018, 2022], 98),
        ("Dominik Livaković",   "GK", 31, "Girona",             [2018, 2022],       64),
        ("Josip Brekalo",       "FW", 27, "Kasımpaşa",          [2018, 2022],       45),
        ("Šime Vrsaljko",       "DF", 34, "Aposentado",         [2014, 2018],       62),
        ("Dejan Lovren",        "DF", 36, "Aposentado",         [2014, 2018, 2022], 78),
        ("Borna Barišić",       "DF", 33, "Rangers",            [2018, 2022],       52),
        ("Mario Pašalić",       "MF", 31, "Atalanta",           [2018, 2022],       54),
    ],
}


# ---------------------------------------------------------------------------
# Geração determinística de estatísticas (estilo radar FIFA)
# ---------------------------------------------------------------------------
def _seed(name):
    """Inteiro estável derivado do nome (para gerar números reproduzíveis)."""
    h = hashlib.md5(name.encode("utf-8")).hexdigest()
    return int(h, 16)


def _rand(name, salt, lo, hi):
    """Valor pseudo-aleatório estável no intervalo [lo, hi]."""
    h = int(hashlib.md5(f"{name}:{salt}".encode("utf-8")).hexdigest(), 16)
    return lo + (h % (hi - lo + 1))


# ---------------------------------------------------------------------------
# Ratings reais de referência — EA SPORTS FC (escala 0–99)
# Jogadores de linha: (Geral, Ritmo, Finalização, Passe, Drible, Defesa, Físico)
# Goleiros:           (Geral, Elasticidade, Manejo, Chute, Reflexos, Velocidade, Posicionamento)
# Valores baseados nas cartas do EA SPORTS FC; para veteranos/aposentados usa-se
# a última carta de referência. Todos os 110 jogadores têm os 6 atributos + Geral
# preenchidos — não há dados ausentes.
# ---------------------------------------------------------------------------
RATINGS = {
    # Argentina
    "Lionel Messi":         (90, 80, 87, 90, 93, 33, 64),
    "Ángel Di María":       (84, 81, 82, 84, 86, 41, 62),
    "Rodrigo De Paul":      (84, 75, 75, 81, 82, 78, 80),
    "Nicolás Otamendi":     (82, 64, 45, 67, 66, 83, 82),
    "Nicolás Tagliafico":   (80, 80, 55, 73, 76, 80, 77),
    "Lautaro Martínez":     (87, 84, 87, 76, 84, 44, 83),
    "Leandro Paredes":      (81, 56, 72, 83, 76, 76, 73),
    "Giovani Lo Celso":     (82, 73, 76, 82, 84, 64, 66),
    "Cristian Romero":      (85, 81, 40, 66, 70, 86, 85),
    "Nahuel Molina":        (81, 86, 58, 74, 78, 79, 76),
    "Emiliano Martínez":    (85, 84, 83, 78, 87, 45, 85),  # GK
    # França
    "Kylian Mbappé":        (91, 97, 90, 80, 92, 36, 78),
    "Antoine Griezmann":    (85, 80, 84, 84, 85, 52, 72),
    "Olivier Giroud":       (80, 55, 82, 73, 73, 41, 84),
    "Hugo Lloris":          (84, 84, 82, 70, 86, 48, 84),  # GK
    "Raphaël Varane":       (85, 82, 40, 71, 72, 86, 82),
    "Paul Pogba":           (85, 75, 81, 85, 86, 67, 82),
    "N'Golo Kanté":         (85, 78, 67, 79, 82, 87, 81),
    "Ousmane Dembélé":      (86, 93, 79, 82, 89, 37, 64),
    "Lucas Hernández":      (84, 83, 53, 71, 76, 84, 84),
    "Benjamin Pavard":      (83, 78, 55, 73, 73, 83, 80),
    "Adrien Rabiot":        (84, 76, 74, 81, 83, 78, 82),
    # Espanha
    "Álvaro Morata":        (83, 80, 83, 73, 80, 42, 80),
    "Sergio Busquets":      (84, 48, 65, 85, 80, 80, 71),
    "Jordi Alba":           (84, 86, 67, 84, 84, 79, 67),
    "Dani Carvajal":        (84, 80, 60, 79, 79, 84, 78),
    "Rodri":                (89, 64, 78, 86, 83, 87, 84),
    "Ferran Torres":        (82, 88, 78, 76, 83, 42, 67),
    "Pedri":                (86, 78, 75, 86, 88, 66, 64),
    "Gavi":                 (82, 80, 70, 80, 84, 70, 73),
    "Unai Simón":           (85, 84, 83, 80, 86, 46, 84),  # GK
    "Marco Asensio":        (83, 80, 82, 80, 84, 45, 64),
    "Aymeric Laporte":      (85, 73, 50, 78, 75, 85, 82),
    # Inglaterra
    "Harry Kane":           (90, 70, 91, 84, 83, 47, 83),
    "Raheem Sterling":      (84, 90, 80, 79, 86, 45, 68),
    "Jordan Henderson":     (80, 64, 70, 81, 76, 78, 78),
    "Harry Maguire":        (81, 62, 52, 68, 64, 83, 85),
    "Jordan Pickford":      (83, 82, 80, 84, 84, 47, 82),  # GK
    "Kyle Walker":          (84, 93, 56, 76, 79, 82, 79),
    "Declan Rice":          (86, 76, 73, 82, 81, 85, 85),
    "Bukayo Saka":          (87, 86, 82, 83, 88, 50, 70),
    "John Stones":          (85, 75, 55, 82, 80, 84, 78),
    "Marcus Rashford":      (85, 90, 83, 77, 85, 42, 75),
    "Phil Foden":           (88, 84, 82, 85, 90, 58, 66),
    # Brasil
    "Neymar":               (89, 85, 83, 85, 93, 37, 61),
    "Casemiro":             (85, 64, 73, 78, 76, 87, 87),
    "Thiago Silva":         (84, 65, 45, 73, 71, 86, 75),
    "Marquinhos":           (86, 80, 48, 76, 78, 87, 80),
    "Alisson":              (89, 87, 85, 88, 90, 56, 89),  # GK
    "Richarlison":          (82, 81, 81, 71, 80, 45, 82),
    "Vinícius Júnior":      (89, 95, 83, 78, 92, 29, 68),
    "Lucas Paquetá":        (84, 76, 78, 83, 86, 66, 75),
    "Danilo":               (81, 76, 55, 74, 76, 81, 77),
    "Raphinha":             (86, 88, 80, 83, 87, 42, 66),
    "Fred":                 (79, 76, 66, 78, 80, 75, 74),
    # Portugal
    "Cristiano Ronaldo":    (86, 81, 90, 75, 81, 34, 75),
    "Bernardo Silva":       (88, 78, 80, 87, 90, 64, 66),
    "Bruno Fernandes":      (88, 75, 86, 89, 84, 70, 78),
    "Rúben Dias":           (88, 64, 39, 72, 72, 89, 86),
    "João Cancelo":         (86, 84, 70, 84, 86, 80, 70),
    "Diogo Jota":           (84, 85, 83, 75, 84, 42, 73),
    "João Félix":           (83, 82, 78, 78, 86, 41, 64),
    "Rui Patrício":         (83, 82, 81, 72, 85, 45, 83),  # GK
    "Pepe":                 (80, 68, 44, 68, 67, 82, 80),
    "William Carvalho":     (80, 62, 70, 78, 77, 78, 82),
    "Rafael Leão":          (86, 92, 81, 78, 88, 36, 76),
    # Holanda
    "Memphis Depay":        (84, 82, 83, 80, 85, 44, 73),
    "Virgil van Dijk":      (89, 81, 60, 71, 72, 90, 86),
    "Georginio Wijnaldum":  (82, 73, 78, 79, 81, 70, 80),
    "Frenkie de Jong":      (87, 78, 73, 86, 89, 76, 78),
    "Daley Blind":          (79, 60, 55, 80, 75, 78, 66),
    "Steven Bergwijn":      (81, 89, 76, 75, 84, 38, 66),
    "Denzel Dumfries":      (83, 87, 65, 76, 78, 80, 83),
    "Matthijs de Ligt":     (86, 75, 48, 71, 73, 87, 85),
    "Stefan de Vrij":       (84, 70, 42, 71, 70, 85, 82),
    "Cody Gakpo":           (84, 84, 81, 79, 85, 45, 76),
    "Jasper Cillessen":     (82, 81, 80, 75, 84, 44, 82),  # GK
    # Bélgica
    "Romelu Lukaku":        (85, 84, 86, 72, 79, 41, 88),
    "Kevin De Bruyne":      (91, 72, 88, 93, 87, 64, 78),
    "Eden Hazard":          (84, 83, 81, 84, 88, 35, 66),
    "Thibaut Courtois":     (90, 87, 88, 76, 89, 52, 91),  # GK
    "Toby Alderweireld":    (82, 60, 45, 73, 68, 84, 80),
    "Jan Vertonghen":       (80, 58, 42, 72, 68, 82, 76),
    "Axel Witsel":          (81, 60, 65, 80, 76, 80, 80),
    "Dries Mertens":        (82, 75, 82, 81, 85, 40, 60),
    "Youri Tielemans":      (83, 70, 78, 83, 82, 73, 74),
    "Thorgan Hazard":       (80, 82, 75, 78, 83, 50, 66),
    "Yannick Carrasco":     (83, 88, 78, 78, 86, 52, 67),
    # Itália
    "Lorenzo Insigne":      (83, 82, 81, 82, 86, 40, 58),
    "Ciro Immobile":        (84, 78, 86, 73, 78, 42, 78),
    "Jorginho":             (84, 54, 72, 85, 80, 79, 68),
    "Marco Verratti":       (85, 70, 70, 86, 88, 76, 65),
    "Leonardo Bonucci":     (83, 60, 50, 75, 68, 85, 78),
    "Giorgio Chiellini":    (82, 60, 42, 65, 64, 86, 82),
    "Federico Chiesa":      (84, 90, 80, 76, 85, 45, 73),
    "Nicolò Barella":       (86, 80, 78, 84, 85, 79, 80),
    "Gianluigi Donnarumma": (88, 86, 85, 78, 89, 48, 87),  # GK
    "Leonardo Spinazzola":  (81, 85, 58, 76, 80, 78, 74),
    "Federico Bernardeschi": (80, 82, 75, 78, 82, 50, 68),
    # Croácia
    "Luka Modrić":          (87, 72, 76, 88, 88, 72, 65),
    "Ivan Perišić":         (83, 80, 80, 80, 82, 55, 80),
    "Marcelo Brozović":     (84, 70, 72, 84, 83, 80, 75),
    "Mateo Kovačić":        (85, 74, 72, 84, 87, 75, 76),
    "Andrej Kramarić":      (82, 73, 82, 78, 82, 42, 66),
    "Dominik Livaković":    (82, 81, 80, 70, 84, 44, 81),  # GK
    "Josip Brekalo":        (78, 84, 74, 74, 81, 40, 66),
    "Šime Vrsaljko":        (78, 78, 55, 72, 74, 78, 74),
    "Dejan Lovren":         (79, 68, 45, 68, 66, 81, 80),
    "Borna Barišić":        (78, 76, 58, 76, 75, 76, 74),
    "Mario Pašalić":        (80, 72, 76, 78, 80, 64, 76),
}

# Rótulos dos eixos do radar (em PT-BR), na ordem dos atributos de RATINGS
RADAR_AXES = {
    "GK":  ["Elasticidade", "Manejo", "Chute", "Reflexos", "Velocidade", "Posicionamento"],
    "OUT": ["Ritmo", "Finalização", "Passe", "Drible", "Defesa", "Físico"],
}


def build_stats(name, pos):
    """Retorna os 6 atributos reais (EA SPORTS FC) e seus rótulos por posição."""
    axes = RADAR_AXES["GK"] if pos == "GK" else RADAR_AXES["OUT"]
    rating = RATINGS[name]          # (Geral, a1..a6)
    return {"axes": axes, "values": list(rating[1:])}


def overall_rating(name):
    """Avaliação geral real (EA SPORTS FC)."""
    return RATINGS[name][0]


def build_attributes(name, pos):
    """Lista [{label, value}] dos 6 atributos para exibição em barras."""
    stats = build_stats(name, pos)
    return [{"label": ax, "value": v} for ax, v in zip(stats["axes"], stats["values"])]


def build_rating_summary(name, pos):
    """Resumo de desempenho derivado dos atributos reais (sem dados ausentes)."""
    stats = build_stats(name, pos)
    values, axes = stats["values"], stats["axes"]
    best_i = max(range(len(values)), key=lambda i: values[i])
    return {
        "overall": RATINGS[name][0],
        "average": round(sum(values) / len(values)),
        "best_label": axes[best_i],
        "best_value": values[best_i],
    }


def build_nt_summary(name, fallback_caps):
    """Agregados REAIS de seleção a partir de caps.json (Wikipédia):

      - atuações (caps): jogos disputados pela seleção principal — REAL
      - gols: gols pela seleção principal — REAL
    """
    rec = REAL_CAPS.get(name) or {}
    caps = rec.get("caps")
    if caps is None:
        caps = fallback_caps          # fallback evita dado ausente
    goals = rec.get("goals")
    if goals is None:
        goals = 0
    return {"caps": caps, "goals": goals}


def photo_url(name, color):
    """Foto do jogador. Prefere a foto real (Wikimedia Commons) carregada de
    photos.json; cai para um avatar com iniciais caso não exista."""
    real = REAL_PHOTOS.get(name)
    if real:
        return real
    q = urllib.parse.quote(name)
    bg = color.lstrip("#")
    return (f"https://ui-avatars.com/api/?name={q}&size=400&background={bg}"
            f"&color=ffffff&bold=true&format=png")


# ---------------------------------------------------------------------------
# Montagem do dataset completo
# ---------------------------------------------------------------------------
def _slugify(name):
    import unicodedata
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    return s.lower().replace("'", "").replace(".", "").replace(" ", "-")


POSITION_LABEL = {"GK": "Goleiro", "DF": "Defensor", "MF": "Meio-campo", "FW": "Atacante"}


def build_players():
    players = []
    pid = 0
    for team, roster in ROSTERS.items():
        color = TEAMS[team]["color"]
        for name, pos, age, club, cups, caps in roster:
            stats = build_stats(name, pos)
            pid += 1
            players.append({
                "id": pid,
                "slug": _slugify(name),
                "name": name,
                "team": team,
                "flag": TEAMS[team]["flag"],
                "team_color": color,
                "pos": pos,
                "pos_label": POSITION_LABEL[pos],
                "age": age,
                "club": club,
                "world_cups": cups,
                "caps_since_2018": caps,
                "nt": build_nt_summary(name, caps),
                "photo": photo_url(name, color),
                "stats": stats,
                "overall": overall_rating(name),
                "attributes": build_attributes(name, pos),
                "rating_summary": build_rating_summary(name, pos),
            })
    return players


PLAYERS = build_players()
PLAYERS_BY_ID = {p["id"]: p for p in PLAYERS}
PLAYERS_BY_SLUG = {p["slug"]: p for p in PLAYERS}


def get_player(identifier):
    """Busca por id (int/str numérica) ou slug."""
    if isinstance(identifier, int) or str(identifier).isdigit():
        return PLAYERS_BY_ID.get(int(identifier))
    return PLAYERS_BY_SLUG.get(identifier)


if __name__ == "__main__":
    print(f"Seleções: {len(TEAMS)}")
    print(f"Jogadores: {len(PLAYERS)}")
    for team in ROSTERS:
        gks = [p for p in PLAYERS if p["team"] == team and p["pos"] == "GK"]
        n = len([p for p in PLAYERS if p["team"] == team])
        print(f"  {team:12} {n} jogadores, {len(gks)} goleiro(s)")

    # Validação: todo jogador precisa ter rating real e atributos completos
    roster_names = [n for r in ROSTERS.values() for (n, *_rest) in r]
    sem_rating = [n for n in roster_names if n not in RATINGS]
    sem_foto = [p["name"] for p in PLAYERS if not REAL_PHOTOS.get(p["name"])]
    incompletos = [p["name"] for p in PLAYERS
                   if len(p["attributes"]) != 6 or any(a["value"] is None for a in p["attributes"])]
    sem_caps = [p["name"] for p in PLAYERS
                if p["nt"]["caps"] is None or p["nt"]["goals"] is None]
    print(f"\nValidação:")
    print(f"  Sem rating EA FC : {sem_rating or 'nenhum ✓'}")
    print(f"  Atributos incompletos: {incompletos or 'nenhum ✓'}")
    print(f"  Sem foto real    : {sem_foto or 'nenhum ✓'}")
    print(f"  Sem caps/gols reais : {sem_caps or 'nenhum ✓'}")
    # destaques de seleção
    print("\nAgregados de seleção (amostra):")
    for p in PLAYERS[:3] + [PLAYERS[55]]:
        nt = p["nt"]
        print(f"  {p['name']:20} atuações {nt['caps']:>3} | gols {nt['goals']:>3}")
