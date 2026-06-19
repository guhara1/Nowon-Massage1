# 페이지별 검색 썸네일(og:image) 생성기. 프리미엄 옵시디언+샴페인골드 테마, 1200x630.
# 메인 대표 이미지(assets/og-image.png)와 페이지별 썸네일(assets/og/*.png)을 함께 생성한다.
import os
from PIL import Image, ImageDraw, ImageFont

OUT = "assets/og"
os.makedirs(OUT, exist_ok=True)
W, H = 1200, 630
NAVY=(5,8,15); GOLD=(212,175,110); GOLD_SOFT=(241,224,182); TEXT=(238,241,248); DIM=(154,165,189)
KO="/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
SE="/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
def ko(sz): return ImageFont.truetype(KO, sz)
def se(sz): return ImageFont.truetype(SE, sz)
BRAND="바로GO"
MARK="바"
PHONE="0508-202-4719"
TAG_AREA="서울 · 노원"
TAG_INFO="바로GO · 노원"

# slug -> (tag, line1, line2)
PAGES = {
 # 대표동
 "wolgye-dong-chuljangmassage":      (TAG_AREA, "월계동 출장마사지", "광운대역 · 월계역 생활권"),
 "gongneung-dong-chuljangmassage":   (TAG_AREA, "공릉동 출장마사지", "공릉역 · 경춘선숲길 생활권"),
 "hagye-dong-chuljangmassage":       (TAG_AREA, "하계동 출장마사지", "하계역 · 중랑천 생활권"),
 "junggye-dong-chuljangmassage":     (TAG_AREA, "중계동 출장마사지", "중계역 · 은행사거리 생활권"),
 "sanggye-dong-chuljangmassage":     (TAG_AREA, "상계동 출장마사지", "노원역 · 상계역 생활권"),
 # 역세권
 "nowon-station-chuljangmassage":    (TAG_AREA, "노원역 출장마사지", "상계동 중심 환승 생활권"),
 "sanggye-station-chuljangmassage":  (TAG_AREA, "상계역 출장마사지", "상계동 주거권 방문 안내"),
 "junggye-station-chuljangmassage":  (TAG_AREA, "중계역 출장마사지", "중계동 · 은행사거리 인접권"),
 "hagye-station-chuljangmassage":    (TAG_AREA, "하계역 출장마사지", "하계동 · 중랑천 생활권"),
 "gongneung-station-chuljangmassage":(TAG_AREA, "공릉역 출장마사지", "공릉동 중심 주거권"),
 "taereung-entrance-station-chuljangmassage":(TAG_AREA, "태릉입구역 출장마사지", "공릉동 · 과기대 인접권"),
 "seokgye-station-chuljangmassage":  (TAG_AREA, "석계역 출장마사지", "월계동 · 석계 인접 생활권"),
 "gwangundae-station-chuljangmassage":(TAG_AREA, "광운대역 출장마사지", "월계동 · 광운대 주변"),
 "wolgye-station-chuljangmassage":   (TAG_AREA, "월계역 출장마사지", "월계동 주거지 생활권"),
 "madeul-station-chuljangmassage":   (TAG_AREA, "마들역 출장마사지", "상계동 북부 생활권"),
 "suraksan-station-chuljangmassage": (TAG_AREA, "수락산역 출장마사지", "상계동 · 수락산 인접권"),
 "danggogae-station-chuljangmassage":(TAG_AREA, "당고개역 출장마사지", "상계동 북부 주거권"),
 # 생활권
 "nowon-station-area-chuljangmassage":(TAG_AREA, "노원역 상권 출장마사지", "노원역 중심 방문 기준"),
 "sanggye-residential-area-chuljangmassage":(TAG_AREA, "상계동 주거지 출장마사지", "상계동 대표 주거권"),
 "junggye-bank-sageori-area-chuljangmassage":(TAG_AREA, "중계 은행사거리 출장마사지", "중계동 중심 생활권"),
 "junggye-academy-area-chuljangmassage":(TAG_AREA, "중계동 학원가 출장마사지", "중계역 · 은행사거리 주변"),
 "gongneung-gyeongchun-line-forest-area-chuljangmassage":(TAG_AREA, "공릉 경춘선숲길 출장마사지", "공릉역 · 대학가 인접권"),
 "wolgye-gwangundae-area-chuljangmassage":(TAG_AREA, "월계 광운대 출장마사지", "광운대역 · 월계역 주변"),
 "hagye-jungnangcheon-area-chuljangmassage":(TAG_AREA, "하계 중랑천 출장마사지", "하계역 · 주거지 방문"),
 "madeul-suraksan-area-chuljangmassage":(TAG_AREA, "마들 · 수락산 출장마사지", "상계동 북부 이동 기준"),
 "taereung-gongneung-area-chuljangmassage":(TAG_AREA, "태릉입구 · 공릉 출장마사지", "공릉동 동쪽 생활권"),
 "seokgye-wolgye-area-chuljangmassage":(TAG_AREA, "석계 · 월계 출장마사지", "월계동 남서부 방문 기준"),
 # 안내 페이지
 "reservation": (TAG_INFO, "예약 안내", "방문 절차 · 이동비 · 결제 기준"),
 "guide":       (TAG_INFO, "이용 전 확인사항", "준비물 · 위생 · 안전 기준"),
 "hometai":     (TAG_INFO, "홈타이 이용 가이드", "진행 방식 · 추천 대상 안내"),
 "support":     (TAG_INFO, "고객센터", "공지 · 자주 묻는 질문 · 문의"),
}

def fit(draw, text, font_factory, max_w, start, min_sz=40):
    sz=start
    while sz>min_sz:
        f=font_factory(sz); bb=draw.textbbox((0,0),text,font=f)
        if bb[2]-bb[0]<=max_w: return f
        sz-=4
    return font_factory(min_sz)

def ctext(d,cx,y,text,font,fill):
    bb=d.textbbox((0,0),text,font=font); w=bb[2]-bb[0]
    d.text((cx-w/2-bb[0], y), text, font=font, fill=fill)

def base():
    """공통 배경: 옵시디언 + 상단 골드 글로우 + 이중 프레임."""
    img=Image.new("RGB",(W,H),NAVY); d=ImageDraw.Draw(img,"RGBA")
    for i,r in enumerate(range(560,0,-44)):
        a=int(12*(1-i/13))
        if a>0: d.ellipse([600-r,-300-r//3,600+r,-300+r],fill=(212,175,110,a))
    d.rectangle([24,24,W-25,H-25],outline=GOLD,width=3)
    d.rectangle([34,34,W-35,H-35],outline=(212,175,110,90),width=1)
    return img,d

def brand_row(d, cy):
    """가운데 정렬된 브랜드 마크(바) + 바로GO."""
    R=40
    bf=ko(46); tb=d.textbbox((0,0),BRAND,font=bf); btw=tb[2]-tb[0]
    gap=18; total=R*2+gap+btw; gx=600-total/2+R
    d.ellipse([gx-R,cy-R,gx+R,cy+R],fill=(10,16,30,255))
    d.ellipse([gx-R+3,cy-R+3,gx+R-3,cy+R-3],outline=GOLD,width=4)
    mf=ko(40); mbb=d.textbbox((0,0),MARK,font=mf)
    d.text((gx-(mbb[2]-mbb[0])/2-mbb[0], cy-(mbb[3]-mbb[1])/2-mbb[1]),MARK,font=mf,fill=GOLD_SOFT)
    d.text((gx+R+gap, cy-(tb[3]-tb[1])/2-tb[1]),BRAND,font=bf,fill=TEXT)

def make(slug, tag, l1, l2):
    img,d=base()
    # tag pill (outline)
    tf=ko(30); bb=d.textbbox((0,0),tag,font=tf); tw=bb[2]-bb[0]
    px0=600-tw/2-26; px1=600+tw/2+26; py0=70; py1=70+54
    d.rounded_rectangle([px0,py0,px1,py1],radius=27,outline=GOLD,width=2)
    d.text((600-tw/2-bb[0], py0+(54-(bb[3]-bb[1]))/2-bb[1]), tag, font=tf, fill=GOLD_SOFT)
    # line1 (auto-fit), line2
    f1=fit(d,l1,ko,1010,92); ctext(d,600,196,l1,f1,GOLD_SOFT)
    f2=fit(d,l2,ko,1010,50); ctext(d,600,322,l2,f2,TEXT)
    # divider
    d.line([520,406,680,406],fill=GOLD,width=3)
    brand_row(d,468)
    # phone pill
    pt=f"예약전화  {PHONE}"; pf=ko(38); pb=d.textbbox((0,0),pt,font=pf); ptw=pb[2]-pb[0]
    qx0=600-ptw/2-34; qx1=600+ptw/2+34; qy0=536; qy1=536+62
    d.rounded_rectangle([qx0,qy0,qx1,qy1],radius=31,fill=GOLD)
    d.text((600-ptw/2-pb[0], qy0+(62-(pb[3]-pb[1]))/2-pb[1]), pt, font=pf, fill=(21,16,10))
    img.save(f"{OUT}/{slug}.png")
    return f"{OUT}/{slug}.png"

def make_main():
    """메인 대표 이미지 assets/og-image.png."""
    img,d=base()
    tag="서울 노원구 전지역 방문 관리"
    tf=ko(30); bb=d.textbbox((0,0),tag,font=tf); tw=bb[2]-bb[0]
    px0=600-tw/2-26; px1=600+tw/2+26; py0=66; py1=66+54
    d.rounded_rectangle([px0,py0,px1,py1],radius=27,outline=GOLD,width=2)
    d.text((600-tw/2-bb[0], py0+(54-(bb[3]-bb[1]))/2-bb[1]), tag, font=tf, fill=GOLD_SOFT)
    f1=fit(d,"노원구 출장마사지",ko,1010,100); ctext(d,600,188,"노원구 출장마사지",f1,GOLD_SOFT)
    f2=fit(d,"노원 홈타이 지역별 예약 안내",ko,1010,52); ctext(d,600,318,"노원 홈타이 지역별 예약 안내",f2,TEXT)
    d.line([520,404,680,404],fill=GOLD,width=3)
    brand_row(d,466)
    pt=f"예약전화  {PHONE}"; pf=ko(38); pb=d.textbbox((0,0),pt,font=pf); ptw=pb[2]-pb[0]
    qx0=600-ptw/2-34; qx1=600+ptw/2+34; qy0=534; qy1=534+62
    d.rounded_rectangle([qx0,qy0,qx1,qy1],radius=31,fill=GOLD)
    d.text((600-ptw/2-pb[0], qy0+(62-(pb[3]-pb[1]))/2-pb[1]), pt, font=pf, fill=(21,16,10))
    img.save("assets/og-image.png")
    return "assets/og-image.png"

if __name__ == "__main__":
    print("wrote", make_main())
    for slug,(tag,l1,l2) in PAGES.items():
        print("wrote", make(slug,tag,l1,l2))
    print("done", len(PAGES)+1)
