import urllib.request
from urllib.parse import urljoin
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import unicodedata


WORLD_OUTPUT = Path("world.m3u")
TURKEY_OUTPUT = Path("turkey.m3u")

TARGET_HEIGHT = 1080

FAMELACK_M3U = (
    "https://raw.githubusercontent.com/"
    "DEvmIb/famelack-channels-m3u/main/m3u/_all.m3u"
)

SOURCES = [
    (
        "iptv-org",
        "https://raw.githubusercontent.com/"
        "iptv-org/iptv/master/streams/tr.m3u",
        100,
    ),
    (
        "discevisita",
        "https://raw.githubusercontent.com/"
        "discevisita/iptv/main/tr.m3u",
        90,
    ),
    (
        "suphero",
        "https://raw.githubusercontent.com/"
        "suphero/IPTV/master/TR.m3u8",
        70,
    ),
]


FALLBACKS = {
    "SHOWTVTR": [
        (
            "Show TV",
            "https://ciner-live.daioncdn.net/showtv/showtv.m3u8",
            0,
        ),
        (
            "Show TV",
            "https://ciner.daioncdn.net/showtv/showtv.m3u8"
            "?ce=3&app=4bc856ef-4c68-4a94-bc87-37dfaaa66558",
            0,
        ),
    ],

    "STARTVTR": [
        (
            "Star TV",
            "https://dogus.daioncdn.net/startv/startv_720p.m3u8"
            "?app=a20ac41e-bdc3-4aa1-934d-26b484480ac9&ce=3",
            720,
        ),
    ],

    "KANALDTR": [
        (
            "Kanal D",
            "https://demiroren.daioncdn.net/kanald/kanald.m3u8"
            "?app=kanald_web&ce=3",
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
            "https://tv8.daioncdn.net/tv8/tv8.m3u8"
            "?app=7ddc255a-ef47-4e81-ab14-c0e5f2949788&ce=3",
            1080,
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

    "NOWTVTR": [
        (
            "NOW",
            "https://uycyyuuzyh.turknet.ercdn.net/"
            "nphindgytw/nowtv/nowtv.m3u8",
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
            0,
        ),
    ],

    "CNNTURKTR": [
        (
            "CNN Türk",
            "https://mn-nl.mncdn.com/"
            "blutv_cnnturk/smil:cnnturk_sd.smil/playlist.m3u8",
            480,
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
            1080,
        ),
    ],

    "TRTSPORTR": [
        (
            "TRT Spor",
            "https://tv-trtspor1.medya.trt.com.tr/master.m3u8",
            1080,
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
            1080,
        ),
    ],
}


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
]


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/151 Safari/537.36"
    ),
    "Accept": "*/*",
}


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


def download(url, timeout=20):
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

        while (
            j < len(lines)
            and lines[j].strip().startswith("#")
        ):
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
            })

        i = j + 1

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


def clean_name(name):
    name = normalize(name)

    name = re.sub(
        r"\([^)]*\)",
        "",
        name
    )

    name = re.sub(
        r"\[[^\]]*\]",
        "",
        name
    )

    name = re.sub(
        r"\bHD\b|\bSD\b|\b4K\b",
        "",
        name
    )

    name = re.sub(
        r"[^A-Z0-9]+",
        "",
        name
    )

    return name


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
            "NOWTR": "NOWTVTR",
            "NOWTVTR": "NOWTVTR",
            "360TR": "TV360TR",
        }

        return aliases.get(
            tid,
            tid
        )

    return clean_name(
        channel_name(info)
    )


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


def rejected_entry(info):
    text = normalize(info)

    if "GEO-BLOCKED" in text:
        return True

    if "NOT 24/7" in text:
        return True

    for blocked in BLOCKED_WORDS:
        if normalize(blocked) in text:
            return True

    return False


def turkey_group(name):
    n = normalize(name)

    if any(x in n for x in [
        "TRT COCUK",
        "MINIKA",
        "COCUK",
        "CARTOON",
    ]):
        return "🇹🇷 TÜRKSAT • Çocuk"

    if any(x in n for x in [
        "TRT SPOR",
        "A SPOR",
        "HT SPOR",
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
        "BLOOMBERG HT",
        "TV100",
        "TVNET",
        "24 TV",
        "FLASH HABER",
        "ULUSAL KANAL",
        "SOZCU",
    ]):
        return "🇹🇷 TÜRKSAT • Haber"

    if any(x in n for x in [
        "TRT BELGESEL",
        "DMAX",
        "TLC",
        "BELGESEL",
    ]):
        return "🇹🇷 TÜRKSAT • Belgesel"

    if any(x in n for x in [
        "TRT MUZIK",
        "KRAL",
        "NUMBER1",
        "POWER TURK",
        "DREAM TURK",
        "MUZIK",
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
        "360",
    ]):
        return "🇹🇷 TÜRKSAT • Ulusal"

    return "🇹🇷 TÜRKSAT • Diğer"


GROUP_ORDER = {
    "🇹🇷 TÜRKSAT • Ulusal": 1,
    "🇹🇷 TÜRKSAT • Haber": 2,
    "🇹🇷 TÜRKSAT • Spor": 3,
    "🇹🇷 TÜRKSAT • Çocuk": 4,
    "🇹🇷 TÜRKSAT • Belgesel": 5,
    "🇹🇷 TÜRKSAT • Müzik": 6,
    "🇹🇷 TÜRKSAT • Diğer": 7,
}


def make_extinf(
    name,
    identity,
    group,
    resolution
):
    suffix = ""

    if resolution:
        suffix = f" ({resolution}p)"

    return (
        f'#EXTINF:-1 '
        f'tvg-id="{identity}" '
        f'group-title="{group}",'
        f'{name}{suffix}'
    )


def test_stream(url):
    try:
        req = urllib.request.Request(
            url,
            headers=HEADERS
        )

        with urllib.request.urlopen(
            req,
            timeout=8
        ) as response:

            data = response.read(
                65536
            ).decode(
                "utf-8",
                errors="ignore"
            )

            return "#EXTM3U" in data

    except Exception:
        return False


def inspect_hls(url):
    try:
        text = download(
            url,
            timeout=10
        )

        if "#EXTM3U" not in text:
            return {
                "working": False,
                "is_master": False,
                "variants": [],
            }

        lines = text.splitlines()
        variants = []

        for i, line in enumerate(lines):

            if not line.startswith(
                "#EXT-X-STREAM-INF:"
            ):
                continue

            res_match = re.search(
                r"RESOLUTION=(\d+)x(\d+)",
                line,
                re.IGNORECASE
            )

            bw_match = re.search(
                r"BANDWIDTH=(\d+)",
                line,
                re.IGNORECASE
            )

            height = 0

            if res_match:
                height = int(
                    res_match.group(2)
                )

            bandwidth = 0

            if bw_match:
                bandwidth = int(
                    bw_match.group(1)
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

            variant_url = urljoin(
                url,
                lines[j].strip()
            )

            variants.append({
                "url": variant_url,
                "height": height,
                "bandwidth": bandwidth,
            })

        return {
            "working": True,
            "is_master": len(variants) > 0,
            "variants": variants,
        }

    except Exception:
        return {
            "working": False,
            "is_master": False,
            "variants": [],
        }


def choose_fixed_variant(
    original_url,
    advertised_resolution
):
    info = inspect_hls(
        original_url
    )

    if not info["working"]:
        return None

    if not info["is_master"]:
        return {
            "url": original_url,
            "height": advertised_resolution,
        }

    variants = info["variants"]

    exact_1080 = [
        v for v in variants
        if v["height"] == TARGET_HEIGHT
    ]

    if exact_1080:
        exact_1080.sort(
            key=lambda v: v["bandwidth"],
            reverse=True
        )

        winner = exact_1080[0]

        return {
            "url": winner["url"],
            "height": 1080,
        }

    lower = [
        v for v in variants
        if (
            v["height"] > 0
            and v["height"] < TARGET_HEIGHT
        )
    ]

    if lower:
        lower.sort(
            key=lambda v: (
                v["height"],
                v["bandwidth"]
            ),
            reverse=True
        )

        winner = lower[0]

        return {
            "url": winner["url"],
            "height": winner["height"],
        }

    higher = [
        v for v in variants
        if v["height"] > TARGET_HEIGHT
    ]

    if higher:
        higher.sort(
            key=lambda v: (
                v["height"],
                v["bandwidth"]
            ),
            reverse=True
        )

        winner = higher[0]

        return {
            "url": winner["url"],
            "height": winner["height"],
        }

    variants.sort(
        key=lambda v: v["bandwidth"],
        reverse=True
    )

    if variants:
        winner = variants[0]

        return {
            "url": winner["url"],
            "height": advertised_resolution,
        }

    return None


# ============================================================
# ADAYLARI TOPLA
# ============================================================

all_candidates = []


for source_name, url, score in SOURCES:

    try:
        print(
            "Kaynak:",
            source_name
        )

        text = download(url)

        all_candidates.extend(
            parse_entries(
                text,
                source_name,
                score
            )
        )

    except Exception as error:

        print(
            source_name,
            "alınamadı:",
            error
        )


# ============================================================
# FALLBACKLER
# ============================================================

for identity, alternatives in FALLBACKS.items():

    for name, url, resolution in alternatives:

        all_candidates.append({
            "info": make_extinf(
                name,
                identity,
                turkey_group(name),
                resolution
            ),
            "url": url,
            "source": "fallback",
            "source_score": 95,
            "forced_resolution": resolution,
        })


# ============================================================
# TEMİZLE
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

    entry["advertised_resolution"] = (
        entry.get(
            "forced_resolution",
            resolution_score(
                entry["info"]
            )
        )
    )

    filtered.append(entry)


# ============================================================
# BÜTÜN STREAMLERİ ANALİZ ET
# ============================================================

analysis_results = {}


def analyze_candidate(entry):

    # Show TV için master URL'yi olduğu gibi koru.
    if entry["identity"] == "SHOWTVTR":

        if test_stream(
            entry["url"]
        ):
            return (
                entry["url"],
                {
                    "url": entry["url"],
                    "height": 0,
                }
            )

        return (
            entry["url"],
            None
        )

    fixed = choose_fixed_variant(
        entry["url"],
        entry["advertised_resolution"]
    )

    return (
        entry["url"],
        fixed
    )


print(
    "Toplam aday:",
    len(filtered)
)


with ThreadPoolExecutor(
    max_workers=12
) as executor:

    futures = [
        executor.submit(
            analyze_candidate,
            entry
        )
        for entry in filtered
    ]

    completed = 0

    for future in as_completed(
        futures
    ):

        url, result = future.result()

        analysis_results[url] = result

        completed += 1

        if completed % 20 == 0:

            print(
                "Analiz:",
                completed,
                "/",
                len(filtered)
            )


# ============================================================
# PUANLA
# ============================================================

usable = []


for entry in filtered:

    result = analysis_results.get(
        entry["url"]
    )

    if not result:
        continue

    fixed_url = result["url"]
    real_height = result["height"]

    # Show TV master URL için ikinci sabit varyant testi yok.
    if entry["identity"] != "SHOWTVTR":

        if not test_stream(
            fixed_url
        ):
            continue

    entry["fixed_url"] = fixed_url

    entry["real_resolution"] = (
        real_height
        if real_height
        else entry["advertised_resolution"]
    )

    https_bonus = (
        20
        if fixed_url.startswith("https://")
        else 0
    )

    entry["rank"] = (
        entry["real_resolution"] * 100
        + entry["source_score"]
        + https_bonus
    )

    usable.append(entry)


# ============================================================
# KANAL BAŞINA EN İYİ KAYNAK
# ============================================================

by_channel = {}


for entry in usable:

    by_channel.setdefault(
        entry["identity"],
        []
    ).append(entry)


selected = []


for identity, alternatives in by_channel.items():

    alternatives.sort(
        key=lambda x: x["rank"],
        reverse=True
    )

    winner = alternatives[0]

    group = turkey_group(
        winner["name"]
    )

    winner["group"] = group


    # --------------------------------------------------------
    # SHOW TV
    # --------------------------------------------------------

    if identity == "SHOWTVTR":

        winner["name"] = "Show TV"

        winner["info"] = make_extinf(
            "Show TV",
            "SHOWTVTR",
            "🇹🇷 TÜRKSAT • Ulusal",
            0
        )

    else:

        winner["info"] = make_extinf(
            winner["name"],
            identity,
            group,
            winner["real_resolution"]
        )

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
        entry["fixed_url"]
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

    famelack_text = download(
        FAMELACK_M3U
    )

    famelack_entries = parse_entries(
        famelack_text,
        "famelack",
        50
    )

    for entry in famelack_entries:

        info = entry["info"]
        url = entry["url"]

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

except Exception as error:

    print(
        "Famelack world hatası:",
        error
    )


for entry in selected:

    if entry["fixed_url"] in world_seen:
        continue

    world_output.extend([
        entry["info"],
        entry["fixed_url"]
    ])

    world_seen.add(
        entry["fixed_url"]
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
print("TAMAMLANDI")
print("--------------------------------")

print(
    "Türkiye kanal sayısı:",
    len(selected)
)

print(
    "Dünya kanal sayısı:",
    len(world_seen)
)


important = [
    "TV8TR",
    "SHOWTVTR",
    "STARTVTR",
    "KANALDTR",
    "ATVTR",
    "HABERTURKTVTR",
    "BLOOMBERGHTTR",
    "CNNTURKTR",
    "AHABERTR",
    "TRTHABERTR",
    "ASPORTR",
]


lookup = {
    item["identity"]: item
    for item in selected
}


print("--------------------------------")
print("ÖNEMLİ KANALLAR")
print("--------------------------------")


for identity in important:

    entry = lookup.get(
        identity
    )

    if entry:

        print(
            identity,
            ": TRUE |",
            entry["real_resolution"],
            "p |",
            entry["source"],
            "|",
            entry["fixed_url"]
        )

    else:

        print(
            identity,
            ": FALSE"
        )
