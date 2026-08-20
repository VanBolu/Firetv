import urllib.request
from pathlib import Path
import re
import unicodedata


# ============================================================
# KAYNAKLAR
# ============================================================

FAMELACK_M3U = (
    "https://raw.githubusercontent.com/"
    "DEvmIb/famelack-channels-m3u/main/m3u/_all.m3u"
)

IPTVORG_TR = (
    "https://raw.githubusercontent.com/"
    "iptv-org/iptv/master/streams/tr.m3u"
)

WORLD_OUTPUT = Path("world.m3u")
TURKEY_OUTPUT = Path("turkey.m3u")


# ============================================================
# MUTLAKA TUTULMASINI İSTEDİĞİMİZ ANA KANALLAR
#
# Önce IPTV-org içinde aranırlar.
# Orada bulunamazlarsa aşağıdaki fallback adresleri test edilir.
# ============================================================

IMPORTANT_CHANNELS = {
    "StarTV.tr": {
        "name": "Star TV",
        "group": "🇹🇷 TÜRKSAT • Ulusal",
        "fallbacks": [
            (
                720,
                "https://dogus.daioncdn.net/startv/"
                "startv_720p.m3u8?"
                "app=a20ac41e-bdc3-4aa1-934d-26b484480ac9"
                "&ce=3&sid=8l4w3lst4co5"
            ),
        ],
    },

    "ShowTV.tr": {
        "name": "Show TV",
        "group": "🇹🇷 TÜRKSAT • Ulusal",
        "fallbacks": [
            (
                1080,
                "https://ciner-live.daioncdn.net/"
                "showtv/showtv_1080p.m3u8"
            ),
            (
                720,
                "https://ciner-live.daioncdn.net/"
                "showtv/showtv_720p.m3u8"
            ),
            (
                0,
                "https://ciner-live.daioncdn.net/"
                "showtv/showtv.m3u8"
            ),
        ],
    },

    "TRT1.tr": {
        "name": "TRT 1",
        "group": "🇹🇷 TÜRKSAT • Ulusal",
        "fallbacks": [
            (
                1440,
                "https://tv-trt1.medya.trt.com.tr/master.m3u8"
            ),
        ],
    },

    "TV8.tr": {
        "name": "TV8",
        "group": "🇹🇷 TÜRKSAT • Ulusal",
        "fallbacks": [
            (
                1080,
                "https://tv8-live.daioncdn.net/tv8/tv8.m3u8"
            ),
        ],
    },

    "ATV.tr": {
        "name": "ATV",
        "group": "🇹🇷 TÜRKSAT • Ulusal",
        "fallbacks": [
            (
                1080,
                "https://rnttwmjcin.turknet.ercdn.net/"
                "lcpmvefbyo/atv/atv.m3u8"
            ),
        ],
    },

    "AHaber.tr": {
        "name": "A Haber",
        "group": "🇹🇷 TÜRKSAT • Haber",
        "fallbacks": [
            (
                1080,
                "https://rnttwmjcin.turknet.ercdn.net/"
                "lcpmvefbyo/ahaber/ahaber.m3u8"
            ),
        ],
    },

    "ASpor.tr": {
        "name": "A Spor",
        "group": "🇹🇷 TÜRKSAT • Spor",
        "fallbacks": [
            (
                1080,
                "https://rnttwmjcin.turknet.ercdn.net/"
                "lcpmvefbyo/aspor/aspor.m3u8"
            ),
        ],
    },

    "TRTHaber.tr": {
        "name": "TRT Haber",
        "group": "🇹🇷 TÜRKSAT • Haber",
        "fallbacks": [
            (
                720,
                "https://tv-trthaber.medya.trt.com.tr/master.m3u8"
            ),
        ],
    },

    "TRTCocuk.tr": {
        "name": "TRT Çocuk",
        "group": "🇹🇷 TÜRKSAT • Çocuk",
        "fallbacks": [
            (
                1440,
                "https://tv-trtcocuk.medya.trt.com.tr/master.m3u8"
            ),
        ],
    },

    "TRTBelgesel.tr": {
        "name": "TRT Belgesel",
        "group": "🇹🇷 TÜRKSAT • Belgesel",
        "fallbacks": [
            (
                720,
                "https://tv-trtbelgesel.medya.trt.com.tr/master.m3u8"
            ),
        ],
    },
}


# ============================================================
# ŞİFRELİ / PAY-TV
# ============================================================

BLOCKED_WORDS = [
    "BEIN",
    "S SPORT",
    "TIVIBU",
    "D-SMART",
    "D SMART",
    "DIGITURK",
    "MOVIESMART",
    "SMART SPOR",
]


# ============================================================
# ÜLKE GRUPLARI
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
    "az": "🇦🇿 Azerbaycan",
    "ge": "🇬🇪 Gürcistan",
    "il": "🇮🇱 İsrail",
    "ae": "🇦🇪 BAE",
    "sa": "🇸🇦 Suudi Arabistan",
    "eg": "🇪🇬 Mısır",
    "ma": "🇲🇦 Fas",
    "za": "🇿🇦 Güney Afrika",
    "in": "🇮🇳 Hindistan",
    "cn": "🇨🇳 Çin",
    "jp": "🇯🇵 Japonya",
    "kr": "🇰🇷 Güney Kore",
    "au": "🇦🇺 Avustralya",
    "nz": "🇳🇿 Yeni Zelanda",
}


# ============================================================
# İNDİRME
# ============================================================

def download(url, timeout=60):

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64)"
            ),
            "Accept": "*/*",
        },
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
# FALLBACK STREAM TESTİ
#
# Sadece önemli fallback kanallar test edilir.
# Böylece yüzlerce stream yüzünden Action çok uzamaz.
# ============================================================

def stream_works(url):

    try:

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64)"
                ),
                "Accept": (
                    "application/vnd.apple.mpegurl,"
                    "application/x-mpegURL,*/*"
                ),
            },
        )

        with urllib.request.urlopen(
            req,
            timeout=12
        ) as response:

            content = response.read(
                32768
            ).decode(
                "utf-8",
                errors="ignore"
            )

            # HLS playlist ise #EXTM3U bulunmalı.
            if "#EXTM3U" in content:
                return True

            return False

    except Exception as error:

        print(
            "Fallback çalışmadı:",
            url,
            str(error)
        )

        return False


# ============================================================
# M3U PARSER
# ============================================================

def parse_entries(text):

    lines = text.splitlines()
    result = []

    i = 0

    while i < len(lines):

        line = lines[i].strip()

        if line.startswith("#EXTINF"):

            info = line
            options = []

            j = i + 1

            while (
                j < len(lines)
                and lines[j].startswith("#")
            ):
                options.append(
                    lines[j].strip()
                )
                j += 1

            if j < len(lines):

                url = lines[j].strip()

                if url.startswith(
                    ("http://", "https://")
                ):

                    result.append({
                        "info": info,
                        "options": options,
                        "url": url,
                    })

            i = j + 1

        else:

            i += 1

    return result


# ============================================================
# YARDIMCILAR
# ============================================================

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


def normalize(text):

    text = text.upper()

    replacements = {
        "İ": "I",
        "Ş": "S",
        "Ğ": "G",
        "Ü": "U",
        "Ö": "O",
        "Ç": "C",
    }

    for old, new in replacements.items():

        text = text.replace(
            old,
            new
        )

    text = unicodedata.normalize(
        "NFKD",
        text
    )

    return "".join(
        c
        for c in text
        if not unicodedata.combining(c)
    )


def clean_name(name):

    n = normalize(name)

    n = re.sub(
        r"\[[^\]]+\]",
        "",
        n
    )

    n = re.sub(
        r"\([^)]*\)",
        "",
        n
    )

    n = re.sub(
        r"\s+",
        " ",
        n
    )

    return n.strip()


def resolution_score(info):

    text = info.upper()

    match = re.search(
        r"\((\d{3,4})P\)",
        text
    )

    if match:
        return int(
            match.group(1)
        )

    if "4K" in text:
        return 2160

    return 0


def bad_entry(info, url):

    upper = normalize(info)

    if "GEO-BLOCKED" in upper:
        return True

    if "NOT 24/7" in upper:
        return True

    for blocked in BLOCKED_WORDS:

        if blocked in upper:
            return True

    # Mümkün olduğunca HTTPS kullan.
    if not url.startswith("https://"):
        return True

    return False


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


def make_extinf(
    name,
    tid,
    group,
    resolution=0
):

    suffix = ""

    if resolution:
        suffix = f" ({resolution}p)"

    return (
        f'#EXTINF:-1 '
        f'tvg-id="{tid}" '
        f'group-title="{group}",'
        f'{name}{suffix}'
    )


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
# TÜRKİYE GRUPLARI
# ============================================================

def turkey_group(name):

    n = normalize(name)

    if any(
        x in n
        for x in [
            "TRT COCUK",
            "MINIKA",
            "COCUK",
            "CARTOON",
        ]
    ):
        return "🇹🇷 TÜRKSAT • Çocuk"

    if any(
        x in n
        for x in [
            "TRT SPOR",
            "A SPOR",
            "HT SPOR",
            "TJK",
            "SPOR",
        ]
    ):
        return "🇹🇷 TÜRKSAT • Spor"

    if any(
        x in n
        for x in [
            "TRT HABER",
            "A HABER",
            "CNN TURK",
            "NTV",
            "HABERTURK",
            "TGRT HABER",
            "HABER GLOBAL",
            "HALK TV",
            "TV100",
            "BLOOMBERG HT",
            "TVNET",
            "24 TV",
            "FLASH HABER",
        ]
    ):
        return "🇹🇷 TÜRKSAT • Haber"

    if any(
        x in n
        for x in [
            "TRT BELGESEL",
            "DMAX",
            "TLC",
            "BELGESEL",
        ]
    ):
        return "🇹🇷 TÜRKSAT • Belgesel"

    if any(
        x in n
        for x in [
            "TRT MUZIK",
            "KRAL",
            "NUMBER 1",
            "NUMBER1",
            "POWER TURK",
            "MUZIK",
        ]
    ):
        return "🇹🇷 TÜRKSAT • Müzik"

    if any(
        x in n
        for x in [
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
            "360 TV",
        ]
    ):
        return "🇹🇷 TÜRKSAT • Ulusal"

    if any(
        x in n
        for x in [
            "TRT TURK",
            "TRT AVAZ",
            "TRT WORLD",
            "TRT KURDI",
        ]
    ):
        return "🇹🇷 TÜRKSAT • TRT Diğer"

    return "🇹🇷 TÜRKSAT • Diğer"


# ============================================================
# KAYNAKLARI ÇEK
# ============================================================

print(
    "IPTV-org Türkiye listesi indiriliyor..."
)

tr_text = download(
    IPTVORG_TR
)

print(
    "Famelack dünya listesi indiriliyor..."
)

world_text = download(
    FAMELACK_M3U
)

tr_entries = parse_entries(
    tr_text
)

world_entries = parse_entries(
    world_text
)


# ============================================================
# HER TÜRK KANALIN EN YÜKSEK KALİTELİ KAYNAĞINI SEÇ
# ============================================================

best = {}


for entry in tr_entries:

    info = entry["info"]
    url = entry["url"]

    if bad_entry(
        info,
        url
    ):
        continue

    name = channel_name(
        info
    )

    if not name:
        continue

    identity = tvg_id(
        info
    )

    if identity:

        # StarTV.tr@SD -> startv.tr
        identity = (
            identity
            .split("@")[0]
            .lower()
        )

    else:

        identity = clean_name(
            name
        ).lower()

    score = resolution_score(
        info
    )

    current = best.get(
        identity
    )

    if (
        current is None
        or score > current["score"]
    ):

        best[identity] = {
            "info": info,
            "url": url,
            "score": score,
        }


# ============================================================
# ÖNEMLİ KANALLARI GARANTİLE
#
# IPTV-org'da yoksa fallback test edilir.
# ============================================================

for tid, channel in IMPORTANT_CHANNELS.items():

    key = tid.lower()

    if key in best:
        print(
            channel["name"],
            "IPTV-org kaynağından bulundu."
        )
        continue

    print(
        channel["name"],
        "IPTV-org'da bulunamadı; fallback aranıyor..."
    )

    candidates = sorted(
        channel["fallbacks"],
        key=lambda item: item[0],
        reverse=True
    )

    for resolution, url in candidates:

        print(
            "Test:",
            channel["name"],
            resolution,
            url
        )

        if stream_works(
            url
        ):

            best[key] = {
                "info": make_extinf(
                    channel["name"],
                    tid,
                    channel["group"],
                    resolution
                ),
                "url": url,
                "score": resolution,
            }

            print(
                "Fallback OK:",
                channel["name"],
                resolution
            )

            break


# ============================================================
# TÜRKİYE LİSTESİNİ SIRALA
# ============================================================

group_order = {
    "🇹🇷 TÜRKSAT • Ulusal": 1,
    "🇹🇷 TÜRKSAT • Haber": 2,
    "🇹🇷 TÜRKSAT • Spor": 3,
    "🇹🇷 TÜRKSAT • Çocuk": 4,
    "🇹🇷 TÜRKSAT • Belgesel": 5,
    "🇹🇷 TÜRKSAT • Müzik": 6,
    "🇹🇷 TÜRKSAT • TRT Diğer": 7,
    "🇹🇷 TÜRKSAT • Diğer": 8,
}


clean_entries = []


for channel in best.values():

    info = channel["info"]
    url = channel["url"]

    name = channel_name(
        info
    )

    group = turkey_group(
        name
    )

    info = replace_group(
        info,
        group
    )

    clean_entries.append(
        (
            group_order.get(
                group,
                99
            ),
            normalize(name),
            info,
            url,
            channel["score"],
        )
    )


clean_entries.sort(
    key=lambda x: (
        x[0],
        x[1]
    )
)


# ============================================================
# TURKEY.M3U
# ============================================================

turkey_output = [
    "#EXTM3U"
]


for _, _, info, url, _ in clean_entries:

    turkey_output.extend([
        info,
        url
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


for entry in world_entries:

    info = entry["info"]
    url = entry["url"]

    if url in world_seen:
        continue

    code = famelack_country(
        info
    )

    # Türkiye'yi Famelack'tan alma.
    if code == "tr":
        continue

    if code:

        group = COUNTRIES.get(
            code,
            "🌍 " + code.upper()
        )

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


# Temiz Türkiye listesini dünya listesine ekle

for _, _, info, url, _ in clean_entries:

    if url in world_seen:
        continue

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
# RAPOR
# ============================================================

print(
    "--------------------------------"
)

print(
    "Playlistler başarıyla oluşturuldu."
)

print(
    "Temiz Türkiye kanal sayısı:",
    len(clean_entries)
)

print(
    "Dünya kanal sayısı:",
    len(world_seen)
)

print(
    "Türkiye dosyası:",
    TURKEY_OUTPUT
)

print(
    "Dünya dosyası:",
    WORLD_OUTPUT
)

print(
    "--------------------------------"
)

print(
    "Star TV mevcut:",
    "startv.tr" in best
)

print(
    "Show TV mevcut:",
    "showtv.tr" in best
)
