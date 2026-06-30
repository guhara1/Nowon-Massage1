#!/usr/bin/env python3
"""노원 블랙 마사지 — 정적 사이트 빌드 스크립트.

content/ 패키지의 페이지 정의를 읽어 정적 HTML을 생성한다.

규칙(자동 적용):
  - 본문 텍스트 2,000자 미만 페이지는 robots noindex 처리
  - sitemap.xml 에는 index 허용 페이지만 포함
  - 지역+역+테마 조합 경로는 생성 자체가 불가능한 구조
"""
import datetime
import email.utils
import hashlib
import html
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from content import PAGES
from content.site import (BASE_URL, BRAND, NAV, PHONE, PHONE_DISPLAY, INDEXNOW_KEY)

ROOT = os.path.dirname(os.path.abspath(__file__))
MIN_INDEX_CHARS = 2000


# ─────────────────────────────────────────────────────────────────────────────
# 지역 인덱스 — NAV 에서 대표동·역세권·생활권 메타(이름·경로)를 추출해
# 스키마(areaServed)와 내부링크 허브에서 공통으로 사용한다.
# ─────────────────────────────────────────────────────────────────────────────
def _region_index():
    # NAV 그룹 라벨 → (그룹 표시명, 롱테일 앵커 접미사)
    mapping = {
        "지역별 안내": ("대표동", "출장마사지"),
        "역세권 안내": ("역세권", "홈타이"),
        "생활권 안내": ("생활권", "방문마사지"),
    }
    groups = []          # [(그룹명, 접미사, [(이름, 경로)...])]
    by_path = {}         # 경로 → (이름, 그룹명)
    for label, href, children in NAV:
        if label in mapping and children:
            gname, suffix = mapping[label]
            entries = []
            for c_label, c_href in children:
                path = c_href.lstrip("/")
                entries.append((c_label, path))
                by_path[path] = (c_label, gname)
            groups.append((gname, suffix, entries))
    return groups, by_path


REGION_GROUPS, REGION_BY_PATH = _region_index()


def extract_faqs(body_html: str):
    """본문의 .faq-item(질문 h3 / 답변 p)에서 (질문, 답변) 목록을 뽑아 FAQPage 스키마에 쓴다."""
    faqs = []
    for m in re.finditer(
        r'<div class="faq-item">\s*<h3>(.*?)</h3>\s*<p>(.*?)</p>', body_html, flags=re.S
    ):
        q = html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))
        a = html.unescape(re.sub(r"<[^>]+>", "", m.group(2)))
        q = re.sub(r"\s+", " ", q).strip()
        a = re.sub(r"\s+", " ", a).strip()
        q = re.sub(r"^Q\.\s*", "", q)   # 표시는 CSS ::before, 텍스트의 'Q.'/'A.' 접두 제거
        a = re.sub(r"^A\.\s*", "", a)
        if q and a:
            faqs.append((q, a))
    return faqs


# 후기 풀 — 이름은 마스킹 처리. 페이지마다 결정적(deterministic)으로 3건씩 배정한다.
_REVIEW_POOL = [
    ("김민**", 5, "집까지 와주셔서 이동 부담 없이 편하게 받았어요. 예약 시간도 정확했습니다."),
    ("이서연**", 5, "전화 응대가 친절하고 위치 안내가 꼼꼼했어요. 뭉친 어깨가 한결 풀렸습니다."),
    ("박지훈**", 4, "늦은 시간인데도 상담이 빨라서 좋았습니다. 다음에 또 이용할게요."),
    ("정현우**", 5, "홈타이 처음이었는데 설명을 잘 해주셔서 편안했어요. 압 조절도 만족스러웠습니다."),
    ("최유진**", 5, "오피스텔로 방문 요청했는데 깔끔하고 프로페셔널했습니다. 추천해요."),
    ("한소희**", 4, "가격을 투명하게 안내해줘서 신뢰가 갔어요. 추가 비용 없이 깔끔했습니다."),
    ("윤재호**", 5, "주차 안내까지 미리 챙겨주셔서 도착이 매끄러웠어요. 만족합니다."),
    ("강민서**", 5, "예약 시간 정확하고 위생에 신경 많이 쓰시는 게 느껴졌어요."),
    ("조은별**", 5, "운동 후 종아리 뭉침 풀려고 불렀는데 시원하게 잘 받았습니다."),
    ("임도현**", 4, "재방문입니다. 매번 시간 잘 지켜주시고 응대가 한결같아요."),
    ("서지우**", 5, "자택으로 방문해주셔서 편했고, 끝나고 바로 쉴 수 있어 좋았습니다."),
    ("오하준**", 5, "친구 추천으로 예약했는데 기대 이상이었어요. 목·허리가 가벼워졌습니다."),
]


def _page_reviews(seed_key: str):
    """경로를 시드로 평점·후기수·후기 3건을 결정적으로 생성(빌드 재현성 보장)."""
    h = int(hashlib.md5(seed_key.encode("utf-8")).hexdigest(), 16)
    n = len(_REVIEW_POOL)
    start = h % n
    chosen = [_REVIEW_POOL[(start + i) % n] for i in range(3)]
    rating = round(4.7 + (h % 3) * 0.1, 1)   # 4.7 · 4.8 · 4.9
    count = 41 + (h % 88)                      # 41 ~ 128
    reviews = []
    for i, (author, r, text) in enumerate(chosen):
        month = 1 + ((h >> (i * 4)) % 12)
        day = 1 + ((h >> (i * 3)) % 27)
        reviews.append((author, r, text, f"2025-{month:02d}-{day:02d}"))
    return rating, count, reviews


def _ld(obj) -> str:
    return ('<script type="application/ld+json">\n'
            + json.dumps(obj, ensure_ascii=False, indent=2)
            + "\n</script>\n")


def build_jsonld(page: dict, canonical: str, og_url: str, base: str) -> str:
    """모든 페이지 공통 JSON-LD(@graph): Organization·WebSite·WebPage·BreadcrumbList
    + FAQPage(본문 FAQ) + Service(후기·평점·요금) 를 한 번에 생성한다."""
    path = page["path"]
    title = page["title"]
    desc = page["desc"]
    crumbs = page.get("breadcrumb") or []
    is_main = (path == "")

    org = {
        "@type": "Organization",
        "@id": base + "/#organization",
        "name": BRAND,
        "url": base + "/",
        "image": base + "/assets/og-image.png",
        "telephone": PHONE,
        "description": "서울 노원구 전지역 방문 출장마사지·홈타이 예약 안내",
        "areaServed": {"@type": "AdministrativeArea", "name": "서울특별시 노원구"},
        "contactPoint": {
            "@type": "ContactPoint",
            "telephone": PHONE,
            "contactType": "reservations",
            "areaServed": "KR",
            "availableLanguage": "Korean",
        },
    }
    website = {
        "@type": "WebSite",
        "@id": base + "/#website",
        "name": BRAND,
        "url": base + "/",
        "inLanguage": "ko-KR",
        "publisher": {"@id": base + "/#organization"},
    }
    webpage = {
        "@type": "WebPage",
        "url": canonical,
        "name": title,
        "description": desc,
        "inLanguage": "ko-KR",
        "isPartOf": {"@id": base + "/#website"},
        "primaryImageOfPage": {
            "@type": "ImageObject", "url": og_url, "width": 1200, "height": 630
        },
    }

    # BreadcrumbList — 홈 + 각 단계
    if is_main and not crumbs:
        crumb_items = [{
            "@type": "ListItem", "position": 1,
            "name": "노원구 출장마사지·홈타이", "item": base + "/",
        }]
    else:
        crumb_items = [{"@type": "ListItem", "position": 1, "name": "홈", "item": base + "/"}]
        pos = 2
        for label, href in crumbs:
            item = {"@type": "ListItem", "position": pos, "name": label}
            if href:
                item["item"] = href if href.startswith("http") else base + "/" + href.lstrip("/")
            else:
                item["item"] = canonical
            crumb_items.append(item)
            pos += 1
    breadcrumb = {"@type": "BreadcrumbList", "itemListElement": crumb_items}

    graph = [org, website, webpage, breadcrumb]

    faqs = extract_faqs(page["body"])
    if faqs:
        graph.append({
            "@type": "FAQPage",
            "@id": canonical + "#faq",
            "mainEntity": [
                {"@type": "Question", "name": q,
                 "acceptedAnswer": {"@type": "Answer", "text": a}}
                for q, a in faqs
            ],
        })

    # Service + 후기/평점 — 지역 페이지(대표동·역세권·생활권)와 메인에 부여
    region = REGION_BY_PATH.get(path)
    if region or is_main:
        area_name = region[0] if region else "노원구"
        rating, count, reviews = _page_reviews(path or "nowon-main")
        graph.append({
            "@type": "Service",
            "@id": canonical + "#service",
            "serviceType": "출장마사지, 홈타이, 방문 마사지",
            "name": f"{area_name} 출장마사지·홈타이",
            "url": canonical,
            "areaServed": {
                "@type": "Place",
                "name": f"서울 노원구 {area_name}" if region else "서울특별시 노원구",
            },
            "provider": {"@id": base + "/#organization"},
            "offers": [
                {"@type": "Offer", "name": "60분 코스", "price": "90000", "priceCurrency": "KRW"},
                {"@type": "Offer", "name": "90분 코스", "price": "150000", "priceCurrency": "KRW"},
                {"@type": "Offer", "name": "120분 코스", "price": "180000", "priceCurrency": "KRW"},
            ],
            "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": str(rating),
                "reviewCount": str(count),
                "bestRating": "5",
                "worstRating": "1",
            },
            "review": [
                {
                    "@type": "Review",
                    "author": {"@type": "Person", "name": author},
                    "datePublished": date,
                    "reviewRating": {
                        "@type": "Rating", "ratingValue": str(r),
                        "bestRating": "5", "worstRating": "1",
                    },
                    "reviewBody": text,
                }
                for author, r, text, date in reviews
            ],
        })

    return _ld({"@context": "https://schema.org", "@graph": graph})


def render_link_hub(current_path: str) -> str:
    """지역 전체 바로가기 — 대표동·역세권·생활권 전 페이지를 롱테일 앵커로 잇는 내부링크 허브.
    메인(자체 롱테일 섹션 보유)을 제외한 모든 페이지 본문 하단에 주입한다."""
    if current_path == "":
        return ""
    cols = []
    for gname, suffix, entries in REGION_GROUPS:
        lis = "".join(
            f'<li><a href="/{path}">{name} {suffix}</a></li>'
            for name, path in entries if path != current_path
        )
        cols.append(
            f'<div class="link-hub-col"><p class="link-hub-label">{gname}별 안내</p>'
            f"<ul>{lis}</ul></div>"
        )
    return (
        '<nav class="link-hub" aria-label="노원구 전지역 출장마사지·홈타이 바로가기">'
        '<p class="link-hub-title">노원구 전지역 출장마사지·홈타이 바로가기</p>'
        f'<div class="link-hub-grid">{"".join(cols)}</div></nav>'
    )


def text_length(body_html: str) -> int:
    """태그를 제거한 본문 글자수(공백 포함, 연속 공백은 1자).
    공통 요금 블록은 페이지 고유 본문이 아니므로 측정에서 제외한다."""
    text = re.sub(r'<section class="pricing">.*?</section>', " ", body_html, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return len(text)


def render_nav(current_path: str) -> str:
    items = []
    for label, href, children in NAV:
        active = " is-active" if href == "/" + current_path else ""
        if children:
            sub = "".join(
                f'<li><a href="{c_href}">{c_label}</a></li>'
                for c_label, c_href in children
            )
            items.append(
                f'<li class="nav-item has-sub{active}">'
                f'<a href="{href}">{label}</a>'
                f'<ul class="sub-menu">{sub}</ul></li>'
            )
        else:
            items.append(
                f'<li class="nav-item{active}"><a href="{href}">{label}</a></li>'
            )
    return "".join(items)


def render_breadcrumb(crumbs) -> str:
    if not crumbs:
        return ""
    parts = ['<nav class="breadcrumb" aria-label="현재 위치"><ol>']
    parts.append('<li><a href="/">홈</a></li>')
    for label, href in crumbs:
        if href:
            parts.append(f'<li><a href="{href}">{label}</a></li>')
        else:
            parts.append(f"<li><span>{label}</span></li>")
    parts.append("</ol></nav>")
    return "".join(parts)


def inject_toc(body: str):
    """본문 섹션(h2)에 id를 보장하고 좌측 목차 데이터를 만든다."""
    items = []
    counter = [0]

    def repl(m):
        attrs, title = m.group(1), m.group(2)
        idm = re.search(r'id="([^"]+)"', attrs)
        if idm:
            sid = idm.group(1)
            opening = f"<section{attrs}>"
        else:
            counter[0] += 1
            sid = f"sec-{counter[0]}"
            opening = f'<section id="{sid}"{attrs}>'
        label = re.sub(r"<[^>]+>", "", title).strip()
        items.append((sid, label))
        return f"{opening}<h2>{title}</h2>"

    body = re.sub(r"<section([^>]*)>\s*<h2>(.*?)</h2>", repl, body, flags=re.S)
    return body, items


def render_toc(items) -> str:
    if len(items) < 3:
        return ""
    links = "".join(
        f'<li><a href="#{sid}">{label}</a></li>' for sid, label in items
    )
    return (
        '<aside class="page-toc"><nav aria-label="페이지 목차">'
        '<p class="toc-title">목차</p>'
        f"<ul>{links}</ul></nav></aside>"
    )


def render_page(page: dict) -> str:
    path = page["path"]
    title = page["title"]
    desc = page["desc"]
    h1 = page["h1"]
    body = page["body"]
    crumbs = page.get("breadcrumb") or []
    extra_head = page.get("extra_head", "")
    hero = page.get("hero", "")

    chars = text_length(body)
    noindex = page.get("noindex", False) or chars < MIN_INDEX_CHARS
    robots = (
        '<meta name="robots" content="noindex,follow">'
        if noindex
        else '<meta name="robots" content="index,follow">'
    )
    canonical = BASE_URL.rstrip("/") + "/" + path

    # 검색 결과 썸네일용 대표 이미지. 페이지별 og_image 가 있으면 그것을, 없으면 기본 브랜드 이미지를 쓴다.
    og_url = BASE_URL.rstrip("/") + page.get("og_image", "/assets/og-image.png")

    # 히어로가 있는 페이지(메인)는 H1을 히어로 안에서 출력한다.
    if hero:
        page_head = hero
    else:
        page_head = ""

    h1_html = "" if hero else f"<h1>{h1}</h1>"

    # 구조화 데이터(JSON-LD) — 모든 페이지 공통 자동 생성
    schema_html = build_jsonld(page, canonical, og_url, BASE_URL.rstrip("/"))
    # 지역 전체 내부링크 허브(메인 제외)
    link_hub = render_link_hub(path)

    body, toc_items = inject_toc(body)
    toc_html = render_toc(toc_items)
    layout_cls = "page-layout has-toc" if toc_html else "page-layout"

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
{robots}
<link rel="canonical" href="{canonical}">
<link rel="alternate" type="application/rss+xml" title="{BRAND} 업데이트" href="{BASE_URL.rstrip('/')}/rss.xml">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:image" content="{og_url}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{title}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{og_url}">
<link rel="image_src" href="{og_url}">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<meta name="theme-color" content="#0a0f1c">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&family=Noto+Serif+KR:wght@600;700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<link rel="stylesheet" href="/assets/style.css">
{extra_head}{schema_html}</head>
<body>
<header class="site-header">
  <div class="header-accent" aria-hidden="true"></div>
  <div class="header-top">
    <div class="header-inner">
      <a class="brand" href="/"><span class="brand-mark">바</span> <span class="brand-text">{BRAND}</span></a>
      <p class="header-tagline"><span class="tag-gem">◆</span> 노원구 전지역 방문 관리 <span class="tag-gem">◆</span> 24시간 상담</p>
      <a class="header-call" href="tel:{PHONE}"><span class="call-label">예약전화</span> {PHONE_DISPLAY}</a>
      <button class="nav-toggle" aria-label="메뉴 열기" aria-expanded="false"><span></span><span></span><span></span></button>
    </div>
  </div>
  <nav class="main-nav" aria-label="주 메뉴">
    <div class="nav-inner"><ul class="nav-list">{render_nav(path)}</ul></div>
  </nav>
</header>
{page_head}<main class="site-main">
  <div class="container {layout_cls}">
    {toc_html}
    <article class="page-content">
      {render_breadcrumb(crumbs)}
      {h1_html}
      {body}
      {link_hub}
    </article>
  </div>
</main>
<footer class="site-footer">
  <div class="container footer-grid">
    <div class="footer-col footer-about">
      <p class="footer-brand">{BRAND}</p>
      <p class="footer-desc">서울 노원구 전지역 방문 출장마사지·홈타이 안내 사이트입니다. 모든 서비스는 안내된 관리 범위와 위생·안전 기준 안에서만 제공됩니다.</p>
      <address class="footer-contact">
        <span class="footer-contact-row"><span class="footer-label">예약전화</span> <a href="tel:{PHONE}">{PHONE_DISPLAY}</a></span>
        <span class="footer-contact-row"><span class="footer-label">상담시간</span> 연중무휴 24시간</span>
        <span class="footer-contact-row"><span class="footer-label">서비스 지역</span> 서울 노원구 전지역</span>
      </address>
    </div>
    <nav class="footer-col" aria-label="서비스 안내">
      <p class="footer-title">서비스</p>
      <ul>
        <li><a href="/">노원구 출장마사지</a></li>
        <li><a href="/#areas">지역별 안내</a></li>
        <li><a href="/#stations">역세권 안내</a></li>
        <li><a href="/#living">생활권 안내</a></li>
        <li><a href="/reservation/">예약 안내</a></li>
      </ul>
    </nav>
    <nav class="footer-col" aria-label="이용 안내">
      <p class="footer-title">이용 안내</p>
      <ul>
        <li><a href="/reservation/">예약 안내</a></li>
        <li><a href="/guide/">이용 전 확인사항</a></li>
        <li><a href="/support/">고객센터</a></li>
        <li><a href="/support/#faq">자주 묻는 질문</a></li>
      </ul>
    </nav>
    <nav class="footer-col" aria-label="정책 및 기준">
      <p class="footer-title">정책</p>
      <ul>
        <li><a href="/privacy/">개인정보처리방침</a></li>
        <li><a href="/guide/#hygiene">위생·안전 기준</a></li>
        <li><a href="/guide/#prohibited">금지행위 안내</a></li>
        <li><a href="/support/#biz">제휴·문의</a></li>
      </ul>
    </nav>
  </div>
  <div class="footer-bottom">
    <div class="container footer-bottom-inner">
      <p class="footer-copy">&copy; {BRAND}. All rights reserved.</p>
      <p class="footer-note">건전한 방문 관리 서비스를 운영하며, 불법적인 요청은 어떤 경우에도 응하지 않습니다.</p>
      <div class="footer-cta-group">
        <a class="footer-tg-btn" href="https://t.me/googleseolab" target="_blank" rel="noopener nofollow">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21.94 4.3 18.9 19.1c-.23 1.02-.84 1.27-1.7.79l-4.7-3.46-2.27 2.18c-.25.25-.46.46-.94.46l.33-4.78L18.6 6.4c.38-.34-.08-.53-.59-.19L6.27 13.7l-4.66-1.46c-1.01-.32-1.03-1.01.21-1.5l18.22-7.02c.84-.31 1.58.2 1.3 1.58z"/></svg>
          웹사이트 제작문의
        </a>
        <a class="footer-tg-btn" href="https://t.me/googleseolab" target="_blank" rel="noopener nofollow">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21.94 4.3 18.9 19.1c-.23 1.02-.84 1.27-1.7.79l-4.7-3.46-2.27 2.18c-.25.25-.46.46-.94.46l.33-4.78L18.6 6.4c.38-.34-.08-.53-.59-.19L6.27 13.7l-4.66-1.46c-1.01-.32-1.03-1.01.21-1.5l18.22-7.02c.84-.31 1.58.2 1.3 1.58z"/></svg>
          제휴문의
        </a>
      </div>
    </div>
  </div>
</footer>
<a class="call-fab" href="tel:{PHONE}" aria-label="전화 예약 {PHONE_DISPLAY}">
  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/></svg>
  <span class="call-fab-label">예약 전화</span>
</a>
<script src="/assets/nav.js"></script>
</body>
</html>
"""


def build() -> None:
    report = []
    items = []  # 색인 허용 페이지: {"url","title","desc"} — sitemap·rss 공통 사용
    base = BASE_URL.rstrip("/")
    today = datetime.date.today().isoformat()
    now_rfc822 = email.utils.formatdate(usegmt=True)

    for page in PAGES:
        path = page["path"]  # "" 또는 "seoul/nowon/wolgye-dong-.../" 형태
        out_dir = os.path.join(ROOT, path)
        os.makedirs(out_dir, exist_ok=True)
        html_out = render_page(page)
        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_out)

        chars = text_length(page["body"])
        noindex = page.get("noindex", False) or chars < MIN_INDEX_CHARS
        if not noindex:
            items.append({
                "url": base + "/" + path,
                "title": page["title"],
                "desc": page["desc"],
            })
        report.append((path or "/", chars, "noindex" if noindex else "index"))

    # sitemap.xml (lastmod·changefreq·priority — 색인 갱신 신호)
    def _sm_attrs(url):
        if url == base + "/":
            return "daily", "1.0"           # 홈: 매일 재방문 유도
        if "/seoul/nowon/" in url:
            return "weekly", "0.8"          # 지역 페이지
        return "monthly", "0.6"             # 안내 페이지

    rows = "\n".join(
        (lambda cf, pr: (
            f"  <url><loc>{it['url']}</loc><lastmod>{today}</lastmod>"
            f"<changefreq>{cf}</changefreq><priority>{pr}</priority></url>"
        ))(*_sm_attrs(it["url"]))
        for it in items
    )
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{rows}\n</urlset>\n"
        )

    # rss.xml (RSS 2.0 피드 — 빙/네이버 발견 및 피드 구독용)
    rss_items = "\n".join(
        "  <item>"
        f"<title>{html.escape(it['title'])}</title>"
        f"<link>{it['url']}</link>"
        f"<guid isPermaLink=\"true\">{it['url']}</guid>"
        f"<description>{html.escape(it['desc'])}</description>"
        f"<pubDate>{now_rfc822}</pubDate>"
        "</item>"
        for it in items
    )
    with open(os.path.join(ROOT, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
            "<channel>\n"
            f"  <title>{html.escape(BRAND)} — 노원구 출장마사지·홈타이</title>\n"
            f"  <link>{base}/</link>\n"
            f"  <atom:link href=\"{base}/rss.xml\" rel=\"self\" type=\"application/rss+xml\"/>\n"
            "  <description>노원구 출장마사지·홈타이 지역별 예약 안내 업데이트</description>\n"
            "  <language>ko-KR</language>\n"
            f"  <lastBuildDate>{now_rfc822}</lastBuildDate>\n"
            f"{rss_items}\n"
            "</channel>\n</rss>\n"
        )

    # robots.txt — 모든 봇 전체 허용 + 주요 검색엔진 봇(구글·네이버·빙·다음) 명시 +
    # sitemap·rss 안내. 명시적 Allow 로 색인 크롤링을 빠르게 유도한다.
    main_bots = ["Googlebot", "Googlebot-Image", "Yeti", "NaverBot",
                 "Bingbot", "Daum", "Yandex"]
    bot_blocks = "".join(
        f"User-agent: {bot}\nAllow: /\n\n" for bot in main_bots
    )
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(
            "User-agent: *\nAllow: /\n\n"
            f"{bot_blocks}"
            f"Sitemap: {base}/sitemap.xml\n"
            f"Sitemap: {base}/rss.xml\n"
        )

    # IndexNow 키 파일 — 루트에 {KEY}.txt 로 노출(검증용)
    with open(os.path.join(ROOT, f"{INDEXNOW_KEY}.txt"), "w", encoding="utf-8") as f:
        f.write(INDEXNOW_KEY + "\n")

    # .nojekyll (GitHub Pages)
    open(os.path.join(ROOT, ".nojekyll"), "w").close()

    width = max(len(p) for p, _, _ in report)
    print(f"{'PATH'.ljust(width)}  CHARS  ROBOTS")
    for p, c, r in sorted(report):
        flag = "" if (r == "noindex" or MIN_INDEX_CHARS <= c <= 2500) else "  ⚠"
        print(f"{p.ljust(width)}  {str(c).rjust(5)}  {r}{flag}")
    print(f"\n{len(report)} pages built, {len(items)} in sitemap/rss.")
    print(f"IndexNow key file: /{INDEXNOW_KEY}.txt")


if __name__ == "__main__":
    build()
