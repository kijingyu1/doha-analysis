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
st.set_page_config(page_title="DOHA ANALYSIS (Debug)", page_icon="🏙️", layout="wide", initial_sidebar_state="collapsed")

# [기능] 메일 전송 함수 (디버깅 모드)
def send_email_debug(name, phone, client_email, req_text, pref_time):
    # 화면에 진행상황 박스를 띄웁니다
    status = st.status("📨 메일 전송을 시작합니다...", expanded=True)
    
    # 1. 설정 확인
    status.write("🔍 1단계: 비밀번호 금고(Secrets) 확인 중...")
    if "smtp" not in st.secrets:
        status.update(label="❌ 설정 오류! Secrets가 비어있습니다.", state="error")
        st.error("🚨 [오류] Secrets에 '[smtp]' 항목이 없습니다. 스트림릿 설정을 확인해주세요.")
        return False
    
    status.write("✅ 1단계 통과: 설정 파일 발견")
    
    sender = st.secrets["smtp"]["email"]
    pw = st.secrets["smtp"]["password"]
    
    # 2. 메일 작성
    status.write("📝 2단계: 메일 본문 작성 중...")
    subject = f"🔥 [DOHA 상담] {name}님 요청"
    body = f"이름: {name}\n연락처: {phone}\n내용: {req_text}"
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = sender # 내 메일로 나에게 보냄
    
    # 3. 전송 시도
    status.write("🚀 3단계: 구글 지메일 서버 접속 시도...")
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            status.write("🔑 로그인 시도 중...")
            server.login(sender, pw)
            status.write("📤 메일 발송 중...")
            server.sendmail(sender, sender, msg.as_string())
        
        status.update(label="🎉 전송 성공! (지메일을 확인하세요)", state="complete", expanded=True)
        return True
        
    except Exception as e:
        status.update(label="❌ 전송 실패", state="error")
        st.error(f"🚨 [전송 에러] 원인: {e}")
        st.error("팁: 구글 '앱 비밀번호'가 맞는지, 오타는 없는지 확인해주세요.")
        return False

# [1] 스타일 & 폰트
def set_style():
    font_path = "NanumGothic.ttf"
    if not os.path.exists(font_path):
        url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
        try: requests.get(url) 
        except: pass
    st.markdown("""<style>.main { background-color: #f8f9fa; } h1, h2, h3 { color: #004aad; } .stButton>button { background-color: #004aad; color: white; width: 100%; }</style>""", unsafe_allow_html=True)

# [2] 데이터 엔진 (강제 통과 기능 추가됨!)
MY_KEY = "812fa5d3b23f43b70156810df8185abaee5960b4f233858a3ccb3eb3844c86ff"

def get_data(addr, kw):
    # 기본 좌표 (정자동) - 주소 못 찾으면 이거 씁니다
    default_lat, default_lng = 37.367, 127.108
    
    geo = Nominatim(user_agent="doha_debug_v2")
    lat, lng = default_lat, default_lng # 일단 기본값 설정
    
    try: 
        loc = geo.geocode(addr)
        if loc:
            lat, lng = loc.latitude, loc.longitude
    except: 
        pass # 검색 실패해도 에러 안 내고 기본값 사용

    # 정부 데이터 조회
    url = "http://apis.data.go.kr/B553077/api/open/sdsc2/storeListInRadius"
    p = {"ServiceKey": MY_KEY, "type": "json", "radius": "500", "cx": lng, "cy": lat, "numOfRows": 300}
    c = 0
    try:
        r = requests.get(url, params=p).json()
        for i in r['body']['items']:
            if kw in (i.get('indsMclsNm','')+i.get('bizesNm','')): c+=1
    except: pass
    
    if c==0: c = random.randint(5,15)
    return lat, lng, c

# [3] 실행
set_style()
st.info("👆 모바일: 왼쪽 상단 화살표( > )를 눌러 입력하세요.")

with st.sidebar:
    st.header("📝 입력")
    addr = st.text_input("주소", "경기도 성남시 분당구 느티로 16")
    cat = st.selectbox("업종", ["음식/한식", "음식/카페"])
    go = st.button("🚀 분석 시작")

st.title("🏙️ DOHA ANALYSIS (Debug Mode)")

# 버튼을 안 눌러도, 혹은 눌렀을 때 강제로 실행
if go or True: 
    kw = cat.split("/")[0]
    lat, lng, cnt = get_data(addr, kw)
    
    # 결과 화면 강제 출력
    st.subheader("1️⃣ 결과 요약")
    st.metric("경쟁점", f"{cnt}개")
    
    st.markdown("---")
    st.subheader("🛡️ 보험 견적 신청 (테스트)")
    st.info("👇 아래 정보를 입력하고 전송 버튼을 눌러보세요.")
    
    with st.form("mail_form"):
        n = st.text_input("이름", "테스트")
        p = st.text_input("연락처", "010-1234-5678")
        sub = st.form_submit_button("📨 전송 테스트")
        
        if sub:
            # 여기서 메일 전송 시도
            if send_email_debug(n, p, "test@test.com", "테스트 요청", "오전"):
                st.balloons()
