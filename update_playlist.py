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

TURKEY_M3U_SOURCE = (
    "https://raw.githubusercontent.com/"
    "iptv-org/iptv/master/streams/tr.m3u"
)

WORLD_OUTPUT = Path("world.m3u")
TURKEY_OUTPUT = Path("turkey.m3u")


# ============================================================
# ŞİFRELİ / PAY-TV / İSTENMEYEN KANALLAR
# ============================================================

BLOCKED_NAMES = [
    "BEIN",
    "S SPORT",
    "S SPORT 2",
    "TIVIBU",
    "D-SMART",
    "D SMART",
    "DIGITURK",
    "SMART SPOR",
    "MOVIESMART",
    "EUROSPORT",
    "NBA TV",
    "FIGHT NETWORK",
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
# YARDIMCI FONKSİYONLAR
# ============================================================

def download(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read().decode(
            "utf-8",
            errors="replace"
        )


def parse_entries(text):
    lines = text.splitlines()
    result = []
    i = 0

    while i < len(lines):

        if lines[i].startswith("#EXTINF"):

            info = lines[i].strip()
            options = []
            j = i + 1

            while j < len(lines) and lines[j].startswith("#"):
                options.append(lines[j].strip())
                j += 1

            if j < len(lines):
                url = lines[j].strip()

                if url.startswith(("http://", "https://")):
                    result.append(
                        {
                            "info": info,
                            "options": options,
                            "url": url
                        }
                    )

            i = j + 1

        else:
            i += 1

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


def normalize(text):
    text = text.upper()

    replacements = {
        "İ": "I",
        "Ş": "S",
        "Ğ": "G",
        "Ü": "U",
        "Ö": "O",
        "Ç": "C"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = unicodedata.normalize("NFKD", text)

    return "".join(
        c for c in text
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
    match = re.search(
        r"\((\d{3,4})p\)",
        info,
        re.IGNORECASE
    )

    if match:
        return int(match.group(1))

    if "4K" in info.upper():
        return 2160

    return 0


def is_bad_entry(info, url):

    upper = info.upper()

    if "[GEO-BLOCKED]" in upper:
        return True

    if "[NOT 24/7]" in upper:
        return True

    if not url.startswith("https://"):
        return True

    name = normalize(
        channel_name(info)
    )

    for blocked in BLOCKED_NAMES:
        if blocked in name:
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


def famelack_country(info):

    match = re.search(
        r'group-title="famelack \(([^)]+)\) \[([^\]]+)\]',
        info,
        re.IGNORECASE
    )

    if not match:
        return None

    return match.group(2).lower().strip()


# ============================================================
# TÜRKİYE KATEGORİLERİ
# ============================================================

def turksat_group(name):

    n = normalize(name)

    if any(x in n for x in [
        "TRT COCUK",
        "MINIKA",
        "CARTOON",
        "COCUK"
    ]):
        return "🇹🇷 TÜRKSAT • Çocuk"

    if any(x in n for x in [
        "TRT SPOR",
        "A SPOR",
        "HT SPOR",
        "TJK",
        "SPOR"
    ]):
        return "🇹🇷 TÜRKSAT • Spor"

    if any(x in n for x in [
        "TRT HABER",
        "A HABER",
        "HABERTURK",
        "CNN TURK",
        "NTV",
        "TGRT HABER",
        "HABER GLOBAL",
        "HALK TV",
        "BLOOMBERG HT",
        "TV100",
        "ULUSAL KANAL",
        "TVNET"
    ]):
        return "🇹🇷 TÜRKSAT • Haber"

    if any(x in n for x in [
        "TRT MUZIK",
        "KRAL",
        "NUMBER 1",
        "NUMBER1",
        "POWER TURK",
        "MUZIK"
    ]):
        return "🇹🇷 TÜRKSAT • Müzik"

    if any(x in n for x in [
        "TRT BELGESEL",
        "DMAX",
        "TLC",
        "BELGESEL"
    ]):
        return "🇹🇷 TÜRKSAT • Belgesel"

    if any(x in n for x in [
        "TRT 1",
        "ATV",
        "KANAL D",
        "SHOW TV",
        "STAR TV",
        "NOW TV",
        "NOW",
        "TV8",
        "KANAL 7",
        "BEYAZ TV",
        "TEVE2",
        "A2",
        "360 TV"
    ]):
        return "🇹🇷 TÜRKSAT • Ulusal"

    if any(x in n for x in [
        "TRT TURK",
        "TRT AVAZ",
        "TRT KURDI",
        "TRT WORLD"
    ]):
        return "🇹🇷 TÜRKSAT • TRT Diğer"

    return "🇹🇷 TÜRKSAT • Diğer"


# ============================================================
# KAYNAKLARI İNDİR
# ============================================================

print("Türkiye IPTV kaynağı indiriliyor...")

turkey_text = download(
    TURKEY_M3U_SOURCE
)

print("Famelack dünya listesi indiriliyor...")

famelack_text = download(
    FAMELACK_M3U
)

turkey_entries = parse_entries(
    turkey_text
)

world_entries = parse_entries(
    famelack_text
)


# ============================================================
# TÜRKİYE KANALLARINI TEMİZLE
# ============================================================

best_channels = {}


for entry in turkey_entries:

    info = entry["info"]
    url = entry["url"]

    if is_bad_entry(info, url):
        continue

    name = channel_name(info)

    if not name:
        continue

    identity = tvg_id(info)

    if not identity:
        identity = clean_name(name)

    score = resolution_score(info)

    current = best_channels.get(
        identity
    )

    if current is None:

        best_channels[identity] = {
            "info": info,
            "url": url,
            "score": score
        }

    elif score > current["score"]:

        best_channels[identity] = {
            "info": info,
            "url": url,
            "score": score
        }


# ============================================================
# TURKEY.M3U OLUŞTUR
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


for channel in best_channels.values():

    info = channel["info"]
    url = channel["url"]

    name = channel_name(
        info
    )

    group = turksat_group(
        name
    )

    info = replace_group(
        info,
        group
    )

    clean_entries.append(
        (
            group_order.get(group, 99),
            normalize(name),
            info,
            url
        )
    )


clean_entries.sort(
    key=lambda x: (
        x[0],
        x[1]
    )
)


turkey_output = [
    "#EXTM3U"
]


for _, _, info, url in clean_entries:

    turkey_output.extend(
        [
            info,
            url
        ]
    )


TURKEY_OUTPUT.write_text(
    "\n".join(turkey_output) + "\n",
    encoding="utf-8"
)


# ============================================================
# WORLD.M3U OLUŞTUR
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

    # Türkiye'yi burada alma.
    # Temiz turkey.m3u aşağıda eklenecek.
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

    world_output.extend(
        [
            info,
            url
        ]
    )

    world_seen.add(
        url
    )


# Temiz Türkiye listesini dünya listesine ekle

for _, _, info, url in clean_entries:

    if url in world_seen:
        continue

    world_output.extend(
        [
            info,
            url
        ]
    )

    world_seen.add(
        url
    )


WORLD_OUTPUT.write_text(
    "\n".join(world_output) + "\n",
    encoding="utf-8"
)


# ============================================================
# SONUÇ
# ============================================================

print("--------------------------------")
print("Playlistler oluşturuldu.")

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
