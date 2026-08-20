import urllib.request
from pathlib import Path
import re

FAMELACK_M3U = (
    "https://raw.githubusercontent.com/"
    "DEvmIb/famelack-channels-m3u/main/m3u/_all.m3u"
)

TURKEY_M3U = (
    "https://iptv-org.github.io/iptv/countries/tr.m3u"
)

OUTPUT = Path("world.m3u")


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


print("Famelack dünya listesi indiriliyor...")
famelack = download(FAMELACK_M3U)

print("Türkiye listesi indiriliyor...")
turkey = download(TURKEY_M3U)

all_entries = entries(famelack)
tr_entries = entries(turkey)

output = ["#EXTM3U"]
seen = set()

for info, url in all_entries:
    if url in seen:
        continue

    output.extend([info, url])
    seen.add(url)

for info, url in tr_entries:
    if url in seen:
        continue

    if 'group-title="' in info:
        info = re.sub(
            r'group-title="[^"]*"',
            'group-title="TÜRKSAT / Türkiye (İnternet)"',
            info
        )
    else:
        info = info.replace(
            "#EXTINF:-1",
            '#EXTINF:-1 group-title="TÜRKSAT / Türkiye (İnternet)"',
            1
        )

    output.extend([info, url])
    seen.add(url)


OUTPUT.write_text(
    "\n".join(output) + "\n",
    encoding="utf-8"
)

print("Playlist oluşturuldu.")
print("Toplam kanal:", len(seen))
print("Dosya:", OUTPUT)
