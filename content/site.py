# 사이트 공통 설정
# 배포 도메인 (Cloudflare Pages)
BASE_URL = "https://nowon-massage1.pages.dev"

BRAND = "바로GO"
PHONE = "0508-202-4719"
PHONE_DISPLAY = "0508-202-4719"

# 상단 메뉴 — 하위 메뉴에는 키워드를 반복하지 않고 지역명·역명만 표시한다.
# 구조: 노원구 → 대표 행정동 → 지하철역 → 생활권. 그룹 부모는 별도 페이지가 아니라
# 메인 페이지의 해당 섹션 앵커(/#areas, /#stations, /#living)로 묶어 얇은 페이지를 만들지 않는다.
NAV = [
    ("홈", "/", []),
    ("지역별 안내", "/#areas", [
        ("월계동", "/seoul/nowon/wolgye-dong-chuljangmassage/"),
        ("공릉동", "/seoul/nowon/gongneung-dong-chuljangmassage/"),
        ("하계동", "/seoul/nowon/hagye-dong-chuljangmassage/"),
        ("중계동", "/seoul/nowon/junggye-dong-chuljangmassage/"),
        ("상계동", "/seoul/nowon/sanggye-dong-chuljangmassage/"),
    ]),
    ("역세권 안내", "/#stations", [
        ("노원역", "/seoul/nowon/nowon-station-chuljangmassage/"),
        ("상계역", "/seoul/nowon/sanggye-station-chuljangmassage/"),
        ("중계역", "/seoul/nowon/junggye-station-chuljangmassage/"),
        ("하계역", "/seoul/nowon/hagye-station-chuljangmassage/"),
        ("공릉역", "/seoul/nowon/gongneung-station-chuljangmassage/"),
        ("태릉입구역", "/seoul/nowon/taereung-entrance-station-chuljangmassage/"),
        ("석계역", "/seoul/nowon/seokgye-station-chuljangmassage/"),
        ("광운대역", "/seoul/nowon/gwangundae-station-chuljangmassage/"),
        ("월계역", "/seoul/nowon/wolgye-station-chuljangmassage/"),
        ("마들역", "/seoul/nowon/madeul-station-chuljangmassage/"),
        ("수락산역", "/seoul/nowon/suraksan-station-chuljangmassage/"),
        ("당고개역", "/seoul/nowon/danggogae-station-chuljangmassage/"),
    ]),
    ("생활권 안내", "/#living", [
        ("노원역 상권", "/seoul/nowon/nowon-station-area-chuljangmassage/"),
        ("상계동 주거지", "/seoul/nowon/sanggye-residential-area-chuljangmassage/"),
        ("중계 은행사거리", "/seoul/nowon/junggye-bank-sageori-area-chuljangmassage/"),
        ("중계동 학원가", "/seoul/nowon/junggye-academy-area-chuljangmassage/"),
        ("공릉 경춘선숲길", "/seoul/nowon/gongneung-gyeongchun-line-forest-area-chuljangmassage/"),
        ("월계 광운대", "/seoul/nowon/wolgye-gwangundae-area-chuljangmassage/"),
        ("하계 중랑천", "/seoul/nowon/hagye-jungnangcheon-area-chuljangmassage/"),
        ("마들·수락산", "/seoul/nowon/madeul-suraksan-area-chuljangmassage/"),
        ("태릉입구·공릉", "/seoul/nowon/taereung-gongneung-area-chuljangmassage/"),
        ("석계·월계", "/seoul/nowon/seokgye-wolgye-area-chuljangmassage/"),
    ]),
    ("예약 안내", "/reservation/", []),
    ("이용 전 확인사항", "/guide/", []),
    ("홈타이 이용 가이드", "/hometai/", []),
    ("고객센터", "/support/", []),
]
