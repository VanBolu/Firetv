import urllib.request
from urllib.parse import urljoin
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from difflib import SequenceMatcher
import re
import unicodedata


# ============================================================
# ÇIKTI DOSYALARI
# ============================================================

TURKEY_OUTPUT = Path("Turkiye.m3u")
WORLD_OUTPUT = Path("Dunya.m3u")
HOTBIRD_OUTPUT = Path("Hotbird.m3u")
ASTRA_OUTPUT = Path("Astra.m3u")

TARGET_HEIGHT = 1080


# ============================================================
# KAYNAKLAR
# ============================================================

FAMELACK_M3U = (
    "https://raw.githubusercontent.com/"
    "DEvmIb/famelack-channels-m3u/main/m3u/_all.m3u"
)

TURKEY_SOURCES = [
    (
        "iptv-org",
        "https://raw.githubusercontent.com/"
        "iptv-org/iptv/master/streams/tr.m3u",
        100,
    ),
    (
        "discevisita",
        "https://raw.githubusercontent.com/"
        "discevisita/iptv/main/tr.m3u",
        90,
    ),
    (
        "suphero",
        "https://raw.githubusercontent.com/"
        "suphero/IPTV/master/TR.m3u8",
        70,
    ),
]


# ============================================================
# KINGOFSAT - FTA UYDU LİSTELERİ
# ============================================================

ASTRA_KINGOFSAT = (
    "https://en.kingofsat.net/"
    "tv.php?filtre=Clear&ordre=freq&pos=19.2E"
)

HOTBIRD_KINGOFSAT = (
    "https://en.kingofsat.net/"
    "tv.php?filtre=Clear&ordre=freq&pos=13E"
)


# ============================================================
# TÜRKİYE YEDEKLERİ
# ============================================================

FALLBACKS = {

    "SHOWTVTR": [
        (
            "Show TV",
            "https://ciner-live.daioncdn.net/showtv/showtv.m3u8",
            0,
        ),
        (
            "Show TV",
            "https://ciner.daioncdn.net/showtv/showtv.m3u8"
            "?ce=3&app=4bc856ef-4c68-4a94-bc87-37dfaaa66558",
            0,
        ),
    ],

    "STARTVTR": [
        (
            "Star TV",
            "https://dogus.daioncdn.net/"
            "startv/startv_720p.m3u8"
            "?app=a20ac41e-bdc3-4aa1-934d-26b484480ac9&ce=3",
            720,
        ),
    ],

    "KANALDTR": [
        (
            "Kanal D",
            "https://demiroren.daioncdn.net/"
            "kanald/kanald.m3u8?app=kanald_web&ce=3",
            1080,
        ),
    ],

    "TV8TR": [
        (
            "TV8",
            "https://rkhubpaomb.turknet.ercdn.net/"
            "fwjkgpasof/tv8/tv8_1080p.m3u8",
            1080,
        ),
        (
            "TV8",
            "https://tv8.daioncdn.net/tv8/tv8.m3u8"
            "?app=7ddc255a-ef47-4e81-ab14-c0e5f2949788&ce=3",
            1080,
        ),
    ],

    "ATVTR": [
        (
            "ATV",
            "https://rnttwmjcin.turknet.ercdn.net/"
            "lcpmvefbyo/atv/atv_1080p.m3u8",
            1080,
        ),
    ],

    "NOWTVTR": [
        (
            "NOW",
            "https://uycyyuuzyh.turknet.ercdn.net/"
            "nphindgytw/nowtv/nowtv.m3u8",
            720,
        ),
    ],

    "HABERTURKTVTR": [
        (
            "Habertürk",
            "https://rmtftbjlne.turknet.ercdn.net/"
            "bpeytmnqyp/haberturktv/haberturktv_1080p.m3u8",
            1080,
        ),
        (
            "Habertürk",
            "https://tv.ensonhaber.com/"
            "haberturk/haberturk.m3u8",
            720,
        ),
    ],

    "BLOOMBERGHTTR": [
        (
            "Bloomberg HT",
            "https://ciner-live.daioncdn.net/"
            "bloomberght/bloomberght.m3u8",
            0,
        ),
    ],

    "CNNTURKTR": [
        (
            "CNN Türk",
            "https://mn-nl.mncdn.com/"
            "blutv_cnnturk/"
            "smil:cnnturk_sd.smil/playlist.m3u8",
            480,
        ),
    ],

    "AHABERTR": [
        (
            "A Haber",
            "https://rnttwmjcin.turknet.ercdn.net/"
            "lcpmvefbyo/ahaber/ahaber_1080p.m3u8",
            1080,
        ),
    ],

    "ASPORTR": [
        (
            "A Spor",
            "https://rnttwmjcin.turknet.ercdn.net/"
            "lcpmvefbyo/aspor/aspor_1080p.m3u8",
            1080,
        ),
    ],

    "TRT1TR": [
        (
            "TRT 1",
            "https://tv-trt1.medya.trt.com.tr/master.m3u8",
            1440,
        ),
    ],

    "TRTHABERTR": [
        (
            "TRT Haber",
            "https://tv-trthaber.medya.trt.com.tr/master.m3u8",
            1080,
        ),
    ],

    "TRTSPORTR": [
        (
            "TRT Spor",
            "https://tv-trtspor1.medya.trt.com.tr/master.m3u8",
            1080,
        ),
    ],

    "TRTCOCUKTR": [
        (
            "TRT Çocuk",
            "https://tv-trtcocuk.medya.trt.com.tr/master.m3u8",
            1440,
        ),
    ],

    "TRTBELGESELTR": [
        (
            "TRT Belgesel",
            "https://tv-trtbelgesel.medya.trt.com.tr/master.m3u8",
            1080,
        ),
    ],
}


# ============================================================
# ŞİFRELİ / PAY-TV
# ============================================================

BLOCKED_WORDS = [
    "BEIN",
    "S SPORT",
    "S-SPORT",
    "DIGITURK",
    "D-SMART",
    "D SMART",
    "TIVIBU",
    "MOVIESMART",
    "MOVIE SMART",
    "SMART SPOR",
]


# ============================================================
# ÜLKE İSİMLERİ
# ============================================================

COUNTRIES = {
    "tr": "🇹🇷 Türkiye",
    "de": "🇩🇪 Almanya",
    "at": "🇦🇹 Avusturya",
    "ch": "🇨🇭 İsviçre",
    "fr": "🇫🇷 Fransa",
    "it": "🇮🇹 İtalya",
    "es": "🇪🇸 İspanya",
    "pt": "🇵🇹 Portekiz",
    "gb": "🇬🇧 Birleşik Krallık",
    "ie": "🇮🇪 İrlanda",
    "us": "🇺🇸 ABD",
    "ca": "🇨🇦 Kanada",
    "mx": "🇲🇽 Meksika",
    "br": "🇧🇷 Brezilya",
    "ar": "🇦🇷 Arjantin",
    "cl": "🇨🇱 Şili",
    "co": "🇨🇴 Kolombiya",
    "nl": "🇳🇱 Hollanda",
    "be": "🇧🇪 Belçika",
    "gr": "🇬🇷 Yunanistan",
    "cy": "🇨🇾 Kıbrıs",
    "pl": "🇵🇱 Polonya",
    "cz": "🇨🇿 Çekya",
    "sk": "🇸🇰 Slovakya",
    "hu": "🇭🇺 Macaristan",
    "ro": "🇷🇴 Romanya",
    "bg": "🇧🇬 Bulgaristan",
    "hr": "🇭🇷 Hırvatistan",
    "rs": "🇷🇸 Sırbistan",
    "si": "🇸🇮 Slovenya",
    "ba": "🇧🇦 Bosna-Hersek",
    "al": "🇦🇱 Arnavutluk",
    "mk": "🇲🇰 Kuzey Makedonya",
    "ua": "🇺🇦 Ukrayna",
    "ru": "🇷🇺 Rusya",
    "se": "🇸🇪 İsveç",
    "no": "🇳🇴 Norveç",
    "dk": "🇩🇰 Danimarka",
    "fi": "🇫🇮 Finlandiya",
    "is": "🇮🇸 İzlanda",
    "az": "🇦🇿 Azerbaycan",
    "ge": "🇬🇪 Gürcistan",
    "am": "🇦🇲 Ermenistan",
    "il": "🇮🇱 İsrail",
    "lb": "🇱🇧 Lübnan",
    "jo": "🇯🇴 Ürdün",
    "iq": "🇮🇶 Irak",
    "ir": "🇮🇷 İran",
    "sa": "🇸🇦 Suudi Arabistan",
    "ae": "🇦🇪 BAE",
    "qa": "🇶🇦 Katar",
    "eg": "🇪🇬 Mısır",
    "ma": "🇲🇦 Fas",
    "dz": "🇩🇿 Cezayir",
    "tn": "🇹🇳 Tunus",
    "za": "🇿🇦 Güney Afrika",
    "in": "🇮🇳 Hindistan",
    "pk": "🇵🇰 Pakistan",
    "bd": "🇧🇩 Bangladeş",
    "cn": "🇨🇳 Çin",
    "jp": "🇯🇵 Japonya",
    "kr": "🇰🇷 Güney Kore",
    "th": "🇹🇭 Tayland",
    "vn": "🇻🇳 Vietnam",
    "id": "🇮🇩 Endonezya",
    "my": "🇲🇾 Malezya",
    "sg": "🇸🇬 Singapur",
    "ph": "🇵🇭 Filipinler",
    "au": "🇦🇺 Avustralya",
    "nz": "🇳🇿 Yeni Zelanda",
}


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/151 Safari/537.36"
    ),
    "Accept": "*/*",
}


# ============================================================
# NORMALIZE
# ============================================================

def normalize(text):
    text = text.upper()

    replacements = {
        "İ": "I",
        "Ş": "S",
        "Ğ": "G",
        "Ü": "U",
        "Ö": "O",
        "Ç": "C",
        "ß": "SS",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = unicodedata.normalize("NFKD", text)

    text = "".join(
        c for c in text
        if not unicodedata.combining(c)
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def match_name(text):
    text = normalize(text)

    text = re.sub(
        r"\([^)]*\)",
        "",
        text
    )

    text = re.sub(
        r"\[[^\]]*\]",
        "",
        text
    )

    text = re.sub(
        r"\bHD\b|\bSD\b|\bUHD\b|\b4K\b",
        "",
        text
    )

    text = re.sub(
        r"\bGERMANY\b|\bITALIA\b|\bITALY\b",
        "",
        text
    )

    text = re.sub(
        r"[^A-Z0-9]+",
        " ",
        text
    )

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


# ============================================================
# DOWNLOAD
# ============================================================

def download(url, timeout=25):
    req = urllib.request.Request(
        url,
        headers=HEADERS
    )

    with urllib.request.urlopen(
        req,
        timeout=timeout
    ) as response:

        return response.read().decode(
            "utf-8",
            errors="replace"
        )


# ============================================================
# M3U
# ============================================================

def parse_entries(text, source="", score=0):
    lines = text.splitlines()
    result = []

    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if not line.startswith("#EXTINF"):
            i += 1
            continue

        info = line
        j = i + 1

        while (
            j < len(lines)
            and lines[j].strip().startswith("#")
        ):
            j += 1

        if j >= len(lines):
            break

        url = lines[j].strip()

        if url.startswith(("http://", "https://")):
            result.append({
                "info": info,
                "url": url,
                "source": source,
                "source_score": score,
            })

        i = j + 1

    return result


def channel_name(info):
    if "," in info:
        return info.split(",", 1)[1].strip()

    return ""


def tvg_id(info):
    m = re.search(
        r'tvg-id="([^"]*)"',
        info,
        re.IGNORECASE
    )

    return (
        m.group(1).strip()
        if m
        else ""
    )


def replace_group(info, group):
    if 'group-title="' in info:
        return re.sub(
            r'group-title="[^"]*"',
            f'group-title="{group}"',
            info
        )

    return info.replace(
        "#EXTINF:-1",
        f'#EXTINF:-1 group-title="{group}"',
        1
    )


# ============================================================
# FAMELACK ÜLKE
# ============================================================

def famelack_country(info):
    m = re.search(
        r'group-title="famelack \(([^)]+)\) \[([^\]]+)\]',
        info,
        re.IGNORECASE
    )

    if not m:
        return None

    return m.group(2).lower().strip()


# ============================================================
# KINGOFSAT HTML PARSER
# ============================================================

class TableParser(HTMLParser):

    def __init__(self):
        super().__init__()

        self.rows = []
        self.current_row = []
        self.current_cell = []
        self.in_row = False
        self.in_cell = False

    def handle_starttag(self, tag, attrs):

        if tag == "tr":
            self.in_row = True
            self.current_row = []

        elif tag in ("td", "th") and self.in_row:
            self.in_cell = True
            self.current_cell = []

    def handle_data(self, data):

        if self.in_cell:
            self.current_cell.append(data)

    def handle_endtag(self, tag):

        if tag in ("td", "th") and self.in_cell:

            text = " ".join(
                self.current_cell
            )

            text = re.sub(
                r"\s+",
                " ",
                text
            ).strip()

            self.current_row.append(
                text
            )

            self.in_cell = False

        elif tag == "tr" and self.in_row:

            if self.current_row:
                self.rows.append(
                    self.current_row
                )

            self.in_row = False


def kingofsat_fta_names(url):

    print(
        "KingOfSat indiriliyor:",
        url
    )

    html = download(
        url,
        timeout=30
    )

    parser = TableParser()
    parser.feed(html)

    names = set()

    for row in parser.rows:

        clean_row = [
            re.sub(r"\s+", " ", x).strip()
            for x in row
        ]

        for index, cell in enumerate(clean_row):

            enc = normalize(cell)

            if enc not in (
                "FTA",
                "CLEAR",
                "FREE",
                "FREE TO AIR",
                "FREI",
            ):
                continue

            # KingOfSat tablosunda:
            # Name | Country | Category | Packages | Encryption
            # Dolayısıyla Encryption'dan 4 hücre gerisi kanal adı.
            if index >= 4:

                name = clean_row[index - 4]

                if (
                    name
                    and len(name) >= 2
                    and normalize(name)
                    not in (
                        "NAME",
                        "CHANNEL",
                        "CHANNEL NAME",
                    )
                ):
                    names.add(name)

    print(
        "KingOfSat FTA kanal adı:",
        len(names)
    )

    return names


# ============================================================
# TÜRKİYE
# ============================================================

def turkey_group(name):
    n = normalize(name)

    if any(x in n for x in [
        "TRT COCUK",
        "MINIKA",
        "CARTOON",
        "COCUK",
    ]):
        return "Türkiye • Çocuk"

    if any(x in n for x in [
        "TRT SPOR",
        "A SPOR",
        "HT SPOR",
        "TJK",
        "SPOR",
    ]):
        return "Türkiye • Spor"

    if any(x in n for x in [
        "TRT HABER",
        "A HABER",
        "CNN TURK",
        "HABERTURK",
        "NTV",
        "TGRT HABER",
        "HABER GLOBAL",
        "HALK TV",
        "BLOOMBERG HT",
        "TV100",
        "TVNET",
        "24 TV",
        "FLASH HABER",
        "ULUSAL KANAL",
        "SOZCU",
    ]):
        return "Türkiye • Haber"

    if any(x in n for x in [
        "TRT BELGESEL",
        "DMAX",
        "TLC",
        "BELGESEL",
    ]):
        return "Türkiye • Belgesel"

    if any(x in n for x in [
        "TRT MUZIK",
        "KRAL",
        "NUMBER1",
        "POWER TURK",
        "DREAM TURK",
        "MUZIK",
    ]):
        return "Türkiye • Müzik"

    if any(x in n for x in [
        "TRT 1",
        "ATV",
        "KANAL D",
        "SHOW TV",
        "STAR TV",
        "NOW",
        "TV8",
        "KANAL 7",
        "BEYAZ TV",
        "TEVE2",
        "A2",
        "360",
    ]):
        return "Türkiye • Ulusal"

    return "Türkiye • Diğer"


def rejected(info):
    n = normalize(info)

    if "GEO-BLOCKED" in n:
        return True

    if "NOT 24/7" in n:
        return True

    for word in BLOCKED_WORDS:
        if normalize(word) in n:
            return True

    return False


def resolution_score(info):
    m = re.search(
        r"\((\d{3,4})P\)",
        info.upper()
    )

    if m:
        return int(
            m.group(1)
        )

    if "4K" in info.upper():
        return 2160

    return 0


def clean_identity(info):
    tid = tvg_id(info)

    if tid:

        tid = tid.split("@")[0]

        return re.sub(
            r"[^A-Z0-9]",
            "",
            normalize(tid)
        )

    return re.sub(
        r"[^A-Z0-9]",
        "",
        normalize(
            channel_name(info)
        )
    )


def resolve_variant(url):

    try:
        text = download(
            url,
            timeout=8
        )

        if "#EXTM3U" not in text:
            return None, 0

        lines = text.splitlines()
        variants = []

        for i, line in enumerate(lines):

            if not line.startswith(
                "#EXT-X-STREAM-INF:"
            ):
                continue

            res = re.search(
                r"RESOLUTION=(\d+)x(\d+)",
                line,
                re.IGNORECASE
            )

            bw = re.search(
                r"BANDWIDTH=(\d+)",
                line,
                re.IGNORECASE
            )

            height = (
                int(res.group(2))
                if res
                else 0
            )

            bandwidth = (
                int(bw.group(1))
                if bw
                else 0
            )

            j = i + 1

            while (
                j < len(lines)
                and (
                    not lines[j].strip()
                    or lines[j].startswith("#")
                )
            ):
                j += 1

            if j >= len(lines):
                continue

            variants.append({
                "url": urljoin(
                    url,
                    lines[j].strip()
                ),
                "height": height,
                "bandwidth": bandwidth,
            })

        if not variants:
            return url, 0

        exact = [
            v for v in variants
            if v["height"] == TARGET_HEIGHT
        ]

        if exact:

            exact.sort(
                key=lambda v: v["bandwidth"],
                reverse=True
            )

            return (
                exact[0]["url"],
                exact[0]["height"]
            )

        lower = [
            v for v in variants
            if 0 < v["height"] < TARGET_HEIGHT
        ]

        if lower:

            lower.sort(
                key=lambda v: (
                    v["height"],
                    v["bandwidth"]
                ),
                reverse=True
            )

            return (
                lower[0]["url"],
                lower[0]["height"]
            )

        higher = [
            v for v in variants
            if v["height"] > TARGET_HEIGHT
        ]

        if higher:

            higher.sort(
                key=lambda v: (
                    v["height"],
                    v["bandwidth"]
                ),
                reverse=True
            )

            return (
                higher[0]["url"],
                higher[0]["height"]
            )

        variants.sort(
            key=lambda v: v["bandwidth"],
            reverse=True
        )

        return (
            variants[0]["url"],
            0
        )

    except Exception:

        return None, 0


def stream_works(url):

    try:
        text = download(
            url,
            timeout=8
        )

        return "#EXTM3U" in text

    except Exception:
        return False


# ============================================================
# TÜRKİYE KAYNAKLARI
# ============================================================

turkey_candidates = []


for source, url, score in TURKEY_SOURCES:

    try:

        print(
            "Türkiye kaynağı:",
            source
        )

        text = download(url)

        turkey_candidates.extend(
            parse_entries(
                text,
                source,
                score
            )
        )

    except Exception as error:

        print(
            source,
            "alınamadı:",
            error
        )


for identity, alternatives in FALLBACKS.items():

    for name, url, resolution in alternatives:

        turkey_candidates.append({
            "info": (
                f'#EXTINF:-1 '
                f'tvg-id="{identity}" '
                f'group-title="{turkey_group(name)}",'
                f'{name}'
            ),
            "url": url,
            "source": "fallback",
            "source_score": 95,
            "forced_resolution": resolution,
        })


def analyze_turkey(entry):

    if rejected(
        entry["info"]
    ):
        return None

    identity = clean_identity(
        entry["info"]
    )

    name = channel_name(
        entry["info"]
    )

    advertised = entry.get(
        "forced_resolution",
        resolution_score(
            entry["info"]
        )
    )

    # Show TV master kalsın.
    if identity == "SHOWTVTR":

        if not stream_works(
            entry["url"]
        ):
            return None

        fixed_url = entry["url"]
        real_res = advertised

    else:

        fixed_url, found_res = resolve_variant(
            entry["url"]
        )

        if not fixed_url:
            return None

        if not stream_works(
            fixed_url
        ):
            return None

        real_res = (
            found_res
            if found_res
            else advertised
        )

    return {
        "identity": identity,
        "name": name,
        "info": entry["info"],
        "url": fixed_url,
        "resolution": real_res,
        "source_score": entry["source_score"],
        "source": entry["source"],
    }


turkey_usable = []


with ThreadPoolExecutor(
    max_workers=12
) as executor:

    futures = [
        executor.submit(
            analyze_turkey,
            entry
        )
        for entry in turkey_candidates
    ]

    for future in as_completed(
        futures
    ):

        result = future.result()

        if result:
            turkey_usable.append(
                result
            )


by_identity = {}


for entry in turkey_usable:

    entry["rank"] = (
        entry["resolution"] * 100
        + entry["source_score"]
    )

    by_identity.setdefault(
        entry["identity"],
        []
    ).append(entry)


turkey_selected = []


for identity, alternatives in by_identity.items():

    alternatives.sort(
        key=lambda x: x["rank"],
        reverse=True
    )

    winner = alternatives[0]

    winner["info"] = replace_group(
        winner["info"],
        turkey_group(
            winner["name"]
        )
    )

    turkey_selected.append(
        winner
    )


turkey_selected.sort(
    key=lambda x: (
        turkey_group(x["name"]),
        normalize(x["name"])
    )
)


turkey_output = [
    "#EXTM3U"
]


for entry in turkey_selected:

    turkey_output.extend([
        entry["info"],
        entry["url"]
    ])


TURKEY_OUTPUT.write_text(
    "\n".join(
        turkey_output
    ) + "\n",
    encoding="utf-8"
)


# ============================================================
# DÜNYA
# ============================================================

print(
    "Dünya listesi indiriliyor..."
)

famelack_text = download(
    FAMELACK_M3U
)

world_entries = parse_entries(
    famelack_text,
    "famelack",
    50
)


world_output = [
    "#EXTM3U"
]

world_seen = set()


for entry in world_entries:

    info = entry["info"]
    url = entry["url"]

    if url in world_seen:
        continue

    code = famelack_country(
        info
    )

    if code == "tr":
        continue

    if code:
        group = COUNTRIES.get(
            code,
            "🌍 " + code.upper()
        )
    else:
        group = "🌍 Diğer"

    world_output.extend([
        replace_group(
            info,
            group
        ),
        url
    ])

    world_seen.add(
        url
    )


WORLD_OUTPUT.write_text(
    "\n".join(
        world_output
    ) + "\n",
    encoding="utf-8"
)


# ============================================================
# KINGOFSAT FTA LİSTELERİ
# ============================================================

try:

    astra_fta_names = kingofsat_fta_names(
        ASTRA_KINGOFSAT
    )

except Exception as error:

    print(
        "Astra KingOfSat hatası:",
        error
    )

    astra_fta_names = set()


try:

    hotbird_fta_names = kingofsat_fta_names(
        HOTBIRD_KINGOFSAT
    )

except Exception as error:

    print(
        "Hotbird KingOfSat hatası:",
        error
    )

    hotbird_fta_names = set()


# ============================================================
# UYDU EŞLEŞTİRME
# ============================================================

def similarity(a, b):

    return SequenceMatcher(
        None,
        a,
        b
    ).ratio()


def satellite_match(
    stream_name,
    satellite_names
):

    stream = match_name(
        stream_name
    )

    if len(stream) < 2:
        return None

    best_name = None
    best_score = 0.0


    for sat_name in satellite_names:

        sat = match_name(
            sat_name
        )

        if len(sat) < 2:
            continue


        # Tam eşleşme
        if stream == sat:
            return sat_name


        # Birinin diğerini içermesi
        if (
            len(stream) >= 4
            and len(sat) >= 4
            and (
                stream in sat
                or sat in stream
            )
        ):

            score = 0.93

        else:

            score = similarity(
                stream,
                sat
            )


        if score > best_score:

            best_score = score
            best_name = sat_name


    # Yanlış eşleşmeleri azaltmak için eşik.
    if best_score >= 0.86:
        return best_name


    return None


# ============================================================
# HOTBIRD / ASTRA OLUŞTURUCU
# ============================================================

def build_satellite_playlist(
    satellite_names,
    group_name,
    output_path
):

    matches = []

    seen_stream_names = set()
    seen_urls = set()


    for entry in world_entries:

        info = entry["info"]
        url = entry["url"]

        name = channel_name(
            info
        )

        if not name:
            continue


        matched_sat_name = satellite_match(
            name,
            satellite_names
        )

        if not matched_sat_name:
            continue


        if url in seen_urls:
            continue


        normalized_name = match_name(
            name
        )

        if normalized_name in seen_stream_names:
            continue


        new_info = replace_group(
            info,
            group_name
        )


        matches.append({
            "info": new_info,
            "url": url,
            "name": name,
            "satellite_name": matched_sat_name,
        })


        seen_urls.add(
            url
        )

        seen_stream_names.add(
            normalized_name
        )


    matches.sort(
        key=lambda x: normalize(
            x["name"]
        )
    )


    output = [
        "#EXTM3U"
    ]


    for item in matches:

        output.extend([
            item["info"],
            item["url"]
        ])


    output_path.write_text(
        "\n".join(
            output
        ) + "\n",
        encoding="utf-8"
    )


    return matches


hotbird_matches = build_satellite_playlist(
    hotbird_fta_names,
    "Hotbird 13°E",
    HOTBIRD_OUTPUT
)


astra_matches = build_satellite_playlist(
    astra_fta_names,
    "Astra 19.2°E",
    ASTRA_OUTPUT
)


# ============================================================
# RAPOR
# ============================================================

print(
    "--------------------------------"
)

print(
    "TAMAMLANDI"
)

print(
    "--------------------------------"
)

print(
    "Turkiye:",
    len(turkey_selected)
)

print(
    "Dunya:",
    len(world_seen)
)

print(
    "KingOfSat Hotbird FTA:",
    len(hotbird_fta_names)
)

print(
    "Hotbird internet yayını eşleşen:",
    len(hotbird_matches)
)

print(
    "KingOfSat Astra FTA:",
    len(astra_fta_names)
)

print(
    "Astra internet yayını eşleşen:",
    len(astra_matches)
)

print(
    "--------------------------------"
)

print(
    "Dosya:",
    TURKEY_OUTPUT
)

print(
    "Dosya:",
    WORLD_OUTPUT
)

print(
    "Dosya:",
    HOTBIRD_OUTPUT
)

print(
    "Dosya:",
    ASTRA_OUTPUT
)
