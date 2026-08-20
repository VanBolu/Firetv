import urllib.request
from pathlib import Path
import re

FAMELACK_M3U = (
    "https://raw.githubusercontent.com/"
    "DEvmIb/famelack-channels-m3u/main/m3u/_all.m3u"
)

TURKEY_M3U = "https://iptv-org.github.io/iptv/countries/tr.m3u"
OUTPUT = Path("world.m3u")

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


def entries(text):
    lines = text.splitlines()
    result = []

    for i, line in enumerate(lines):
        if line.startswith("#EXTINF") and i + 1 < len(lines):
            url = lines[i + 1].strip()

            if url.startswith(("http://", "https://")):
                result.append((line.strip(), url))

    return result


def country_group(info):
    # Famelack örneği:
    # group-title="famelack (de) [de] [False]"
    match = re.search(
        r'group-title="famelack \(([^)]+)\) \[([^\]]+)\]',
        info,
        re.IGNORECASE
    )

    if not match:
        return None

    code = match.group(2).lower().strip()

    if code in COUNTRIES:
        return COUNTRIES[code]

    # Listede tanımlanmamış ülke kodları da kaybolmasın.
    return "🌍 " + code.upper()


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


print("Famelack dünya listesi indiriliyor...")
famelack = download(FAMELACK_M3U)

print("Türkiye ek yayınları indiriliyor...")
turkey = download(TURKEY_M3U)

world_entries = entries(famelack)
turkey_entries = entries(turkey)

output = ["#EXTM3U"]
seen = set()

# Dünya kanalları
for info, url in world_entries:

    if url in seen:
        continue

    group = country_group(info)

    if group:
        info = replace_group(info, group)

    output.extend([info, url])
    seen.add(url)


# Türkiye için ilave internet yayınları
for info, url in turkey_entries:

    if url in seen:
        continue

    info = replace_group(
        info,
        "🇹🇷 TÜRKSAT • Ek Türkiye Kanalları"
    )

    output.extend([info, url])
    seen.add(url)


OUTPUT.write_text(
    "\n".join(output) + "\n",
    encoding="utf-8"
)

print("--------------------------------")
print("Playlist başarıyla oluşturuldu.")
print("Toplam kanal:", len(seen))
print("Dosya:", OUTPUT)
