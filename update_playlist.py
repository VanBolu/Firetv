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
# AYARLAR
# ============================================================

TURKEY_OUTPUT = Path("Turkiye.m3u")
WORLD_OUTPUT = Path("Dunya.m3u")
HOTBIRD_OUTPUT = Path("Hotbird.m3u")
ASTRA_OUTPUT = Path("Astra.m3u")

TARGET_HEIGHT = 1080

# Hız / kalite dengesi
MAX_WORKERS = 20
MAX_CANDIDATES_PER_CHANNEL = 2

HTTP_TIMEOUT = 5
FFPROBE_TIMEOUT = 5


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
# TÜRKİYE ÖZEL YEDEKLERİ
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


# Show TV'nin master URL'sini koruyoruz
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
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*",
}


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
# HTTP
# ============================================================

def download(url, timeout=HTTP_TIMEOUT):

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
# M3U
# ============================================================

def parse_entries(
    text,
    source="",
    score=0
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
# KINGOFSAT
# ============================================================

class KingOfSatParser(HTMLParser):

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

    try:

        html = download(
            url,
            timeout=20
        )

    except Exception as error:

        print(
            "Uydu listesi alınamadı:",
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


                candidate = (
                    row[index].strip()
                )


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


                key = compact_name(
                    candidate
                )


                if (
                    key
                    and key not in seen
                ):

                    seen.add(
                        key
                    )

                    result.append(
                        candidate
                    )


                break


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
# FİLTRE
# ============================================================

def rejected(info):

    n = normalize(info)

    if (
        "GEO-BLOCKED" in n
        or "NOT 24/7" in n
    ):

        return True


    for word in BLOCKED_WORDS:

        if normalize(word) in n:

            return True


    return False


# ============================================================
# DİL / VERSİYON
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
# ÇÖZÜNÜRLÜK
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

def codec_score(codec):

    codec = (
        codec
        or ""
    ).lower()

    score = 0


    # LG webOS için H264 öncelik
    if (
        "avc1" in codec
        or "h264" in codec
    ):

        score += 500

    elif (
        "hvc1" in codec
        or "hev1" in codec
        or "hevc" in codec
    ):

        score += 300

    elif (
        "av01" in codec
        or "av1" in codec
    ):

        score += 150


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


    if height == 1080:

        resolution_score = 10000

    elif height == 720:

        resolution_score = 8500

    elif height > 1080:

        resolution_score = 9000

    elif height >= 576:

        resolution_score = 6500

    elif height >= 480:

        resolution_score = 5000

    else:

        resolution_score = 2500


    if fps >= 49:

        fps_score = 800

    elif fps >= 29:

        fps_score = 400

    elif fps >= 24:

        fps_score = 200

    else:

        fps_score = 0


    bitrate_score = min(
        int(
            bitrate / 10000
        ),
        600
    )


    return (
        resolution_score
        + fps_score
        + bitrate_score
        + codec_score(
            v["codecs"]
        )
    )


def inspect_hls(url):

    try:

        text = download(
            url
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


        frame_rate = re.search(
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


        variants.append({

            "url": urljoin(
                url,
                lines[j].strip()
            ),

            "height": (
                int(
                    resolution.group(2)
                )
                if resolution
                else 0
            ),

            "bandwidth": (
                int(
                    bandwidth.group(1)
                )
                if bandwidth
                else 0
            ),

            "fps": (
                float(
                    frame_rate.group(1)
                )
                if frame_rate
                else 0.0
            ),

            "codecs": (
                codecs.group(1)
                if codecs
                else ""
            ),
        })


    return {

        "master": bool(
            variants
        ),

        "variants": variants,
    }


def choose_manifest(entry):

    result = inspect_hls(
        entry["url"]
    )


    if not result:

        return None


    if not result["master"]:

        return {
            "url": entry["url"],
            "height": advertised_resolution(
                entry["info"]
            ),
            "bandwidth": 0,
            "fps": 0,
            "codecs": "",
            "manifest_score": 0,
        }


    best = max(
        result["variants"],
        key=variant_score
    )


    return {
        **best,

        "manifest_score": variant_score(
            best
        ),
    }


# ============================================================
# FFPROBE - SADECE GEREKTİĞİNDE
# ============================================================

def ffprobe_stream(url):

    if shutil.which(
        "ffprobe"
    ) is None:

        return {}


    command = [
        "ffprobe",

        "-v",
        "error",

        "-rw_timeout",
        "3500000",

        "-analyzeduration",
        "800000",

        "-probesize",
        "800000",

        "-show_entries",
        (
            "stream="
            "codec_type,"
            "codec_name,"
            "width,"
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
            timeout=FFPROBE_TIMEOUT
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


        result = {}


        if video:

            result[
                "video_codec"
            ] = video.get(
                "codec_name",
                ""
            )


            result[
                "height"
            ] = int(
                video.get(
                    "height",
                    0
                )
                or 0
            )


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

                numerator, denominator = (
                    frame.split("/")
                )


                result[
                    "fps"
                ] = (
                    float(numerator)
                    / float(denominator)
                    if float(denominator)
                    else 0
                )

            except Exception:

                result["fps"] = 0


            try:

                result[
                    "bitrate"
                ] = int(
                    video.get(
                        "bit_rate",
                        0
                    )
                    or 0
                )

            except Exception:

                result[
                    "bitrate"
                ] = 0


        if audio:

            result[
                "audio_codec"
            ] = audio.get(
                "codec_name",
                ""
            )


        return result


    except Exception:

        return {}


# ============================================================
# FFPROBE PUANI
# ============================================================

def probe_score(probe):

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


    if height == 1080:

        score = 10000

    elif height == 720:

        score = 8500

    elif height > 1080:

        score = 9000

    elif height >= 576:

        score = 6500

    elif height >= 480:

        score = 5000

    else:

        score = 2500


    if fps >= 49:

        score += 900

    elif fps >= 29:

        score += 450

    elif fps >= 24:

        score += 200


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

    elif video == "av1":

        score += 150


    if audio == "aac":

        score += 250


    score += min(
        int(
            bitrate / 10000
        ),
        750
    )


    return score


# ============================================================
# KANAL ANALİZİ
# ============================================================

def analyze_candidate(entry):

    if rejected(
        entry["info"]
    ):

        return None


    name = channel_name(
        entry["info"]
    )


    if not name:

        return None


    identity = compact_name(
        name
    )


    manifest = choose_manifest(
        entry
    )


    if not manifest:

        return None


    if identity in KEEP_MASTER:

        final_url = entry[
            "url"
        ]

    else:

        final_url = manifest[
            "url"
        ]


    # --------------------------------------------------------
    # HIZ KAZANCI:
    #
    # Master manifest bize hem çözünürlük hem codec verdiyse
    # FFPROBE ÇALIŞTIRMIYORUZ.
    #
    # Yalnız bilgi gerçekten eksikse ffprobe.
    # --------------------------------------------------------

    need_probe = (

        manifest.get(
            "height",
            0
        ) == 0

        or

        not manifest.get(
            "codecs"
        )
    )


    if need_probe:

        probe = ffprobe_stream(
            final_url
        )

    else:

        probe = {}


    if probe:

        quality = probe_score(
            probe
        )

        height = probe.get(
            "height",
            0
        )

        fps = probe.get(
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

        quality = manifest.get(
            "manifest_score",
            0
        )

        height = manifest.get(
            "height",
            0
        )

        fps = manifest.get(
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


    total_score = (

        quality

        +

        entry.get(
            "source_score",
            0
        ) * 5
    )


    return {
        **entry,

        "name": name,

        "final_url": final_url,

        "height": height,

        "fps": fps,

        "video_codec": video_codec,

        "audio_codec": audio_codec,

        "bitrate": bitrate,

        "total_score": total_score,
    }


# ============================================================
# HIZLI ÖN PUAN
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

        score += 500

    elif resolution > 1080:

        score += 450

    elif resolution == 720:

        score += 400

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
# PARALEL ANALİZ
# ============================================================

def analyze_groups(groups):

    shortlist = []


    for options in groups.values():

        options.sort(
            key=coarse_score,
            reverse=True
        )


        shortlist.extend(

            options[
                :MAX_CANDIDATES_PER_CHANNEL
            ]
        )


    print(
        "Detaylı test adayı:",
        len(shortlist),
        flush=True
    )


    tested = []


    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:


        futures = [

            executor.submit(
                analyze_candidate,
                entry
            )

            for entry in shortlist
        ]


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


            if index % 100 == 0:

                print(
                    "Analiz:",
                    index,
                    "/",
                    len(shortlist),
                    flush=True
                )


    return tested


# ============================================================
# İSİM EŞLEŞTİRME
# ============================================================

def name_similarity(
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

        return 0.0


    if first == second:

        return 1.0


    if (
        min(
            len(first),
            len(second)
        ) >= 5

        and

        (
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
# UYDU PLAYLIST
# ============================================================

def build_satellite(
    satellite_names,
    internet_pool,
    group_title,
    output_path,
    turkey_mode=False
):

    selected = []


    for satellite_name in satellite_names:

        winner = None

        winner_rank = -1


        for entry in internet_pool:

            similarity = name_similarity(
                satellite_name,
                entry["name"]
            )


            if similarity < 0.92:

                continue


            rank = (

                similarity * 100000

                +

                entry[
                    "total_score"
                ]
            )


            if rank > winner_rank:

                winner_rank = rank

                winner = entry


        if winner:

            group = (

                turkey_group(
                    satellite_name
                )

                if turkey_mode

                else group_title
            )


            selected.append({
                **winner,

                "satellite_name":
                    satellite_name,

                "info":
                    (
                        '#EXTINF:-1 '
                        f'group-title="{group}",'
                        f'{satellite_name}'
                    ),
            })


    # aynı kanal + dil tekrarı
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

            or

            entry[
                "total_score"
            ]
            >
            current[
                "total_score"
            ]
        ):

            dedupe[key] = entry


    selected = list(
        dedupe.values()
    )


    selected.sort(
        key=lambda item:
        normalize(
            item[
                "satellite_name"
            ]
        )
    )


    output = [
        "#EXTM3U"
    ]


    seen_urls = set()


    for entry in selected:

        url = entry[
            "final_url"
        ]


        if url in seen_urls:

            continue


        seen_urls.add(
            url
        )


        output.extend([
            entry["info"],
            url,
        ])


    output_path.write_text(
        "\n".join(output) + "\n",
        encoding="utf-8"
    )


    return selected


# ============================================================
# BAŞLA
# ============================================================

print(
    "Famelack indiriliyor...",
    flush=True
)


famelack_entries = parse_entries(
    download(
        FAMELACK_M3U,
        timeout=20
    ),
    "famelack",
    80
)


print(
    "IPTV-org dünya indiriliyor...",
    flush=True
)


try:

    iptv_world_entries = parse_entries(

        download(
            IPTVORG_WORLD,
            timeout=30
        ),

        "iptv-org-world",

        110
    )


except Exception as error:

    print(
        "IPTV-org dünya hatası:",
        error,
        flush=True
    )

    iptv_world_entries = []


# ============================================================
# TÜRKİYE EK KAYNAKLARI
# ============================================================

turkey_extra = []


for source, url, score in TURKEY_SOURCES:

    try:

        turkey_extra.extend(

            parse_entries(

                download(
                    url,
                    timeout=15
                ),

                source,

                score
            )
        )


    except Exception as error:

        print(
            source,
            "hatası:",
            error,
            flush=True
        )


# fallbacks
for identity, alternatives in FALLBACKS.items():

    for (
        name,
        url,
        resolution
    ) in alternatives:


        turkey_extra.append({

            "info":
                (
                    '#EXTINF:-1 '
                    f'tvg-id="{identity}" '
                    f'group-title="{turkey_group(name)}",'
                    f'{name} ({resolution}p)'
                ),

            "url": url,

            "source":
                "fallback",

            "source_score":
                115,
        })


# ============================================================
# DÜNYA
# ============================================================

all_world_candidates = (

    famelack_entries

    +

    iptv_world_entries
)


world_groups = {}


for entry in all_world_candidates:

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
        )
    )


    world_groups.setdefault(
        key,
        []
    ).append(
        entry
    )


world_tested = analyze_groups(
    world_groups
)


best_world = {}


for entry in world_tested:

    key = (

        infer_country(
            entry
        ),

        version_key(
            entry["name"]
        )
    )


    current = best_world.get(
        key
    )


    if (
        current is None

        or

        entry[
            "total_score"
        ]
        >
        current[
            "total_score"
        ]
    ):

        best_world[key] = entry


world_selected = list(
    best_world.values()
)


world_selected.sort(
    key=lambda item: (
        infer_country(
            item
        ),
        normalize(
            item["name"]
        )
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
# TÜRKİYE ÖZEL KAYNAKLARI ANALİZ ET
# ============================================================

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
    ).append(
        entry
    )


turkey_tested = analyze_groups(
    turkey_groups
)


# Dünya + özel Türkiye kaynakları
turkey_pool = (

    turkey_tested

    +

    world_selected
)


# ============================================================
# FTA UYDU LİSTELERİ
# ============================================================

print(
    "FTA listeleri indiriliyor...",
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


# ============================================================
# 4 DOSYA
# ============================================================

turkey_selected = build_satellite(
    turksat_channels,
    turkey_pool,
    "Türkiye",
    TURKEY_OUTPUT,
    turkey_mode=True
)


hotbird_selected = build_satellite(
    hotbird_channels,
    world_selected,
    "Hotbird 13°E",
    HOTBIRD_OUTPUT
)


astra_selected = build_satellite(
    astra_channels,
    world_selected,
    "Astra 19.2°E",
    ASTRA_OUTPUT
)


# ============================================================
# RAPOR
# ============================================================

print(
    "================================",
    flush=True
)

print(
    "TAMAMLANDI",
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
    "ffprobe:",
    shutil.which(
        "ffprobe"
    ) is not None,
    flush=True
)

print(
    "================================",
    flush=True
)
