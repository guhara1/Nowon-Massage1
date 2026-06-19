# 색인(인덱싱) 자동화 도구

노원구 출장마사지·홈타이 사이트의 **빠른 색인** 도구 모음입니다.
페이지를 새로 올리거나 수정할 때 검색엔진에 즉시 통보합니다.

## 검색엔진별 전략

| 검색엔진 | 방법 | 스크립트 |
|----------|------|----------|
| **Bing** | IndexNow (즉시) | `tools/indexnow.py` |
| **Naver** | IndexNow (즉시) + 서치어드바이저 사이트맵 | `tools/indexnow.py` |
| **Google** | Indexing API (즉시) + Search Console 사이트맵 | `tools/google_indexing.py` |

> 참고: 과거의 **sitemap ping**(`google.com/ping?sitemap=`, `bing.com/ping?sitemap=`)은
> 2023년 구글·빙이 모두 **지원 종료**했습니다. 현재 즉시 통보의 표준은 **IndexNow**이며,
> 구글은 IndexNow 미참여이므로 Indexing API 또는 Search Console을 사용합니다.

## 0. 빌드 산출물 (자동 생성)

`python3 build.py` 를 실행하면 다음이 생성됩니다.

- `sitemap.xml` — `lastmod`/`changefreq`/`priority` 포함 (색인 갱신 신호)
- `rss.xml` — RSS 2.0 피드 (빙/네이버 발견·구독용, 각 페이지 head에 `<link rel="alternate">` 연결)
- `robots.txt` — `Sitemap:` 로 sitemap.xml·rss.xml 안내
- `09e51a5cb711d20c4a81684684ab09ca.txt` — IndexNow 키 검증 파일 (루트 노출)

## 1. IndexNow — Bing·Naver 즉시 통보

```bash
# 첫 일괄 통보: sitemap.xml 의 모든 URL을 빙·네이버에 즉시 통보
python3 tools/indexnow.py

# 글/페이지를 새로 올릴 때마다 해당 URL만 통보
python3 tools/indexnow.py https://nowon-massage1.pages.dev/seoul/nowon/<slug>/
```

- 키는 `content/site.py` 의 `INDEXNOW_KEY` 하나로 관리됩니다.
  키를 바꾸면 빌드 시 루트 키 파일과 통보가 함께 갱신됩니다.
- 배포 후 `https://나의도메인/<KEY>.txt` 가 열려야 통보가 검증됩니다(반드시 배포 먼저).
- 응답 200/202 = 접수 성공, 403 = 키 불일치, 422 = host/URL 불일치.

## 2. Google Indexing API — 구글 즉시 통보(선택)

```bash
pip install google-auth requests          # 최초 1회
python3 tools/google_indexing.py          # sitemap 전체
python3 tools/google_indexing.py <url>    # 지정 URL
```

사전 준비: Google Cloud에서 Indexing API 사용 설정 → 서비스 계정 JSON 키 발급 →
`GOOGLE_APPLICATION_CREDENTIALS` 또는 `tools/service_account.json` 지정 →
Search Console 속성에 서비스 계정 이메일을 **소유자**로 추가. (자세한 안내는 스크립트 상단 주석)

## 3. 수동 제출(가장 확실, 권장 병행)

- **네이버 서치어드바이저**: 사이트 등록 → 사이트맵 `https://나의도메인/sitemap.xml` 제출,
  RSS `https://나의도메인/rss.xml` 제출, 웹페이지 수집요청.
- **구글 Search Console**: 색인 → Sitemaps 에 `sitemap.xml` 제출, URL 검사로 개별 색인요청.

## 발행 워크플로 요약

```bash
python3 build.py                      # 1) 빌드(사이트맵·rss·키파일 갱신)
git add -A && git commit && git push  # 2) 배포(Cloudflare Pages 자동 반영)
python3 tools/indexnow.py             # 3) 빙·네이버 즉시 통보
python3 tools/google_indexing.py      # 4) (선택) 구글 즉시 통보
```
