#!/usr/bin/env python3
"""IndexNow 즉시 색인 통보 — Bing·Naver 등 IndexNow 참여 검색엔진에 URL 변경을 알린다.

구글은 IndexNow에 참여하지 않으므로, 구글은 tools/google_indexing.py 또는
Search Console 사이트맵 제출을 사용한다.

사전 준비(1회):
  - content/site.py 의 INDEXNOW_KEY 가 설정되어 있어야 한다.
  - 빌드(python3 build.py) 시 루트에 {INDEXNOW_KEY}.txt 가 생성되며, 배포 후
    https://<도메인>/{INDEXNOW_KEY}.txt 로 접근 가능해야 한다(키 검증용).

사용법:
  python3 tools/indexnow.py                  # sitemap.xml 의 모든 URL을 일괄 통보(첫 통보)
  python3 tools/indexnow.py <url> [<url> …]  # 지정한 URL만 통보(글/페이지 올릴 때마다)
"""
import json
import os
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from content.site import BASE_URL, INDEXNOW_KEY  # noqa: E402

HOST = BASE_URL.split("://", 1)[-1].strip("/")
KEY_LOCATION = f"{BASE_URL.rstrip('/')}/{INDEXNOW_KEY}.txt"

# api.indexnow.org 는 모든 참여 엔진(Bing·Naver·Yandex·Seznam…)으로 전파한다.
# Bing·Naver 전용 엔드포인트도 함께 호출해 둔다(중복 통보는 무해).
ENDPOINTS = [
    "https://api.indexnow.org/indexnow",
    "https://www.bing.com/indexnow",
    "https://searchadvisor.naver.com/indexnow",
]


def read_sitemap_urls():
    tree = ET.parse(os.path.join(ROOT, "sitemap.xml"))
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    return [loc.text.strip() for loc in tree.iter(f"{ns}loc")]


def submit(urls):
    payload = json.dumps({
        "host": HOST,
        "key": INDEXNOW_KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls,
    }).encode("utf-8")
    for ep in ENDPOINTS:
        req = urllib.request.Request(
            ep, data=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                print(f"  [{r.status}] {ep}  ({len(urls)} urls)")
        except urllib.error.HTTPError as e:
            # 200/202=성공, 403=키 불일치, 422=host/url 불일치, 429=과다요청
            print(f"  [{e.code}] {ep}  {e.reason}")
        except Exception as e:  # noqa: BLE001
            print(f"  [ERR] {ep}  {e}")


def main():
    urls = sys.argv[1:] or read_sitemap_urls()
    if not urls:
        print("통보할 URL이 없습니다. 먼저 python3 build.py 로 sitemap.xml 을 생성하세요.")
        sys.exit(1)
    print(f"host={HOST}  keyLocation={KEY_LOCATION}")
    print(f"총 {len(urls)}개 URL 통보:")
    # IndexNow는 1회 요청 최대 10,000 URL
    for i in range(0, len(urls), 10000):
        submit(urls[i:i + 10000])
    print("완료.")


if __name__ == "__main__":
    main()
