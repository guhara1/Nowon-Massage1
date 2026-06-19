# 바로GO — 노원구 출장마사지·홈타이 안내 사이트

서울 노원구 전지역 방문 관리(출장마사지·홈타이) 안내용 지역 SEO 정적 사이트입니다.
예약전화: **0508-202-4719**

## 구조

노원구는 **노원구 → 대표동 → 지하철역 → 생활권** 순서로 구성합니다.
번호로 나뉜 행정동(상계1~10동, 중계본동·1·2·3·4동, 공릉1·2동, 하계1·2동, 월계1·2·3동)은
각각 페이지로 만들지 않고 대표동(상계·중계·공릉·하계·월계)으로 통합합니다.

- 정적 HTML 사이트 — GitHub Pages / Netlify / 일반 웹서버 어디서나 서빙 가능
- `build.py` + `content/` 패키지에서 페이지를 생성하는 빌드 방식
- 생성물(각 디렉터리의 `index.html`, `sitemap.xml`, `robots.txt`)도 저장소에 포함

```
build.py            # 빌드 스크립트 (레이아웃·목차·글자수 검사·sitemap 생성 + 페이지별 og:image 주입)
content/
  site.py           # 상호(바로GO)·전화·BASE_URL·메뉴(NAV) 구조
  main.py           # 메인 (+ WebPage/ImageObject/BreadcrumbList/Organization/FAQPage JSON-LD)
  areas.py          # 대표동 5개 (월계·공릉·하계·중계·상계)
  stations.py       # 지하철역 12개 (노원·상계·중계·하계·공릉·태릉입구·석계·광운대·월계·마들·수락산·당고개)
  living.py         # 생활권·주요 거점 10개
  info.py           # 예약 안내·이용 전 확인사항·홈타이 가이드·고객센터·개인정보 처리방침
assets/             # CSS(프리미엄 옵시디언+샴페인 골드, Pretendard), 모바일 내비 JS, 파비콘, OG 이미지
scripts/gen_thumbs.py  # 페이지별 og 썸네일 + 메인 og-image 생성기 (Pillow)
```

## 페이지 구성 (총 33개)

| 구분 | 개수 | URL 예시 |
|------|------|----------|
| 메인 | 1 | `/` |
| 대표동 | 5 | `/seoul/nowon/sanggye-dong-chuljangmassage/` |
| 역세권 | 12 | `/seoul/nowon/nowon-station-chuljangmassage/` |
| 생활권 | 10 | `/seoul/nowon/junggye-bank-sageori-area-chuljangmassage/` |
| 안내 | 4 | `/reservation/` `/guide/` `/hometai/` `/support/` |
| 정책 | 1 | `/privacy/` (noindex) |

> 메인 허브 페이지는 단독 도메인의 홈페이지이므로 루트 `/`에 둡니다.
> (지시서의 `/seoul/nowon-gu-chuljangmassage/`는 다지역 통합 사이트용 경로 규약이며,
> 단독 노원 도메인에서는 홈페이지가 가장 강한 권위를 받도록 루트에 배치하는 것이 유리합니다.)

## 빌드

```bash
python3 build.py
```

빌드 시 페이지별 본문 글자수와 색인 여부가 출력됩니다.

검색 썸네일(og:image)을 다시 만들려면:

```bash
pip install Pillow            # 최초 1회
python3 scripts/gen_thumbs.py # assets/og/*.png + assets/og-image.png 생성
```

## SEO 운영 원칙 (빌드에 강제됨)

- 본문 **2,000자 미만 페이지는 자동 `noindex`** 처리되고 sitemap에서 제외
- 모든 페이지 **메타 디스크립션 80자 이내**
- 대표동은 대표 동 단위만 — 번호 행정동(상계1동·중계1동 등) 개별 페이지 없음
- 역은 역 1개당 페이지 1개 — 환승역(노원·태릉입구·석계역)도 URL 하나, 노선별·출구별 페이지 없음
- 석계역은 성북구 경계라 월계동 인접 생활권으로, 태릉입구역은 노원·중랑 경계라 공릉동 인접 생활권으로 설명
- 실제 오프라인 매장 주소가 없으므로 **LocalBusiness 대신 Organization Schema** 사용 + 선호 썸네일 `ImageObject` 명시
- 모든 페이지 본문은 페이지별 고유 작성 (지역명만 바꾼 복붙 없음)

## 배포 전 해야 할 일

1. `content/site.py`의 `BASE_URL`을 실제 도메인으로 변경
2. `python3 build.py` 재실행 (canonical·sitemap·robots.txt에 반영됨)
3. Google Search Console / 네이버 서치어드바이저에 `sitemap.xml` 제출
