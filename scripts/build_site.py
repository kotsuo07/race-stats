"""data/boat/summary.json と content/ から静的サイトを _site/ に生成する。"""
import glob
import html
import json
import os
import shutil
from datetime import datetime, timezone, timedelta
from email.utils import format_datetime

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader

JST = timezone(timedelta(hours=9))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "_site")
SITE = json.load(open(os.path.join(ROOT, "config/site.json"), encoding="utf-8"))


def u(path):
    return SITE["base_path"] + path


def f1(x):
    return "—" if x is None else f"{x:.1f}"


def line_chart(points, label):
    """points: [(月, 値)] 1系列の折れ線(SVG)"""
    pts = [(m, v) for m, v in points if v is not None]
    if len(pts) < 2:
        return "<p class='note'>データ蓄積中です。</p>"
    W, H, L, R, T, B = 440, 240, 34, 10, 10, 28
    vals = [v for _, v in pts]
    lo, hi = int(min(vals) // 5 * 5), int(-(-max(vals) // 5) * 5)
    if hi == lo:
        hi = lo + 5
    n = len(pts)
    x = lambda i: L + (W - L - R) * i / (n - 1)  # noqa: E731
    y = lambda v: T + (H - T - B) * (1 - (v - lo) / (hi - lo))  # noqa: E731
    p = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="{html.escape(label)}">']
    step = 5 if hi - lo <= 30 else 10
    for g in range(lo, hi + 1, step):
        p.append(f'<line x1="{L}" x2="{W - R}" y1="{y(g):.1f}" y2="{y(g):.1f}" stroke="var(--line)"/>')
        p.append(f'<text x="{L - 6}" y="{y(g) + 4:.1f}" text-anchor="end" font-size="11" fill="var(--muted)">{g}%</text>')
    for i, (m, _) in enumerate(pts):
        if i % max(1, n // 6) == 0 or i == n - 1:
            p.append(f'<text x="{x(i):.1f}" y="{H - 8}" text-anchor="middle" font-size="11" fill="var(--muted)">{m[2:].replace("-", "/")}</text>')
    p.append('<polyline fill="none" stroke="var(--s1)" stroke-width="2" stroke-linejoin="round" points="' +
             " ".join(f"{x(i):.1f},{y(v):.1f}" for i, (_, v) in enumerate(pts)) + '"/>')
    for i, (m, v) in enumerate(pts):
        p.append(f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="4" fill="var(--s1)" stroke="var(--surface)" stroke-width="2">'
                 f'<title>{m}: {v:.1f}%</title></circle>')
    p.append("</svg>")
    return "".join(p) + '<p class="note">点に触れると値が出ます。</p>'


def load_md(path):
    text = open(path, encoding="utf-8").read()
    meta = {}
    if text.startswith("---"):
        _, fm, text = text.split("---", 2)
        meta = yaml.safe_load(fm) or {}
    body = markdown.markdown(text, extensions=["tables", "fenced_code", "toc"])
    return meta, body


def write(path, content):
    full = os.path.join(OUT, path.lstrip("/"))
    if full.endswith("/"):
        full += "index.html"
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    env = Environment(loader=FileSystemLoader(os.path.join(ROOT, "templates")), autoescape=True)
    env.globals.update(f1=f1, u=u)
    now = datetime.now(JST)
    common = {"site": SITE, "u": u, "f1": f1, "year": now.year}

    posts = []
    for f in glob.glob(os.path.join(ROOT, "content/posts/*.md")):
        meta, body = load_md(f)
        if meta.get("draft"):
            continue
        slug = os.path.splitext(os.path.basename(f))[0]
        posts.append({"slug": slug, "path": f"/posts/{slug}/", "title": meta["title"],
                      "date": str(meta["date"]), "updated": str(meta.get("updated") or ""),
                      "description": meta.get("description", ""), "tags": meta.get("tags", []), "body": body})
    posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)

    for p in posts:
        related = [q for q in posts if q is not p and set(q["tags"]) & set(p["tags"])][:5] or \
                  [q for q in posts if q is not p][:5]
        jsonld = json.dumps({"@context": "https://schema.org", "@type": "Article", "headline": p["title"],
                             "datePublished": p["date"], "dateModified": p["updated"] or p["date"],
                             "author": {"@type": "Person", "name": SITE["operator"]}}, ensure_ascii=False)
        write(p["path"], env.get_template("post.html").render(
            **common, title=p["title"], description=p["description"], path=p["path"], is_post=True,
            date=p["date"], updated=p["updated"], body=p["body"], related=related, jsonld=jsonld))

    for f in glob.glob(os.path.join(ROOT, "content/pages/*.md")):
        meta, body = load_md(f)
        slug = os.path.splitext(os.path.basename(f))[0]
        write(f"/{slug}/", env.get_template("page.html").render(
            **common, title=meta["title"], description=meta.get("description"), path=f"/{slug}/", body=body))

    write("/posts/", env.get_template("posts.html").render(**common, title="記事一覧", path="/posts/", posts=posts))

    sp = os.path.join(ROOT, "data/boat/summary.json")
    extra_urls = []
    if os.path.exists(sp):
        s = json.load(open(sp, encoding="utf-8"))
        nat_chart = line_chart([(m["month"], m["c1_win"]) for m in s["monthly_c1"][-24:]], "1コース1着率の推移")
        write("/", env.get_template("index.html").render(**common, title=None, path="/", posts=posts, s=s,
                                                          chart=nat_chart))
        venues = [(j, v["name"]) for j, v in s["venues"].items()]
        rank = {r["jcd"]: i + 1 for i, r in enumerate(s["venue_rank_c1"])}
        write("/boat/venues/", env.get_template("venues.html").render(
            **common, title="ボートレース場別データ一覧", path="/boat/venues/", s=s,
            rows=[(j, v) for j, v in s["venues"].items() if v["year_races"]]))
        extra_urls.append("/boat/venues/")
        for j, v in s["venues"].items():
            path = f"/boat/venue/{j}/"
            ch = line_chart([(m["month"], m["c1_win"]) for m in v["monthly_c1"]], f"{v['name']} 1コース1着率の推移")
            write(path, env.get_template("venue.html").render(
                **common, title=f"{v['name']}ボートのコース別1着率・決まり手・配当データ", path=path,
                description=f"{v['name']}ボートレース場の進入コース別1着率・2連対率・3連対率、決まり手、3連単の平均配当と万舟率。公式成績を毎日集計。",
                s=s, v=v, rank=rank.get(j, "—"), venues=venues, chart=ch))
            extra_urls.append(path)
    else:
        write("/", env.get_template("posts.html").render(**common, title=None, path="/", posts=posts))

    urls = ["/", "/posts/"] + extra_urls + [p["path"] for p in posts] + \
           [f"/{os.path.splitext(os.path.basename(f))[0]}/" for f in glob.glob(os.path.join(ROOT, "content/pages/*.md"))]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"<url><loc>{SITE['site_url']}{x}</loc></url>" for x in urls]
    sm.append("</urlset>")
    write("/sitemap.xml", "\n".join(sm))
    write("/robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE['site_url']}/sitemap.xml\n")

    items = []
    for p in posts[:20]:
        d = datetime.fromisoformat(p["date"]).replace(tzinfo=JST)
        items.append(f"<item><title>{html.escape(p['title'])}</title><link>{SITE['site_url']}{p['path']}</link>"
                     f"<guid>{SITE['site_url']}{p['path']}</guid><pubDate>{format_datetime(d)}</pubDate>"
                     f"<description>{html.escape(p['description'])}</description></item>")
    write("/feed.xml", f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
                       f"<title>{html.escape(SITE['name'])}</title><link>{SITE['site_url']}/</link>"
                       f"<description>{html.escape(SITE['description'])}</description>{''.join(items)}</channel></rss>")
    open(os.path.join(OUT, ".nojekyll"), "w").close()
    print(f"built {len(posts)} posts, {len(extra_urls)} data pages")


if __name__ == "__main__":
    main()
