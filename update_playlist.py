import urllib.request
from pathlib import Path
import re
import unicodedata


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


# ------------------------------------------------------------
# IPTV-org'da bulunmayan / özellikle tutulmasını istediğimiz
# birkaç ana kanal için yedek kaynaklar
# ------------------------------------------------------------

FALLBACK_CHANNELS = [
    (
        "Show TV",
        "ShowTV.tr",
        "🇹🇷 TÜRKSAT • Ulusal",
        "https://ciner-live.daioncdn.net/showtv/showtv.m3u8"
    ),
]


BLOCKED_WORDS = [
    "BEIN",
    "S SPORT",
    "TIVIBU",
    "D-SMART",
    "D SMART",
    "DIGITURK",
    "MOVIESMART",
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
        line = lines[i].strip()

        if line.startswith("#EXTINF"):
            info = line
            options = []
            j = i + 1

            while j < len(lines) and lines[j].startswith("#"):
                options.append(lines[j].strip())
                j += 1

            if j < len(lines):
                url = lines[j].strip()

                if url.startswith(("http://", "https://")):
                    result.append({
                        "info": info,
                        "options": options,
                        "url": url
                    })

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
    text = info.upper()

    match = re.search(
        r"\((\d{3,4})P\)",
        text
    )

    if match:
        return int(match.group(1))

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


def famelack_country(info):
    match = re.search(
        r'group-title="famelack \(([^)]+)\) \[([^\]]+)\]',
        info,
        re.IGNORECASE
    )

    if not match:
        return None

    return match.group(2).lower().strip()


def make_extinf(name, tid, group):
    return (
        f'#EXTINF:-1 '
        f'tvg-id="{tid}" '
        f'group-title="{group}",'
        f'{name}'
    )


def turkey_group(name):
    n = normalize(name)

    if any(x in n for x in [
        "TRT COCUK",
        "MINIKA",
        "COCUK",
        "CARTOON"
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
        "FLASH HABER"
    ]):
        return "🇹🇷 TÜRKSAT • Haber"

    if any(x in n for x in [
        "TRT BELGESEL",
        "DMAX",
        "TLC",
        "BELGESEL"
    ]):
        return "🇹🇷 TÜRKSAT • Belgesel"

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
        "360 TV"
    ]):
        return "🇹🇷 TÜRKSAT • Ulusal"

    if any(x in n for x in [
        "TRT TURK",
        "TRT AVAZ",
        "TRT WORLD",
        "TRT KURDI"
    ]):
        return "🇹🇷 TÜRKSAT • TRT Diğer"

    return "🇹🇷 TÜRKSAT • Diğer"


print("IPTV-org Türkiye listesi indiriliyor...")
tr_text = download(IPTVORG_TR)

print("Famelack dünya listesi indiriliyor...")
world_text = download(FAMELACK_M3U)

tr_entries = parse_entries(tr_text)
world_entries = parse_entries(world_text)


# ============================================================
# TÜRKİYE: HER KANALIN EN YÜKSEK KALİTELİ KAYNAĞINI SEÇ
# ============================================================

best = {}


for entry in tr_entries:

    info = entry["info"]
    url = entry["url"]

    if bad_entry(info, url):
        continue

    name = channel_name(info)

    if not name:
        continue

    identity = tvg_id(info)

    if identity:
        identity = identity.split("@")[0].lower()
    else:
        identity = clean_name(name)

    score = resolution_score(info)

    current = best.get(identity)

    if current is None or score > current["score"]:
        best[identity] = {
            "info": info,
            "url": url,
            "score": score
        }


# ============================================================
# SHOW TV GİBİ FALLBACK KANALLARI EKLE
# ============================================================

for name, tid, group, url in FALLBACK_CHANNELS:

    identity = tid.lower()

    if identity not in best:
        best[identity] = {
            "info": make_extinf(name, tid, group),
            "url": url,
            "score": 1080
        }


# ============================================================
# TÜRKİYE PLAYLIST OLUŞTUR
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

    name = channel_name(info)

    group = turkey_group(name)

    info = replace_group(
        info,
        group
    )

    clean_entries.append(
        (
            group_order.get(group, 99),
            normalize(name),
            info,
            url,
            channel["score"]
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


for _, _, info, url, _ in clean_entries:

    turkey_output.extend([
        info,
        url
    ])


TURKEY_OUTPUT.write_text(
    "\n".join(turkey_output) + "\n",
    encoding="utf-8"
)


# ============================================================
# WORLD PLAYLIST
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

    code = famelack_country(info)

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

    world_seen.add(url)


for _, _, info, url, _ in clean_entries:

    if url in world_seen:
        continue

    world_output.extend([
        info,
        url
    ])

    world_seen.add(url)


WORLD_OUTPUT.write_text(
    "\n".join(world_output) + "\n",
    encoding="utf-8"
)


print("--------------------------------")
print("Playlistler başarıyla oluşturuldu.")

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
