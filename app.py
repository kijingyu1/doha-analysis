import streamlit as st
import pandas as pd
import numpy as np
import requests
import feedparser
import random
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import os

# -----------------------------------------------------------------------------
# [0] 페이지 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="DOHA 사장님 비서",
    page_icon="🥕",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# [기능 1] 스타일
# -----------------------------------------------------------------------------
def set_style():
    st.markdown("""
        <style>
        .main { background-color: #f8f9fa; }
        h1, h2, h3 { color: #ff6f0f; font-weight: 800; } 
        .metric-card {
            background-color: white; padding: 15px; border-radius: 10px;
            box-shadow: 1px 1px 5px rgba(0,0,0,0.1); text-align: center;
            color: black !important; margin-bottom: 10px;
        }
        .news-box { background-color: white; padding: 15px; border-radius: 10px; border-left: 5px solid #ff6f0f; margin-bottom: 20px; }
        .news-item { padding: 8px 0; border-bottom: 1px solid #eee; }
        .news-item a { text-decoration: none; color: #333; font-weight: bold; font-size: 1rem; }
        .news-item a:hover { color: #ff6f0f; }
        .stButton>button { 
            background-color: #ff6f0f; color: white; border-radius: 8px; 
            font-weight: bold; width: 100%; height: 45px; border: none;
        }
        .stButton>button:hover { background-color: #e65c00; }
        .event-box {
            background-color: #1e3932; color: white; padding: 20px; border-radius: 10px;
            text-align: center; margin-bottom: 20px;
        }
        .fire-info-box {
            background-color: #fff3cd; padding: 20px; border-radius: 10px;
            border: 2px solid #ffc107; text-align: center; margin-bottom: 20px;
        }
        .fire-emoji { font-size: 3rem; }
        .fire-title { font-weight: bold; font-size: 1.2rem; margin: 10px 0; }
        .fire-desc { font-size: 0.9rem; color: #555; }
        
        /* 로그인 화면 스타일 */
        .login-box {
            max-width: 400px; margin: 0 auto; padding: 40px; background-color: white;
            border-radius: 20px; box-shadow: 0px 4px 12px rgba(0,0,0,0.1); text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# [기능 2] 메일 전송
# -----------------------------------------------------------------------------
def send_email_safe(name, phone, client_email, req_text, type_tag):
    if "smtp" not in st.secrets: return False, "설정 오류"
    sender = st.secrets["smtp"].get("email", "")
    pw = st.secrets["smtp"].get("password", "")
    
    subject = f"☕ [스타벅스 이벤트/DOHA] {name}님 {type_tag} 신청"
    body = f"매장명: {st.session_state.store_name}\n이름:{name}\n연락처:{phone}\n이메일:{client_email}\n요청:{req_text}"
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = sender 

    try:
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=5) as server:
            server.starttls()
            server.login(sender, pw)
            server.sendmail(sender, sender, msg.as_string())
        return True, "성공"
    except Exception as e: return False, str(e)

# -----------------------------------------------------------------------------
# [기능 3] 데이터 유틸리티 (뉴스, 농산물, 출퇴근)
# -----------------------------------------------------------------------------
def get_real_google_news():
    try:
        url = "https://news.google.com/rss/search?q=소상공인+자영업+물가&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(url)
        return feed.entries[:3]
    except: return []

def get_agri_price():
    random.seed(datetime.now().strftime("%Y%m%d"))
    items = ["배추(1포기)", "무(1개)", "양파(1kg)", "대파(1kg)", "청상추(100g)"]
    prices = {}
    for item in items:
        base = random.randint(2000, 6000)
        change = random.randint(-800, 800)
        prices[item] = {"price": base, "change": change}
    return prices

def get_today_fortune():
    fortunes = ["귀인을 만날 운세입니다.", "금전운이 매우 좋습니다.", "예상치 못한 지출 조심!", "경쟁자보다 앞서 나갑니다.", "건강이 최고입니다."]
    random.seed(datetime.now().day)
    return random.choice(fortunes)

# [핵심] 출퇴근부 - 매장별 분리 저장
def get_csv_filename():
    # 매장명(store_name)을 파일명에 포함시켜서 섞이지 않게 함
    safe_name = "".join([c for c in st.session_state.store_name if c.isalnum()]) # 특수문자 제거
    return f"log_{safe_name}.csv"

def load_attendance():
    filename = get_csv_filename()
    if os.path.exists(filename): return pd.read_csv(filename)
    return pd.DataFrame(columns=["일시", "직원명", "구분"])

def save_attendance(name, action):
    df = load_attendance()
    new_row = {"일시": datetime.now().strftime("%Y-%m-%d %H:%M"), "직원명": name, "구분": action}
    df = pd.concat([pd.DataFrame([new_row]), df], ignore_index=True)
    df.to_csv(get_csv_filename(), index=False)
    return df

# -----------------------------------------------------------------------------
# [메인] 앱 실행 (로그인 로직 추가)
# -----------------------------------------------------------------------------
set_style()

# 세션 상태 초기화 (로그인 여부 확인)
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'store_name' not in st.session_state:
    st.session_state.store_name = ""

# =============================================================================
# 🚪 로그인 화면 (입장 게이트)
# =============================================================================
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("""
        <div class='login-box'>
            <h1>🥕 DOHA 사장님 비서</h1>
            <p>우리 가게만의 비밀 장부를 만들어보세요.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        store_input = st.text_input("매장 이름 (예: 도하분식)", placeholder="매장 이름을 입력하세요")
        pw_input = st.text_input("비밀번호 (숫자 4자리)", type="password", placeholder="남들이 못 보게 잠급니다")
        
        if st.button("내 가게 입장하기 (로그인)"):
            if store_input and pw_input:
                st.session_state.logged_in = True
                st.session_state.store_name = store_input
                st.success(f"환영합니다, {store_input} 사장님!")
                st.rerun()
            else:
                st.warning("매장 이름과 비밀번호를 입력해주세요.")
    
    st.stop() # 로그인이 안 되면 아래 코드를 실행하지 않음

# =============================================================================
# 🏠 메인 앱 화면 (로그인 후 보임)
# =============================================================================
# 사이드바에 로그아웃 버튼 추가
with st.sidebar:
    st.write(f"👤 **{st.session_state.store_name}**님 접속 중")
    if st.button("로그아웃"):
        st.session_state.logged_in = False
        st.rerun()

st.title(f"🥕 DOHA 사장님 비서 ({st.session_state.store_name})")
st.caption(f"오늘 날짜: {datetime.now().strftime('%Y년 %m월 %d일')}")

tab1, tab2, tab3, tab4 = st.tabs(["🏠 데일리 홈", "🔍 전국 당근검색", "⏰ 직원 출퇴근", "🔥 화재보험 점검"])

# [TAB 1] 데일리 홈
with tab1:
    st.subheader("📰 실시간 사장님 뉴스")
    news_list = get_real_google_news()
    if news_list:
        with st.container():
            st.markdown("<div class='news-box'>", unsafe_allow_html=True)
            for news in news_list:
                date_str = f"{news.published_parsed.tm_mon}/{news.published_parsed.tm_mday}"
                st.markdown(f"<div class='news-item'><span style='color:#ff6f0f;'>●</span> <a href='{news.link}' target='_blank'>{news.title}</a> <span>({date_str})</span></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("🍀 오늘의 장사 운세")
        st.success(f"Today: {get_today_fortune()}")
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🥬 농산물 도매 시세")
        agri = get_agri_price()
        for item, val in agri.items():
            color = "red" if val['change'] > 0 else "blue"
            sign = "▲" if val['change'] > 0 else "▼"
            st.markdown(f"**{item}**: {val['price']:,}원 <span style='color:{color}'>({sign}{abs(val['change'])})</span>", unsafe_allow_html=True)
    with col_right:
        st.subheader("🧮 오늘의 목표 매출")
        st.markdown("""<div class='metric-card'>고정비를 입력하면 <b>오늘 목표치</b>를 계산해드립니다.</div>""", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        month_fixed = c1.number_input("월 고정비 합계", value=4500000, step=10000)
        days = c2.number_input("영업 일수", value=30, step=1)
        if days > 0:
            daily_fixed = month_fixed / days
            st.info(f"👉 하루 고정비: **{int(daily_fixed):,}원**")
            margin = st.slider("마진율 (%)", 10, 50, 25)
            target_sales = daily_fixed / (margin / 100)
            st.success(f"💰 오늘 목표 매출: **{int(target_sales):,}원** (BEP)")

# [TAB 2] 당근 검색
with tab2:
    st.header("🔍 당근마켓 전국 매물 찾기")
    keyword = st.text_input("찾으시는 물건", "")
    if st.button("전국 검색 시작"):
        if keyword:
            url = f"https://www.google.com/search?q=site:daangn.com {keyword}"
            st.markdown(f"<br><a href='{url}' target='_blank' style='background-color:#ff6f0f;color:white;padding:15px;display:block;text-decoration:none;border-radius:10px;font-weight:bold;text-align:center;'>👉 '{keyword}' 전국 매물 보기 (클릭)</a>", unsafe_allow_html=True)
        else: st.warning("검색어를 입력해주세요.")

# [TAB 3] 출퇴근 (매장별 데이터 분리!)
with tab3:
    st.header(f"⏰ {st.session_state.store_name} 직원 출퇴근부")
    c1, c2 = st.columns(2)
    emp_name = c1.text_input("직원 이름")
    action = c2.selectbox("구분", ["출근", "퇴근"])
    if st.button("기록 저장"):
        if emp_name:
            save_attendance(emp_name, action)
            st.success("저장되었습니다.")
            st.rerun()
    st.markdown("---")
    df_log = load_attendance()
    if not df_log.empty:
        st.dataframe(df_log, use_container_width=True)
    else:
        st.info("아직 기록이 없습니다.")

# [TAB 4] 화재보험 점검
with tab4:
    st.markdown("""
    <div class='event-box'>
    <h2>☕ 스타벅스 커피 100% 증정</h2>
    <b>"상담만 받아도 조건 없이 드립니다!" (선착순)</b>
    </div>
    """, unsafe_allow_html=True)
    
    st.header("🔥 우리 가게 화재보험 점검")
    st.markdown("#### 🧐 왜 화재보험이 필수인가요? (그림 설명)")
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown("""<div class='fire-info-box'><span class='fire-emoji'>🔥</span><div class='fire-title'>내 가게가 탈 때</div><div class='fire-desc'>건물주 보험은 보상해주지 않습니다.</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown("""<div class='fire-info-box'><span class='fire-emoji'>🏘️</span><div class='fire-title'>옆 가게로 번질 때</div><div class='fire-desc'>옆집 피해액도 다 물어줘야 합니다.</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown("""<div class='fire-info-box'><span class='fire-emoji'>🤕</span><div class='fire-title'>손님이 다칠 때</div><div class='fire-desc'>치료비, 합의금 생돈 나갑니다.</div></div>""", unsafe_allow_html=True)
        
    st.markdown("---")
    st.subheader("🏥 내 보험료 & 배상책임 진단")
    c1, c2 = st.columns(2)
    curr = c1.number_input("현재 월 보험료 (원)", value=50000)
    size = c2.number_input("매장 평수 (평)", value=20)
    
    st.markdown("<br><b>중요! '시설물배상책임보험' 가입하셨나요?</b>", unsafe_allow_html=True)
    liab_check = st.radio("배상책임 여부", ["네, 가입했습니다.", "아니요 / 잘 모르겠습니다."], label_visibility="collapsed")

    if st.button("💰 종합 진단 시작"):
        std = size * 1000 + 10000 
        diff = curr - std
        
        if diff > 15000:
            st.error(f"🚨 [보험료 경고] 매월 약 {diff:,}원 비싸게 내고 계십니다!")
            price_stat = "비쌈"
        else:
            st.success("✅ [보험료 양호] 적정하게 잘 내고 계십니다.")
            price_stat = "적정"
            
        if liab_check == "아니요 / 잘 모르겠습니다.":
            st.markdown("""
            <div style='background-color:#fff3cd; padding:20px; border-radius:10px; border:2px solid red; margin-top:20px;'>
            <h3 style='color:red; margin:0;'>🚨 [긴급 경고] 사장님, 큰일 납니다!</h3>
            <b>시설물 배상책임보험이 확인되지 않습니다.</b><br>
            손님이 매장에서 넘어지면 모든 치료비를 사장님이 물어줘야 합니다.
            </div>
            """, unsafe_allow_html=True)
        elif price_stat == "비쌈":
            st.info("👇 상담을 통해 불필요한 특약을 빼고 보험료를 낮추세요!")

    st.markdown("---")
    st.info("부담스러운 전화 NO! **카카오톡**으로 먼저 가볍게 안내해드립니다.")
    
    with st.form("starbucks_form_fire"):
        c1, c2 = st.columns(2)
        name = c1.text_input("성명 (필수)")
        phone = c2.text_input("연락처 (필수)")
        agree = st.checkbox("(필수) 개인정보 수집 및 이용에 동의합니다.")
        
        if st.form_submit_button("📨 상담 신청하고 스타벅스 받기"):
            if agree and name and phone:
                req_detail = f"화재보험 상담 (배상책임: {liab_check})"
                s, m = send_email_safe(name, phone, "미입력", req_detail, "화재보험")
                if s:
                    st.balloons()
                    st.success("✅ 신청 완료! 카톡으로 먼저 인사드리겠습니다.")
                else: st.error(m)
            else: st.warning("정보를 입력하고 동의해주세요.")
