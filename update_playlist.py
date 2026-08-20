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


# ============================================================
# ÖNCELİKLİ KANALLAR
# Resmî/kanal-CDN kaynakları önce gelir.
# ============================================================

PRIORITY = [

    # ULUSAL

    (
        "TRT 1",
        "TRT1.tr",
        "🇹🇷 TÜRKSAT • Ulusal",
        "https://tv-trt1.medya.trt.com.tr/master.m3u8"
    ),

    (
        "Kanal D",
        "KanalD.tr",
        "🇹🇷 TÜRKSAT • Ulusal",
        "https://demiroren.daioncdn.net/kanald/kanald.m3u8?app=kanald_web&ce=3"
    ),

    (
        "ATV",
        "ATV.tr",
        "🇹🇷 TÜRKSAT • Ulusal",
        "https://rnttwmjcin.turknet.ercdn.net/lcpmvefbyo/atv/atv.m3u8"
    ),

    (
        "Show TV",
        "ShowTV.tr",
        "🇹🇷 TÜRKSAT • Ulusal",
        "https://ciner.daioncdn.net/showtv/showtv.m3u8?ce=3&app=4bc856ef-4c68-4a94-bc87-37dfaaa66558"
    ),

    (
        "Star TV",
        "StarTV.tr",
        "🇹🇷 TÜRKSAT • Ulusal",
        "https://dogus-live.daioncdn.net/startv/startv.m3u8"
    ),

    (
        "NOW",
        "NOWTV.tr",
        "🇹🇷 TÜRKSAT • Ulusal",
        "https://uycyyuuzyh.turknet.ercdn.net/nphindgytw/nowtv/nowtv.m3u8"
    ),

    (
        "TV8",
        "TV8.tr",
        "🇹🇷 TÜRKSAT • Ulusal",
        "https://rkhubpaomb.turknet.ercdn.net/fwjkgpasof/tv8/tv8_1080p.m3u8"
    ),

    (
        "Kanal 7",
        "Kanal7.tr",
        "🇹🇷 TÜRKSAT • Ulusal",
        "https://kanal7-live.daioncdn.net/kanal7/kanal7_1080p.m3u8"
    ),

    (
        "Beyaz TV",
        "BeyazTV.tr",
        "🇹🇷 TÜRKSAT • Ulusal",
        "https://beyaztv-live.daioncdn.net/beyaztv/beyaztv_1080p.m3u8"
    ),

    (
        "teve2",
        "Teve2.tr",
        "🇹🇷 TÜRKSAT • Ulusal",
        "https://demiroren-live.daioncdn.net/teve2/teve2_1080p.m3u8"
    ),

    (
        "360 TV",
        "TV360.tr",
        "🇹🇷 TÜRKSAT • Ulusal",
        "https://turkmedya-live.ercdn.net/tv360/tv360_1080p.m3u8"
    ),

    # HABER

    (
        "TRT Haber",
        "TRTHaber.tr",
        "🇹🇷 TÜRKSAT • Haber",
        "https://tv-trthaber.medya.trt.com.tr/master.m3u8"
    ),

    (
        "NTV",
        "NTV.tr",
        "🇹🇷 TÜRKSAT • Haber",
        "https://dogus.daioncdn.net/ntv/ntv.m3u8?app=ntv_web"
    ),

    (
        "A Haber",
        "AHaber.tr",
        "🇹🇷 TÜRKSAT • Haber",
        "https://rnttwmjcin.turknet.ercdn.net/lcpmvefbyo/ahaber/ahaber.m3u8"
    ),

    (
        "Haber Global",
        "HaberGlobal.tr",
        "🇹🇷 TÜRKSAT • Haber",
        "https://tv.ensonhaber.com/haberglobal/haberglobal.m3u8"
    ),

    (
        "Habertürk",
        "HaberturkTV.tr",
        "🇹🇷 TÜRKSAT • Haber",
        "https://tv.ensonhaber.com/haberturk/haberturk.m3u8"
    ),

    (
        "TGRT Haber",
        "TGRTHaber.tr",
        "🇹🇷 TÜRKSAT • Haber",
        "https://canli.tgrthaber.com/tgrt.m3u8"
    ),

    (
        "Halk TV",
        "HalkTV.tr",
        "🇹🇷 TÜRKSAT • Haber",
        "https://halktv.daioncdn.net/halktv/halktv_1080p.m3u8"
    ),

    # SPOR

    (
        "TRT Spor",
        "TRTSpor.tr",
        "🇹🇷 TÜRKSAT • Spor",
        "https://tv-trtspor1.medya.trt.com.tr/master.m3u8"
    ),

    (
        "A Spor",
        "ASpor.tr",
        "🇹🇷 TÜRKSAT • Spor",
        "https://rnttwmjcin.turknet.ercdn.net/lcpmvefbyo/aspor/aspor.m3u8"
    ),

    (
        "HT Spor",
        "HTSpor.tr",
        "🇹🇷 TÜRKSAT • Spor",
        "https://ciner.daioncdn.net/ht-spor/ht-spor.m3u8?app=web"
    ),

    # ÇOCUK / BELGESEL

    (
        "TRT Çocuk",
        "TRTCocuk.tr",
        "🇹🇷 TÜRKSAT • Çocuk",
        "https://tv-trtcocuk.medya.trt.com.tr/master.m3u8"
    ),

    (
        "TRT Belgesel",
        "TRTBelgesel.tr",
        "🇹🇷 TÜRKSAT • Belgesel",
        "https://tv-trtbelgesel.medya.trt.com.tr/master.m3u8"
    ),

    (
        "DMAX",
        "DMAX.tr",
        "🇹🇷 TÜRKSAT • Belgesel",
        "https://dogus-live.daioncdn.net/dmax/dmax_720p.m3u8"
    ),

    (
        "TLC",
        "TLC.tr",
        "🇹🇷 TÜRKSAT • Belgesel",
        "https://dogus-live.daioncdn.net/tlc/tlc_720p.m3u8"
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
        "Ç": "C",
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
    n = re.sub(r"\([^)]*\)", "", n)
    n = re.sub(r"\[[^\]]*\]", "", n)
    n = re.sub(r"\s+", " ", n)
    return n.strip()


def tvg_id(info):
    m = re.search(r'tvg-id="([^"]+)"', info)

    if m:
        return m.group(1)

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
        "HABER",
        "CNN TURK",
        "NTV",
        "HABERTURK",
        "HALK TV",
        "TV100",
        "BLOOMBERG HT",
        "TVNET"
    ]):
        return "🇹🇷 TÜRKSAT • Haber"

    if any(x in n for x in [
        "BELGESEL",
        "DMAX",
        "TLC"
    ]):
        return "🇹🇷 TÜRKSAT • Belgesel"

    if any(x in n for x in [
        "MUZIK",
        "KRAL",
        "NUMBER 1",
        "NUMBER1",
        "POWER TURK"
    ]):
        return "🇹🇷 TÜRKSAT • Müzik"

    return "🇹🇷 TÜRKSAT • Diğer"


def bad_entry(info):
    upper = normalize(info)

    if "GEO-BLOCKED" in upper:
        return True

    if "NOT 24/7" in upper:
        return True

    for blocked in BLOCKED_WORDS:
        if blocked in upper:
            return True

    return False


# ============================================================
# KAYNAKLARI İNDİR
# ============================================================

print("Kaynaklar indiriliyor...")

iptv_text = download(IPTVORG_TR)
famelack_text = download(FAMELACK_M3U)

iptv_entries = parse_entries(iptv_text)
world_entries = parse_entries(famelack_text)


# ============================================================
# TÜRKİYE PLAYLIST
# ============================================================

turkey_output = ["#EXTM3U"]

seen_ids = set()
seen_names = set()
seen_urls = set()


# 1) Öncelikli CDN yayınları

for name, tid, group, url in PRIORITY:

    turkey_output.extend([
        make_extinf(name, tid, group),
        url
    ])

    seen_ids.add(tid.lower())
    seen_names.add(clean_name(name))
    seen_urls.add(url)


# 2) IPTV-org'daki eksik açık kanallar

for info, url in iptv_entries:

    if bad_entry(info):
        continue

    if url in seen_urls:
        continue

    name = channel_name(info)

    if not name:
        continue

    tid = tvg_id(info)

    base_tid = tid.split("@")[0].lower()

    if base_tid and base_tid in seen_ids:
        continue

    cleaned = clean_name(name)

    if cleaned in seen_names:
        continue

    group = turkey_group(name)

    info = replace_group(
        info,
        group
    )

    turkey_output.extend([
        info,
        url
    ])

    if base_tid:
        seen_ids.add(base_tid)

    seen_names.add(cleaned)
    seen_urls.add(url)


TURKEY_OUTPUT.write_text(
    "\n".join(turkey_output) + "\n",
    encoding="utf-8"
)


# ============================================================
# WORLD PLAYLIST
# ============================================================

world_output = ["#EXTM3U"]
world_seen = set()


# Famelack dünya listesi

for info, url in world_entries:

    if url in world_seen:
        continue

    # Famelack Türkiye kanallarını alma.
    # Temiz turkey.m3u aşağıda eklenecek.

    if re.search(
        r'group-title="famelack \(tr\)',
        info,
        re.IGNORECASE
    ):
        continue

    world_output.extend([
        info,
        url
    ])

    world_seen.add(url)


# Temiz Türkiye listesini ekle

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

        if url not in world_seen:
            world_output.extend([
                info,
                url
            ])
            world_seen.add(url)

        i += 2

    else:
        i += 1


WORLD_OUTPUT.write_text(
    "\n".join(world_output) + "\n",
    encoding="utf-8"
)


print("--------------------------------")
print("Playlistler oluşturuldu.")
print("Türkiye kanal sayısı:", len(seen_names))
print("Dünya kanal sayısı:", len(world_seen))
print("Türkiye dosyası:", TURKEY_OUTPUT)
print("Dünya dosyası:", WORLD_OUTPUT)
