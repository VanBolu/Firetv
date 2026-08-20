import urllib.request
from urllib.parse import urljoin
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from difflib import SequenceMatcher
import subprocess
import json
import re
import unicodedata
import shutil


# ============================================================
# DOSYALAR
# ============================================================

TURKEY_OUTPUT = Path("Turkiye.m3u")
WORLD_OUTPUT = Path("Dunya.m3u")
HOTBIRD_OUTPUT = Path("Hotbird.m3u")
ASTRA_OUTPUT = Path("Astra.m3u")

TARGET_HEIGHT = 1080

# Bir kanal/dil/sürüm için kaç alternatif detaylı test edilecek
MAX_CANDIDATES_PER_CHANNEL = 4

# Paralel test
MAX_WORKERS = 12


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
        120,
    ),
    (
        "discevisita",
        "https://raw.githubusercontent.com/"
        "discevisita/iptv/main/tr.m3u",
        105,
    ),
    (
        "suphero",
        "https://raw.githubusercontent.com/"
        "suphero/IPTV/master/TR.m3u8",
        75,
    ),
]


# ============================================================
# UYDU FTA LİSTELERİ
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
# TÜRKİYE YEDEKLERİ
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
            "https://dogus.daioncdn.net/startv/startv_720p.m3u8"
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
            "bpeytmnqyp/haberturktv/haberturktv_1080p.m3u8",
            1080,
        ),
        (
            "Habertürk",
            "https://tv.ensonhaber.com/haberturk/haberturk.m3u8",
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
            "blutv_cnnturk/smil:cnnturk_sd.smil/playlist.m3u8",
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
# MASTER URL OLARAK KORUNACAK KANALLAR
# ============================================================

KEEP_MASTER = {
    "SHOWTV",
}


# ============================================================
# İSTENMEYEN PAY-TV
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
        "AppleWebKit/537.36 Chrome/151 Safari/537.36"
    ),
    "Accept": "*/*",
}


# ============================================================
# NORMALIZE
# ============================================================

def normalize(text):

    text = (text or "").upper()

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

    text = unicodedata.normalize(
        "NFKD",
        text
    )

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


# ============================================================
# HTTP
# ============================================================

def download(url, timeout=20):

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
        options = []

        j = i + 1

        while (
            j < len(lines)
            and lines[j].strip().startswith("#")
        ):

            options.append(
                lines[j].strip()
            )

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
                "options": options,
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
# FAMELACK ÜLKE
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
# KINGOFSAT
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

    try:

        html = download(
            url,
            timeout=35
        )

    except Exception as error:

        print(
            "Uydu listesi alınamadı:",
            error
        )

        return []


    parser = KingOfSatParser()
    parser.feed(html)

    result = []
    seen = set()


    for row in parser.rows:

        clear_indexes = [
            i
            for i, cell in enumerate(row)
            if normalize(cell) == "CLEAR"
        ]


        for clear_index in clear_indexes:

            candidates = []

            for offset in (
                4,
                3,
                5,
            ):

                idx = (
                    clear_index
                    - offset
                )

                if 0 <= idx < len(row):

                    candidates.append(
                        row[idx]
                    )


            chosen = None


            for candidate in candidates:

                test = normalize(
                    candidate
                )

                if len(candidate) < 2:
                    continue

                if test in {
                    "NAME",
                    "CHANNEL",
                    "TV",
                    "GENERAL",
                    "NEWS",
                    "SPORT",
                    "MUSIC",
                    "MOVIES",
                    "CLEAR",
                }:
                    continue

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


    return result


# ============================================================
# TÜRKİYE GRUP
# ============================================================

def turkey_group(name):

    n = normalize(name)


    if any(x in n for x in [
        "TRT COCUK",
        "MINIKA",
        "COCUK",
        "CARTOON",
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
# KÖTÜ KAYIT
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
# META / DİL / BÖLGE
# ============================================================

LANGUAGE_WORDS = {
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
    "RUSSIAN",
    "RUS",
}


def language_variant(name):

    tokens = set(
        match_name(name).split()
    )

    for word in LANGUAGE_WORDS:

        if word in tokens:
            return word

    return ""


def version_key(name):

    return (
        compact_name(name),
        language_variant(name)
    )


# ============================================================
# ÇÖZÜNÜRLÜK METADATA
# ============================================================

def advertised_resolution(info):

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
# HLS MANIFEST ANALİZİ
# ============================================================

def inspect_hls(url):

    try:

        text = download(
            url,
            timeout=10
        )

    except Exception:

        return None


    if "#EXTM3U" not in text:

        return None


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
            r"(?:AVERAGE-)?BANDWIDTH=(\d+)",
            line,
            re.IGNORECASE
        )

        frame = re.search(
            r"FRAME-RATE=([\d.]+)",
            line,
            re.IGNORECASE
        )

        codecs = re.search(
            r'CODECS="([^"]+)"',
            line,
            re.IGNORECASE
        )


        width = (
            int(res.group(1))
            if res
            else 0
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

        fps = (
            float(frame.group(1))
            if frame
            else 0.0
        )

        codec_text = (
            codecs.group(1)
            if codecs
            else ""
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
            "width": width,
            "height": height,
            "bandwidth": bandwidth,
            "fps": fps,
            "codecs": codec_text,
        })


    return {
        "master": bool(variants),
        "variants": variants,
        "text": text,
    }


# ============================================================
# HLS VARYANT PUANI
# ============================================================

def codec_score(codec_text):

    codec = (
        codec_text or ""
    ).lower()

    score = 0


    # LG webOS için AVC/H264 en güvenli
    if (
        "avc1" in codec
        or "h264" in codec
    ):
        score += 500


    # HEVC ikinci
    elif (
        "hvc1" in codec
        or "hev1" in codec
        or "hevc" in codec
    ):
        score += 300


    # AV1 daha düşük LG uyumluluk puanı
    elif (
        "av01" in codec
        or "av1" in codec
    ):
        score += 150


    # AAC
    if (
        "mp4a" in codec
        or "aac" in codec
    ):
        score += 200


    return score


def variant_score(v):

    height = v["height"]
    fps = v["fps"]
    bitrate = v["bandwidth"]


    # 1080p merkezli tercih.
    if height == 1080:
        resolution_points = 10000

    elif height == 720:
        resolution_points = 8500

    elif height > 1080:
        # 1440/2160 yerine LG'de stabil 1080'i tercih ediyoruz.
        resolution_points = 9000

    elif height >= 576:
        resolution_points = 6500

    elif height >= 480:
        resolution_points = 5000

    else:
        resolution_points = 2500


    fps_points = 0

    if fps >= 49:
        fps_points = 800

    elif fps >= 29:
        fps_points = 400

    elif fps >= 24:
        fps_points = 200


    bitrate_points = min(
        int(bitrate / 10000),
        600
    )


    return (
        resolution_points
        + fps_points
        + bitrate_points
        + codec_score(
            v["codecs"]
        )
    )


def choose_hls_variant(url):

    result = inspect_hls(url)


    if not result:

        return None


    # Media playlist zaten sabit stream.
    if not result["master"]:

        return {
            "url": url,
            "height": 0,
            "fps": 0,
            "bandwidth": 0,
            "codecs": "",
            "manifest_score": 0,
        }


    variants = result[
        "variants"
    ]


    variants.sort(
        key=variant_score,
        reverse=True
    )


    winner = variants[0]


    return {
        **winner,
        "manifest_score": variant_score(
            winner
        ),
    }


# ============================================================
# FFPROBE
# ============================================================

def ffprobe_available():

    return shutil.which(
        "ffprobe"
    ) is not None


def ffprobe_stream(url):

    if not ffprobe_available():

        return {}


    command = [
        "ffprobe",

        "-v",
        "error",

        "-rw_timeout",
        "8000000",

        "-analyzeduration",
        "3000000",

        "-probesize",
        "3000000",

        "-show_entries",
        (
            "stream=codec_type,codec_name,width,height,"
            "avg_frame_rate,r_frame_rate,bit_rate"
        ),

        "-of",
        "json",

        url,
    ]


    try:

        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=15,
        )


        if process.returncode != 0:

            return {}


        data = json.loads(
            process.stdout
        )


        video = None
        audio = None


        for stream in data.get(
            "streams",
            []
        ):

            if (
                stream.get("codec_type")
                == "video"
                and video is None
            ):

                video = stream


            elif (
                stream.get("codec_type")
                == "audio"
                and audio is None
            ):

                audio = stream


        result = {}


        if video:

            result["video_codec"] = (
                video.get(
                    "codec_name",
                    ""
                )
            )

            result["width"] = int(
                video.get(
                    "width",
                    0
                )
                or 0
            )

            result["height"] = int(
                video.get(
                    "height",
                    0
                )
                or 0
            )


            fps_text = (
                video.get(
                    "avg_frame_rate"
                )
                or video.get(
                    "r_frame_rate"
                )
                or "0/1"
            )


            try:

                num, den = (
                    fps_text.split("/")
                )

                result["fps"] = (
                    float(num)
                    / float(den)
                    if float(den)
                    else 0
                )

            except Exception:

                result["fps"] = 0


            try:

                result["bitrate"] = int(
                    video.get(
                        "bit_rate",
                        0
                    )
                    or 0
                )

            except Exception:

                result["bitrate"] = 0


        if audio:

            result["audio_codec"] = (
                audio.get(
                    "codec_name",
                    ""
                )
            )


        return result


    except Exception:

        return {}


# ============================================================
# GERÇEK STREAM PUANI
# ============================================================

def probe_score(probe):

    score = 0


    height = probe.get(
        "height",
        0
    )

    fps = probe.get(
        "fps",
        0
    )

    bitrate = probe.get(
        "bitrate",
        0
    )


    video = probe.get(
        "video_codec",
        ""
    ).lower()

    audio = probe.get(
        "audio_codec",
        ""
    ).lower()


    # Çözünürlük
    if height == 1080:
        score += 10000

    elif height == 720:
        score += 8500

    elif height > 1080:
        score += 9000

    elif height >= 576:
        score += 6500

    elif height >= 480:
        score += 5000

    else:
        score += 2500


    # FPS
    if fps >= 49:
        score += 900

    elif fps >= 29:
        score += 450

    elif fps >= 24:
        score += 200


    # Codec
    if video in (
        "h264",
        "avc",
    ):
        score += 600

    elif video in (
        "hevc",
        "h265",
    ):
        score += 350

    elif video in (
        "av1",
    ):
        score += 150


    # Ses
    if audio == "aac":
        score += 250


    # Bitrate
    score += min(
        int(bitrate / 10000),
        750
    )


    return score


# ============================================================
# STREAM ANALİZİ
# ============================================================

def analyze_candidate(entry):

    name = channel_name(
        entry["info"]
    )


    if not name:
        return None


    if rejected(
        entry["info"]
    ):
        return None


    identity = compact_name(
        name
    )


    original_url = entry[
        "url"
    ]


    # Show TV benzeri istisnalarda master URL korunur.
    if identity in KEEP_MASTER:

        hls = inspect_hls(
            original_url
        )


        if not hls:

            return None


        final_url = original_url

        manifest = {
            "height": advertised_resolution(
                entry["info"]
            ),
            "fps": 0,
            "bandwidth": 0,
            "codecs": "",
            "manifest_score": 0,
        }


    else:

        manifest = choose_hls_variant(
            original_url
        )


        if not manifest:

            return None


        final_url = manifest[
            "url"
        ]


    # Gerçek codec/fps/çözünürlük
    probe = ffprobe_stream(
        final_url
    )


    # ffprobe başarısız olsa bile HLS manifest çalışıyorsa tamamen atma.
    if probe:

        quality_score = probe_score(
            probe
        )

        actual_height = probe.get(
            "height",
            0
        )

        actual_fps = probe.get(
            "fps",
            0
        )

        video_codec = probe.get(
            "video_codec",
            ""
        )

        audio_codec = probe.get(
            "audio_codec",
            ""
        )

        bitrate = probe.get(
            "bitrate",
            0
        )


    else:

        quality_score = manifest.get(
            "manifest_score",
            0
        )

        actual_height = manifest.get(
            "height",
            0
        )

        actual_fps = manifest.get(
            "fps",
            0
        )

        video_codec = manifest.get(
            "codecs",
            ""
        )

        audio_codec = ""

        bitrate = manifest.get(
            "bandwidth",
            0
        )


    # Kaynak güvenilirliği de ekle.
    total_score = (
        quality_score
        + entry.get(
            "source_score",
            0
        ) * 5
    )


    return {
        **entry,

        "name": name,

        "identity": identity,

        "final_url": final_url,

        "height": actual_height,

        "fps": actual_fps,

        "video_codec": video_codec,

        "audio_codec": audio_codec,

        "bitrate": bitrate,

        "quality_score": (
            quality_score
        ),

        "total_score": (
            total_score
        ),
    }


# ============================================================
# İSİM EŞLEŞTİRME
# ============================================================

def name_similarity(a, b):

    a = compact_name(a)
    b = compact_name(b)


    if not a or not b:
        return 0.0


    if a == b:
        return 1.0


    if (
        min(
            len(a),
            len(b)
        ) >= 5
        and (
            a in b
            or b in a
        )
    ):

        return 0.96


    return SequenceMatcher(
        None,
        a,
        b
    ).ratio()


# ============================================================
# DÜNYA KAYNAKLARI
# ============================================================

print(
    "Famelack indiriliyor..."
)

famelack_text = download(
    FAMELACK_M3U
)

famelack_entries = parse_entries(
    famelack_text,
    "famelack",
    80
)


print(
    "IPTV-org dünya listesi indiriliyor..."
)

try:

    iptv_world_text = download(
        IPTVORG_WORLD,
        timeout=45
    )

    iptv_world_entries = (
        parse_entries(
            iptv_world_text,
            "iptv-org-world",
            110
        )
    )

except Exception as error:

    print(
        "IPTV-org world hatası:",
        error
    )

    iptv_world_entries = []


# ============================================================
# TÜRKİYE EK KAYNAKLARI
# ============================================================

turkey_extra = []


for source, url, score in TURKEY_SOURCES:

    try:

        text = download(
            url
        )

        turkey_extra.extend(
            parse_entries(
                text,
                source,
                score
            )
        )

    except Exception as error:

        print(
            source,
            "hatası:",
            error
        )


for fallback_id, alternatives in FALLBACKS.items():

    for name, url, resolution in alternatives:

        turkey_extra.append({
            "info": (
                '#EXTINF:-1 '
                f'tvg-id="{fallback_id}" '
                f'group-title="{turkey_group(name)}",'
                f'{name} ({resolution}p)'
            ),

            "url": url,

            "source": "fallback",

            "source_score": 115,

            "options": [],
        })


# ============================================================
# TÜM INTERNET ADAYLARI
# ============================================================

all_candidates = (
    famelack_entries
    + iptv_world_entries
    + turkey_extra
)


# ============================================================
# ÖN ELEME / KANAL BAŞINA KISA LİSTE
# ============================================================

def coarse_candidate_score(entry):

    score = (
        entry.get(
            "source_score",
            0
        )
    )


    advertised = advertised_resolution(
        entry["info"]
    )


    if advertised == 1080:
        score += 500

    elif advertised == 720:
        score += 400

    elif advertised > 1080:
        score += 450

    elif advertised:
        score += 250


    if entry[
        "url"
    ].startswith(
        "https://"
    ):

        score += 50


    return score


# ============================================================
# DÜNYA - ÜLKE BAZINDA ADAY GRUPLAMA
# ============================================================

world_groups = {}


for entry in all_candidates:

    if rejected(
        entry["info"]
    ):
        continue


    name = channel_name(
        entry["info"]
    )


    if not name:
        continue


    country = (
        famelack_country(
            entry["info"]
        )
        if entry["source"]
        == "famelack"
        else None
    )


    if not country:

        # tvg-id çoğunlukla Channel.xx
        tid = tvg_id(
            entry["info"]
        )

        match = re.search(
            r"\.([A-Za-z]{2})"
            r"(?:@|$)",
            tid
        )

        if match:

            country = (
                match.group(1)
                .lower()
            )


    if not country:

        country = "xx"


    key = (
        country,
        version_key(name)
    )


    world_groups.setdefault(
        key,
        []
    ).append(
        entry
    )


# ============================================================
# EN İYİ KISA ADAYLAR
# ============================================================

world_shortlist = []


for key, options in world_groups.items():

    options.sort(
        key=coarse_candidate_score,
        reverse=True
    )


    world_shortlist.extend(
        options[
            :MAX_CANDIDATES_PER_CHANNEL
        ]
    )


print(
    "Dünya detaylı test adayı:",
    len(world_shortlist)
)


# ============================================================
# TÜM DÜNYA ADAYLARINI AYNI MANTIKLA TEST ET
# ============================================================

world_tested = []


with ThreadPoolExecutor(
    max_workers=MAX_WORKERS
) as executor:

    futures = [
        executor.submit(
            analyze_candidate,
            entry
        )

        for entry in world_shortlist
    ]


    completed = 0


    for future in as_completed(
        futures
    ):

        try:

            result = (
                future.result()
            )


            if result:

                world_tested.append(
                    result
                )

        except Exception:

            pass


        completed += 1


        if completed % 100 == 0:

            print(
                "Dünya analiz:",
                completed,
                "/",
                len(world_shortlist)
            )


# ============================================================
# DÜNYA - EN İYİ STREAM
# ============================================================

best_world = {}


for entry in world_tested:

    name = entry[
        "name"
    ]


    country = (
        famelack_country(
            entry["info"]
        )
        if entry["source"]
        == "famelack"
        else None
    )


    if not country:

        tid = tvg_id(
            entry["info"]
        )

        m = re.search(
            r"\.([A-Za-z]{2})"
            r"(?:@|$)",
            tid
        )

        if m:

            country = (
                m.group(1)
                .lower()
            )


    country = (
        country
        or "xx"
    )


    key = (
        country,
        version_key(
            name
        )
    )


    current = best_world.get(
        key
    )


    if (
        current is None
        or entry["total_score"]
        > current["total_score"]
    ):

        best_world[key] = (
            entry
        )


# ============================================================
# DUNYA.M3U
# ============================================================

world_selected = list(
    best_world.values()
)


world_selected.sort(
    key=lambda x: (
        famelack_country(
            x["info"]
        )
        or "zz",
        normalize(
            x["name"]
        )
    )
)


world_output = [
    "#EXTM3U"
]


for entry in world_selected:

    country = (
        famelack_country(
            entry["info"]
        )
    )


    if not country:

        tid = tvg_id(
            entry["info"]
        )

        m = re.search(
            r"\.([A-Za-z]{2})"
            r"(?:@|$)",
            tid
        )

        if m:

            country = (
                m.group(1)
                .lower()
            )


    group = COUNTRIES.get(
        country,
        "🌍 Diğer"
    )


    info = replace_group(
        entry["info"],
        group
    )


    world_output.extend([
        info,
        entry["final_url"]
    ])


WORLD_OUTPUT.write_text(
    "\n".join(
        world_output
    ) + "\n",
    encoding="utf-8"
)


# ============================================================
# UYDU FTA LİSTELERİ
# ============================================================

print(
    "Türksat FTA alınıyor..."
)

turksat_channels = get_fta_channels(
    TURKSAT_URL
)

print(
    "Hotbird FTA alınıyor..."
)

hotbird_channels = get_fta_channels(
    HOTBIRD_URL
)

print(
    "Astra FTA alınıyor..."
)

astra_channels = get_fta_channels(
    ASTRA_URL
)


# ============================================================
# UYDU LİSTESİ - DÜNYA EN İYİ STREAMLERİYLE EŞLEŞTİR
# ============================================================

def build_satellite(
    satellite_names,
    group_title,
    output_path,
    turkey_mode=False
):

    selected = []


    internet_pool = (
        world_selected
        + world_tested
    )


    for satellite_name in satellite_names:

        candidates = []


        for entry in internet_pool:

            similarity = (
                name_similarity(
                    satellite_name,
                    entry["name"]
                )
            )


            if similarity < 0.92:
                continue


            rank = (
                similarity * 100000
                + entry[
                    "total_score"
                ]
            )


            candidates.append(
                (
                    rank,
                    entry
                )
            )


        # Türkiye özel kaynaklarını da özellikle dahil et.
        if turkey_mode:

            for entry in world_tested:

                similarity = (
                    name_similarity(
                        satellite_name,
                        entry["name"]
                    )
                )


                if similarity < 0.92:
                    continue


                rank = (
                    similarity * 100000
                    + entry[
                        "total_score"
                    ]
                )


                candidates.append(
                    (
                        rank,
                        entry
                    )
                )


        if not candidates:
            continue


        candidates.sort(
            key=lambda x: x[0],
            reverse=True
        )


        winner = (
            candidates[0][1]
        )


        if turkey_mode:

            group = turkey_group(
                satellite_name
            )

        else:

            group = group_title


        info = (
            '#EXTINF:-1 '
            f'group-title="{group}",'
            f'{satellite_name}'
        )


        selected.append({
            **winner,
            "info": info,
            "satellite_name": (
                satellite_name
            ),
        })


    # aynı kanal + dil + bölge yalnız bir kere
    dedupe = {}


    for entry in selected:

        key = version_key(
            entry[
                "satellite_name"
            ]
        )


        current = dedupe.get(
            key
        )


        if (
            current is None
            or entry[
                "total_score"
            ]
            > current[
                "total_score"
            ]
        ):

            dedupe[key] = entry


    selected = list(
        dedupe.values()
    )


    selected.sort(
        key=lambda x: normalize(
            x[
                "satellite_name"
            ]
        )
    )


    output = [
        "#EXTM3U"
    ]


    seen_urls = set()


    for entry in selected:

        if (
            entry["final_url"]
            in seen_urls
        ):

            continue


        output.extend([
            entry["info"],
            entry["final_url"]
        ])


        seen_urls.add(
            entry["final_url"]
        )


    output_path.write_text(
        "\n".join(
            output
        ) + "\n",
        encoding="utf-8"
    )


    return selected


# ============================================================
# 3 UYDU LİSTESİ
# ============================================================

turkey_selected = build_satellite(
    turksat_channels,
    "Türkiye",
    TURKEY_OUTPUT,
    turkey_mode=True
)


hotbird_selected = build_satellite(
    hotbird_channels,
    "Hotbird 13°E",
    HOTBIRD_OUTPUT
)


astra_selected = build_satellite(
    astra_channels,
    "Astra 19.2°E",
    ASTRA_OUTPUT
)


# ============================================================
# RAPOR
# ============================================================

print(
    "================================"
)

print(
    "LG webOS optimize işlemi tamamlandı"
)

print(
    "================================"
)

print(
    "Dunya:",
    len(world_selected)
)

print(
    "Turkiye:",
    len(turkey_selected),
    "/ FTA:",
    len(turksat_channels)
)

print(
    "Hotbird:",
    len(hotbird_selected),
    "/ FTA:",
    len(hotbird_channels)
)

print(
    "Astra:",
    len(astra_selected),
    "/ FTA:",
    len(astra_channels)
)

print(
    "ffprobe:",
    ffprobe_available()
)


print(
    "================================"
)

print(
    "Örnek kaliteli kanallar:"
)


for wanted in [
    "TV8",
    "SHOWTV",
    "KANALD",
    "STARTV",
    "TRT1",
    "HABERTURK",
    "BLOOMBERGHT",
    "CNNTURK",
]:

    matches = [
        x
        for x in turkey_selected
        if compact_name(
            x["satellite_name"]
        ) == wanted
    ]


    if matches:

        x = matches[0]

        print(
            wanted,
            "|",
            x.get(
                "height",
                0
            ),
            "p |",
            round(
                x.get(
                    "fps",
                    0
                ),
                2
            ),
            "fps |",
            x.get(
                "video_codec",
                ""
            ),
            "|",
            x.get(
                "audio_codec",
                ""
            ),
            "|",
            x[
                "final_url"
            ]
        )

    else:

        print(
            wanted,
            "| YOK"
        )
