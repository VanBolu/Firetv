import urllib.request
from pathlib import Path

# Famelack dünya listesi
FAMELACK_URL = (
    "https://raw.githubusercontent.com/"
    "famelack/famelack-data/main/famelack-channels-m3u.m3u"
)

# Türkiye için ek açık internet yayınları
TURKEY_URL = (
    "https://iptv-org.github.io/iptv/countries/tr.m3u"
)

OUTPUT = Path("world.m3u")


def download(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def get_entries(text):
    lines = text.splitlines()
    entries = []

    for i, line in enumerate(lines):
        if line.startswith("#EXTINF") and i + 1 < len(lines):
            url = lines[i + 1].strip()

            if url.startswith(("http://", "https://")):
                entries.append((line.strip(), url))

    return entries


print("Famelack listesi indiriliyor...")
famelack = download(FAMELACK_URL)

print("Türkiye listesi indiriliyor...")
turkey = download(TURKEY_URL)

world_entries = get_entries(famelack)
turkey_entries = get_entries(turkey)

output = ["#EXTM3U"]

existing_urls = set()

# Famelack dünya kanalları
for info, url in world_entries:
    if url not in existing_urls:
        output.extend([info, url])
        existing_urls.add(url)

# Türkiye'de bulunan ilave yayınlar
for info, url in turkey_entries:

    if url in existing_urls:
        continue

    if 'group-title="' in info:
        import re
        info = re.sub(
            r'group-title="[^"]*"',
            'group-title="TÜRKSAT / Türkiye (İnternet)"',
            info
        )

    output.extend([info, url])
    existing_urls.add(url)


OUTPUT.write_text(
    "\n".join(output) + "\n",
    encoding="utf-8"
)

print("--------------------------------")
print("Playlist oluşturuldu.")
print("Toplam kanal:", len(existing_urls))
print("Dosya:", OUTPUT)
