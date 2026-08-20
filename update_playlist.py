import urllib.request
from urllib.parse import urljoin
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher
from html.parser import HTMLParser
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
# INTERNET KAYNAKLARI
# ============================================================

FAMELACK_M3U = (
    "https://raw.githubusercontent.com/"
    "DEvmIb/famelack-channels-m3u/main/m3u/_all.m3u"
)

IPTVORG_WORLD = (
    "https://iptv-org.github.io/iptv/index.m3u"
)

TURKEY_SOURCES = [
    (
        "iptv-org-tr",
        "https://raw.githubusercontent.com/"
        "iptv-org/iptv/master/streams/tr.m3u",
        110,
    ),
    (
        "discevisita",
        "https://raw.githubusercontent.com/"
        "discevisita/iptv/main/tr.m3u",
        100,
    ),
    (
        "suphero",
        "https://raw.githubusercontent.com/"
        "suphero/IPTV/master/TR.m3u8",
        80,
    ),
]


# ============================================================
# UYDU FTA KAYNAKLARI
# lim=500 ile mümkün olduğunca tüm FTA TV kayıtlarını iste
# ============================================================

TURKSAT_URL = (
    "https://en.kingofsat.net/tv.php?"
    "aff=list&filtre=Clear&lim=500&ordre=freq&pos=42E&standard=All"
)

HOTBIRD_URL = (
    "https://en.kingofsat.net/tv.php?"
    "aff=list&filtre=Clear&lim=500&ordre=freq&pos=13E&standard=All"
)

ASTRA_URL = (
    "https://en.kingofsat.net/tv.php?"
    "aff=list&filtre=Clear&lim=500&ordre=freq&pos=19.2E&standard=All"
)


# ============================================================
# TÜRKİYE ÖZEL YEDEKLER
# Ana kaynaklarda yoksa bunlar denenir.
# ============================================================

FALLBACKS = {

    "SHOWTV": [
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

    "STARTV": [
        (
            "Star TV",
            "https://dogus.daioncdn.net/"
            "startv/startv_720p.m3u8"
            "?app=a20ac41e-bdc3-4aa1-934d-26b484480ac9&ce=3",
            720,
        ),
    ],

    "KANALD": [
        (
            "Kanal D",
            "https://demiroren.daioncdn.net/"
            "kanald/kanald.m3u8?app=kanald_web&ce=3",
            1080,
        ),
    ],

    "TV8": [
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

    "ATV": [
        (
            "ATV",
            "https://rnttwmjcin.turknet.ercdn.net/"
            "lcpmvefbyo/atv/atv_1080p.m3u8",
            1080,
        ),
    ],

    "NOW": [
        (
            "NOW",
            "https://uycyyuuzyh.turknet.ercdn.net/"
            "nphindgytw/nowtv/nowtv.m3u8",
            720,
        ),
    ],

    "HABERTURK": [
        (
            "Habertürk",
            "https://rmtftbjlne.turknet.ercdn.net/"
            "bpeytmnqyp/haberturktv/"
            "haberturktv_1080p.m3u8",
            1080,
        ),
        (
            "Habertürk",
            "https://tv.ensonhaber.com/"
            "haberturk/haberturk.m3u8",
            720,
        ),
    ],

    "BLOOMBERGHT": [
        (
            "Bloomberg HT",
            "https://ciner-live.daioncdn.net/"
            "bloomberght/bloomberght.m3u8",
            0,
        ),
    ],

    "CNNTURK": [
        (
            "CNN Türk",
            "https://mn-nl.mncdn.com/"
            "blutv_cnnturk/"
            "smil:cnnturk_sd.smil/playlist.m3u8",
            480,
        ),
    ],

    "AHABER": [
        (
            "A Haber",
            "https://rnttwmjcin.turknet.ercdn.net/"
            "lcpmvefbyo/ahaber/ahaber_1080p.m3u8",
            1080,
        ),
    ],

    "ASPOR": [
        (
            "A Spor",
            "https://rnttwmjcin.turknet.ercdn.net/"
            "lcpmvefbyo/aspor/aspor_1080p.m3u8",
            1080,
        ),
    ],

    "TRT1": [
        (
            "TRT 1",
            "https://tv-trt1.medya.trt.com.tr/master.m3u8",
            1440,
        ),
    ],

    "TRTHABER": [
        (
            "TRT Haber",
            "https://tv-trthaber.medya.trt.com.tr/master.m3u8",
            1080,
        ),
    ],

    "TRTSPOR": [
        (
            "TRT Spor",
            "https://tv-trtspor1.medya.trt.com.tr/master.m3u8",
            1080,
        ),
    ],

    "TRTCOCUK": [
        (
            "TRT Çocuk",
            "https://tv-trtcocuk.medya.trt.com.tr/master.m3u8",
            1440,
        ),
    ],

    "TRTBELGESEL": [
        (
            "TRT Belgesel",
            "https://tv-trtbelgesel.medya.trt.com.tr/master.m3u8",
            1080,
        ),
    ],
}


# ============================================================
# ŞİFRELİ / PAY-TV İSİM FİLTRESİ
# Uydu kaynakları zaten Clear filtresinden geliyor.
# Bu filtre internet kaynaklarında ek koruma.
# ============================================================

BLOCKED_WORDS = [
    "BEIN",
    "DIGITURK",
    "D-SMART",
    "D SMART",
    "TIVIBU",
    "MOVIESMART",
    "MOVIE SMART",
    "SMART SPOR",
    "S SPORT",
    "S-SPORT",
]


# ============================================================
# DÜNYA ÜLKE ADLARI
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
# TEMEL YARDIMCILAR
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

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


def match_name(text):

    text = normalize(text)

    # çözünürlük ve genel ekleri kaldır
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
        r"\b(UHD|FHD|FULL HD|HD|SD|4K)\b",
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


def compact_name(text):

    return re.sub(
        r"[^A-Z0-9]",
        "",
        match_name(text)
    )


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

        # #EXTVLCOPT gibi satırları atla
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

        return info.split(
            ",",
            1
        )[1].strip()

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
# FAMELACK ÜLKE KODU
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
# KINGOFSAT HTML PARSER
# ============================================================

class KingOfSatParser(HTMLParser):

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

        elif (
            tag in ("td", "th")
            and self.in_row
        ):

            self.in_cell = True
            self.current_cell = []


    def handle_data(self, data):

        if self.in_cell:

            self.current_cell.append(
                data
            )


    def handle_endtag(self, tag):

        if (
            tag in ("td", "th")
            and self.in_cell
        ):

            value = " ".join(
                self.current_cell
            )

            value = re.sub(
                r"\s+",
                " ",
                value
            ).strip()

            self.current_row.append(
                value
            )

            self.in_cell = False


        elif (
            tag == "tr"
            and self.in_row
        ):

            if self.current_row:

                self.rows.append(
                    self.current_row
                )

            self.in_row = False


def get_fta_channels(url):

    print(
        "FTA uydu listesi indiriliyor:",
        url
    )

    html = download(
        url,
        timeout=35
    )

    parser = KingOfSatParser()

    parser.feed(
        html
    )

    result = []

    seen = set()


    for row in parser.rows:

        # KingOfSat'ın güncel tablosunda kanal satırında
        # Country / Category / Packages / Encryption alanları var.
        #
        # Clear kelimesini bulup geriye doğru kanal adını arıyoruz.

        clear_indexes = []

        for index, cell in enumerate(row):

            if normalize(cell) == "CLEAR":

                clear_indexes.append(
                    index
                )


        for clear_index in clear_indexes:

            # tipik yapı:
            # Name | Country | Category | Packages | Clear
            #
            # dolayısıyla genellikle 4 hücre geride kanal adı var.

            possible = []

            for offset in (
                4,
                3,
                5,
            ):

                index = (
                    clear_index
                    - offset
                )

                if (
                    index >= 0
                    and index < len(row)
                ):

                    possible.append(
                        row[index]
                    )


            chosen = None

            for candidate in possible:

                c = normalize(
                    candidate
                )

                if (
                    len(candidate) >= 2
                    and c not in (
                        "IMAGE",
                        "NAME",
                        "CHANNEL",
                        "TV",
                        "GENERAL",
                        "NEWS",
                        "SPORT",
                        "MUSIC",
                        "MOVIES",
                        "SERIES",
                        "RELIGIOUS",
                        "CLEAR",
                    )
                ):

                    # frekans / sayı gibi hücreleri at
                    if re.fullmatch(
                        r"[\d\s.,/+:-]+",
                        candidate
                    ):
                        continue

                    chosen = candidate
                    break


            if not chosen:
                continue


            key = compact_name(
                chosen
            )

            if (
                key
                and key not in seen
            ):

                result.append(
                    chosen
                )

                seen.add(
                    key
                )


    print(
        "FTA kanal adı bulundu:",
        len(result)
    )

    return result


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
        "TV 100",
        "TVNET",
        "TV NET",
        "24 TV",
        "FLASH HABER",
        "ULUSAL KANAL",
        "SOZCU",
        "EKOTURK",
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
        "NUMBER 1",
        "POWER TURK",
        "DREAM TURK",
        "MUZIK",
        "MUSIC",
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
# INTERNET KAYDI FİLTRESİ
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
# HLS MASTER → SABİT ÇÖZÜNÜRLÜK
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


            res_match = re.search(
                r"RESOLUTION=(\d+)x(\d+)",
                line,
                re.IGNORECASE
            )

            bandwidth_match = re.search(
                r"BANDWIDTH=(\d+)",
                line,
                re.IGNORECASE
            )


            height = (
                int(
                    res_match.group(2)
                )
                if res_match
                else 0
            )


            bandwidth = (
                int(
                    bandwidth_match.group(1)
                )
                if bandwidth_match
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


        # zaten sabit media playlist
        if not variants:

            return url, 0


        # önce 1080p
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
                1080
            )


        # sonra 1080 altındaki en yüksek
        lower = [
            v for v in variants
            if (
                v["height"] > 0
                and v["height"] < TARGET_HEIGHT
            )
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


        # sadece daha yüksek varsa
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
# İSİM EŞLEŞTİRME
# ============================================================

def similarity(a, b):

    return SequenceMatcher(
        None,
        a,
        b
    ).ratio()


def names_match_score(
    satellite_name,
    internet_name
):

    sat = match_name(
        satellite_name
    )

    net = match_name(
        internet_name
    )


    if (
        not sat
        or not net
    ):

        return 0.0


    if sat == net:

        return 1.0


    sat_compact = compact_name(
        sat
    )

    net_compact = compact_name(
        net
    )


    if sat_compact == net_compact:

        return 1.0


    # uzun isimlerde biri diğerinin tamamını içeriyorsa
    if (
        min(
            len(sat_compact),
            len(net_compact)
        ) >= 5
        and (
            sat_compact in net_compact
            or net_compact in sat_compact
        )
    ):

        return 0.96


    return similarity(
        sat_compact,
        net_compact
    )


# ============================================================
# DİL / BÖLGE VARYANTINI KORUMAK İÇİN ANAHTAR
# ============================================================

LANGUAGE_WORDS = [
    "ENGLISH",
    "EN",
    "DEUTSCH",
    "GERMAN",
    "DE",
    "FRANCAIS",
    "FRENCH",
    "FR",
    "ITALIANO",
    "ITALIAN",
    "IT",
    "ESPANOL",
    "SPANISH",
    "ES",
    "ARABIC",
    "ARABI",
    "AR",
    "TURK",
    "TURKCE",
    "POLSKA",
    "POLISH",
    "RU",
    "RUSSIAN",
]


def version_key(name):

    n = match_name(
        name
    )

    language = ""

    tokens = set(
        n.split()
    )

    for word in LANGUAGE_WORDS:

        if word in tokens:

            language = word
            break


    return (
        compact_name(n),
        language
    )


# ============================================================
# DÜNYA INTERNET KAYNAKLARINI TOPLA
# ============================================================

print(
    "Famelack dünya listesi indiriliyor..."
)

famelack_text = download(
    FAMELACK_M3U
)

famelack_entries = parse_entries(
    famelack_text,
    "famelack",
    70
)


print(
    "IPTV-org dünya listesi indiriliyor..."
)

try:

    iptv_world_text = download(
        IPTVORG_WORLD,
        timeout=45
    )

    iptv_world_entries = parse_entries(
        iptv_world_text,
        "iptv-org-world",
        100
    )

except Exception as error:

    print(
        "IPTV-org dünya kaynağı alınamadı:",
        error
    )

    iptv_world_entries = []


all_world_candidates = (
    famelack_entries
    + iptv_world_entries
)


# ============================================================
# DUNYA.M3U
# Famelack'ın ülke bilgisi daha düzenli olduğu için temel kaynak.
# ============================================================

world_output = [
    "#EXTM3U"
]

world_seen_urls = set()


for entry in famelack_entries:

    info = entry["info"]
    url = entry["url"]

    if url in world_seen_urls:
        continue


    code = famelack_country(
        info
    )


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


    world_seen_urls.add(
        url
    )


WORLD_OUTPUT.write_text(
    "\n".join(
        world_output
    ) + "\n",
    encoding="utf-8"
)


# ============================================================
# TÜRKSAT / HOTBIRD / ASTRA FTA LİSTELERİNİ AL
# ============================================================

turksat_channels = get_fta_channels(
    TURKSAT_URL
)

hotbird_channels = get_fta_channels(
    HOTBIRD_URL
)

astra_channels = get_fta_channels(
    ASTRA_URL
)


# ============================================================
# TÜRKİYE İNTERNET ADAYLARI
# ============================================================

turkey_candidates = []


for source, url, score in TURKEY_SOURCES:

    try:

        print(
            "Türkiye internet kaynağı:",
            source
        )

        text = download(
            url
        )

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


# dünya kaynağındaki Türkiye benzeri kanalları da aramaya izin ver
turkey_candidates.extend(
    all_world_candidates
)


# fallbackleri ekle
for identity, alternatives in FALLBACKS.items():

    for (
        name,
        url,
        resolution
    ) in alternatives:

        turkey_candidates.append({
            "info": (
                f'#EXTINF:-1 '
                f'tvg-id="{identity}" '
                f'group-title="{turkey_group(name)}",'
                f'{name}'
            ),
            "url": url,
            "source": "fallback",
            "source_score": 105,
            "forced_resolution": resolution,
        })


# ============================================================
# ADAY STREAMİ ANALİZ ET
# ============================================================

def analyze_stream(entry, keep_master=False):

    if rejected(
        entry["info"]
    ):

        return None


    url = entry["url"]


    advertised = entry.get(
        "forced_resolution",
        resolution_score(
            entry["info"]
        )
    )


    if keep_master:

        if not stream_works(
            url
        ):

            return None


        return {
            **entry,
            "final_url": url,
            "resolution": advertised,
        }


    fixed_url, found_res = resolve_variant(
        url
    )


    if not fixed_url:

        return None


    if not stream_works(
        fixed_url
    ):

        return None


    return {
        **entry,
        "final_url": fixed_url,
        "resolution": (
            found_res
            if found_res
            else advertised
        ),
    }


# ============================================================
# UYDU KANAL LİSTESİNİ INTERNET STREAMLERİYLE EŞLEŞTİR
# ============================================================

def build_satellite_playlist(
    satellite_channels,
    internet_candidates,
    output_path,
    group_name,
    turkey_mode=False
):

    print(
        "Eşleştirme başlıyor:",
        group_name
    )


    # önce isim indeksini hazırla
    indexed = []

    for entry in internet_candidates:

        name = channel_name(
            entry["info"]
        )

        if not name:
            continue


        indexed.append({
            **entry,
            "name": name,
            "match": match_name(name),
        })


    # Her uydu kanalı için güçlü isim eşleşmelerini bul.
    candidate_matches = []


    for sat_name in satellite_channels:

        scored = []


        for entry in indexed:

            score = names_match_score(
                sat_name,
                entry["name"]
            )


            # düşük benzerliği hiç alma
            if score < 0.91:
                continue


            scored.append(
                (
                    score,
                    entry
                )
            )


        if not scored:
            continue


        scored.sort(
            key=lambda x: (
                x[0],
                x[1]["source_score"],
                resolution_score(
                    x[1]["info"]
                )
            ),
            reverse=True
        )


        # Her uydu kanalı için en fazla 5 iyi alternatif test edilir.
        for score, entry in scored[:5]:

            candidate_matches.append({
                "satellite_name": sat_name,
                "match_score": score,
                "entry": entry,
            })


    print(
        group_name,
        "internet aday eşleşmesi:",
        len(candidate_matches)
    )


    # Streamleri paralel test et.
    tested = []


    def test_match(item):

        entry = item["entry"]


        keep_master = (
            turkey_mode
            and compact_name(
                item["satellite_name"]
            ) == "SHOWTV"
        )


        result = analyze_stream(
            entry,
            keep_master=keep_master
        )


        if not result:
            return None


        result["satellite_name"] = (
            item["satellite_name"]
        )

        result["match_score"] = (
            item["match_score"]
        )


        return result


    with ThreadPoolExecutor(
        max_workers=14
    ) as executor:


        futures = [
            executor.submit(
                test_match,
                item
            )
            for item in candidate_matches
        ]


        for future in as_completed(
            futures
        ):

            try:

                result = future.result()

                if result:
                    tested.append(
                        result
                    )

            except Exception:

                pass


    # Uydu kanalı + dil/bölge sürümü bazında en iyi kaydı seç.
    grouped = {}


    for item in tested:

        key = (
            compact_name(
                item["satellite_name"]
            ),
            version_key(
                item["name"]
            )[1]
        )


        item["rank"] = (
            item["match_score"] * 100000
            + item["resolution"] * 100
            + item["source_score"]
        )


        grouped.setdefault(
            key,
            []
        ).append(
            item
        )


    selected = []


    for key, options in grouped.items():

        options.sort(
            key=lambda x: x["rank"],
            reverse=True
        )


        winner = options[0]


        if turkey_mode:

            group = turkey_group(
                winner["satellite_name"]
            )

        else:

            group = group_name


        winner["info"] = (
            f'#EXTINF:-1 '
            f'group-title="{group}",'
            f'{winner["satellite_name"]}'
        )


        selected.append(
            winner
        )


    selected.sort(
        key=lambda x: normalize(
            x["satellite_name"]
        )
    )


    output = [
        "#EXTM3U"
    ]


    seen_urls = set()


    for item in selected:

        if item["final_url"] in seen_urls:
            continue


        output.extend([
            item["info"],
            item["final_url"]
        ])


        seen_urls.add(
            item["final_url"]
        )


    output_path.write_text(
        "\n".join(
            output
        ) + "\n",
        encoding="utf-8"
    )


    print(
        group_name,
        "son kanal sayısı:",
        len(selected)
    )


    return selected


# ============================================================
# 4 PLAYLIST
# ============================================================

turkey_selected = build_satellite_playlist(
    turksat_channels,
    turkey_candidates,
    TURKEY_OUTPUT,
    "Türkiye",
    turkey_mode=True
)


hotbird_selected = build_satellite_playlist(
    hotbird_channels,
    all_world_candidates,
    HOTBIRD_OUTPUT,
    "Hotbird 13°E",
    turkey_mode=False
)


astra_selected = build_satellite_playlist(
    astra_channels,
    all_world_candidates,
    ASTRA_OUTPUT,
    "Astra 19.2°E",
    turkey_mode=False
)


# ============================================================
# RAPOR
# ============================================================

print(
    "================================"
)

print(
    "TAMAMLANDI"
)

print(
    "================================"
)

print(
    "Türksat FTA TV:",
    len(turksat_channels)
)

print(
    "Turkiye.m3u çalışan eşleşme:",
    len(turkey_selected)
)

print(
    "Hotbird FTA TV:",
    len(hotbird_channels)
)

print(
    "Hotbird.m3u çalışan eşleşme:",
    len(hotbird_selected)
)

print(
    "Astra FTA TV:",
    len(astra_channels)
)

print(
    "Astra.m3u çalışan eşleşme:",
    len(astra_selected)
)

print(
    "Dunya.m3u:",
    len(world_seen_urls)
)

print(
    "================================"
)


# Özellikle görmek istediğimiz Türkiye kanalları
checks = [
    "SHOW TV",
    "STAR TV",
    "KANAL D",
    "TV8",
    "ATV",
    "NOW",
    "HABERTURK",
    "BLOOMBERG HT",
    "CNN TURK",
    "NTV",
    "A HABER",
    "HABER GLOBAL",
    "TRT HABER",
    "TRT 1",
    "TRT SPOR",
]


turkey_names = {
    compact_name(
        item["satellite_name"]
    )
    for item in turkey_selected
}


for name in checks:

    print(
        name,
        ":",
        compact_name(name)
        in turkey_names
    )
