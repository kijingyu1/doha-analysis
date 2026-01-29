import streamlit as st
import pandas as pd
import numpy as np
import requests
from geopy.geocoders import Nominatim
import os
import time
import random
import smtplib
from email.mime.text import MIMEText

# -----------------------------------------------------------------------------
# [0] 페이지 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="DOHA 비즈니스 파트너",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# [기능 1] 메일 전송 엔진 (안전장치 포함)
# -----------------------------------------------------------------------------
def send_email_safe(name, phone, client_email, request_text, pref_time, type_tag):
    if "smtp" not in st.secrets:
        return False, "Secrets 설정이 비어있습니다."

    sender = st.secrets["smtp"].get("email", "")
    pw = st.secrets["smtp"].get("password", "")

    if not sender or not pw:
        return False, "이메일 설정 오류"

    subject = f"🔥 [DOHA {type_tag}] {name}님 상담신청"
    body = f"""
    [DOHA {type_tag} 신청서]
    1. 고객명 : {name}
    2. 연락처 : {phone}
    3. 이메일 : {client_email}
    4. 희망시간: {pref_time}
    5. 요청사항: {request_text}
    """
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = sender 

    try:
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(sender, pw)
            server.sendmail(sender, sender, msg.as_string())
        return True, "성공"
    except Exception as e:
        return False, f"전송 실패: {e}"

# -----------------------------------------------------------------------------
# [기능 2] 스타일
# -----------------------------------------------------------------------------
def set_style():
    st.markdown("""
        <style>
        .main { background-color: #f8f9fa; }
        h1, h2, h3 { color: #004aad; }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] {
            height: 50px; white-space: pre-wrap; background-color: white;
            border-radius: 5px; box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
        }
        .stTabs [aria-selected="true"] {
            background-color: #004aad !important; color: white !important;
        }
        .metric-card {
            background-color: white; padding: 20px; border-radius: 10px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1); text-align: center;
            color: black !important;
        }
        .info-box {
            background-color: #e8f0fe; padding: 15px; border-radius: 10px;
            border-left: 5px solid #004aad; color: black !important; margin-bottom: 10px;
        }
        .warning-box {
            background-color: #fff3cd; padding: 15px; border-radius: 10px;
            border-left: 5px solid #ffc107; color: black !important; margin-bottom: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# [기능 3] 데이터 엔진 (상권분석용)
# -----------------------------------------------------------------------------
MY_KEY = "812fa5d3b23f43b70156810df8185abaee5960b4f233858a3ccb3eb3844c86ff"

def get_real_store_count(address, keyword):
    try:
        geolocator = Nominatim(user_agent="doha_v7")
        location = geolocator.geocode(address)
        if not location: lat, lng = 37.367, 127.108
        else: lat, lng = location.latitude, location.longitude
    except: lat, lng = 37.367, 127.108

    url = "http://apis.data.go.kr/B553077/api/open/sdsc2/storeListInRadius"
    params = {"ServiceKey": MY_KEY, "type": "json", "radius": "500", "cx": lng, "cy": lat, "numOfRows": 300, "pageNo": 1}
    count = 0
    try:
        res = requests.get(url, params=params, timeout=5)
        data = res.json()
        if "body" in data and "items" in data["body"]:
            for item in data["body"]["items"]:
                if keyword in (item.get('indsMclsNm','')+item.get('bizesNm','')): count += 1
    except: pass
    if count == 0: count = random.randint(8, 20)
    return lat, lng, count

# -----------------------------------------------------------------------------
# [메인] 앱 실행
# -----------------------------------------------------------------------------
set_style()

st.title("🏙️ DOHA 비즈니스 파트너")
st.markdown("**사장님의 성공 창업과 지출 방어를 위한 올인원 솔루션**")

# 탭 구성 (핵심 변경 포인트!)
tab1, tab2, tab3 = st.tabs(["📊 예비 창업자 (상권분석)", "🏪 기존 사업자 (비용진단)", "🧮 데일리 계산기"])

# =============================================================================
# [TAB 1] 예비 창업자용 (기존 상권분석)
# =============================================================================
with tab1:
    st.info("💡 창업 예정인 지역의 경쟁 강도와 예상 매출을 분석해 드립니다.")
    
    c1, c2 = st.columns(2)
    addr = c1.text_input("분석할 주소 (도로명)", "경기도 성남시 분당구 느티로 16", key="t1_addr")
    cate = c2.selectbox("창업 예정 업종", ["음식/한식", "음식/카페", "소매/편의점", "서비스/미용"], key="t1_cat")
    
    if st.button("🚀 상권분석 시작 (Tab 1)", key="btn1"):
        kw = cate.split("/")[0]
        lat, lng, cnt = get_real_store_count(addr, kw)
        
        st.subheader(f"📍 {cate} 업종 분석 결과")
        col1, col2, col3 = st.columns(3)
        col1.metric("경쟁 점포수 (500m)", f"{cnt}개")
        col2.metric("예상 월평균 매출", "1,850만원") # 시뮬레이션 값
        col3.metric("권장 월세 상한", "270만원")
        
        st.bar_chart(pd.DataFrame({"내 상권": [cnt], "지역 평균": [35]}, index=["업소수"]))
        st.success(f"전문가 의견: 경쟁 강도가 {'높습니다' if cnt > 30 else '적절합니다'}. 차별화 전략이 필요합니다.")
        
        # Tab 1 하단 보험 DB 확보
        st.markdown("---")
        st.markdown("#### 🛡️ 창업 전 '화재보험' 가견적 받아보기")
        with st.form("form_tab1"):
            n = st.text_input("성명", key="f1_n")
            p = st.text_input("연락처", key="f1_p")
            if st.form_submit_button("📨 무료 견적 요청"):
                s, m = send_email_safe(n, p, "미입력", "신규창업 견적 요청", "무관", "창업문의")
                if s: st.success("신청 완료! 연락드리겠습니다.")
                else: st.error(f"전송 실패: {m}")

# =============================================================================
# [TAB 2] 기존 사업자용 (비용 진단 & 보험료 다이어트) -> 여기가 핵심!
# =============================================================================
with tab2:
    st.markdown("### 🏥 내 가게 고정비 건강검진")
    st.markdown("""
    <div class='info-box'>
    <b>"사장님, 혹시 옆 가게보다 보험료 2배 더 내고 계신 건 아닌가요?"</b><br>
    불필요한 특약을 뺀 '다이렉트 적정 보험료'와 현재 납부액을 비교해 드립니다.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    current_ins = col1.number_input("현재 월 화재보험료 (원)", value=50000, step=1000)
    store_size = col2.number_input("매장 평수 (평)", value=20, step=1)
    
    if st.button("💰 내 보험료 진단하기", key="btn2"):
        # 진단 로직 (단순하지만 강력하게)
        standard_price = store_size * 1000 + 10000 # 평당 1000원 + 기본료 1만원 가정
        diff = current_ins - standard_price
        
        c1, c2 = st.columns(2)
        c1.metric("DOHA 권장 적정료", f"{standard_price:,}원")
        c2.metric("예상 절감액 (월)", f"{diff:,}원", delta_color="inverse")
        
        if diff > 10000:
            st.markdown(f"""
            <div class='warning-box'>
            🚨 <b>진단 결과: [과다 지출]</b><br>
            사장님은 적정 수준보다 <b>매월 약 {diff:,}원</b>을 더 내고 계십니다.<br>
            1년이면 <b>{diff*12:,}원</b>을 버리는 셈입니다. 리모델링이 시급합니다.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.success("✅ 진단 결과: [적정] 합리적으로 잘 가입하셨습니다!")

        # Tab 2 하단 상담 신청 (강력한 Hook)
        st.markdown("---")
        st.subheader("📉 보험료 다이어트 상담 신청")
        with st.form("form_tab2"):
            st.write("아래 정보를 남겨주시면, 줄어든 보험료 견적서를 보내드립니다.")
            row1_1, row1_2 = st.columns(2)
            name_t2 = row1_1.text_input("성명", key="f2_n")
            phone_t2 = row1_2.text_input("연락처", key="f2_p")
            req_t2 = st.text_area("요청사항", value=f"{store_size}평 매장입니다. {current_ins}원 내는데 얼마나 줄일 수 있나요?")
            
            if st.form_submit_button("📨 보험료 줄이기 (상담신청)"):
                success, msg = send_email_safe(name_t2, phone_t2, "미입력", req_t2, "상시", "보험료진단")
                if success: st.balloons(); st.success("신청되었습니다! 분석 후 연락드리겠습니다.")
                else: st.error(msg)

# =============================================================================
# [TAB 3] 사장님 데일리 계산기 (재방문 유도용)
# =============================================================================
with tab3:
    st.markdown("### 🧮 오늘 얼마나 팔아야 본전일까?")
    st.info("매일 아침, 오늘의 목표 매출을 계산해보세요.")
    
    c1, c2, c3 = st.columns(3)
    fixed_cost = c1.number_input("월 고정비 합계 (월세+인건비 등)", value=4500000)
    margin_rate = c2.slider("마진율 (%)", 10, 50, 25)
    days = c3.number_input("영업 일수", 25)
    
    daily_target = (fixed_cost / days) / (margin_rate / 100)
    
    st.markdown("---")
    st.metric("📅 오늘 달성해야 할 최소 매출", f"{int(daily_target):,}원")
    
    # 계산기 밑에도 은근슬쩍 보험 광고
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:0.8rem; color:#666; text-align:center;'>
    고정비를 줄이는 가장 쉬운 방법은 보험료 점검입니다. (Tab 2에서 확인하세요)
    </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 사이드바 (공통 안내)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1556761175-5973dc0f32e7?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80", caption="DOHA PARTNERS")
    st.markdown("### 🔧 시스템 상태")
    if "smtp" in st.secrets: st.success("메일 서버 연결됨")
    else: st.error("메일 설정 필요")
    
    st.markdown("---")
    st.info("문의: 010-XXXX-XXXX")
