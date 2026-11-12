#!/usr/bin/env python3
"""Mirror airvine.com (pages from sitemaps + same-host assets) into a static folder
served under a base path (GitHub Pages project site)."""
import os, re, sys, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

OUT = sys.argv[1]
BASE = sys.argv[2] if len(sys.argv) > 2 else "/airvine/"
UA = "Mozilla/5.0 (site-mirror for owner preview)"
HOST_RE = r"(?:https?:)?(?://|\\/\\/)(?:www\.)?airvine\.com"
ASSET_EXT = re.compile(r"\.(css|js|png|jpe?g|gif|svg|webp|ico|woff2?|ttf|eot|otf|mp4|webm|pdf|json|avif)$", re.I)

def get(url):
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read(), r.headers.get("Content-Type", "")
        except Exception as e:
            err = e
            time.sleep(2)
    print("FAIL", url, err, flush=True)
    return None, ""

def local_path(path):
    path = urllib.parse.unquote(path.split("?")[0].split("#")[0])
    if path.endswith("/") or not os.path.splitext(path)[1]:
        path = path.rstrip("/") + "/index.html"
    return os.path.join(OUT, path.lstrip("/"))

def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)

def rewrite(text):
    text = re.sub(r"https?:\\/\\/(?:www\.)?airvine\.com\\/", BASE.replace("/", "\\/"), text)
    text = re.sub(r"(?:https?:)?//(?:www\.)?airvine\.com/", BASE, text)
    text = re.sub(r"(?:https?:)?//(?:www\.)?airvine\.com(?=[\"'])", BASE.rstrip("/") or "/", text)
    # root-relative wp paths
    text = re.sub(r"([\"'(=]\s*)/(wp-content|wp-includes)/", lambda m: m.group(1) + BASE + m.group(2) + "/", text)
    return text

def find_assets(text, ctx_url):
    found = set()
    for m in re.finditer(HOST_RE + r"((?:/|\\/)[^\"'\s)<>,]+)", text):
        p = m.group(1).replace("\\/", "/")
        found.add(p)
    for m in re.finditer(r"[\"'(]\s*(/wp-(?:content|includes)/[^\"'\s)<>,]+)", text):
        found.add(m.group(1))
    if ctx_url:  # css: relative url()
        for m in re.finditer(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)", text):
            u = m.group(1)
            if u.startswith("data:") or u.startswith("#"):
                continue
            absu = urllib.parse.urljoin(ctx_url, u)
            pu = urllib.parse.urlparse(absu)
            if pu.netloc.replace("www.", "") == "airvine.com":
                found.add(pu.path)
    out = set()
    for p in found:
        p = p.split("?")[0].split("#")[0]
        p = re.sub(r"&quot;.*$", "", p)
        if ASSET_EXT.search(p) and "/wp-json/" not in p:
            out.add(p)
    return out

# 1. pages from sitemaps
idx, _ = get("https://airvine.com/sitemap_index.xml")
maps = re.findall(r"<loc>([^<]+)</loc>", idx.decode())
pages = []
for sm in maps:
    d, _ = get(sm)
    if d:
        pages += re.findall(r"<loc>([^<]+)</loc>", d.decode())
pages = sorted(set(u for u in pages if not ASSET_EXT.search(u)))
print(len(pages), "pages", flush=True)

assets = set()
def do_page(u):
    d, ct = get(u)
    if not d or "html" not in ct:
        return set()
    t = d.decode("utf-8", "replace")
    a = find_assets(t, None)
    save(local_path(urllib.parse.urlparse(u).path), rewrite(t).encode())
    print("page", u, flush=True)
    return a

with ThreadPoolExecutor(3) as ex:
    for a in ex.map(do_page, pages):
        assets |= a

# 2. assets (css may reference more)
done = set()
queue = set(assets)
def do_asset(p):
    url = "https://airvine.com" + urllib.parse.quote(urllib.parse.unquote(p), safe="/-_.~%")
    d, ct = get(url)
    if d is None:
        return set()
    more = set()
    if p.lower().endswith(".css"):
        t = d.decode("utf-8", "replace")
        more = find_assets(t, url)
        d = rewrite(t).encode()
    elif p.lower().endswith(".js"):
        t = d.decode("utf-8", "replace")
        d = rewrite(t).encode()
    save(local_path(p), d)
    return more

while queue:
    batch = list(queue - done)
    done |= set(batch)
    queue = set()
    print("asset batch", len(batch), flush=True)
    with ThreadPoolExecutor(4) as ex:
        for m in ex.map(do_asset, batch):
            queue |= m - done
print("DONE", len(pages), "pages", len(done), "assets", flush=True)
