"""Gera o site do Império do Mercador: páginas em pt (raiz), en/ e es/, e a arte copiada do jogo.

Uso (na raiz do site):
    python tools/build_site.py              # páginas + arte
    python tools/build_site.py --no-assets  # só as páginas (arte já copiada)

Variáveis de ambiente:
    SITE_BASE   endereço público do site, com / no fim (vai em canonical, hreflang, og e sitemap)
    GAME_DIR    pasta do jogo (padrão: ../imperio-do-mercador)
    LOVEC       lovec.exe do LÖVE, para exportar o logo de cada idioma (lovec . --logo <idioma>)

A arte vem do jogo: sprites e animações de assets/gfx, as capturas de build/store/<idioma>/ (gere antes com
`node tools/build_store.mjs` no jogo) e o logo exportado pelo próprio jogo.
"""
import html
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from content_pt import PT, EMAIL  # noqa: E402
from content_en import EN  # noqa: E402
from content_es import ES  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
GAME = Path(os.environ.get("GAME_DIR", ROOT.parent / "imperio-do-mercador")).resolve()
BASE = os.environ.get("SITE_BASE", "https://italobandeira.github.io/imperiodomercador/")
LOVEC = os.environ.get("LOVEC", r"C:\Program Files\LOVE\lovec.exe")
SAVE_DIR = Path(os.environ.get("APPDATA", "")) / "LOVE" / "imperio_do_mercador"
PLAY_URL = "https://play.google.com/store/apps/details?id=com.italobandeira.imperiodomercador"
UPDATED = "2026-10-21"

# Português na raiz; os outros idiomas em subpastas com os mesmos nomes de arquivo.
LANGS = [("pt", PT, ""), ("en", EN, "en/"), ("es", ES, "es/")]
PAGES = ["index.html", "privacy.html", "terms.html", "contact.html"]

SPRITES = [
    "logo_crest", "cloud_1", "cloud_2", "portrait_nix", "portrait_pip", "bust_warrior", "album_aldric",
    "icon_fair_banner", "chest_open", "icon_video", "icon_check", "icon_star", "icon_chest", "icon_crown",
    "icon_gem", "icon_gold", "tex_planks", "ui_parchment", "ui_wood", "ui_dark", "ui_btn_gold", "ui_btn_blue",
    "ui_inset", "bg_mountains", "bg_houses", "bg_street",
]
ANIMS = [
    "hero_warrior_walk", "hero_archer_walk", "hero_mage_walk", "hero_cleric_walk", "boss_goblin_king",
    "shop_potions", "merchant_idle", "merchant_front_lumen", "coin_spin",
]

esc = html.escape


# Arte -------------------------------------------------------------------------------------------------------

def copy_assets():
    from PIL import Image

    img = ROOT / "assets" / "img"
    for sub in ("sprites", "anims", "screens"):
        (img / sub).mkdir(parents=True, exist_ok=True)
    gfx = GAME / "assets" / "gfx"
    for name in SPRITES:
        shutil.copy2(gfx / "sprites" / f"{name}.png", img / "sprites" / f"{name}.png")
    for name in ANIMS:
        shutil.copy2(gfx / "anims" / f"{name}.png", img / "anims" / f"{name}.png")
        shutil.copy2(gfx / "anims" / f"{name}.json", img / "anims" / f"{name}.json")

    fonts = ROOT / "assets" / "fonts"
    fonts.mkdir(parents=True, exist_ok=True)
    for f in ("Jersey10.ttf", "OFL.txt"):
        shutil.copy2(GAME / "assets" / "fonts" / f, fonts / f)

    store = GAME / "build" / "store"
    icon = Image.open(store / "icon_512.png").convert("RGBA")
    icon.save(img / "icon_512.png")
    icon.resize((192, 192), Image.NEAREST).save(img / "icon_192.png")
    icon.resize((32, 32), Image.LANCZOS).save(img / "favicon_32.png")

    for code, _, _ in LANGS:
        # Logo do idioma, exportado pelo jogo em fundo transparente e recortado no que tem desenho.
        subprocess.run([LOVEC, str(GAME), "--logo", code], check=True, capture_output=True)
        logo = Image.open(SAVE_DIR / f"logo_{code}.png").convert("RGBA")
        logo.crop(logo.getbbox()).save(img / f"logo_{code}.png")
        # Capturas da ficha da Play (1080x1920) em WebP na metade do tamanho; destaque para o og:image.
        shots = img / "screens" / code
        shots.mkdir(exist_ok=True)
        for k in range(1, 9):
            im = Image.open(store / code / f"{k}.png").convert("RGB")
            im.resize((540, 960), Image.LANCZOS).save(shots / f"{k}.webp", "WEBP", quality=82, method=6)
        shutil.copy2(store / code / "feature.png", img / f"og_{code}.png")
    print(f"arte copiada de {GAME}")


def sprite_size(name):
    from PIL import Image
    return Image.open(ROOT / "assets" / "img" / "sprites" / f"{name}.png").size


def sprite(name, scale, root, alt="", cls="px"):
    w, h = sprite_size(name)
    alt_attr = f'alt="{esc(alt)}"' if alt else 'alt="" aria-hidden="true"'
    return (f'<img class="{cls}" src="{root}assets/img/sprites/{name}.png" width="{w * scale}" height="{h * scale}" '
            f'{alt_attr} loading="lazy">')


def anim(name, scale, root, cls="", style=""):
    """Animação de quadros do jogo (sprite sheet horizontal) com CSS steps()."""
    data = json.loads((ROOT / "assets" / "img" / "anims" / f"{name}.json").read_text(encoding="utf8"))
    frames = list(data["frames"].values())
    fw, fh = frames[0]["frame"]["w"], frames[0]["frame"]["h"]
    dur = sum(f.get("duration", 100) for f in frames)
    n = len(frames)
    css = (f"--img:url('{root}assets/img/anims/{name}.png');--w:{fw * scale}px;--h:{fh * scale}px;"
           f"--sheet:{fw * scale * n}px;--frames:{n};--dur:{dur}ms;{style}")
    return f'<span class="anim {cls}" style="{css}" aria-hidden="true"></span>'


# Peças comuns -----------------------------------------------------------------------------------------------

PLAY_SVG = ('<svg class="btn-ico" viewBox="0 0 10 12" aria-hidden="true" shape-rendering="crispEdges">'
            '<path d="M0 0h2v1h2v1h2v1h2v1h2v4h-2v1h-2v1h-2v1h-2v1h-2z" fill="currentColor"/></svg>')

LEDGER_SPRITE = {"phone": "icon_chest", "ad": "icon_video", "card": "icon_gem", "crown": "icon_crown"}


def head(L, page, prefix, root, title, description):
    code = L["html_lang"]
    links = []
    for c, Lx, p in LANGS:
        links.append(f'<link rel="alternate" hreflang="{Lx["html_lang"]}" href="{BASE}{p}{page_url(page)}">')
    links.append(f'<link rel="alternate" hreflang="x-default" href="{BASE}{page_url(page)}">')
    lang_code = [c for c, Lx, p in LANGS if Lx is L][0]
    return f"""<!DOCTYPE html>
<html lang="{code}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#2a1a14">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="index, follow">
  <meta name="author" content="Italo Bandeira">
  <link rel="canonical" href="{BASE}{prefix}{page_url(page)}">
  {chr(10).join("  " + x for x in links).strip()}
  <meta property="og:type" content="{"website" if page == "index.html" else "article"}">
  <meta property="og:locale" content="{L["og_locale"]}">
  <meta property="og:site_name" content="{esc(L["home"]["hero_alt"])}">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{BASE}{prefix}{page_url(page)}">
  <meta property="og:image" content="{BASE}assets/img/og_{lang_code}.png">
  <meta property="og:image:width" content="1024">
  <meta property="og:image:height" content="500">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" type="image/png" sizes="32x32" href="{root}assets/img/favicon_32.png">
  <link rel="apple-touch-icon" href="{root}assets/img/icon_192.png">
  <link rel="preload" href="{root}assets/fonts/Jersey10.ttf" as="font" type="font/ttf" crossorigin>
  <link rel="stylesheet" href="{root}style.css">
</head>"""


def page_url(page):
    return "" if page == "index.html" else page


def header(L, page, prefix, root):
    u = L["ui"]
    home = "" if page == "index.html" else "index.html"
    nav = [
        (f"{home}#jogo", u["nav_game"], None),
        (f"{home}#recursos", u["nav_features"], None),
        (f"{home}#telas", u["nav_screens"], None),
        (f"{home}#duvidas", u["nav_faq"], None),
        ("contact.html", u["nav_contact"], "contact.html"),
    ]
    current = ' aria-current="page"'
    items = "".join(
        f'<a href="{href}"{current if cur == page else ""}>{esc(label)}</a>' for href, label, cur in nav)
    return f"""<body>
  <a class="skip-link" href="#conteudo">{esc(u["skip"])}</a>
  <header class="site-header">
    <div class="wrap header-inner">
      <a class="brand" href="{root}{prefix}index.html" aria-label="{esc(u["home_aria"])}">
        <img class="brand-crest" src="{root}assets/img/icon_192.png" width="46" height="46" alt="">
        <span>{esc(L["home"]["hero_alt"])}</span>
      </a>
      <nav class="header-nav" aria-label="Menu">
        {items}
      </nav>
      {lang_switch(L, page, root)}
    </div>
  </header>"""


def lang_switch(L, page, root):
    out = []
    for c, Lx, p in LANGS:
        if Lx is L:
            out.append(f'<span class="lang-cur" aria-current="true">{Lx["short"]}</span>')
        else:
            out.append(f'<a class="lang-link" href="{root}{p}{page}" hreflang="{Lx["html_lang"]}" lang="{Lx["html_lang"]}" '
                       f'title="{esc(Lx["label"])}">{Lx["short"]}</a>')
    return f'<span class="lang-switch">{"".join(out)}</span>'


def footer(L, page, prefix, root):
    u = L["ui"]
    home = "" if page == "index.html" else "index.html"
    langs = " · ".join(
        f'<a href="{root}{p}{page}" hreflang="{Lx["html_lang"]}" lang="{Lx["html_lang"]}">{Lx["label"]}</a>'
        for c, Lx, p in LANGS)
    def cur(p):
        return ' aria-current="page"' if p == page else ""
    return f"""  <footer class="site-footer">
    <div class="wrap footer-inner">
      <div class="footer-brand">
        <a class="brand" href="{home or "#"}" aria-label="{esc(u["home_aria"])}"><img class="brand-crest" src="{root}assets/img/icon_192.png" width="46" height="46" alt=""><span>{esc(L["home"]["hero_alt"])}</span></a>
        <p>{esc(u["footer_tagline"])}</p>
        <a class="btn btn-gold btn-small" href="{PLAY_URL}" target="_blank" rel="noopener noreferrer">{PLAY_SVG}{esc(u["play_small"])}</a>
      </div>
      <nav class="footer-col" aria-label="{esc(u["footer_game"])}">
        <h2>{esc(u["footer_game"])}</h2>
        <a href="{home}#jogo">{esc(u["nav_game"])}</a>
        <a href="{home}#recursos">{esc(u["nav_features"])}</a>
        <a href="{home}#telas">{esc(u["nav_screens"])}</a>
        <a href="{home}#duvidas">{esc(u["nav_faq"])}</a>
      </nav>
      <nav class="footer-col" aria-label="{esc(u["footer_support"])}">
        <h2>{esc(u["footer_support"])}</h2>
        <a href="contact.html"{cur("contact.html")}>{esc(u["nav_contact"])}</a>
        <a href="mailto:{EMAIL}">{esc(u["footer_email"])}</a>
      </nav>
      <nav class="footer-col" aria-label="{esc(u["footer_legal"])}">
        <h2>{esc(u["footer_legal"])}</h2>
        <a href="privacy.html"{cur("privacy.html")}>{esc(u["nav_privacy"])}</a>
        <a href="terms.html"{cur("terms.html")}>{esc(u["nav_terms"])}</a>
      </nav>
    </div>
    <div class="wrap footer-bottom">
      <p>{esc(u["footer_rights"])}</p>
      <p>{esc(u["footer_credits"])}</p>
      <p class="footer-langs">{langs}</p>
    </div>
  </footer>
</body>
</html>
"""


# Páginas ----------------------------------------------------------------------------------------------------

def home_page(L, code, prefix, root):
    h, u = L["home"], L["ui"]
    walkers = "".join(
        f'<span class="walker" style="--walk-delay:{d}s;--walk-time:{t}s">{anim(f"hero_{cls}_walk", 3, root, "walker-sprite")}</span>'
        for cls, d, t in (("warrior", 0, 26), ("mage", -7, 26), ("archer", -13, 26), ("cleric", -19.5, 26)))
    badges = "".join(f"<li>{sprite('icon_check', 2, root)}{esc(b)}</li>" for b in h["badges"])
    step_art = [anim("shop_potions", 3, root), sprite("bust_warrior", 3, root), sprite("icon_crown", 5, root)]
    steps = "".join(
        f'<li class="card parchment step"><span class="step-num">{k + 1}</span><div class="step-art">{step_art[k]}</div>'
        f"<h3>{esc(t)}</h3><p>{esc(d)}</p></li>"
        for k, (t, d) in enumerate(h["steps"]))
    feat_art = [sprite("portrait_nix", 3, root), anim("boss_goblin_king", 2, root), anim("merchant_front_lumen", 3, root),
                sprite("icon_fair_banner", 5, root), sprite("album_aldric", 3, root), sprite("chest_open", 4, root)]
    features = "".join(
        f'<li class="card parchment feature"><div class="feature-art">{feat_art[k]}</div><div><h3>{esc(t)}</h3><p>{esc(d)}</p></div></li>'
        for k, (t, d) in enumerate(h["features"]))
    shots = "".join(
        f'<li><figure><img src="{root}assets/img/screens/{code}/{k + 1}.webp" width="540" height="960" '
        f'alt="{esc(cap)}" loading="lazy"><figcaption>{esc(cap)}</figcaption></figure></li>'
        for k, cap in enumerate(h["screens"]))
    fair_icons = ["icon_gem", "icon_video", "icon_chest", "icon_star"]
    fair = "".join(
        f'<li><span class="ico">{sprite(fair_icons[k], 3, root)}</span><div><h3>{esc(t)}</h3><p>{esc(d)}</p></div></li>'
        for k, (t, d) in enumerate(h["fair"]))
    faq = "".join(
        f'<details class="faq-item"><summary>{esc(q)}</summary><div class="faq-answer"><p>{a}</p></div></details>'
        for q, a in h["faq"])
    lw, lh = logo_size(code)
    clouds = (f'<span class="cloud cloud-a">{sprite("cloud_1", 4, root)}</span>'
              f'<span class="cloud cloud-b">{sprite("cloud_2", 4, root)}</span>'
              f'<span class="cloud cloud-c">{sprite("cloud_1", 3, root)}</span>')
    return (head(L, "index.html", prefix, root, h["title"], h["description"]) + "\n"
            + header(L, "index.html", prefix, root) + f"""
  <main id="conteudo">
    <section class="hero" id="jogo" aria-labelledby="hero-title">
      <div class="hero-sky" aria-hidden="true">{clouds}</div>
      <div class="wrap hero-content">
        <h1 id="hero-title" class="hero-logo"><img src="{root}assets/img/logo_{code}.png" width="{lw}" height="{lh}" alt="{esc(h["hero_alt"])}"></h1>
        <p class="hero-tag">{esc(h["hero_tag"])}</p>
        <div class="hero-cta">
          <a class="btn btn-gold" href="{PLAY_URL}" target="_blank" rel="noopener noreferrer">{PLAY_SVG}{esc(u["play"])}</a>
          <a class="btn btn-blue" href="#telas">{esc(h["cta_screens"])}</a>
        </div>
        <ul class="badges">{badges}</ul>
      </div>
      <div class="hero-street" aria-hidden="true">
        <div class="layer layer-mountains"></div>
        <div class="layer layer-houses"></div>
        <div class="layer layer-street"></div>
        {walkers}
      </div>
    </section>

    <section class="section intro">
      <div class="wrap">
        <div class="card parchment intro-card">
          <div class="intro-art">{anim("merchant_idle", 5, root)}</div>
          <div>
            <h2 class="title-ink">{esc(h["intro_title"])}</h2>
            <p>{esc(h["intro"])}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="section" aria-labelledby="como-funciona">
      <div class="wrap">
        <h2 class="title" id="como-funciona">{esc(h["steps_title"])}</h2>
        <ol class="steps">{steps}</ol>
      </div>
    </section>

    <section class="section" id="recursos" aria-labelledby="recursos-title">
      <div class="wrap">
        <h2 class="title" id="recursos-title">{esc(h["features_title"])}</h2>
        <ul class="features">{features}</ul>
      </div>
    </section>

    <section class="section" id="telas" aria-labelledby="telas-title">
      <div class="wrap">
        <h2 class="title" id="telas-title">{esc(h["screens_title"])}</h2>
        <p class="section-hint">{esc(h["screens_hint"])}</p>
      </div>
      <ul class="shots" tabindex="0" aria-label="{esc(h["screens_title"])}">{shots}</ul>
    </section>

    <section class="section" aria-labelledby="justo-title">
      <div class="wrap">
        <div class="card wood fair">
          <h2 class="title" id="justo-title">{esc(h["fair_title"])}</h2>
          <ul class="fair-list">{fair}</ul>
        </div>
      </div>
    </section>

    <section class="section" id="duvidas" aria-labelledby="duvidas-title">
      <div class="wrap narrow">
        <h2 class="title" id="duvidas-title">{esc(h["faq_title"])}</h2>
        <div class="faq">{faq}</div>
      </div>
    </section>

    <section class="section final">
      <div class="wrap final-inner">
        {sprite("logo_crest", 3, root, cls="px final-crest")}
        <h2 class="title">{esc(h["final_title"])}</h2>
        <p>{esc(h["final_text"])}</p>
        <a class="btn btn-gold" href="{PLAY_URL}" target="_blank" rel="noopener noreferrer">{PLAY_SVG}{esc(u["play"])}</a>
        <div class="final-coins" aria-hidden="true">{anim("coin_spin", 3, root)}{anim("coin_spin", 3, root, style="animation-delay:-160ms")}{anim("coin_spin", 3, root, style="animation-delay:-330ms")}</div>
      </div>
    </section>
  </main>
""" + footer(L, "index.html", prefix, root))


def logo_size(code):
    from PIL import Image
    w, h = Image.open(ROOT / "assets" / "img" / f"logo_{code}.png").size
    return w, h


def legal_page(L, code, prefix, root, key, page):
    d, u = L[key], L["ui"]
    ledger = "".join(
        f'<div><dt>{sprite(LEDGER_SPRITE[icon], 3, root)}</dt><dd>{esc(text)}</dd></div>' for icon, text in d["ledger"])
    toc = "".join(f'<li><a href="#{sid}">{esc(t.split(". ", 1)[-1])}</a></li>' for sid, t, _ in d["sections"])
    sections = "".join(f'<section class="legal-section" id="{sid}"><h2>{esc(t)}</h2>{body}</section>'
                       for sid, t, body in d["sections"])
    return (head(L, page, prefix, root, f'{d["title"]} | {L["home"]["hero_alt"]}', d["description"]) + "\n"
            + header(L, page, prefix, root) + f"""
  <main id="conteudo" class="legal">
    <section class="legal-hero">
      <div class="wrap legal-hero-grid">
        <div>
          <h1 class="title">{esc(d["title"])}</h1>
          <p class="lead">{esc(d["lead"])}</p>
          <p class="doc-meta">{esc(u["effective"])} <time datetime="{UPDATED}">{esc(u["date_long"])}</time></p>
        </div>
        <dl class="card parchment ledger">{ledger}</dl>
      </div>
    </section>
    <div class="wrap legal-layout">
      <nav class="toc card dark" aria-label="{esc(u["in_this_doc"])}">
        <strong>{esc(u["in_this_doc"])}</strong>
        <ol>{toc}</ol>
      </nav>
      <article class="card parchment legal-doc">
        <aside class="summary"><h2>{esc(d["summary_title"])}</h2><p>{esc(d["summary"])}</p></aside>
        {sections}
      </article>
    </div>
  </main>
""" + footer(L, page, prefix, root))


def contact_page(L, code, prefix, root):
    d, u = L["contact"], L["ui"]
    include = "".join(f"<li>{esc(x)}</li>" for x in d["include"])
    topic_icons = ["icon_check", "icon_gem", "icon_chest", "icon_star"]
    topics = "".join(f'<li><span class="ico">{sprite(topic_icons[k], 3, root)}</span><div><h3>{esc(t)}</h3><p>{esc(x)}</p></div></li>'
                     for k, (t, x) in enumerate(d["topics"]))
    return (head(L, "contact.html", prefix, root, f'{d["title"]} | {L["home"]["hero_alt"]}', d["description"]) + "\n"
            + header(L, "contact.html", prefix, root) + f"""
  <main id="conteudo" class="legal">
    <section class="legal-hero">
      <div class="wrap contact-grid">
        <div>
          <h1 class="title">{esc(d["title"])}</h1>
          <p class="lead">{esc(d["lead"])}</p>
        </div>
        <div class="card parchment contact-card">
          {sprite("portrait_pip", 3, root)}
          <p class="contact-label">{esc(d["email_label"])}</p>
          <a class="contact-email" href="mailto:{EMAIL}">{EMAIL}</a>
          <a class="btn btn-gold" href="mailto:{EMAIL}?subject={esc(L['home']['hero_alt'])}">{esc(d["write"])}</a>
          <p class="contact-reply">{esc(d["reply"])}</p>
        </div>
      </div>
    </section>
    <div class="wrap contact-body">
      <section class="card parchment">
        <h2 class="title-ink">{esc(d["topics_title"])}</h2>
        <ul class="topics">{topics}</ul>
      </section>
      <section class="card parchment">
        <h2 class="title-ink">{esc(d["include_title"])}</h2>
        <ul class="include">{include}</ul>
      </section>
    </div>
  </main>
""" + footer(L, "contact.html", prefix, root))


def write_pages():
    for code, L, prefix in LANGS:
        root = "../" * prefix.count("/")
        out = ROOT / prefix
        out.mkdir(parents=True, exist_ok=True)
        files = {
            "index.html": home_page(L, code, prefix, root),
            "privacy.html": legal_page(L, code, prefix, root, "privacy", "privacy.html"),
            "terms.html": legal_page(L, code, prefix, root, "terms", "terms.html"),
            "contact.html": contact_page(L, code, prefix, root),
        }
        for name, text in files.items():
            (out / name).write_text(text, encoding="utf8", newline="\n")
    # Mapa do site e robots.
    urls = []
    for page in PAGES:
        alts = "".join(f'\n    <xhtml:link rel="alternate" hreflang="{Lx["html_lang"]}" href="{BASE}{p}{page_url(page)}"/>'
                       for c, Lx, p in LANGS)
        for c, Lx, p in LANGS:
            urls.append(f"  <url>\n    <loc>{BASE}{p}{page_url(page)}</loc>\n    <lastmod>{UPDATED}</lastmod>{alts}\n  </url>")
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(urls) + "\n</urlset>\n", encoding="utf8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap.xml\n", encoding="utf8")
    (ROOT / ".nojekyll").write_text("", encoding="utf8")
    print(f"{len(LANGS) * len(PAGES)} páginas geradas (base {BASE})")


if __name__ == "__main__":
    if "--no-assets" not in sys.argv:
        copy_assets()
    write_pages()
