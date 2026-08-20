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


PRIORITY_CHANNELS = [
    (
        "TRT 1",
        "🇹🇷 TÜRKSAT • Ulusal",
        "https://tv-trt1.medya.trt.com.tr/master.m3u8"
    ),
    (
        "ATV",
        "🇹🇷 TÜRKSAT • Ulusal",
        "https://rnttwmjcin.turknet.ercdn.net/lcpmvefbyo/atv/atv.m3u8"
    ),
    (
        "A2",
        "🇹🇷 TÜRKSAT • Ulusal",
        "https://rnttwmjcin.turknet.ercdn.net/lcpmvefbyo/a2tv/a2tv.m3u8"
    ),
    (
        "TV8",
        "🇹🇷 TÜRKSAT • Ulusal",
        "https://tv8-live.daioncdn.net/tv8/tv8.m3u8"
    ),
    (
        "A Haber",
        "🇹🇷 TÜRKSAT • Haber",
        "https://rnttwmjcin.turknet.ercdn.net/lcpmvefbyo/ahaber/ahaber.m3u8"
    ),
    (
        "NTV",
        "🇹🇷 TÜRKSAT • Haber",
        "https://dogus.daioncdn.net/ntv/ntv.m3u8?app=ntv_web"
    ),
    (
        "Haber Global",
        "🇹🇷 TÜRKSAT • Haber",
        "https://tv.ensonhaber.com/haberglobal/haberglobal.m3u8"
    ),
    (
        "Habertürk",
        "🇹🇷 TÜRKSAT • Haber",
        "https://tv.ensonhaber.com/haberturk/haberturk.m3u8"
    ),
    (
        "TGRT Haber",
        "🇹🇷 TÜRKSAT • Haber",
        "https://canli.tgrthaber.com/tgrt.m3u8"
    ),
    (
        "Halk TV",
        "🇹🇷 TÜRKSAT • Haber",
        "https://halktv-live.daioncdn.net/halktv/halktv.m3u8"
    ),
    (
        "A Spor",
        "🇹🇷 TÜRKSAT • Spor",
        "https://rnttwmjcin.turknet.ercdn.net/lcpmvefbyo/aspor/aspor.m3u8"
    ),
    (
        "HT Spor",
        "🇹🇷 TÜRKSAT • Spor",
        "https://ciner.daioncdn.net/ht-spor/ht-spor.m3u8?app=web"
    ),
    (
        "TJK TV",
        "🇹🇷 TÜRKSAT • Spor",
        "https://tjktv-live.tjk.org/tjktv.m3u8"
    ),
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


def download(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_entries(text):
    lines = text.splitlines()
    result = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("#EXTINF") and i + 1 < len(lines):
            url = lines[i + 1].strip()

            if url.startswith(("http://", "https://")):
                result.append((line, url))

            i += 2
        else:
            i += 1

    return result


def channel_name(info):
    if "," in info:
        return info.split(",", 1)[1].strip()
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
    n = re.sub(r"\[[^\]]+\]", "", n)
    n = re.sub(r"\([^)]*\)", "", n)
    n = re.sub(r"\s+", " ", n)
    return n.strip()


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


def make_extinf(name, group):
    return f'#EXTINF:-1 group-title="{group}",{name}'


def turksat_group(name):
    n = normalize(name)

    if any(x in n for x in [
        "TRT COCUK", "MINIKA", "CARTOON", "COCUK"
    ]):
        return "🇹🇷 TÜRKSAT • Çocuk"

    if any(x in n for x in [
        "TRT SPOR", "A SPOR", "HT SPOR",
        "TJK", "SPORT", "SPOR"
    ]):
        return "🇹🇷 TÜRKSAT • Spor"

    if any(x in n for x in [
        "TRT HABER", "A HABER", "HABERTURK",
        "CNN TURK", "NTV", "TGRT HABER",
        "HABER GLOBAL", "HALK TV",
        "ULUSAL KANAL", "BLOOMBERG HT",
        "TV100", "EKOTURK", "A NEWS"
    ]):
        return "🇹🇷 TÜRKSAT • Haber"

    if any(x in n for x in [
        "TRT MUZIK", "KRAL", "NUMBER1",
        "DREAM TURK", "POWER TURK",
        "MUZIK", "MUSIC"
    ]):
        return "🇹🇷 TÜRKSAT • Müzik"

    if any(x in n for x in [
        "TRT BELGESEL", "DMAX", "TLC", "BELGESEL"
    ]):
        return "🇹🇷 TÜRKSAT • Belgesel"

    if any(x in n for x in [
        "TRT 1", "KANAL D", "ATV", "STAR TV",
        "SHOW TV", "TV8", "NOW", "KANAL 7",
        "BEYAZ TV", "TEVE2", "360", "A2"
    ]):
        return "🇹🇷 TÜRKSAT • Ulusal"

    if any(x in n for x in [
        "TRT TURK", "TRT AVAZ", "TRT ARABI",
        "TRT WORLD", "TRT KURDI"
    ]):
        return "🇹🇷 TÜRKSAT • TRT Diğer"

    return "🇹🇷 Türkiye • Diğer"


print("Famelack dünya listesi indiriliyor...")
famelack_text = download(FAMELACK_M3U)

print("IPTV-org Türkiye listesi indiriliyor...")
iptvorg_text = download(IPTVORG_TR)

world_entries = parse_entries(famelack_text)
tr_entries = parse_entries(iptvorg_text)


turkey_output = ["#EXTM3U"]
seen_urls = set()
seen_names = set()


for name, group, url in PRIORITY_CHANNELS:
    n = clean_name(name)

    if url in seen_urls or n in seen_names:
        continue

    turkey_output.extend([
        make_extinf(name, group),
        url
    ])

    seen_urls.add(url)
    seen_names.add(n)


for info, url in tr_entries:
    name = channel_name(info)
    n = clean_name(name)

    if not name:
        continue

    if url in seen_urls:
        continue

    duplicate_priority = False

    for priority_name, _, _ in PRIORITY_CHANNELS:
        p = clean_name(priority_name)

        if p and (
            n == p
            or n.startswith(p + " ")
            or p.startswith(n + " ")
        ):
            duplicate_priority = True
            break

    if duplicate_priority:
        continue

    info = replace_group(
        info,
        turksat_group(name)
    )

    turkey_output.extend([
        info,
        url
    ])

    seen_urls.add(url)
    seen_names.add(n)


for info, url in world_entries:
    if famelack_country(info) != "tr":
        continue

    name = channel_name(info)
    n = clean_name(name)

    if not name:
        continue

    if url in seen_urls:
        continue

    if n in seen_names:
        continue

    info = replace_group(
        info,
        turksat_group(name)
    )

    turkey_output.extend([
        info,
        url
    ])

    seen_urls.add(url)
    seen_names.add(n)


TURKEY_OUTPUT.write_text(
    "\n".join(turkey_output) + "\n",
    encoding="utf-8"
)


world_output = ["#EXTM3U"]
world_seen_urls = set()


for info, url in world_entries:
    if url in world_seen_urls:
        continue

    country = famelack_country(info)

    if country == "tr":
        continue

    if country:
        group = COUNTRIES.get(
            country,
            "🌍 " + country.upper()
        )

        info = replace_group(
            info,
            group
        )

    world_output.extend([
        info,
        url
    ])

    world_seen_urls.add(url)


turkey_lines = TURKEY_OUTPUT.read_text(
    encoding="utf-8"
).splitlines()

i = 1

while i < len(turkey_lines):
    if (
        turkey_lines[i].startswith("#EXTINF")
        and i + 1 < len(turkey_lines)
    ):
        info = turkey_lines[i]
        url = turkey_lines[i + 1]

        if url not in world_seen_urls:
            world_output.extend([
                info,
                url
            ])

            world_seen_urls.add(url)

        i += 2
    else:
        i += 1


WORLD_OUTPUT.write_text(
    "\n".join(world_output) + "\n",
    encoding="utf-8"
)


print("--------------------------------")
print("Playlistler başarıyla oluşturuldu.")
print("Türkiye kanal sayısı:", len(seen_urls))
print("Dünya kanal sayısı:", len(world_seen_urls))
print("Türkiye dosyası:", TURKEY_OUTPUT)
print("Dünya dosyası:", WORLD_OUTPUT)
