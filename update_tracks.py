"""Günde bir kez çalışır: sanatçılar için YouTube'da arama yapıp tracks.json dosyasını günceller."""
import html, json, os, random, sys, unicodedata, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone

KEY = os.environ.get("YOUTUBE_API_KEY", "").strip()
PICKS = int(os.environ.get("ARTIST_COUNT", "8"))   # her çalıştırmada taranacak sanatçı sayısı (arama başına 100 birim)
PER_ARTIST = 15
MAX_TRACKS = 400
OUT = "tracks.json"

ARTISTS = ["Musa Eroğlu","Arif Sağ","Mustafa Özarslan","Güler Duman","Gülay","Hüseyin Korkankorkmaz","Okan Murat Öztürk","Nida Ateş","Grup Yorum","Muharrem Temiz","Mahsuni Şerif","Neşet Ertaş","Zülfi Livaneli","Gürsoy","Sabahat Akkiraz","Yavuz Bingöl","Gani Peşken","Özcan Türe","5 Quartet","İsmail Türüt","Cem Erdost","Nida Tüfekçi","Deniz Türkan","Tolga Sağ","Hüseyin Karakuş","Kıvırcık Ali","Hulusi Gökmeşe","Hasret Gültekin","Dil Tengi"]
SIMILAR = ["Âşık Veysel","Ruhi Su","Selda Bağcan","Ferhat Tunç","Ali Ekber Çiçek","Muhlis Akarsu","Metin Kemal Kahraman","Erdal Erzincan","Davut Sulari","Âşık Ali İzzet","Çetin Akdeniz","Fuat Saka","Hakkı Bulut","Edip Akbayram","Ahmet Kaya"]

def norm(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().replace("ı", "i")

def search(artist):
    q = urllib.parse.urlencode({
        "part": "snippet", "type": "video", "videoEmbeddable": "true", "videoCategoryId": "10",
        "maxResults": 25, "q": artist + " türkü", "key": KEY})
    with urllib.request.urlopen("https://www.googleapis.com/youtube/v3/search?" + q, timeout=30) as r:
        data = json.load(r)
    items = [{"artist": artist, "title": html.unescape(v["snippet"]["title"]),
              "channel": html.unescape(v["snippet"]["channelTitle"]), "yt": v["id"]["videoId"]}
             for v in data.get("items", []) if v.get("id", {}).get("videoId")]
    n = norm(artist)
    match = [v for v in items if n in norm(v["title"] + " " + v["channel"])]
    if len(match) >= 3:
        items = match
    return [{"artist": v["artist"], "title": v["title"], "yt": v["yt"]} for v in items[:PER_ARTIST]]

def main():
    if not KEY:
        sys.exit("YOUTUBE_API_KEY tanımlı değil (GitHub Secrets).")
    try:
        old = json.load(open(OUT, encoding="utf-8")).get("tracks", [])
    except Exception:
        old = []
    pool = ARTISTS + SIMILAR
    picks = random.sample(ARTISTS, min(PICKS - PICKS // 4, len(ARTISTS))) + \
            random.sample(SIMILAR, min(PICKS // 4, len(SIMILAR)))
    seen = {t["yt"] for t in old}
    new, errors = [], 0
    for a in picks:
        try:
            for t in search(a):
                if t["yt"] not in seen:
                    seen.add(t["yt"]); new.append(t)
            print("tamam:", a)
        except urllib.error.HTTPError as e:
            errors += 1
            print("hata:", a, e.code, e.read().decode("utf-8", "ignore")[:200])
            if e.code == 403:
                break
        except Exception as e:
            errors += 1
            print("hata:", a, e)
    if not new and errors:
        sys.exit("Yeni türkü alınamadı.")
    tracks = (old + new)[-MAX_TRACKS:]
    json.dump({"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "tracks": tracks},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(new)} yeni türkü eklendi, toplam {len(tracks)}.")

main()
