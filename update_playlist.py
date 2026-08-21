import subprocess
import json
import re
import unicodedata
import os
from pathlib import Path
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from difflib import SequenceMatcher
from threading import Lock


# ============================================================
# AYARLAR
# ============================================================

FINAL_FILES = {
    "turkey": Path("Turkiye.m3u"),
    "world": Path("Dunya.m3u"),
    "hotbird": Path("Hotbird.m3u"),
    "astra": Path("Astra.m3u"),
}

TEMP_FILES = {
    key: Path(str(path) + ".tmp")
    for key, path in FINAL_FILES.items()
}

TARGET_HEIGHT = 1080

# Detaylı mod
MAX_CANDIDATES_PER_CHANNEL = 5

# Hızlı manifest taraması
MANIFEST_WORKERS = 40

# Ağır ffprobe taraması
PROBE_WORKERS = 20

# Manifest taramasından sonra kanal başına kaç aday gerçek ffprobe alacak?
PROBE_TOP_N = 3

CURL_CONNECT_TIMEOUT = 3
CURL_TOTAL_TIMEOUT = 7

FFPROBE_TIMEOUT = 10


# ============================================================
# KAYNAKLAR
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
        140,
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
# UYDU FTA KAYNAKLARI
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


# Master adresi korunacak kanallar
KEEP_MASTER = {
    "SHOWTV",
}


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


MANIFEST_CACHE = {}
PROBE_CACHE = {}

CACHE_LOCK = Lock()


# ============================================================
# METİN NORMALİZASYONU
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
# DOWNLOAD
# ============================================================

def curl_text(
    url,
    total_timeout=CURL_TOTAL_TIMEOUT
):
    command = [
        "curl",
        "-L",
        "-sS",
        "--fail",
        "--connect-timeout",
        str(CURL_CONNECT_TIMEOUT),
        "--max-time",
        str(total_timeout),
        "-A",
        "Mozilla/5.0",
        url,
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=total_timeout + 3,
        )

        if result.returncode != 0:
            return None

        return result.stdout

    except Exception:
        return None


def download_source(
    url,
    timeout=40
):
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

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout + 5,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Kaynak indirilemedi: {url}"
        )

    return result.stdout


# ============================================================
# M3U
# ============================================================

def parse_entries(
    text,
    source="",
    source_score=0
):
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
                "source_score": source_score,
            })

        i = j + 1

    return result


def channel_name(info):
    if "," not in info:
        return ""

    return info.split(
        ",",
        1
    )[1].strip()


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


def replace_group(
    info,
    group
):
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
    if entry[
        "source"
    ] == "famelack":

        result = famelack_country(
            entry["info"]
        )

        if result:
            return result

    tid = tvg_id(
        entry["info"]
    )

    match = re.search(
        r"\.([A-Za-z]{2})(?:@|$)",
        tid
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
# DİL / SÜRÜM
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
    words = set(
        match_name(
            name
        ).split()
    )

    for item in LANGUAGE_WORDS:
        if item in words:
            return item

    return ""


def version_key(name):
    return (
        compact_name(name),
        language_variant(name),
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

class KingOfSatParser(
    HTMLParser
):
    def __init__(self):
        super().__init__()

        self.rows = []

        self.row = []
        self.cell = []

        self.in_row = False
        self.in_cell = False


    def handle_starttag(
        self,
        tag,
        attrs
    ):
        if tag == "tr":
            self.in_row = True
            self.row = []

        elif (
            tag in ("td", "th")
            and self.in_row
        ):
            self.in_cell = True
            self.cell = []


    def handle_data(
        self,
        data
    ):
        if self.in_cell:
            self.cell.append(
                data
            )


    def handle_endtag(
        self,
        tag
    ):
        if (
            tag in ("td", "th")
            and self.in_cell
        ):
            value = " ".join(
                self.cell
            )

            value = re.sub(
                r"\s+",
                " ",
                value
            ).strip()

            self.row.append(
                value
            )

            self.in_cell = False

        elif (
            tag == "tr"
            and self.in_row
        ):
            if self.row:
                self.rows.append(
                    self.row
                )

            self.in_row = False


def get_fta_channels(url):
    html = download_source(
        url,
        timeout=40
    )

    parser = KingOfSatParser()

    parser.feed(html)

    result = []
    seen = set()

    for row in parser.rows:
        for clear_index, cell in enumerate(
            row
        ):
            if normalize(
                cell
            ) != "CLEAR":
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
                    0
                    <= index
                    < len(row)
                ):
                    continue

                candidate = row[
                    index
                ].strip()

                if len(
                    candidate
                ) < 2:
                    continue

                if normalize(
                    candidate
                ) in {
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
                result.append(
                    chosen
                )

    return result


# ============================================================
# ÇÖZÜNÜRLÜK / PUAN
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


def codec_points(codec):
    codec = (
        codec
        or ""
    ).lower()

    score = 0

    if (
        "avc1" in codec
        or "h264" in codec
    ):
        score += 700

    elif (
        "hvc1" in codec
        or "hev1" in codec
        or "hevc" in codec
        or "h265" in codec
    ):
        score += 400

    elif (
        "av1" in codec
        or "av01" in codec
    ):
        score += 180

    if (
        "aac" in codec
        or "mp4a" in codec
    ):
        score += 300

    return score


def quality_score(
    height,
    fps,
    bitrate,
    codec
):
    if height == 1080:
        score = 10000

    elif height > 1080:
        score = 9400

    elif height == 720:
        score = 8500

    elif height >= 576:
        score = 6500

    elif height >= 480:
        score = 5000

    elif height:
        score = 3000

    else:
        score = 1800

    if fps >= 49:
        score += 1000

    elif fps >= 29:
        score += 500

    elif fps >= 24:
        score += 250

    score += min(
        int(
            bitrate / 10000
        ),
        800
    )

    score += codec_points(
        codec
    )

    return score


# ============================================================
# HLS MANIFEST TARAMASI
# ============================================================

def inspect_manifest(entry):
    url = entry[
        "url"
    ]

    with CACHE_LOCK:
        if url in MANIFEST_CACHE:
            cached = MANIFEST_CACHE[
                url
            ]

            if not cached:
                return None

            return {
                **entry,
                **cached,
            }

    text = curl_text(
        url
    )

    if not text:
        with CACHE_LOCK:
            MANIFEST_CACHE[
                url
            ] = False

        return None

    # Direkt medya URL ise ffprobe aşamasına bırak.
    if "#EXTM3U" not in text:
        result = {
            "final_url": url,
            "manifest_height":
                advertised_resolution(
                    entry["info"]
                ),
            "manifest_fps": 0,
            "manifest_bitrate": 0,
            "manifest_codec": "",
            "manifest_score": 1500,
            "needs_probe": True,
        }

        with CACHE_LOCK:
            MANIFEST_CACHE[
                url
            ] = result

        return {
            **entry,
            **result,
        }

    lines = text.splitlines()

    variants = []

    for i, line in enumerate(
        lines
    ):
        if not line.startswith(
            "#EXT-X-STREAM-INF:"
        ):
            continue

        resolution = re.search(
            r"RESOLUTION=(\d+)x(\d+)",
            line,
            re.IGNORECASE
        )

        bitrate = re.search(
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

        band = (
            int(
                bitrate.group(1)
            )
            if bitrate
            else 0
        )

        frame = (
            float(
                fps.group(1)
            )
            if fps
            else 0
        )

        codec = (
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
            "bitrate": band,
            "codec": codec,
            "score": quality_score(
                height,
                frame,
                band,
                codec,
            ),
        })

    if variants:
        best = max(
            variants,
            key=lambda x: x[
                "score"
            ]
        )

        identity = compact_name(
            channel_name(
                entry["info"]
            )
        )

        result = {
            "final_url": (
                url
                if identity in KEEP_MASTER
                else best["url"]
            ),

            "manifest_height":
                best["height"],

            "manifest_fps":
                best["fps"],

            "manifest_bitrate":
                best["bitrate"],

            "manifest_codec":
                best["codec"],

            "manifest_score":
                best["score"],

            "needs_probe": (
                best["height"] == 0
                or not best["codec"]
            ),
        }

    else:
        # Media playlist
        result = {
            "final_url": url,

            "manifest_height":
                advertised_resolution(
                    entry["info"]
                ),

            "manifest_fps": 0,

            "manifest_bitrate": 0,

            "manifest_codec": "",

            "manifest_score": (
                2500
                if advertised_resolution(
                    entry["info"]
                )
                else 1800
            ),

            "needs_probe": True,
        }

    with CACHE_LOCK:
        MANIFEST_CACHE[
            url
        ] = result

    return {
        **entry,
        **result,
    }


# ============================================================
# FFPROBE
# ============================================================

def probe_url(entry):
    url = entry[
        "final_url"
    ]

    with CACHE_LOCK:
        cached = PROBE_CACHE.get(
            url
        )

    if cached is not None:
        if not cached:
            return {
                **entry,
                "final_score":
                    entry[
                        "manifest_score"
                    ],
            }

        return {
            **entry,
            **cached,
        }

    command = [
        "ffprobe",
        "-v",
        "error",
        "-rw_timeout",
        "5000000",
        "-analyzeduration",
        "1200000",
        "-probesize",
        "1200000",
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
            raise RuntimeError()

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
            raise RuntimeError()

        height = int(
            video.get(
                "height",
                0
            )
            or entry[
                "manifest_height"
            ]
            or 0
        )

        frame_value = (
            video.get(
                "avg_frame_rate"
            )
            or video.get(
                "r_frame_rate"
            )
            or "0/1"
        )

        try:
            numerator, denominator = (
                frame_value.split("/")
            )

            fps = (
                float(numerator)
                / float(denominator)
                if float(denominator)
                else 0
            )

        except Exception:
            fps = (
                entry[
                    "manifest_fps"
                ]
            )

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

        if not bitrate:
            bitrate = entry[
                "manifest_bitrate"
            ]

        video_codec = video.get(
            "codec_name",
            ""
        )

        audio_codec = (
            audio.get(
                "codec_name",
                ""
            )
            if audio
            else ""
        )

        codec_string = (
            video_codec
            + " "
            + audio_codec
        )

        score = quality_score(
            height,
            fps,
            bitrate,
            codec_string,
        )

        result = {
            "height": height,
            "fps": fps,
            "bitrate": bitrate,
            "video_codec":
                video_codec,
            "audio_codec":
                audio_codec,
            "final_score":
                score,
        }

        with CACHE_LOCK:
            PROBE_CACHE[
                url
            ] = result

        return {
            **entry,
            **result,
        }

    except Exception:
        with CACHE_LOCK:
            PROBE_CACHE[
                url
            ] = False

        return {
            **entry,

            "height":
                entry[
                    "manifest_height"
                ],

            "fps":
                entry[
                    "manifest_fps"
                ],

            "bitrate":
                entry[
                    "manifest_bitrate"
                ],

            "video_codec":
                entry[
                    "manifest_codec"
                ],

            "audio_codec": "",

            "final_score":
                entry[
                    "manifest_score"
                ],
        }


# ============================================================
# KABA PUAN
# ============================================================

def coarse_score(entry):
    score = entry.get(
        "source_score",
        0
    )

    height = advertised_resolution(
        entry["info"]
    )

    if height == 1080:
        score += 600

    elif height > 1080:
        score += 550

    elif height == 720:
        score += 450

    elif height:
        score += 250

    if entry[
        "url"
    ].startswith(
        "https://"
    ):
        score += 50

    return score


# ============================================================
# DETAYLI KANAL ANALİZİ
# ============================================================

def analyze_channel_groups(
    groups,
    label
):
    # ----------------------------------------
    # AŞAMA 1:
    # Her kanal için maksimum 5 en iyi metadata adayı.
    # ----------------------------------------

    preliminary = []

    for key, options in groups.items():
        unique = {}

        for entry in options:
            url = entry[
                "url"
            ]

            if (
                url not in unique
                or coarse_score(
                    entry
                )
                >
                coarse_score(
                    unique[url]
                )
            ):
                unique[
                    url
                ] = entry

        options = list(
            unique.values()
        )

        options.sort(
            key=coarse_score,
            reverse=True
        )

        for entry in options[
            :MAX_CANDIDATES_PER_CHANNEL
        ]:
            preliminary.append({
                **entry,
                "_group_key": key,
            })

    print(
        label,
        "- manifest adayı:",
        len(preliminary),
        flush=True
    )

    # ----------------------------------------
    # AŞAMA 2:
    # Hızlı manifest/erişim taraması.
    # ----------------------------------------

    working = []

    with ThreadPoolExecutor(
        max_workers=MANIFEST_WORKERS
    ) as executor:

        futures = [
            executor.submit(
                inspect_manifest,
                entry
            )
            for entry in preliminary
        ]

        total = len(futures)

        for index, future in enumerate(
            as_completed(futures),
            1
        ):
            try:
                item = future.result()

                if item:
                    working.append(
                        item
                    )

            except Exception:
                pass

            if (
                index % 500 == 0
                or index == total
            ):
                print(
                    label,
                    "- manifest:",
                    index,
                    "/",
                    total,
                    flush=True
                )

    # ----------------------------------------
    # AŞAMA 3:
    # Her kanal için çalışan adayları puanla.
    # En iyi 3 tanesi ffprobe.
    # ----------------------------------------

    working_groups = {}

    for entry in working:
        working_groups.setdefault(
            entry[
                "_group_key"
            ],
            []
        ).append(entry)

    probe_candidates = []

    for key, options in working_groups.items():
        options.sort(
            key=lambda x: (
                x[
                    "manifest_score"
                ],
                x.get(
                    "source_score",
                    0
                ),
            ),
            reverse=True
        )

        probe_candidates.extend(
            options[
                :PROBE_TOP_N
            ]
        )

    print(
        label,
        "- ffprobe adayı:",
        len(probe_candidates),
        flush=True
    )

    # ----------------------------------------
    # AŞAMA 4:
    # Ağır gerçek stream analizi.
    # ----------------------------------------

    probed = []

    with ThreadPoolExecutor(
        max_workers=PROBE_WORKERS
    ) as executor:

        futures = [
            executor.submit(
                probe_url,
                entry
            )
            for entry in probe_candidates
        ]

        total = len(futures)

        for index, future in enumerate(
            as_completed(futures),
            1
        ):
            try:
                item = future.result()

                if item:
                    item[
                        "total_score"
                    ] = (
                        item[
                            "final_score"
                        ]
                        +
                        item.get(
                            "source_score",
                            0
                        ) * 5
                    )

                    probed.append(
                        item
                    )

            except Exception:
                pass

            if (
                index % 250 == 0
                or index == total
            ):
                print(
                    label,
                    "- ffprobe:",
                    index,
                    "/",
                    total,
                    flush=True
                )

    # ----------------------------------------
    # AŞAMA 5:
    # Her kanal/dil/bölge için en iyi çalışan stream.
    # ----------------------------------------

    winners = {}

    for entry in probed:
        key = entry[
            "_group_key"
        ]

        current = winners.get(
            key
        )

        if (
            current is None
            or entry[
                "total_score"
            ]
            >
            current[
                "total_score"
            ]
        ):
            winners[
                key
            ] = entry

    print(
        label,
        "- seçilen:",
        len(winners),
        flush=True
    )

    return list(
        winners.values()
    )


# ============================================================
# İSİM BENZERLİĞİ
# ============================================================

def similarity(
    first,
    second
):
    first = compact_name(
        first
    )

    second = compact_name(
        second
    )

    if (
        not first
        or not second
    ):
        return 0

    if first == second:
        return 1.0

    if (
        min(
            len(first),
            len(second)
        ) >= 5
        and (
            first in second
            or second in first
        )
    ):
        return 0.96

    return SequenceMatcher(
        None,
        first,
        second
    ).ratio()


# ============================================================
# UYDU EŞLEŞTİRME
# ============================================================

def build_satellite(
    satellite_channels,
    stream_pool,
    title,
    temporary_file,
    turkey=False,
):
    exact = {}

    for entry in stream_pool:
        name = channel_name(
            entry["info"]
        )

        exact.setdefault(
            compact_name(
                name
            ),
            []
        ).append(entry)

    selected = []

    for sat_name in satellite_channels:
        key = compact_name(
            sat_name
        )

        candidates = exact.get(
            key,
            []
        )

        if not candidates:
            fuzzy = []

            for entry in stream_pool:
                score = similarity(
                    sat_name,
                    channel_name(
                        entry["info"]
                    )
                )

                if score >= 0.90:
                    fuzzy.append(
                        (
                            score,
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
                for item in fuzzy[
                    :5
                ]
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
            if turkey
            else title
        )

        selected.append({
            **winner,

            "satellite_name":
                sat_name,

            "output_info":
                (
                    '#EXTINF:-1 '
                    f'group-title="{group}",'
                    f'{sat_name}'
                ),
        })

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
            >
            current[
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
        key=lambda x: normalize(
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
            entry[
                "output_info"
            ],
            entry[
                "final_url"
            ],
        ])

    temporary_file.write_text(
        "\n".join(
            output
        ) + "\n",
        encoding="utf-8"
    )

    return selected


# ============================================================
# WORLD PLAYLIST
# ============================================================

def write_world(
    entries,
    target
):
    entries.sort(
        key=lambda x: (
            infer_country(x),
            normalize(
                channel_name(
                    x["info"]
                )
            ),
        )
    )

    output = [
        "#EXTM3U"
    ]

    for entry in entries:
        country = infer_country(
            entry
        )

        group = COUNTRIES.get(
            country,
            "🌍 Diğer"
        )

        output.extend([
            replace_group(
                entry["info"],
                group
            ),

            entry[
                "final_url"
            ],
        ])

    target.write_text(
        "\n".join(
            output
        ) + "\n",
        encoding="utf-8"
    )


# ============================================================
# TEMP DOSYA TEMİZLİĞİ
# ============================================================

def cleanup_temp():
    for path in TEMP_FILES.values():
        try:
            if path.exists():
                path.unlink()
        except Exception:
            pass


cleanup_temp()


# ============================================================
# ANA PROGRAM
# ============================================================

try:
    print(
        "1/8 Kaynaklar indiriliyor...",
        flush=True
    )

    famelack = parse_entries(
        download_source(
            FAMELACK_M3U,
            45
        ),
        "famelack",
        90,
    )

    try:
        iptv_world = parse_entries(
            download_source(
                IPTVORG_WORLD,
                60
            ),
            "iptv-org-world",
            140,
        )

    except Exception as error:
        print(
            "IPTV-org world hatası:",
            error,
            flush=True
        )

        iptv_world = []

    turkey_extra = []

    for (
        source,
        url,
        source_score
    ) in TURKEY_SOURCES:

        try:
            turkey_extra.extend(
                parse_entries(
                    download_source(
                        url,
                        30
                    ),
                    source,
                    source_score,
                )
            )

        except Exception as error:
            print(
                source,
                "hatası:",
                error,
                flush=True
            )

    for identity, alternatives in FALLBACKS.items():
        for (
            name,
            url,
            resolution
        ) in alternatives:

            turkey_extra.append({
                "info": (
                    '#EXTINF:-1 '
                    f'tvg-id="{identity}" '
                    f'group-title="{turkey_group(name)}",'
                    f'{name} ({resolution}p)'
                ),

                "url": url,

                "source":
                    "fallback",

                "source_score":
                    170,
            })


    # ========================================================
    # DÜNYA GRUPLARI
    # ========================================================

    print(
        "2/8 Dünya kanal grupları hazırlanıyor...",
        flush=True
    )

    world_groups = {}

    for entry in (
        famelack
        + iptv_world
    ):
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


    # ========================================================
    # DÜNYA DETAYLI ANALİZ
    # ========================================================

    print(
        "3/8 Dünya detaylı analiz...",
        flush=True
    )

    world_selected = (
        analyze_channel_groups(
            world_groups,
            "DUNYA"
        )
    )

    write_world(
        world_selected,
        TEMP_FILES[
            "world"
        ]
    )


    # ========================================================
    # TÜRKİYE EK ADAYLARI
    # ========================================================

    print(
        "4/8 Türkiye özel kaynak analizi...",
        flush=True
    )

    turkey_groups = {}

    for entry in turkey_extra:
        if rejected(
            entry["info"]
        ):
            continue

        name = channel_name(
            entry["info"]
        )

        if not name:
            continue

        turkey_groups.setdefault(
            version_key(
                name
            ),
            []
        ).append(entry)

    turkey_selected_extra = (
        analyze_channel_groups(
            turkey_groups,
            "TURKIYE-OZEL"
        )
    )

    turkey_pool = (
        turkey_selected_extra
        + world_selected
    )


    # ========================================================
    # FTA UYDU LİSTELERİ
    # ========================================================

    print(
        "5/8 FTA uydu listeleri...",
        flush=True
    )

    turksat_fta = get_fta_channels(
        TURKSAT_URL
    )

    hotbird_fta = get_fta_channels(
        HOTBIRD_URL
    )

    astra_fta = get_fta_channels(
        ASTRA_URL
    )

    print(
        "Türksat FTA:",
        len(turksat_fta),
        flush=True
    )

    print(
        "Hotbird FTA:",
        len(hotbird_fta),
        flush=True
    )

    print(
        "Astra FTA:",
        len(astra_fta),
        flush=True
    )


    # ========================================================
    # GÜVENLİK KONTROLÜ
    # ========================================================

    if len(
        world_selected
    ) < 1000:
        raise RuntimeError(
            "Dünya kanal sayısı anormal derecede düşük."
        )

    if len(
        turksat_fta
    ) < 50:
        raise RuntimeError(
            "Türksat FTA verisi anormal derecede düşük."
        )

    if len(
        hotbird_fta
    ) < 50:
        raise RuntimeError(
            "Hotbird FTA verisi anormal derecede düşük."
        )

    if len(
        astra_fta
    ) < 50:
        raise RuntimeError(
            "Astra FTA verisi anormal derecede düşük."
        )


    # ========================================================
    # UYDU LİSTELERİ
    # ========================================================

    print(
        "6/8 Uydu eşleştirme...",
        flush=True
    )

    turkey_final = build_satellite(
        turksat_fta,
        turkey_pool,
        "Türkiye",
        TEMP_FILES[
            "turkey"
        ],
        turkey=True,
    )

    hotbird_final = build_satellite(
        hotbird_fta,
        world_selected,
        "Hotbird 13°E",
        TEMP_FILES[
            "hotbird"
        ],
    )

    astra_final = build_satellite(
        astra_fta,
        world_selected,
        "Astra 19.2°E",
        TEMP_FILES[
            "astra"
        ],
    )


    # ========================================================
    # SONUÇ KONTROLÜ
    # ========================================================

    print(
        "7/8 Sonuç kontrolü...",
        flush=True
    )

    if len(
        turkey_final
    ) < 30:
        raise RuntimeError(
            "Turkiye.m3u anormal derecede küçük."
        )

    if len(
        hotbird_final
    ) < 30:
        raise RuntimeError(
            "Hotbird.m3u anormal derecede küçük."
        )

    if len(
        astra_final
    ) < 30:
        raise RuntimeError(
            "Astra.m3u anormal derecede küçük."
        )


    # ========================================================
    # ATOMIC REPLACE
    # ========================================================

    # Buraya ancak tüm işlem başarılı olursa gelinir.
    # Bir hata/timeout olursa eski Github dosyaları korunur.

    for key in (
        "world",
        "turkey",
        "hotbird",
        "astra",
    ):
        os.replace(
            TEMP_FILES[key],
            FINAL_FILES[key],
        )


    # ========================================================
    # RAPOR
    # ========================================================

    print(
        "8/8 TAMAMLANDI",
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
        len(turkey_final),
        "/ FTA:",
        len(turksat_fta),
        flush=True
    )

    print(
        "Hotbird:",
        len(hotbird_final),
        "/ FTA:",
        len(hotbird_fta),
        flush=True
    )

    print(
        "Astra:",
        len(astra_final),
        "/ FTA:",
        len(astra_fta),
        flush=True
    )

    print(
        "Manifest cache:",
        len(
            MANIFEST_CACHE
        ),
        flush=True
    )

    print(
        "FFprobe cache:",
        len(
            PROBE_CACHE
        ),
        flush=True
    )

    print(
        "================================",
        flush=True
    )


except Exception as error:
    cleanup_temp()

    print(
        "",
        flush=True
    )

    print(
        "GÜNCELLEME BAŞARISIZ:",
        error,
        flush=True
    )

    print(
        "Mevcut M3U dosyaları değiştirilmedi.",
        flush=True
    )

    raise
