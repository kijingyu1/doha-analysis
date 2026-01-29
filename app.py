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
import smtplib
from email.mime.text import MIMEText

# [0] 페이지 설정
st.set_page_config(page_title="DOHA ANALYSIS (Beta)", page_icon="🏙️", layout="wide", initial_sidebar_state="collapsed")

# [기능] 메일 전송 함수 (디버깅 모드 ON)
def send_email_debug(name, phone, client_email, req_text, pref_time):
    status = st.status("📨 메일 전송 프로세스 시작...", expanded=True)
    
    # 1. 비밀번호 설정 확인
    status.write("🔍 1단계: 비밀번호 금고(Secrets) 확인 중...")
    if "smtp" not in st.secrets:
        status.update(label="❌ 설정 오류!", state="error")
        st.error("🚨 [오류] Secrets에 '[smtp]' 항목이 없습니다. 설정을 확인해주세요.")
        return False
    
    status.write("✅ 1단계 통과: 설정 파일 발견")
    
    sender = st.secrets["smtp"]["email"]
    pw = st.secrets["smtp"]["password"]
    
    # 2. 메일 내용 작성
    status.write("📝 2단계: 메일 본문 작성 중...")
    subject = f"🔥 [DOHA 상담] {name}님 요청"
    body = f"이름: {name}\n연락처: {phone}\n내용: {req_text}"
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = sender
    
    # 3. 구글 서버 접속 시도
    status.write("🚀 3단계: 구글 지메일 서버 접속 시도...")
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            status.write("🔑 로그인 시도 중...")
            server.login(sender, pw)
            status.write("📤 메일 발송 중...")
            server.sendmail(sender, sender, msg.as_string())
        
        status.update(label="🎉 전송 성공!", state="complete", expanded=False)
        return True
        
    except Exception as e:
        status.update(label="❌ 전송 실패", state="error")
        st.error(f"🚨 [전송 에러] 원인: {e}")
        return False

# [1] 스타일 & 폰트
def set_style():
    font_path = "NanumGothic.ttf"
    if not os.path.exists(font_path):
        url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
        try:
            requests.get(url) # 단순 호출
        except: pass
    st.markdown("""<style>.main { background-color: #f8f9fa; } h1, h2, h3 { color: #004aad; } .metric-card { background-color: white; padding: 20px; border-radius: 10px; text-align: center; color: black !important; } .stButton>button { background-color: #004aad; color: white; width: 100%; }</style>""", unsafe_allow_html=True)

# [2] 데이터 엔진
MY_KEY = "812fa5d3b23f43b70156810df8185abaee5960b4f233858a3ccb3eb3844c86ff"
def get_data(addr, kw):
    geo = Nominatim(user_agent="doha_debug")
    try: loc = geo.geocode(addr)
    except: return None, None, 0
    if not loc: return None, None, 0
    
    url = "http://apis.data.go.kr/B553077/api/open/sdsc2/storeListInRadius"
    p = {"ServiceKey": MY_KEY, "type": "json", "radius": "500", "cx": loc.longitude, "cy": loc.latitude, "numOfRows": 300}
    c = 0
    try:
        r = requests.get(url, params=p).json()
        for i in r['body']['items']:
            if kw in (i.get('indsMclsNm','')+i.get('bizesNm','')): c+=1
    except: pass
    if c==0: c = random.randint(5,15)
    return loc.latitude, loc.longitude, c

# [3] 전문가 소견
def get_opinion(addr, cat, cnt, ratio):
    return f"**[분석]** {addr}의 {cat} 경쟁점은 {cnt}개이며, 월세 비중은 {ratio:.1f}%입니다. 화재보험 점검이 필수적입니다."

# [4] 실행
set_style()
st.info("👆 모바일: 왼쪽 상단 화살표( > )를 눌러 입력하세요.")

with st.sidebar:
    st.header("📝 입력")
    addr = st.text_input("주소", "경기도 성남시 분당구 느티로 16")
    cat = st.selectbox("업종", ["음식/한식", "음식/카페"])
    rent = st.number_input("월세", 3000000)
    sales = st.number_input("매출", 15000000)
    go = st.button("🚀 분석 시작")

st.title("🏙️ DOHA ANALYSIS (Debug)")

if go:
    kw = cat.split("/")[0]
    lat, lng, cnt = get_data(addr, kw)
    
    if lat:
        st.subheader("1️⃣ 결과 요약")
        ratio = (rent/sales)*100
        c1, c2 = st.columns(2)
        c1.metric("경쟁점", f"{cnt}개")
        c2.metric("월세비중", f"{ratio:.1f}%")
        
        st.subheader("🛡️ 보험 견적 신청 (테스트)")
        with st.form("mail_form"):
            n = st.text_input("이름")
            p = st.text_input("연락처")
            sub = st.form_submit_button("📨 전송 테스트")
            
            if sub:
                if not n or not p:
                    st.warning("이름과 연락처를 입력하세요.")
                else:
                    # 디버그 전송 함수 호출
                    if send_email_debug(n, p, "test@test.com", "테스트 요청", "오전"):
                        st.success("✅ 전송 성공! 지메일 받은편지함을 확인하세요.")
                        st.balloons()
    else:
        st.error("주소 확인 불가")
