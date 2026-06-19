# 코스별 기본 요금 — 메인·지역 페이지 공통 삽입 블록.
# build.py 의 text_length() 가 <section class="pricing">…</section> 를 글자수 계산에서 제외하므로
# 이 블록은 색인 기준(2,000자) 본문 분량에 영향을 주지 않는다(공통 블록이라 중복 콘텐츠로 보지 않게).
from .site import PHONE

PRICING = f"""
<section class="pricing">
<h2>코스별 기본 요금</h2>
<p class="pricing-lead">60·90·120분 코스별 기본 요금입니다. 숨겨진 추가 비용 없이 투명하게 안내합니다.</p>
<div class="price-grid">
  <div class="price-card">
    <p class="price-name">60분 코스</p>
    <p class="price-value">90,000<span>원</span></p>
    <p class="price-time">60분</p>
    <p class="price-desc">기본 컨디션·릴랙스 케어</p>
    <a class="price-btn" href="tel:{PHONE}">예약 문의</a>
  </div>
  <div class="price-card featured">
    <p class="price-badge">추천</p>
    <p class="price-name">90분 코스</p>
    <p class="price-value">150,000<span>원</span></p>
    <p class="price-time">90분</p>
    <p class="price-desc">아로마 포함 추천 구성</p>
    <a class="price-btn primary" href="tel:{PHONE}">예약 문의</a>
  </div>
  <div class="price-card">
    <p class="price-name">120분 코스</p>
    <p class="price-value">180,000<span>원</span></p>
    <p class="price-time">120분</p>
    <p class="price-desc">전신 집중 프리미엄 케어</p>
    <a class="price-btn" href="tel:{PHONE}">예약 문의</a>
  </div>
</div>
<p class="price-note">지역·예약 시간대·이동 거리에 따라 상담 시 최종 확인됩니다. <a href="/reservation/">상세 요금 안내 보기 →</a></p>
</section>
"""
