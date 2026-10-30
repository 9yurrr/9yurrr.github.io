"""혜택알림 정적 사이트 생성기 (GitHub Pages용).

posts/*.json, pages/*.json → _site/ 에 HTML·sitemap·RSS·검색 색인을 만든다.
주소 체계는 예전 블로그스팟과 같다: /2026/10/글.html, /p/카테고리.html

  python site.py            # _site/ 생성
  SITE_URL=https://example.com python site.py   # 도메인 바꿀 때
"""
import html, json, os, re, shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "_site"
SITE = os.environ.get("SITE_URL", "https://9yurrr.github.io").rstrip("/")
NAME = "혜택알림"
DESC = "정부·지자체 지원금을 대상, 금액, 신청기간으로 정리해 매일 업데이트합니다."
GA = "G-NP7EJ17EZH"
KST = timezone(timedelta(hours=9))
OLD_HOSTS = ("https://hyetaek-alrim.blogspot.com", "http://hyetaek-alrim.blogspot.com")
OLD_CDN = re.compile(r"https://cdn\.jsdelivr\.net/gh/9yurrr/hyetaek-alrim-img@main")

# (블로그 라벨, 주소, 버튼 문구) — publish.py HUBS와 같은 순서
HUBS = [("청년", "cheongnyeon", "월세·자산형성·취업"), ("신혼·출산", "sinhon-chulsan", "출산지원금·주거·육아"),
        ("소상공인", "sosanggongin", "정책자금·경영안정"), ("어르신", "eoreusin", "기초연금·돌봄·일자리"),
        ("저소득", "jeosodeuk", "생계·의료·주거급여"), ("장애인", "jangaein", "수당·활동지원"),
        ("농어민", "nongeomin", "직불금·영농지원"), ("마감임박", "magam-imbak", "이번 주 신청 마감")]
HUB_NAME = {"저소득": "저소득·취약계층"}
NAV = ["cheongnyeon", "sinhon-chulsan", "sosanggongin", "eoreusin", "magam-imbak"]
FOOTER = [("소개", "/p/blog-page.html"), ("개인정보처리방침", "/p/blog-page_01.html"),
          ("문의", "/p/blog-page_862.html"), ("면책 고지", "/p/blog-page_630.html")]
STATIC = ["cards", "brand", "og"]
esc = html.escape


def localize(s):
    """옛 블로그·CDN 주소를 사이트 내부 경로로."""
    s = OLD_CDN.sub("", s)
    for h in OLD_HOSTS:
        s = s.replace(h + "/", "/").replace(h, SITE)
    return s


def text_of(h):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def load_posts():
    posts = []
    for f in (HERE / "posts").glob("*.json"):
        p = json.loads(f.read_text(encoding="utf-8"))
        c = localize(p["content"])
        c = re.sub(r"<!--related-->.*?<!--/related-->", "", c, flags=re.S)
        intro = c.split("<!--more-->")[0]
        img = re.search(r'<img[^>]+src="([^"]+)"', c)
        p.update(content=c, img=img.group(1) if img else "/og/home.jpg",
                 summary=text_of(re.sub(r"<img[^>]*>", "", intro))[:150],
                 date=datetime.fromisoformat(p["published"]).astimezone(KST))
        posts.append(p)
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def page(title, body, path, desc=DESC, image="/og/home.jpg", og_type="website", extra_head=""):
    canon = SITE + path
    full_title = title if title == NAME else f"{title} | {NAME}"
    img = image if image.startswith("http") else SITE + image
    nav = "".join(f'<a href="/p/{s}.html">{esc(l)}</a>' for l, s, _ in HUBS if s in NAV)
    foot = "".join(f'<a href="{u}">{esc(t)}</a>' for t, u in FOOTER)
    return f"""<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canon}">
<meta name="robots" content="max-image-preview:large">
<meta name="naver-site-verification" content="759c5064d4ab03716065d60aae54c08efb3029b2">
<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="{NAME}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canon}"><meta property="og:image" content="{img}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" sizes="64x64" href="/brand/favicon-64.png">
<link rel="apple-touch-icon" href="/brand/favicon-180.png">
<link rel="alternate" type="application/rss+xml" title="{NAME}" href="/feed.xml">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="/style.css">
<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','{GA}');</script>
{extra_head}</head><body>
<header class="hx-header"><div class="hx-wrap">
<a class="hx-logo" href="/"><img src="/brand/icon.png" alt="" width="38" height="28">{NAME}</a>
<nav class="hx-nav">{nav}<a href="/p/blog-page.html">소개</a></nav>
</div></header>
{body}
<footer class="hx-footer"><div class="hx-wrap">
<div class="hx-links">{foot}</div>
<small>혜택알림은 공공데이터(보조금24·공공데이터포털)를 바탕으로 정리한 참고용 정보를 제공합니다. 정부 기관이 아니며 신청을 대행하지 않습니다.</small>
<small>© {NAME}</small>
</div></footer>
</body></html>
"""


def card(p):
    return (f'<a class="card" href="{p["path"]}"><span class="thumb"><img src="{p["img"]}" alt="" loading="lazy" width="1200" height="675"></span>'
            f'<time>{p["date"]:%Y.%m.%d}</time><b>{esc(p["title"])}</b><span class="sum">{esc(p["summary"])}</span></a>')


def related(p, posts, n=4):
    label = next((l for l in p["labels"] if l in dict((h[0], h[1]) for h in HUBS)), None)
    pool = [q for q in posts if q is not p and (label in q["labels"] if label else True)][:n]
    if not pool:
        return ""
    head = f"함께 보면 좋은 {esc(label)} 혜택" if label else "최근 올라온 혜택"
    lis = "".join(f'<li><a href="{q["path"]}">{esc(q["title"])}</a></li>' for q in pool)
    more = f'<p><a href="/p/{dict((h[0], h[1]) for h in HUBS)[label]}.html">{esc(label)} 지원금·혜택 전체 보기 →</a></p>' if label else ""
    return f"<h2>{head}</h2><ul>{lis}</ul>{more}"


def write(path, s):
    f = OUT / path.lstrip("/")
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(s, encoding="utf-8")


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for d in STATIC:
        if (HERE / d).exists():
            shutil.copytree(HERE / d, OUT / d)
    shutil.copy(HERE / "style.css", OUT / "style.css")
    posts = load_posts()
    slug_of = {h[0]: h[1] for h in HUBS}

    for p in posts:  # 글
        c = p["content"]
        rel = related(p, posts)
        c = c.replace("<h2>공식 원문</h2>", rel + "<h2>공식 원문</h2>", 1) if "<h2>공식 원문</h2>" in c else c + rel
        tags = "".join(f'<a href="/p/{slug_of[l]}.html">{esc(HUB_NAME.get(l, l))}</a>' for l in p["labels"] if l in slug_of)
        ld = json.dumps({"@context": "https://schema.org", "@type": "Article", "headline": p["title"], "image": [SITE + p["img"]],
                         "datePublished": p["published"], "dateModified": p.get("updated", p["published"]),
                         "author": {"@type": "Organization", "name": NAME}, "publisher": {"@type": "Organization", "name": NAME,
                         "logo": {"@type": "ImageObject", "url": SITE + "/brand/favicon-180.png"}}}, ensure_ascii=False)
        body = (f'<main class="hx-wrap post"><article><h1>{esc(p["title"])}</h1>'
                f'<p class="meta"><time datetime="{p["published"]}">{p["date"]:%Y년 %m월 %d일}</time>{" · " + tags if tags else ""}</p>'
                f'<div class="post-body">{c}</div></article></main>')
        write(p["path"], page(p["title"], body, p["path"], p["summary"], p["img"], "article",
                              f'<script type="application/ld+json">{ld}</script>\n'))

    grid = lambda ps: f'<div class="grid">{"".join(card(p) for p in ps)}</div>' if ps else '<p class="empty">아직 등록된 글이 없습니다. 곧 업데이트됩니다.</p>'
    cats = "".join(f'<a class="hx-cat" href="/p/{s}.html"><img src="/brand/cats/{s}.svg" alt="" width="48" height="48" loading="lazy">'
                   f'<b>{esc(HUB_NAME.get(l, l))}</b><span>{esc(t)}</span></a>' for l, s, t in HUBS)
    home = (f'<section class="hx-hero"><div class="hx-wrap"><h1>받을 수 있는 지원금,<br>놓치지 마세요</h1><p>{DESC}</p>'
            f'<form class="hx-search" action="/search.html" method="get"><input name="q" aria-label="지원금 검색" placeholder="예: 청년 월세, 출산, 소상공인 대출">'
            f'<button type="submit">검색</button></form></div></section>'
            f'<section class="hx-sec"><div class="hx-wrap"><h2>대상별로 찾기</h2><div class="hx-cats">{cats}</div>'
            f'<h2 class="hx-latest">최신 지원금</h2>{grid(posts[:30])}'
            f'<p class="more"><a href="/archive.html">전체 지원금 {len(posts)}개 보기 →</a></p></div></section>')
    write("/index.html", page(NAME, home, "/"))

    for l, s, _ in HUBS:  # 카테고리 모음
        ps = [p for p in posts if l in p["labels"]]
        name = HUB_NAME.get(l, l)
        body = (f'<main class="hx-wrap hub"><img src="/brand/cats/{s}.svg" alt="" width="72" height="72"><h1>{esc(name)} 지원금·혜택 모음</h1>'
                f'<p>{esc(name)} 대상 정부·지자체 지원금과 혜택을 한곳에 모았습니다. 매일 새 지원금이 추가되며, 각 글에서 지원 대상·지원 내용·신청 기간·신청 방법을 확인할 수 있습니다.</p>'
                f'{grid(ps)}</main>')
        write(f"/p/{s}.html", page(f"{name} 지원금·혜택 모음", body, f"/p/{s}.html", f"{name} 대상 정부·지자체 지원금 {len(ps)}개 모음"))

    for f in (HERE / "pages").glob("*.json"):  # 소개·정책 페이지 (카테고리 모음은 위에서 새로 만듦)
        pg = json.loads(f.read_text(encoding="utf-8"))
        if pg["path"] in {f"/p/{s}.html" for _, s, _ in HUBS}:
            continue
        body = f'<main class="hx-wrap post"><article><h1>{esc(pg["title"])}</h1><div class="post-body">{localize(pg["content"])}</div></article></main>'
        write(pg["path"], page(pg["title"], body, pg["path"]))

    rows = "".join(f'<li><time>{p["date"]:%Y.%m.%d}</time> <a href="{p["path"]}">{esc(p["title"])}</a></li>' for p in posts)
    write("/archive.html", page("전체 지원금", f'<main class="hx-wrap post"><h1>전체 지원금 {len(posts)}개</h1><ul class="archive">{rows}</ul></main>', "/archive.html"))

    write("/search.json", json.dumps([{"t": p["title"], "u": p["path"], "s": p["summary"], "i": p["img"], "d": f'{p["date"]:%Y.%m.%d}',
                                       "l": " ".join(p["labels"])} for p in posts], ensure_ascii=False))
    search = ('<main class="hx-wrap post"><h1 id="q">검색</h1><div id="r" class="grid"></div></main>'
              '<script>(async()=>{const q=new URLSearchParams(location.search).get("q")||"";'
              'document.getElementById("q").textContent=q?`"${q}" 검색 결과`:"검색";'
              'const w=q.toLowerCase().split(/\\s+/).filter(Boolean),d=await (await fetch("/search.json")).json();'
              'const e=s=>s.replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",\'"\':"&quot;"}[c]));'
              'const hit=d.filter(p=>w.every(x=>(p.t+" "+p.s+" "+p.l).toLowerCase().includes(x)));'
              'document.getElementById("r").innerHTML=hit.length?hit.map(p=>`<a class="card" href="${p.u}"><span class="thumb"><img src="${p.i}" alt="" loading="lazy"></span><time>${p.d}</time><b>${e(p.t)}</b><span class="sum">${e(p.s)}</span></a>`).join("")'
              ':`<p class="empty">찾는 지원금이 없어요. 다른 단어로 검색해 보세요.</p>`})()</script>')
    write("/search.html", page("검색", search, "/search.html", extra_head='<meta name="robots" content="noindex">\n'))
    write("/404.html", page("페이지를 찾을 수 없어요", '<main class="hx-wrap post"><h1>페이지를 찾을 수 없어요</h1><p><a href="/">홈으로 가기</a></p></main>', "/404.html"))

    urls = ["/", "/archive.html"] + [f"/p/{s}.html" for _, s, _ in HUBS] + [p["path"] for p in posts]
    lastmod = {p["path"]: p.get("updated", p["published"]) for p in posts}
    write("/sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
          + "".join(f"<url><loc>{SITE}{u}</loc>" + (f"<lastmod>{lastmod[u]}</lastmod>" if u in lastmod else "") + "</url>" for u in urls) + "</urlset>\n")
    write("/robots.txt", f"User-agent: *\nDisallow: /search.html\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    items = "".join(f"<item><title>{esc(p['title'])}</title><link>{SITE}{p['path']}</link><guid>{SITE}{p['path']}</guid>"
                    f"<pubDate>{p['date']:%a, %d %b %Y %H:%M:%S %z}</pubDate><description>{esc(p['summary'])}</description></item>" for p in posts[:30])
    write("/feed.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{NAME}</title><link>{SITE}/</link>'
          f"<description>{esc(DESC)}</description><language>ko</language>{items}</channel></rss>\n")
    (OUT / ".nojekyll").write_text("")
    print(f"사이트 생성: 글 {len(posts)}편 → {OUT}")
    return posts


if __name__ == "__main__":
    build()
