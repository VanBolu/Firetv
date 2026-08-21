import subprocess
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from difflib import SequenceMatcher
from threading import Lock


# ============================================================
# DOSYALAR
# ============================================================

TURKEY_OUTPUT = Path("Turkiye.m3u")
WORLD_OUTPUT = Path("Dunya.m3u")
HOTBIRD_OUTPUT = Path("Hotbird.m3u")
ASTRA_OUTPUT = Path("Astra.m3u")


# ============================================================
# PERFORMANS
# ============================================================

MAX_WORKERS = 32

CURL_CONNECT_TIMEOUT = 2
CURL_TOTAL_TIMEOUT = 4

FFPROBE_TIMEOUT = 5

# Bir kanal için ağır analize kaç aday girebilir?
MAX_CANDIDATES = 2

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
        130,
    ),
    (
        "discevisita",
        "https://raw.githubusercontent.com/"
        "discevisita/iptv/main/tr.m3u",
        110,
    ),
    (
        "suphero",
        "https://raw.githubusercontent.com/"
        "suphero/IPTV/master/TR.m3u8",
        80,
    ),
]


# ============================================================
# UYDU FTA
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
# TÜRKİYE ÖZEL / YEDEK STREAMLER
# ============================================================

FALLBACKS = {
    "SHOWTV": [
        (
            "Show TV",
            "https://ciner-live.daioncdn.net/showtv/showtv.m3u8",
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


# Show TV'de master adresini koru
KEEP_MASTER = {
    "SHOWTV",
}


# ============================================================
# ENGELLENECEK PAY-TV
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
# ÜLKE ADLARI
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
# CACHE
# ============================================================

URL_ANALYSIS_CACHE = {}
CACHE_LOCK = Lock()


# ============================================================
# METİN
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
        r"\([^)]*\)|\[[^\]]*\]",
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
# CURL - SERT TIMEOUT
# ============================================================

def curl_text(url, timeout=CURL_TOTAL_TIMEOUT):
    command = [
        "curl",
        "-L",
        "-sS",
        "--fail",
        "--connect-timeout",
        str(CURL_CONNECT_TIMEOUT),
        "--max-time",
        str(timeout),
        "-A",
        "Mozilla/5.0",
        url,
    ]

    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout + 2,
        )

        if process.returncode != 0:
            return None

        return process.stdout

    except Exception:
        return None


def download_source(url, timeout=30):
    command = [
        "curl",
        "-L",
        "-sS",
        "--fail",
        "--connect-timeout",
        "5",
        "--max-time",
        str(timeout),
        "-A",
        "Mozilla/5.0",
        url,
    ]

    process = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout + 5,
    )

    if process.returncode != 0:
        raise RuntimeError(
            f"Kaynak indirilemedi: {url}"
        )

    return process.stdout


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

    return (
        match.group(1).strip()
        if match
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
# ÜLKE
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


def infer_country(entry):
    if entry["source"] == "famelack":
        country = famelack_country(
            entry["info"]
        )

        if country:
            return country

    identity = tvg_id(
        entry["info"]
    )

    match = re.search(
        r"\.([A-Za-z]{2})(?:@|$)",
        identity
    )

    if match:
        return match.group(1).lower()

    return "xx"


# ============================================================
# FİLTRE
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
# DİL
# ============================================================

LANGUAGE_WORDS = {
    "ENGLISH",
    "DEUTSCH",
    "GERMAN",
    "FRANCAIS",
    "FRENCH",
    "ITALIANO",
    "ITALIAN",
    "ESPANOL",
    "SPANISH",
    "ARABIC",
    "ARABI",
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
# TÜRKİYE GRUPLARI
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
        html = download_source(
            url,
            timeout=30
        )

    except Exception as error:
        print(
            "FTA kaynak hatası:",
            error,
            flush=True
        )

        return []

    parser = KingOfSatParser()

    parser.feed(
        html
    )

    result = []
    seen = set()

    for row in parser.rows:
        for clear_index, cell in enumerate(row):

            if normalize(cell) != "CLEAR":
                continue

            chosen = None

            for offset in (
                4,
                3,
                5,
            ):
                index = (
                    clear_index
                    - offset
                )

                if not (
                    0 <= index < len(row)
                ):
                    continue

                candidate = row[
                    index
                ].strip()

                if len(candidate) < 2:
                    continue

                if normalize(candidate) in {
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
                seen.add(key)
                result.append(chosen)

    return result


# ============================================================
# ADVERTISED RESOLUTION
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
# HLS
# ============================================================

def codec_score(codec):
    codec = (
        codec
        or ""
    ).lower()

    score = 0

    if (
        "avc1" in codec
        or "h264" in codec
    ):
        score += 600

    elif (
        "hvc1" in codec
        or "hev1" in codec
        or "hevc" in codec
    ):
        score += 350

    elif (
        "av01" in codec
        or "av1" in codec
    ):
        score += 150

    if (
        "mp4a" in codec
        or "aac" in codec
    ):
        score += 250

    return score


def quality_score(
    height,
    fps,
    bandwidth,
    codecs
):
    if height == 1080:
        score = 10000

    elif height > 1080:
        score = 9300

    elif height == 720:
        score = 8500

    elif height >= 576:
        score = 6500

    elif height >= 480:
        score = 5000

    elif height:
        score = 3000

    else:
        score = 2000

    if fps >= 49:
        score += 900

    elif fps >= 29:
        score += 450

    elif fps >= 24:
        score += 200

    score += min(
        int(
            bandwidth / 10000
        ),
        700
    )

    score += codec_score(
        codecs
    )

    return score


def inspect_hls(url):
    text = curl_text(
        url
    )

    if not text:
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

        resolution = re.search(
            r"RESOLUTION=(\d+)x(\d+)",
            line,
            re.IGNORECASE
        )

        bandwidth = re.search(
            r"(?:AVERAGE-)?BANDWIDTH=(\d+)",
            line,
            re.IGNORECASE
        )

        fps = re.search(
            r"FRAME-RATE=([\d.]+)",
            line,
            re.IGNORECASE
        )

        codecs = re.search(
            r'CODECS="([^"]+)"',
            line,
            re.IGNORECASE
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

        height = (
            int(
                resolution.group(2)
            )
            if resolution
            else 0
        )

        bit = (
            int(
                bandwidth.group(1)
            )
            if bandwidth
            else 0
        )

        frame = (
            float(
                fps.group(1)
            )
            if fps
            else 0
        )

        codec_text = (
            codecs.group(1)
            if codecs
            else ""
        )

        variant_url = urljoin(
            url,
            lines[j].strip()
        )

        variants.append({
            "url": variant_url,
            "height": height,
            "fps": frame,
            "bandwidth": bit,
            "codecs": codec_text,
            "score": quality_score(
                height,
                frame,
                bit,
                codec_text
            ),
        })

    if not variants:
        return {
            "url": url,
            "height": 0,
            "fps": 0,
            "bandwidth": 0,
            "codecs": "",
            "score": 2000,
            "needs_probe": True,
        }

    best = max(
        variants,
        key=lambda x: x[
            "score"
        ]
    )

    best[
        "needs_probe"
    ] = (
        best["height"] == 0
        or not best["codecs"]
    )

    return best


# ============================================================
# FFPROBE - HARD TIMEOUT
# ============================================================

def ffprobe_stream(url):
    command = [
        "ffprobe",
        "-v",
        "error",
        "-rw_timeout",
        "2500000",
        "-analyzeduration",
        "600000",
        "-probesize",
        "600000",
        "-show_entries",
        (
            "stream="
            "codec_type,"
            "codec_name,"
            "height,"
            "avg_frame_rate,"
            "r_frame_rate,"
            "bit_rate"
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
            timeout=FFPROBE_TIMEOUT,
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
                stream.get(
                    "codec_type"
                )
                == "video"
                and video is None
            ):
                video = stream

            elif (
                stream.get(
                    "codec_type"
                )
                == "audio"
                and audio is None
            ):
                audio = stream

        if not video:
            return {}

        frame = (
            video.get(
                "avg_frame_rate"
            )
            or video.get(
                "r_frame_rate"
            )
            or "0/1"
        )

        try:
            num, den = frame.split("/")

            fps = (
                float(num)
                / float(den)
                if float(den)
                else 0
            )

        except Exception:
            fps = 0

        try:
            bitrate = int(
                video.get(
                    "bit_rate",
                    0
                )
                or 0
            )

        except Exception:
            bitrate = 0

        return {
            "height": int(
                video.get(
                    "height",
                    0
                )
                or 0
            ),

            "fps": fps,

            "bandwidth": bitrate,

            "video_codec": video.get(
                "codec_name",
                ""
            ),

            "audio_codec": (
                audio.get(
                    "codec_name",
                    ""
                )
                if audio
                else ""
            ),
        }

    except Exception:
        return {}


# ============================================================
# ADAY ANALİZ
# ============================================================

def analyze_url(entry):
    url = entry["url"]

    with CACHE_LOCK:
        cached = (
            URL_ANALYSIS_CACHE.get(
                url
            )
        )

    if cached is not None:
        if not cached:
            return None

        return {
            **entry,
            **cached,
        }

    manifest = inspect_hls(
        url
    )

    if not manifest:
        with CACHE_LOCK:
            URL_ANALYSIS_CACHE[
                url
            ] = False

        return None

    identity = compact_name(
        channel_name(
            entry["info"]
        )
    )

    final_url = (
        url
        if identity in KEEP_MASTER
        else manifest["url"]
    )

    result = {
        "final_url": final_url,

        "height": (
            manifest["height"]
            or advertised_resolution(
                entry["info"]
            )
        ),

        "fps": manifest["fps"],

        "bitrate": (
            manifest[
                "bandwidth"
            ]
        ),

        "video_codec": (
            manifest["codecs"]
        ),

        "audio_codec": "",

        "quality_score": (
            manifest["score"]
        ),
    }

    # Yalnız manifest bilgisi eksikse probe
    if manifest[
        "needs_probe"
    ]:
        probe = ffprobe_stream(
            final_url
        )

        if probe:
            video_codec = probe.get(
                "video_codec",
                ""
            )

            audio_codec = probe.get(
                "audio_codec",
                ""
            )

            codec_text = (
                video_codec
                + " "
                + audio_codec
            )

            result.update({
                "height": (
                    probe.get(
                        "height",
                        0
                    )
                    or result[
                        "height"
                    ]
                ),

                "fps": probe.get(
                    "fps",
                    0
                ),

                "bitrate": probe.get(
                    "bandwidth",
                    0
                ),

                "video_codec":
                    video_codec,

                "audio_codec":
                    audio_codec,
            })

            result[
                "quality_score"
            ] = quality_score(
                result["height"],
                result["fps"],
                result["bitrate"],
                codec_text,
            )

    result[
        "total_score"
    ] = (
        result[
            "quality_score"
        ]
        + entry.get(
            "source_score",
            0
        ) * 5
    )

    with CACHE_LOCK:
        URL_ANALYSIS_CACHE[
            url
        ] = result

    return {
        **entry,
        **result,
    }


# ============================================================
# COARSE SCORE
# ============================================================

def coarse_score(entry):
    score = entry.get(
        "source_score",
        0
    )

    resolution = advertised_resolution(
        entry["info"]
    )

    if resolution == 1080:
        score += 600

    elif resolution > 1080:
        score += 550

    elif resolution == 720:
        score += 450

    elif resolution:
        score += 250

    if entry[
        "url"
    ].startswith(
        "https://"
    ):
        score += 50

    return score


# ============================================================
# ADAY SAYISINI DÜŞÜR
# ============================================================

def make_shortlist(groups):
    shortlist = []

    seen_urls = set()

    for options in groups.values():

        # URL tekrarlarını önce kaldır
        unique = {}

        for entry in options:
            url = entry["url"]

            existing = unique.get(
                url
            )

            if (
                existing is None
                or coarse_score(entry)
                > coarse_score(
                    existing
                )
            ):
                unique[url] = entry

        options = list(
            unique.values()
        )

        options.sort(
            key=coarse_score,
            reverse=True
        )

        if not options:
            continue

        # Her zaman en iyi metadata adayı
        chosen = [
            options[0]
        ]

        # İkinci aday yalnız gerçekten yakınsa.
        if (
            len(options) > 1
            and (
                coarse_score(
                    options[0]
                )
                - coarse_score(
                    options[1]
                )
                <= 120
            )
        ):
            chosen.append(
                options[1]
            )

        for entry in chosen:
            url = entry[
                "url"
            ]

            if url in seen_urls:
                continue

            seen_urls.add(url)
            shortlist.append(
                entry
            )

    return shortlist


# ============================================================
# PARALEL ANALİZ
# ============================================================

def analyze_groups(groups):
    shortlist = make_shortlist(
        groups
    )

    print(
        "Ağır analiz adayı:",
        len(shortlist),
        flush=True
    )

    tested = []

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        futures = [
            executor.submit(
                analyze_url,
                entry
            )
            for entry in shortlist
        ]

        total = len(futures)

        for index, future in enumerate(
            as_completed(futures),
            1
        ):
            try:
                result = future.result()

                if result:
                    tested.append(
                        result
                    )

            except Exception:
                pass

            if (
                index % 250 == 0
                or index == total
            ):
                print(
                    "Analiz:",
                    index,
                    "/",
                    total,
                    flush=True
                )

    return tested


# ============================================================
# EN İYİ DÜNYA KAYDI
# ============================================================

def select_best_world(tested):
    best = {}

    for entry in tested:
        key = (
            infer_country(
                entry
            ),
            version_key(
                channel_name(
                    entry["info"]
                )
            ),
        )

        current = best.get(
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
            best[key] = entry

    return list(
        best.values()
    )


# ============================================================
# İSİM BENZERLİĞİ
# ============================================================

def name_similarity(a, b):
    a = compact_name(a)
    b = compact_name(b)

    if not a or not b:
        return 0

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
# UYDU EŞLEŞTİRME
# ============================================================

def build_satellite(
    satellite_names,
    internet_pool,
    group_name,
    output_file,
    turkey_mode=False,
):
    # Exact-name index
    exact_index = {}

    for entry in internet_pool:
        name = channel_name(
            entry["info"]
        )

        exact_index.setdefault(
            compact_name(name),
            []
        ).append(entry)

    selected = []

    for sat_name in satellite_names:
        sat_key = compact_name(
            sat_name
        )

        candidates = exact_index.get(
            sat_key,
            []
        )

        # Exact yoksa fuzzy
        if not candidates:
            fuzzy = []

            for entry in internet_pool:
                name = channel_name(
                    entry["info"]
                )

                similarity = name_similarity(
                    sat_name,
                    name
                )

                if similarity >= 0.92:
                    fuzzy.append(
                        (
                            similarity,
                            entry
                        )
                    )

            fuzzy.sort(
                key=lambda x: (
                    x[0],
                    x[1][
                        "total_score"
                    ]
                ),
                reverse=True
            )

            candidates = [
                item[1]
                for item in fuzzy[:3]
            ]

        if not candidates:
            continue

        winner = max(
            candidates,
            key=lambda x: x[
                "total_score"
            ]
        )

        group = (
            turkey_group(
                sat_name
            )
            if turkey_mode
            else group_name
        )

        selected.append({
            **winner,

            "satellite_name":
                sat_name,

            "info":
                (
                    '#EXTINF:-1 '
                    f'group-title="{group}",'
                    f'{sat_name}'
                ),
        })

    # Aynı uydu kanalını bir kez tut
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
            dedupe[
                key
            ] = entry

    selected = list(
        dedupe.values()
    )

    selected.sort(
        key=lambda x:
        normalize(
            x[
                "satellite_name"
            ]
        )
    )

    output = [
        "#EXTM3U"
    ]

    for entry in selected:
        output.extend([
            entry["info"],
            entry["final_url"],
        ])

    output_file.write_text(
        "\n".join(
            output
        ) + "\n",
        encoding="utf-8"
    )

    return selected


# ============================================================
# BAŞLA
# ============================================================

print(
    "1/7 Kaynaklar indiriliyor...",
    flush=True
)


famelack_entries = parse_entries(
    download_source(
        FAMELACK_M3U,
        timeout=30
    ),
    "famelack",
    80,
)


try:
    iptv_world_entries = parse_entries(
        download_source(
            IPTVORG_WORLD,
            timeout=40
        ),
        "iptv-org-world",
        120,
    )

except Exception as error:
    print(
        "IPTV-org world alınamadı:",
        error,
        flush=True
    )

    iptv_world_entries = []


# ============================================================
# TÜRKİYE KAYNAKLARI
# ============================================================

turkey_extra = []


for source, url, score in TURKEY_SOURCES:
    try:
        turkey_extra.extend(
            parse_entries(
                download_source(
                    url,
                    timeout=20
                ),
                source,
                score,
            )
        )

    except Exception as error:
        print(
            source,
            "alınamadı:",
            error,
            flush=True
        )


for identity, alternatives in FALLBACKS.items():
    for name, url, resolution in alternatives:

        turkey_extra.append({
            "info": (
                '#EXTINF:-1 '
                f'tvg-id="{identity}" '
                f'group-title="{turkey_group(name)}",'
                f'{name} ({resolution}p)'
            ),

            "url": url,

            "source": "fallback",

            "source_score": 140,
        })


# ============================================================
# DÜNYA GRUPLARI
# ============================================================

print(
    "2/7 Dünya adayları hazırlanıyor...",
    flush=True
)


world_candidates = (
    famelack_entries
    + iptv_world_entries
)


world_groups = {}


for entry in world_candidates:
    if rejected(
        entry["info"]
    ):
        continue

    name = channel_name(
        entry["info"]
    )

    if not name:
        continue

    key = (
        infer_country(
            entry
        ),
        version_key(
            name
        ),
    )

    world_groups.setdefault(
        key,
        []
    ).append(entry)


print(
    "Dünya kanal/sürüm grubu:",
    len(world_groups),
    flush=True
)


# ============================================================
# DÜNYA ANALİZ
# ============================================================

print(
    "3/7 Dünya streamleri analiz ediliyor...",
    flush=True
)


world_tested = analyze_groups(
    world_groups
)


world_selected = select_best_world(
    world_tested
)


print(
    "Çalışan dünya kanal/sürüm:",
    len(world_selected),
    flush=True
)


# ============================================================
# DUNYA.M3U
# ============================================================

world_selected.sort(
    key=lambda entry: (
        infer_country(
            entry
        ),
        normalize(
            channel_name(
                entry["info"]
            )
        ),
    )
)


world_output = [
    "#EXTM3U"
]


for entry in world_selected:
    country = infer_country(
        entry
    )

    group = COUNTRIES.get(
        country,
        "🌍 Diğer"
    )

    world_output.extend([
        replace_group(
            entry["info"],
            group
        ),

        entry[
            "final_url"
        ],
    ])


WORLD_OUTPUT.write_text(
    "\n".join(
        world_output
    ) + "\n",
    encoding="utf-8"
)


# ============================================================
# TÜRKİYE EK STREAM ANALİZ
# ============================================================

print(
    "4/7 Türkiye özel streamleri analiz ediliyor...",
    flush=True
)


turkey_groups = {}


for entry in turkey_extra:
    name = channel_name(
        entry["info"]
    )

    if not name:
        continue

    turkey_groups.setdefault(
        version_key(name),
        []
    ).append(entry)


turkey_tested = analyze_groups(
    turkey_groups
)


turkey_pool = (
    turkey_tested
    + world_selected
)


# ============================================================
# FTA UYDU
# ============================================================

print(
    "5/7 FTA uydu listeleri indiriliyor...",
    flush=True
)


turksat_channels = get_fta_channels(
    TURKSAT_URL
)

hotbird_channels = get_fta_channels(
    HOTBIRD_URL
)

astra_channels = get_fta_channels(
    ASTRA_URL
)


print(
    "Türksat FTA:",
    len(turksat_channels),
    flush=True
)

print(
    "Hotbird FTA:",
    len(hotbird_channels),
    flush=True
)

print(
    "Astra FTA:",
    len(astra_channels),
    flush=True
)


# ============================================================
# UYDU PLAYLISTLER
# ============================================================

print(
    "6/7 Uydu eşleştirmeleri yapılıyor...",
    flush=True
)


turkey_selected = build_satellite(
    turksat_channels,
    turkey_pool,
    "Türkiye",
    TURKEY_OUTPUT,
    turkey_mode=True,
)


hotbird_selected = build_satellite(
    hotbird_channels,
    world_selected,
    "Hotbird 13°E",
    HOTBIRD_OUTPUT,
)


astra_selected = build_satellite(
    astra_channels,
    world_selected,
    "Astra 19.2°E",
    ASTRA_OUTPUT,
)


# ============================================================
# RAPOR
# ============================================================

print(
    "7/7 TAMAMLANDI",
    flush=True
)

print(
    "================================",
    flush=True
)

print(
    "Dunya:",
    len(world_selected),
    flush=True
)

print(
    "Turkiye:",
    len(turkey_selected),
    "/ FTA:",
    len(turksat_channels),
    flush=True
)

print(
    "Hotbird:",
    len(hotbird_selected),
    "/ FTA:",
    len(hotbird_channels),
    flush=True
)

print(
    "Astra:",
    len(astra_selected),
    "/ FTA:",
    len(astra_channels),
    flush=True
)

print(
    "Tekil analiz edilen URL:",
    len(URL_ANALYSIS_CACHE),
    flush=True
)

print(
    "================================",
    flush=True
)
