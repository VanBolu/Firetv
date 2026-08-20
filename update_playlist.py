import urllib.request
from urllib.parse import urljoin
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
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
# TÜRKİYE YEDEK KAYNAKLARI
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
            "https://tv.ensonhaber.com/haberturk/haberturk.m3u8",
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
            "blutv_cnnturk/smil:cnnturk_sd.smil/playlist.m3u8",
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
    "SKY SPORT",
    "SKY CINEMA",
    "CANAL+",
    "CANAL PLUS",
    "POLsat SPORT PREMIUM",
]


# ============================================================
# DÜNYA ÜLKE İSİMLERİ
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


# ============================================================
# ASTRA 19.2E
#
# FTA / serbest yayın tarafında sık görülen kanallar.
# Stream mevcutsa Astra.m3u'ya girer.
# ============================================================

ASTRA_CHANNELS = [
    "DAS ERSTE",
    "ARD",
    "ZDF",
    "ZDF NEO",
    "ZDF INFO",
    "3SAT",
    "ARTE",
    "PHOENIX",
    "ONE",
    "TAGESSCHAU24",
    "ARD ALPHA",

    "BR FERNSEHEN",
    "HR FERNSEHEN",
    "MDR",
    "NDR",
    "RBB",
    "SWR",
    "WDR",

    "SAT.1",
    "SAT1",
    "PROSIEBEN",
    "PRO 7",
    "KABEL EINS",
    "KABEL1",

    "RTL",
    "RTL ZWEI",
    "RTL2",
    "VOX",
    "SUPER RTL",
    "NITRO",
    "RTL UP",

    "N-TV",
    "NTV DE",
    "WELT",

    "SPORT1",
    "EUROSPORT 1",

    "SERVUS TV",
    "SERVUSTV",
    "ORF 1",
    "ORF 2",
    "ORF III",

    "PULS 4",
    "ATV2",

    "SRF INFO",

    "DELUXE MUSIC",
    "SCHLAGER DELUXE",
    "MTV",

    "QVC",
    "HSE",
    "HSE24",

    "BIBEL TV",
    "K-TV",
]


# ============================================================
# HOTBIRD 13E
#
# FTA / açık yayınlarda sık görülen uluslararası kanallar.
# ============================================================

HOTBIRD_CHANNELS = [
    "TVP POLONIA",
    "TV POLONIA",
    "TVP INFO",
    "TVP WORLD",

    "POLONIA 1",
    "TELE 5",

    "RAI 1",
    "RAI 2",
    "RAI 3",
    "RAI NEWS 24",
    "RAI STORIA",
    "RAI SCUOLA",
    "RAI SPORT",

    "MEDIASET ITALIA",
    "TGCOM24",

    "TV5MONDE",
    "TV5 MONDE",
    "FRANCE 24",

    "EURONEWS",

    "BBC WORLD NEWS",
    "BBC NEWS",

    "CNN INTERNATIONAL",

    "AL JAZEERA",
    "AL JAZEERA ENGLISH",

    "DW",
    "DW ENGLISH",
    "DEUTSCHE WELLE",

    "NHK WORLD",
    "CGTN",
    "CGTN DOCUMENTARY",

    "TRT WORLD",
    "TRT TURK",
    "TRT ARABI",
    "TRT AVAZ",

    "PRESS TV",
    "IRIB",
    "IRAN INTERNATIONAL",

    "AL ARABIYA",
    "AL HADATH",

    "FRANCE 24 ARABIC",

    "TVE INTERNACIONAL",
    "RTVE",
    "24 HORAS",

    "RTP INTERNACIONAL",
    "RTP INTERNATIONAL",

    "TBN",
    "GOD TV",
]


# ============================================================
# HTTP
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/151 Safari/537.36"
    ),
    "Accept": "*/*",
}


def download(url, timeout=20):
    request = urllib.request.Request(
        url,
        headers=HEADERS
    )

    with urllib.request.urlopen(
        request,
        timeout=timeout
    ) as response:
        return response.read().decode(
            "utf-8",
            errors="replace"
        )


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
        "Ä": "A",
        "Ö": "O",
        "Ü": "U",
        "ß": "SS",
        "É": "E",
        "È": "E",
        "À": "A",
        "Á": "A",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = unicodedata.normalize(
        "NFKD",
        text
    )

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


# ============================================================
# M3U PARSER
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

        if url.startswith(
            ("http://", "https://")
        ):
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
    match = re.search(
        r'tvg-id="([^"]*)"',
        info,
        re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    return ""


# ============================================================
# COUNTRY
# ============================================================

def famelack_country(info):
    match = re.search(
        r'group-title="famelack '
        r'\(([^)]+)\) '
        r'\[([^\]]+)\]',
        info,
        re.IGNORECASE
    )

    if not match:
        return None

    return match.group(2).lower().strip()


# ============================================================
# GROUP-TITLE
# ============================================================

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
# TÜRKİYE GRUPLARI
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


# ============================================================
# BAD ENTRY
# ============================================================

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


# ============================================================
# ÇÖZÜNÜRLÜK
# ============================================================

def resolution_score(info):
    match = re.search(
        r"\((\d{3,4})P\)",
        info.upper()
    )

    if match:
        return int(
            match.group(1)
        )

    if "4K" in info.upper():
        return 2160

    return 0


# ============================================================
# MASTER PLAYLIST → SABİT VARYANT
# ============================================================

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

        # Media playlist, master değil.
        if not variants:
            return url, 0

        exact = [
            x for x in variants
            if x["height"] == 1080
        ]

        if exact:
            exact.sort(
                key=lambda x: x["bandwidth"],
                reverse=True
            )

            return (
                exact[0]["url"],
                1080
            )

        below = [
            x for x in variants
            if 0 < x["height"] < 1080
        ]

        if below:
            below.sort(
                key=lambda x: (
                    x["height"],
                    x["bandwidth"]
                ),
                reverse=True
            )

            return (
                below[0]["url"],
                below[0]["height"]
            )

        above = [
            x for x in variants
            if x["height"] > 1080
        ]

        if above:
            above.sort(
                key=lambda x: (
                    x["height"],
                    x["bandwidth"]
                ),
                reverse=True
            )

            return (
                above[0]["url"],
                above[0]["height"]
            )

        return url, 0

    except Exception:
        return None, 0


# ============================================================
# STREAM TEST
# ============================================================

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
# TURKEY: ID
# ============================================================

def clean_identity(info):
    tid = tvg_id(info)

    if tid:
        tid = tid.split("@")[0]
        return normalize(
            tid
        ).replace(".", "").replace("-", "")

    return re.sub(
        r"[^A-Z0-9]",
        "",
        normalize(
            channel_name(info)
        )
    )


# ============================================================
# TURKIYE KAYNAKLARINI TOPLA
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


# FALLBACK
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


# ============================================================
# TURKIYE: ÇALIŞAN EN İYİ KANALI SEÇ
# ============================================================

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

    # Show TV master olarak kalsın.
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
    ).append(
        entry
    )


turkey_selected = []


for identity, alternatives in by_identity.items():

    alternatives.sort(
        key=lambda x: x["rank"],
        reverse=True
    )

    winner = alternatives[0]

    group = turkey_group(
        winner["name"]
    )

    winner["info"] = replace_group(
        winner["info"],
        group
    )

    turkey_selected.append(
        winner
    )


turkey_selected.sort(
    key=lambda x: (
        x["info"],
        normalize(
            x["name"]
        )
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
# FAMELACK DÜNYA KAYNAĞINI İNDİR
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


# ============================================================
# DUNYA.M3U
# ============================================================

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

    info = replace_group(
        info,
        group
    )

    world_output.extend([
        info,
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
# UYDU EŞLEŞTİRME
# ============================================================

def matches_satellite(
    channel_name_text,
    satellite_names
):
    n = normalize(
        channel_name_text
    )

    # Çözünürlük vb temizle
    n = re.sub(
        r"\([^)]*\)",
        "",
        n
    )

    n = re.sub(
        r"\[[^\]]*\]",
        "",
        n
    )

    for candidate in satellite_names:

        c = normalize(
            candidate
        )

        if (
            n == c
            or n.startswith(c + " ")
            or c.startswith(n + " ")
        ):
            return True

    return False


# ============================================================
# HOTBIRD.M3U
# ============================================================

hotbird_output = [
    "#EXTM3U"
]

hotbird_seen = set()


for entry in world_entries:

    info = entry["info"]
    url = entry["url"]

    name = channel_name(
        info
    )

    if not matches_satellite(
        name,
        HOTBIRD_CHANNELS
    ):
        continue

    if rejected(
        info
    ):
        continue

    if url in hotbird_seen:
        continue

    info = replace_group(
        info,
        "Hotbird 13°E"
    )

    hotbird_output.extend([
        info,
        url
    ])

    hotbird_seen.add(
        url
    )


HOTBIRD_OUTPUT.write_text(
    "\n".join(
        hotbird_output
    ) + "\n",
    encoding="utf-8"
)


# ============================================================
# ASTRA.M3U
# ============================================================

astra_output = [
    "#EXTM3U"
]

astra_seen = set()


for entry in world_entries:

    info = entry["info"]
    url = entry["url"]

    name = channel_name(
        info
    )

    if not matches_satellite(
        name,
        ASTRA_CHANNELS
    ):
        continue

    if rejected(
        info
    ):
        continue

    if url in astra_seen:
        continue

    info = replace_group(
        info,
        "Astra 19.2°E"
    )

    astra_output.extend([
        info,
        url
    ])

    astra_seen.add(
        url
    )


ASTRA_OUTPUT.write_text(
    "\n".join(
        astra_output
    ) + "\n",
    encoding="utf-8"
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
    len(turkey_selected),
    "kanal"
)

print(
    "Dunya:",
    len(world_seen),
    "kanal"
)

print(
    "Hotbird:",
    len(hotbird_seen),
    "kanal"
)

print(
    "Astra:",
    len(astra_seen),
    "kanal"
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
