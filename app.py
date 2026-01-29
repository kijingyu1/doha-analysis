import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import requests
from geopy.geocoders import Nominatim
import os
import time

# -----------------------------------------------------------------------------
# [0] 기본 설정
# -----------------------------------------------------------------------------
st.set_page_config(page_title="DOHA ANALYSIS", page_icon="🏙️", layout="wide")

# 한글 폰트 설정 (나눔바른고딕 다운로드 방식)
def set_korean_font():
    font_path = "NanumBarunGothic.ttf"
    # 폰트 파일이 없으면 다운로드 (스트림릿 클라우드용)
    if not os.path.exists(font_path):
        url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf" 
        # 나눔바른고딕 대신 구글 폰트의 나눔고딕을 사용 (안정성 위함)
        response = requests.get(url)
        with open("NanumGothic.ttf", "wb") as f:
            f.write(response.content)
        font_path = "NanumGothic.ttf"

    fm.fontManager.addfont(font_path)
    plt.rc('font', family='NanumGothic')
    plt.rcParams['axes.unicode_minus'] = False

# -----------------------------------------------------------------------------
# [1] 데이터 수집 (사장님 인증키 적용됨)
# -----------------------------------------------------------------------------
MY_KEY = "812fa5d3b23f43b70156810df8185abaee5960b4f233858a3ccb3eb3844c86ff"

def get_real_data(address, keyword):
    geolocator = Nominatim(user_agent="doha_app_v3")
    try:
        location = geolocator.geocode(address)
        if not location:
            return None, None, 0
        lat = location.latitude
        lng = location.longitude
    except:
        return None, None, 0

    url = "http://apis.data.go.kr/B553077/api/open/sdsc2/storeListInRadius"
    params = {
        "ServiceKey": MY_KEY, "type": "json", "radius": "300", 
        "cx": lng, "cy": lat, "numOfRows": 300, "pageNo": 1
    }
    
    competitor_count = 0
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if "body" in data and "items" in data["body"]:
            for item in data["body"]["items"]:
                cat_name = item.get('indsMclsNm', '') + item.get('indsSclsNm', '')
                store_name = item.get('bizesNm', '')
                if keyword in cat_name or keyword in store_name:
                    competitor_count += 1
    except:
        pass
    
    return lat, lng, competitor_count

# -----------------------------------------------------------------------------
# [2] 화면 구성 (UI)
# -----------------------------------------------------------------------------
set_korean_font() # 폰트 적용

st.title("🏙️ DOHA ANALYSIS")
st.markdown("### 세상에 없던 상권분석 프로그램 (Ver 3.0)")
st.markdown("---")

with st.sidebar:
    st.header("📝 정보 입력")
    input_address = st.text_input("주소 입력 (도로명)", "경기도 성남시 분당구 느티로 16")
    input_category = st.selectbox("업종 선택", ["음식/한식", "음식/카페", "소매/편의점", "서비스/미용"])
    input_rent = st.number_input("월세 (원)", value=3000000, step=100000)
    input_sales = st.number_input("목표 월매출 (원)", value=15000000, step=500000)
    input_households = st.number_input("배후 세대수", value=2500, step=100)
    run_btn = st.button("🚀 분석 시작", type="primary")

if run_btn:
    with st.spinner("🔍 정부 데이터를 분석 중입니다..."):
        keyword = input_category.split("/")[0] if "/" in input_category else input_category
        lat, lng, count = get_real_data(input_address, keyword)
    
    if lat:
        # 결과 화면
        rent_ratio = (input_rent/input_sales)*100
        risk = "위험 🚨" if rent_ratio > 15 else "적정 ✅"
        comp_stat = "과열 🔥" if count > 50 else "기회 🌊"

        col1, col2, col3 = st.columns(3)
        col1.metric("실제 경쟁점포(300m)", f"{count}개")
        col2.metric("월세 비중", f"{rent_ratio:.1f}%")
        col3.metric("종합 판정", risk)

        st.markdown("---")
        st.subheader("📊 상세 분석 리포트")
        
        # 그래프
        chart_data = pd.DataFrame({
            "내 상권": [count], "지역 평균": [30]
        }, index=["경쟁점 수"])
        st.bar_chart(chart_data)

        st.info(f"""
        **전문가 소견:**
        현재 이 상권은 경쟁강도가 **[{comp_stat}]** 상태이며, 월세 부담은 **[{risk}]** 수준입니다.
        예상치 못한 매출 하락을 대비해 고정비 관리와 리스크 헷징이 필수적입니다.
        """)

        st.error("🛡️ [DOHA SOLUTION] 사장님, 화재/배상책임 보험은 준비되셨나요?")
        st.markdown("최저가 보장, 맞춤형 화재보험 견적을 1분 만에 받아보세요.")
        st.link_button("📞 무료 상담 신청하기", "https://open.kakao.com/o/your_link")
    else:
        st.error("주소를 찾을 수 없습니다. 도로명 주소를 정확히 입력해주세요.")
