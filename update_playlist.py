import urllib.request
from pathlib import Path
import re
import unicodedata

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
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=60) as response:
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
    text = "".join(c for c in text if not unicodedata.combining(c))

    return text


def turksat_group(name):
    n = normalize(name)

    # Çocuk
    if any(x in n for x in [
        "TRT COCUK",
        "MINIKA",
        "CARTOON",
        "DISNEY",
        "COCUK"
    ]):
        return "🇹🇷 TÜRKSAT • Çocuk"

    # Spor
    if any(x in n for x in [
        "TRT SPOR",
        "A SPOR",
        "SPORT",
        "SPOR",
        "TJK",
        "HT SPOR"
    ]):
        return "🇹🇷 TÜRKSAT • Spor"

    # Haber
    if any(x in n for x in [
        "TRT HABER",
        "A HABER",
        "HABERTURK",
        "CNN TURK",
        "NTV",
        "TGRT HABER",
        "HABER GLOBAL",
        "ULUSAL KANAL",
        "BLOOMBERG HT",
        "TV100",
        "EKOTURK",
        "A NEWS"
    ]):
        return "🇹🇷 TÜRKSAT • Haber"

    # Müzik
    if any(x in n for x in [
        "TRT MUZIK",
        "KRAL",
        "NUMBER1",
        "DREAM TURK",
        "MUZIK",
        "MUSIC",
        "POWER TURK"
    ]):
        return "🇹🇷 TÜRKSAT • Müzik"

    # Belgesel
    if any(x in n for x in [
        "TRT BELGESEL",
        "DMAX",
        "TLC",
        "BELGESEL"
    ]):
        return "🇹🇷 TÜRKSAT • Belgesel"

    # Ulusal büyük kanallar
    if any(x in n for x in [
        "TRT 1",
        "KANAL D",
        "ATV",
        "STAR TV",
        "SHOW TV",
        "TV8",
        "NOW",
        "KANAL 7",
        "360",
        "A2",
        "BEYAZ TV",
        "TEVE2"
    ]):
        return "🇹🇷 TÜRKSAT • Ulusal"

    # TRT uluslararası / tematik
    if any(x in n for x in [
        "TRT TURK",
        "TRT AVAZ",
        "TRT ARABI",
        "TRT WORLD",
        "TRT KURDI"
    ]):
        return "🇹🇷 TÜRKSAT • TRT Diğer"

    # Yerel kanallar için yaygın ifadeler
    if any(x in n for x in [
        "KANAL URFA",
        "KADIRGA",
        "EDESSA",
        "LINE TV",
        "GRT",
        "KON TV",
        "KAYSERI",
        "BURSA",
        "KONYA",
        "GAZIANTEP",
        "URFA",
        "DIYARBAKIR",
        "TRABZON",
        "ERZURUM",
        "SAMSUN",
        "ADANA",
        "ANTALYA",
        "DENIZLI",
        "MALATYA"
    ]):
        return "🇹🇷 TÜRKSAT • Yerel"

    return "🇹🇷 Türkiye • Diğer"


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


print("Famelack dünya listesi indiriliyor...")
famelack = download(FAMELACK_M3U)

print("Türkiye listesi indiriliyor...")
turkey = download(TURKEY_M3U)

world_entries = entries(famelack)
turkey_entries = entries(turkey)

output = ["#EXTM3U"]
seen_urls = set()

# Famelack dünya listesi
for info, url in world_entries:

    if url in seen_urls:
        continue

    code = famelack_country(info)

    if code == "tr":
        name = channel_name(info)
        info = replace_group(info, turksat_group(name))

    elif code:
        group = COUNTRIES.get(code, "🌍 " + code.upper())
        info = replace_group(info, group)

    output.extend([info, url])
    seen_urls.add(url)


# IPTV-org Türkiye listesinden eksik kanalları ekle
for info, url in turkey_entries:

    if url in seen_urls:
        continue

    name = channel_name(info)
    info = replace_group(info, turksat_group(name))

    output.extend([info, url])
    seen_urls.add(url)


OUTPUT.write_text(
    "\n".join(output) + "\n",
    encoding="utf-8"
)

print("--------------------------------")
print("Playlist başarıyla oluşturuldu.")
print("Toplam kanal:", len(seen_urls))
print("Dosya:", OUTPUT)
