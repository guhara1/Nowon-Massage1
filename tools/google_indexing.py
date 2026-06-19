#!/usr/bin/env python3
"""Google Indexing API 즉시 색인 요청 (URL_UPDATED / URL_DELETED).

구글은 IndexNow에 참여하지 않으므로, 구글 측 즉시 통보는 이 스크립트를 사용한다.
(공식 지원 콘텐츠는 채용·라이브스트림이지만 일반 URL에도 동작하는 경우가 많다.
 가장 확실한 방법은 Search Console 사이트맵 제출 + URL 검사 도구다.)

사전 준비(1회):
  1) Google Cloud 콘솔에서 'Indexing API' 사용 설정
  2) 서비스 계정 생성 → JSON 키 발급 → 아래 둘 중 하나로 지정
       - 환경변수 GOOGLE_APPLICATION_CREDENTIALS=/경로/key.json
       - 또는 tools/service_account.json 에 저장 (이 파일은 .gitignore 처리됨)
  3) Search Console 속성(도메인)에 서비스 계정 이메일을 '소유자'로 추가
  4) pip install google-auth requests

사용법:
  python3 tools/google_indexing.py                 # sitemap.xml 의 모든 URL
  python3 tools/google_indexing.py <url> [<url> …] # 지정 URL
  python3 tools/google_indexing.py --delete <url>  # 삭제 통보(URL_DELETED)

참고: 기본 일일 쿼터 200건.
"""
import os
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRED = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or os.path.join(ROOT, "tools", "service_account.json")
ENDPOINT = "https://indexing.googleapis.com/v3/urlNotifications:publish"
SCOPES = ["https://www.googleapis.com/auth/indexing"]


def read_sitemap_urls():
    tree = ET.parse(os.path.join(ROOT, "sitemap.xml"))
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    return [loc.text.strip() for loc in tree.iter(f"{ns}loc")]


def main():
    args = sys.argv[1:]
    notify_type = "URL_UPDATED"
    if args and args[0] == "--delete":
        notify_type = "URL_DELETED"
        args = args[1:]

    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import AuthorizedSession
    except ImportError:
        print("필요 패키지가 없습니다:  pip install google-auth requests")
        sys.exit(1)

    if not os.path.exists(CRED):
        print(f"서비스 계정 키 파일이 없습니다: {CRED}")
        print("GOOGLE_APPLICATION_CREDENTIALS 환경변수 또는 tools/service_account.json 을 설정하세요.")
        sys.exit(1)

    creds = service_account.Credentials.from_service_account_file(CRED, scopes=SCOPES)
    session = AuthorizedSession(creds)

    urls = args or read_sitemap_urls()
    print(f"{notify_type}  {len(urls)}개 URL:")
    ok = 0
    for u in urls:
        r = session.post(ENDPOINT, json={"url": u, "type": notify_type}, timeout=30)
        print(f"  [{r.status_code}] {u}")
        if r.status_code == 200:
            ok += 1
        else:
            print("     ", r.text[:200])
    print(f"완료: {ok}/{len(urls)} 성공.")


if __name__ == "__main__":
    main()
