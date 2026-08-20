import urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import unicodedata
import time


# ============================================================
# KAYNAKLAR
# ============================================================

SOURCES = [
    (
        "iptv-org",
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/tr.m3u",
        100
    ),
    (
        "discevisita",
        "https://raw.githubusercontent.com/discevisita/iptv/main/tr.m3u",
        90
    ),
    (
        "suphero",
        "https://raw.githubusercontent.com/suphero/IPTV/master/TR.m3u8",
        70
    ),
]

FAMELACK_M3U = (
    "https://raw.githubusercontent.com/"
    "DEvmIb/famelack-channels-m3u/main/m3u/_all.m3u"
)

WORLD_OUTPUT = Path("world.m3u")
TURKEY_OUTPUT = Path("turkey.m3u")


# ============================================================
# ÖZEL YEDEK KANALLAR
#
# Önce yukarıdaki kaynaklarda aranır.
# Bulunmaz / çalışmazsa bunlar denenir.
# ============================================================

FALLBACKS = {

    "SHOWTVTR": [
        (
            "Show TV",
            "https://ciner.daioncdn.net/showtv/showtv.m3u8"
            "?ce=3&app=4bc856ef-4c68-4a94-bc87-37dfaaa66558",
            1080,
        ),
        (
            "Show TV",
            "https://ciner-live.daioncdn.net/showtv/showtv.m3u8",
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
            720,
        ),
        (
            "Bloomberg HT",
            "https://ensonhaber-live.ercdn.net/"
            "bloomberght/bloomberght.m3u8",
            720,
        ),
    ],

    "CNNTURKTR": [
        (
            "CNN Türk",
            "https://raw.githubusercontent.com/"
            "pinkisso/mored/refs/heads/main/res/ytbe/cnnturk.m3u8",
            720,
        ),
        (
            "CNN Türk",
            "https://mn-nl.mncdn.com/"
            "blutv_cnnturk/smil:cnnturk_sd.smil/playlist.m3u8",
            480,
        ),
    ],

    "STARTVTR": [
        (
            "Star TV",
            "http://dygvideo.dygdigital.com/"
            "live/hls/startv4puhu?m3u8",
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
            "https://tv8-live.daioncdn.net/tv8/tv8.m3u8",
            720,
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

    "TV100TR": [
        (
            "TV100",
            "https://ensonhaber-live.ercdn.net/"
            "tv100/tv100.m3u8",
            720,
        ),
    ],

    "HALKTVTR": [
        (
            "Halk TV",
            "https://halktv-live.daioncdn.net/"
            "halktv/halktv_1080p.m3u8",
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
            720,
        ),
    ],

    "TRTSPORTR": [
        (
            "TRT Spor",
            "https://tv-trtspor1.medya.trt.com.tr/master.m3u8",
            720,
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
            720,
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

    "BEYAZTVTR": [
        (
            "Beyaz TV",
            "https://beyaztv-live.daioncdn.net/"
            "beyaztv/beyaztv_1080p.m3u8",
            1080,
        ),
    ],

    "TV360TR": [
        (
            "360 TV",
            "https://turkmedya-live.ercdn.net/"
            "tv360/tv360_720p.m3u8",
            720,
        ),
    ],

    "TV24TR": [
        (
            "24 TV",
            "https://turkmedya-live.ercdn.net/tv24/tv24.m3u8",
            720,
        ),
    ],
}


# ============================================================
# ŞİFRELİ / PAY-TV KANALLARI DIŞARI AT
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
    "EUROSPORT",
    "NBA TV",
    "FIGHT NETWORK",
]


# ============================================================
# TÜRKİYE KANAL GRUPLARI
# ============================================================

def normalize(text):

    text = text.upper()

    replacements = {
        "İ": "I",
        "İ": "I",
        "Ş": "S",
        "Ğ": "G",
        "Ü": "U",
        "Ö": "O",
        "Ç": "C",
        "Â": "A",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = unicodedata.normalize("NFKD", text)

    return "".join(
        c for c in text
        if not unicodedata.combining(c)
    )


def turkey_group(name):

    n = normalize(name)

    if any(x in n for x in [
        "TRT COCUK",
        "MINIKA",
        "COCUK",
        "CARTOON",
        "KIDZ",
    ]):
        return "🇹🇷 TÜRKSAT • Çocuk"

    if any(x in n for x in [
        "TRT SPOR",
        "A SPOR",
        "HT SPOR",
        "SPORTS TV",
        "SPORTSTV",
        "TJK",
        "SPOR",
    ]):
        return "🇹🇷 TÜRKSAT • Spor"

    if any(x in n for x in [
        "TRT HABER",
        "A HABER",
        "CNN TURK",
        "HABERTURK",
        "NTV",
        "TGRT HABER",
        "HABER GLOBAL",
        "HALK TV",
        "SOZCU",
        "BLOOMBERG HT",
        "TV100",
        "TV 100",
        "TVNET",
        "24 TV",
        "FLASH HABER",
        "ULUSAL KANAL",
        "BENGUTURK",
        "EKOTURK",
        "CNBC",
    ]):
        return "🇹🇷 TÜRKSAT • Haber"

    if any(x in n for x in [
        "TRT BELGESEL",
        "DMAX",
        "TLC",
        "BELGESEL",
        "NATIONAL GEOGRAPHIC",
    ]):
        return "🇹🇷 TÜRKSAT • Belgesel"

    if any(x in n for x in [
        "TRT MUZIK",
        "KRAL",
        "NUMBER 1",
        "NUMBER1",
        "POWER TURK",
        "DREAM TURK",
        "MUZIK",
        "MUSIC",
    ]):
        return "🇹🇷 TÜRKSAT • Müzik"

    if any(x in n for x in [
        "TRT 1",
        "ATV",
        "KANAL D",
        "SHOW TV",
        "STAR TV",
        "NOW",
        "TV8",
        "TV 8",
        "KANAL 7",
        "BEYAZ TV",
        "TEVE2",
        "A2",
        "360",
        "TV4",
    ]):
        return "🇹🇷 TÜRKSAT • Ulusal"

    if any(x in n for x in [
        "TRT TURK",
        "TRT AVAZ",
        "TRT WORLD",
        "TRT KURDI",
        "TRT ARABI",
    ]):
        return "🇹🇷 TÜRKSAT • TRT Diğer"

    return "🇹🇷 TÜRKSAT • Diğer"


GROUP_ORDER = {
    "🇹🇷 TÜRKSAT • Ulusal": 1,
    "🇹🇷 TÜRKSAT • Haber": 2,
    "🇹🇷 TÜRKSAT • Spor": 3,
    "🇹🇷 TÜRKSAT • Çocuk": 4,
    "🇹🇷 TÜRKSAT • Belgesel": 5,
    "🇹🇷 TÜRKSAT • Müzik": 6,
    "🇹🇷 TÜRKSAT • TRT Diğer": 7,
    "🇹🇷 TÜRKSAT • Diğer": 8,
}


# ============================================================
# DOWNLOAD
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


def download(url, timeout=45):

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

def parse_entries(text, source, source_score):

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

        options = []

        while (
            j < len(lines)
            and lines[j].strip().startswith("#")
        ):
            options.append(lines[j].strip())
            j += 1

        if j >= len(lines):
            break

        url = lines[j].strip()

        if url.startswith(("http://", "https://")):

            result.append({
                "info": info,
                "url": url,
                "source": source,
                "source_score": source_score,
                "options": options,
            })

        i = j + 1

    return result


# ============================================================
# KANAL BİLGİLERİ
# ============================================================

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

    if m:
        return m.group(1).strip()

    return ""


def clean_name(name):

    n = normalize(name)

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

    n = re.sub(
        r"\bHD\b|\bSD\b|\b4K\b",
        "",
        n
    )

    n = re.sub(
        r"[^A-Z0-9]+",
        "",
        n
    )

    return n


def canonical_id(info):

    tid = tvg_id(info)

    if tid:

        tid = tid.split("@")[0]

        tid = normalize(tid)

        tid = re.sub(
            r"[^A-Z0-9]",
            "",
            tid
        )

        aliases = {
            "CNNTURKHDTR": "CNNTURKTR",
            "HABERTURKTR": "HABERTURKTVTR",
            "HABERTURKTVTR": "HABERTURKTVTR",
            "BLOOMBERGHTTR": "BLOOMBERGHTTR",
            "STARTVTR": "STARTVTR",
            "SHOWTVTR": "SHOWTVTR",
            "TV8TR": "TV8TR",
            "KANALDTR": "KANALDTR",
            "NOWTR": "NOWTVTR",
            "NOWTVTR": "NOWTVTR",
            "TV360TR": "TV360TR",
            "360TR": "TV360TR",
        }

        return aliases.get(
            tid,
            tid
        )

    return clean_name(
        channel_name(info)
    )


# ============================================================
# ÇÖZÜNÜRLÜK
# ============================================================

def resolution_score(info):

    upper = info.upper()

    match = re.search(
        r"\((\d{3,4})P\)",
        upper
    )

    if match:
        return int(match.group(1))

    if "2160P" in upper or "4K" in upper:
        return 2160

    if "1440P" in upper:
        return 1440

    if "1080P" in upper:
        return 1080

    if "720P" in upper:
        return 720

    if "576P" in upper:
        return 576

    if "480P" in upper:
        return 480

    if "360P" in upper:
        return 360

    return 0


# ============================================================
# KÖTÜ KAYITLARI ELE
# ============================================================

def rejected_entry(info):

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
# STREAM ÇALIŞIYOR MU?
# ============================================================

def test_stream(url):

    try:

        req = urllib.request.Request(
            url,
            headers={
                **HEADERS,
                "Accept": (
                    "application/vnd.apple.mpegurl,"
                    "application/x-mpegURL,"
                    "application/octet-stream,*/*"
                ),
            },
        )

        with urllib.request.urlopen(
            req,
            timeout=8
        ) as response:

            status = getattr(
                response,
                "status",
                200
            )

            if status >= 400:
                return False

            data = response.read(
                65536
            )

            text = data.decode(
                "utf-8",
                errors="ignore"
            )

            if "#EXTM3U" in text:
                return True

            content_type = (
                response.headers
                .get("Content-Type", "")
                .lower()
            )

            if (
                "mpegurl" in content_type
                or "application/octet-stream" in content_type
            ):
                return True

            return False

    except Exception:
        return False


# ============================================================
# GRUP DEĞİŞTİR
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


def make_extinf(name, tid, group, resolution):

    res = ""

    if resolution:
        res = f" ({resolution}p)"

    return (
        f'#EXTINF:-1 '
        f'tvg-id="{tid}" '
        f'group-title="{group}",'
        f'{name}{res}'
    )


# ============================================================
# TÜM TÜRKİYE KAYNAKLARINI İNDİR
# ============================================================

all_candidates = []


for source_name, url, source_score in SOURCES:

    print(
        "Kaynak indiriliyor:",
        source_name
    )

    try:

        text = download(url)

        entries = parse_entries(
            text,
            source_name,
            source_score
        )

        all_candidates.extend(
            entries
        )

        print(
            source_name,
            "kayıt:",
            len(entries)
        )

    except Exception as exc:

        print(
            "Kaynak indirilemedi:",
            source_name,
            exc
        )


# ============================================================
# FAMELACK TÜRKİYE KANALLARINI DA EKLE
# ============================================================

print("Famelack indiriliyor...")

try:

    famelack_text = download(
        FAMELACK_M3U
    )

    famelack_entries = parse_entries(
        famelack_text,
        "famelack",
        55
    )

    for entry in famelack_entries:

        info = entry["info"]

        if re.search(
            r'group-title="famelack \(tr\)',
            info,
            re.IGNORECASE
        ):

            all_candidates.append(
                entry
            )

except Exception as exc:

    print(
        "Famelack alınamadı:",
        exc
    )


# ============================================================
# FALLBACKLERİ DE ADAYLARA EKLE
# ============================================================

for identity, fallbacks in FALLBACKS.items():

    for name, url, resolution in fallbacks:

        group = turkey_group(
            name
        )

        all_candidates.append({
            "info": make_extinf(
                name,
                identity,
                group,
                resolution
            ),
            "url": url,
            "source": "fallback",
            "source_score": 85,
            "options": [],
            "forced_resolution": resolution,
        })


# ============================================================
# REDDEDİLENLERİ TEMİZLE
# ============================================================

filtered = []


for entry in all_candidates:

    if rejected_entry(
        entry["info"]
    ):
        continue

    entry["identity"] = canonical_id(
        entry["info"]
    )

    entry["name"] = channel_name(
        entry["info"]
    )

    entry["resolution"] = entry.get(
        "forced_resolution",
        resolution_score(
            entry["info"]
        )
    )

    # HTTPS ufak avantaj.
    https_bonus = (
        20
        if entry["url"].startswith("https://")
        else 0
    )

    entry["rank"] = (
        entry["resolution"] * 10
        + entry["source_score"]
        + https_bonus
    )

    filtered.append(
        entry
    )


# ============================================================
# AYNI URL'LERİ TEKİLLEŞTİR
# ============================================================

unique_urls = {}

for entry in filtered:

    url = entry["url"]

    current = unique_urls.get(
        url
    )

    if (
        current is None
        or entry["rank"] > current["rank"]
    ):

        unique_urls[url] = entry


filtered = list(
    unique_urls.values()
)


# ============================================================
# STREAMLERİ PARALEL TEST ET
# ============================================================

print(
    "Stream testi başlıyor. Aday sayısı:",
    len(filtered)
)

working_urls = {}


with ThreadPoolExecutor(
    max_workers=16
) as executor:

    futures = {
        executor.submit(
            test_stream,
            entry["url"]
        ): entry["url"]

        for entry in filtered
    }

    completed = 0

    for future in as_completed(
        futures
    ):

        url = futures[future]

        try:
            working_urls[url] = (
                future.result()
            )
        except Exception:
            working_urls[url] = False

        completed += 1

        if completed % 25 == 0:
            print(
                "Test edilen:",
                completed,
                "/",
                len(filtered)
            )


# ============================================================
# HER KANAL İÇİN ÇALIŞAN EN İYİ KAYNAĞI SEÇ
# ============================================================

by_channel = {}


for entry in filtered:

    if not working_urls.get(
        entry["url"],
        False
    ):
        continue

    identity = entry["identity"]

    if not identity:
        continue

    by_channel.setdefault(
        identity,
        []
    ).append(
        entry
    )


selected = []


for identity, candidates in by_channel.items():

    candidates.sort(
        key=lambda x: x["rank"],
        reverse=True
    )

    winner = candidates[0]

    name = winner["name"]

    group = turkey_group(
        name
    )

    winner["info"] = replace_group(
        winner["info"],
        group
    )

    winner["group"] = group

    selected.append(
        winner
    )


# ============================================================
# SIRALA
# ============================================================

selected.sort(
    key=lambda x: (
        GROUP_ORDER.get(
            x["group"],
            99
        ),
        normalize(
            x["name"]
        )
    )
)


# ============================================================
# TURKEY.M3U
# ============================================================

turkey_output = [
    "#EXTM3U"
]


for entry in selected:

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
# WORLD.M3U
# ============================================================

world_output = [
    "#EXTM3U"
]

world_seen = set()


try:

    all_world = parse_entries(
        famelack_text,
        "famelack",
        50
    )

    for entry in all_world:

        info = entry["info"]
        url = entry["url"]

        # Türkiye'yi buradan atla.
        if re.search(
            r'group-title="famelack \(tr\)',
            info,
            re.IGNORECASE
        ):
            continue

        if url in world_seen:
            continue

        world_output.extend([
            info,
            url
        ])

        world_seen.add(
            url
        )

except Exception:
    pass


# Temiz Türkiye listesini dünyaya ekle

for entry in selected:

    if entry["url"] in world_seen:
        continue

    world_output.extend([
        entry["info"],
        entry["url"]
    ])

    world_seen.add(
        entry["url"]
    )


WORLD_OUTPUT.write_text(
    "\n".join(
        world_output
    ) + "\n",
    encoding="utf-8"
)


# ============================================================
# RAPOR
# ============================================================

print("--------------------------------")
print("Tamamlandı.")
print(
    "Çalışan Türkiye kanalı:",
    len(selected)
)
print(
    "Dünya kanal sayısı:",
    len(world_seen)
)

important_checks = [
    "SHOWTVTR",
    "STARTVTR",
    "HABERTURKTVTR",
    "BLOOMBERGHTTR",
    "CNNTURKTR",
    "KANALDTR",
    "TV8TR",
    "NOWTVTR",
]

available = {
    entry["identity"]
    for entry in selected
}

for channel in important_checks:

    print(
        channel,
        ":",
        channel in available
    )
