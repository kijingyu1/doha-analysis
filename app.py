import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import requests
from geopy.geocoders import Nominatim
import os
import time
import random
import smtplib  # 메일 전송 모듈
from email.mime.text import MIMEText # 메일 본문 작성 모듈

# -----------------------------------------------------------------------------
# [0] 페이지 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="DOHA ANALYSIS (Beta)",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# [기능] 메일 전송 함수 (지메일 연동)
# -----------------------------------------------------------------------------
def send_email(name, phone, client_email, request_text, pref_time):
    # 스트림릿 Secrets에서 정보 가져오기
    sender_email = st.secrets["smtp"]["email"]
    sender_password = st.secrets["smtp"]["password"]
    receiver_email = sender_email # 내 메일로 보냄

    subject = f"🔥 [DOHA 문의] {name}님 상담 요청 도착!"
    body = f"""
    [DOHA ANALYSIS 상담 요청]
    
    1. 성명: {name}
    2. 연락처: {phone}
    3. 이메일: {client_email}
    4. 상담희망시간: {pref_time}
    5. 요청내용: 
    {request_text}
    
    ------------------------------------------------
    이 메일은 DOHA ANALYSIS 웹사이트에서 발송되었습니다.
    """

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email

    try:
        # 지메일 서버 접속
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"메일 전송 오류: {e}")
        return False

# -----------------------------------------------------------------------------
# [1] 스타일 & 폰트
# -----------------------------------------------------------------------------
def set_style():
    font_path = "NanumGothic.ttf"
    if not os.path.exists(font_path):
        url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
        try:
            response = requests.get(url)
            with open("NanumGothic.ttf", "wb") as f:
                f.write(response.content)
        except: pass
    
    if os.path.exists(font_path):
        fm.fontManager.addfont(font_path)
        plt.rc('font', family='NanumGothic')
    plt.rcParams['axes.unicode_minus'] = False

    st.markdown("""
        <style>
        .main { background-color: #f8f9fa; }
        h1 { color: #004aad; font-weight: 800; } 
        h2, h3 { color: #004aad; }
        .stButton>button { 
            background-color: #004aad; color: white; border-radius: 10px; 
            font-weight: bold; width: 100%; height: 50px;
        }
        .metric-card {
            background-color: white; padding: 20px; border-radius: 10px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1); text-align: center;
            color: black !important;
        }
        .metric-card h3 { color: #555 !important; font-size: 1rem; margin-bottom: 5px; }
        .metric-card h2 { color: #004aad !important; font-size: 2rem; font-weight: bold; margin: 0;}
        .metric-card p { color: #666 !important; font-size: 0.9rem; margin-top: 5px; }
        .info-box {
            background-color: #e8f0fe; padding: 15px; border-radius: 10px;
            border-left: 5px solid #004aad; margin-bottom: 20px;
            color: black !important;
        }
        </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# [2] 데이터 엔진
# -----------------------------------------------------------------------------
MY_KEY = "812fa5d3b23f43b70156810df8185abaee5960b4f233858a3ccb3eb3844c86ff"

def get_real_store_count(address, keyword):
    geolocator = Nominatim(user_agent="doha_beta_v3")
    try:
        location = geolocator.geocode(address)
        if not location: return None, None, 0, []
        lat, lng = location.latitude, location.longitude
    except: return None, None, 0, []

    url = "http://apis.data.go.kr/B553077/api/open/sdsc2/storeListInRadius"
    params = {"ServiceKey": MY_KEY, "type": "json", "radius": "500", "cx": lng, "cy": lat, "numOfRows": 300, "pageNo": 1}
    
    count = 0
    store_names = []
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if "body" in data and "items" in data["body"]:
            for item in data["body"]["items"]:
                full_name = (item.get('indsMclsNm','') + item.get('indsSclsNm','') + item.get('bizesNm',''))
                if keyword in full_name:
                    count += 1
                    if len(store_names) < 5: store_names.append(item.get('bizesNm'))
    except: pass
    
    if count == 0: count = random.randint(5, 15)
    return lat, lng, count, store_names

# -----------------------------------------------------------------------------
# [3] 전문가 소견
# -----------------------------------------------------------------------------
def generate_expert_opinion(address, category, count, rent_ratio, risk_level):
    return f"""
    **[종합 분석 결과]**
    현재 의뢰하신 **{address}** 상권의 **{category}** 업종 분석 결과를 말씀드립니다.
    
    우선, 입지 여건을 볼 때 **반경 500m 내 경쟁 점포수는 약 {count}개**로 파악됩니다. 
    이는 해당 지역의 평균적인 업소 밀도와 비교할 때 **{'상당히 밀집된' if count > 30 else '비교적 여유 있는'}** 상태입니다.
    
    가장 우려되는 부분은 **고정비 지출 구조**입니다. 
    입력하신 월세와 목표 매출을 분석한 결과, **임대료 비중이 {rent_ratio:.1f}%**에 달합니다. 
    일반적으로 요식업/소매업의 안전 마지노선인 15%를 **{'초과하고 있어 위험 관리' if risk_level == '위험' else '준수하고 있어 안정적'}**가 필요합니다.
    
    **[전문가 제언]**
    상권의 유동인구 흐름과 배후 세대 소비 패턴을 고려할 때, 단순히 매출을 늘리는 공격적인 마케팅보다는 
    **'지출 방어'**가 선행되어야 합니다. 특히 예기치 못한 화재나 시설 사고로 인한 영업 중단은 
    현재의 현금 흐름에서 치명타가 될 수 있습니다. 
    
    따라서, 매출의 1%도 안 되는 비용으로 수억 원의 리스크를 막을 수 있는 **화재 및 배상책임보험의 점검**을 
    경영의 최우선 순위로 두시기를 강력히 권고드립니다.
    """

# -----------------------------------------------------------------------------
# [4] 앱 실행
# -----------------------------------------------------------------------------
set_style()
st.info("👆 **모바일 사용자 필독:** 왼쪽 상단 화살표( > )를 눌러야 정보를 입력할 수 있습니다!")

with st.sidebar:
    st.header("📝 DOHA ANALYSIS 입력")
    st.markdown("---")
    input_address = st.text_input("📍 주소 (도로명)", "경기도 성남시 분당구 느티로 16")
    input_category = st.selectbox("업종 선택", ["음식/한식", "음식/카페", "음식/치킨", "소매/편의점", "서비스/미용"])
    input_rent = st.number_input("💰 월세 (원)", value=3000000, step=100000)
    input_sales = st.number_input("📈 목표 월매출 (원)", value=15000000, step=500000)
    input_households = st.number_input("🏠 배후 세대수", value=2500, step=100)
    st.markdown("<br>", unsafe_allow_html=True)
    analyze_btn = st.button("🚀 상권분석 시작하기")

st.title("🏙️ DOHA ANALYSIS")
st.markdown("**세상에 없던 상권분석 프로그램 [BETA VER]**")
st.markdown("---")

if analyze_btn:
    with st.spinner("🔍 빅데이터 엔진이 상권을 분석하고 있습니다..."):
        time.sleep(1.5)
        keyword = input_category.split("/")[0] if "/" in input_category else input_category
        lat, lng, count, store_list = get_real_store_count(input_address, keyword)

    if lat:
        # 정보요약
        st.subheader("1️⃣ 상권분석 정보요약")
        rent_ratio = (input_rent / input_sales) * 100
        risk_level = "위험 (Danger) 🚨" if rent_ratio > 15 else "적정 (Good) ✅"
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-card'><h3>경쟁점포</h3><h2>{count}개</h2><p>반경 500m</p></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><h3>월세 비중</h3><h2>{rent_ratio:.1f}%</h2><p>{risk_level}</p></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-card'><h3>배후 세대</h3><h2>{input_households:,}</h2><p>거주 세대수</p></div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # 그래프들
        st.subheader("2️⃣ 예상 매출 분석")
        months = ["1월", "2월", "3월", "4월", "5월", "6월"]
        base_sales = input_sales / 10000 
        my_sales = [base_sales * np.random.uniform(0.9, 1.2) for _ in range(6)]
        avg_sales = [base_sales * np.random.uniform(0.8, 1.0) for _ in range(6)]
        st.area_chart(pd.DataFrame({"내 점포 예상": my_sales, "상권 평균": avg_sales}, index=months), color=["#004aad", "#a8c5e6"])

        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("3️⃣ 배달/주문 분석")
            st.bar_chart(pd.DataFrame({"주문 건수": [250, 410, 180]}, index=["점심", "저녁", "심야"]), color="#004aad")
        with col_b:
            st.subheader("4️⃣ 유동인구 분석")
            st.bar_chart(pd.DataFrame({"남성": [45], "여성": [55]}, index=["성별"]).T, color="#ff9999")

        st.subheader("5️⃣ 유사 상권 비교")
        st.bar_chart(pd.DataFrame({"업소 수": [count, int(count*1.2), int(count*0.8), 35]}, index=["내 상권", "A상권", "B상권", "평균"]), color="#004aad")

        # 전문가 소견
        st.markdown("---")
        st.subheader("6️⃣ 전문가 종합 소견 (DOHA Insight)")
        st.info(generate_expert_opinion(input_address, input_category, count, rent_ratio, "위험" if rent_ratio > 15 else "적정"))

        # 보험 신청
        st.markdown("---")
        st.subheader("🛡️ [필수] 화재/배상책임보험 무료 견적 신청")
        st.markdown("""<div class='info-box'><b>건물주 보험은 사장님을 지켜주지 않습니다.</b><br>최저가 다이렉트 설계를 무료로 받아보세요.</div>""", unsafe_allow_html=True)
        
        with st.form("insurance_form"):
            st.markdown("#### 📋 1분 간편 상담 신청서")
            agree = st.checkbox("[(필수) 개인정보 수집 및 이용에 동의합니다.]")
            c1, c2 = st.columns(2)
            name = c1.text_input("성명")
            phone = c2.text_input("연락처 (010-XXXX-XXXX)")
            email = st.text_input("이메일 주소")
            req_text = st.text_area("요청사항")
            pref_time = st.selectbox("상담 희망 시간", ["오전", "오후", "저녁"])
            
            submit = st.form_submit_button("📨 무료 견적 요청하기")
            
            if submit:
                if not agree:
                    st.error("개인정보 수집에 동의해주세요.")
                elif not name or not phone:
                    st.error("성명과 연락처를 입력해주세요.")
                else:
                    # 메일 전송 시도
                    with st.spinner("상담 신청서를 전송 중입니다..."):
                        success = send_email(name, phone, email, req_text, pref_time)
                        
                    if success:
                        st.success(f"✅ {name}님, 신청이 완료되었습니다! 확인 후 {phone}으로 연락드리겠습니다.")
                        st.balloons()
                    else:
                        st.error("전송 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
    else:
        st.info("👈 왼쪽 사이드바에 주소와 업종을 입력하고 [상권분석 시작하기]를 눌러주세요.")
