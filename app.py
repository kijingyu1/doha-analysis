import streamlit as st
import pandas as pd
import numpy as np
import requests
import feedparser # 뉴스 크롤링용
import random
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

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
# [기능 1] 스타일 & 한글 폰트
# -----------------------------------------------------------------------------
def set_style():
    st.markdown("""
        <style>
        .main { background-color: #f8f9fa; }
        h1, h2, h3 { color: #ff6f0f; font-weight: 800; } /* 당근색 포인트 */
        .metric-card {
            background-color: white; padding: 15px; border-radius: 10px;
            box-shadow: 1px 1px 5px rgba(0,0,0,0.1); text-align: center;
            color: black !important; margin-bottom: 10px;
        }
        .news-card {
            background-color: white; padding: 15px; border-radius: 10px;
            border-left: 5px solid #ff6f0f; margin-bottom: 10px; color: black;
        }
        .news-card a { text-decoration: none; color: #333; font-weight: bold; }
        .stButton>button { 
            background-color: #ff6f0f; color: white; border-radius: 8px; 
            font-weight: bold; width: 100%; height: 45px; border: none;
        }
        .stButton>button:hover { background-color: #e65c00; color: white; }
        </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# [기능 2] 메일 전송 (보험 DB용)
# -----------------------------------------------------------------------------
def send_email_safe(name, phone, client_email, req_text, type_tag):
    if "smtp" not in st.secrets: return False, "설정 오류"
    sender = st.secrets["smtp"].get("email", "")
    pw = st.secrets["smtp"].get("password", "")
    
    subject = f"🔥 [DOHA {type_tag}] {name}님 문의"
    body = f"이름:{name}\n연락처:{phone}\n내용:{req_text}"
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
# [기능 3] 유틸리티 엔진 (뉴스, 농산물, 운세)
# -----------------------------------------------------------------------------
def get_news():
    # 구글 뉴스(경제/사업 섹션) RSS 크롤링
    try:
        url = "https://news.google.com/rss/search?q=소상공인+자영업&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(url)
        return feed.entries[:5] # 최신 5개만
    except:
        return []

def get_agri_price():
    # 실제 API 연동 전에는 '시뮬레이션 데이터'로 작동 (변동폭 보여주기 위함)
    # 나중에 공공데이터포털 '농산물 유통 정보(KAMIS)' API 붙이면 실시간 됨
    items = ["배추(1포기)", "무(1개)", "양파(1kg)", "대파(1kg)", "청상추(100g)"]
    prices = {}
    for item in items:
        base = random.randint(1500, 5000)
        change = random.randint(-500, 500)
        prices[item] = {"price": base, "change": change}
    return prices

def get_today_fortune():
    fortunes = [
        "오늘은 귀인을 만날 운세입니다. 손님에게 친절하세요!",
        "금전운이 트이는 날입니다. 재고 관리에 신경 쓰세요.",
        "예상치 못한 지출이 생길 수 있으니 꼼꼼히 체크하세요.",
        "경쟁자보다 한 발 앞서 나가는 아이디어가 떠오를 겁니다.",
        "건강 관리가 재산입니다. 오늘은 일찍 퇴근해보세요."
    ]
    return random.choice(fortunes)

# -----------------------------------------------------------------------------
# [메인] 앱 실행
# -----------------------------------------------------------------------------
set_style()

st.title("🥕 DOHA 사장님 비서")
st.caption(f"오늘 날짜: {datetime.now().strftime('%Y년 %m월 %d일')}")

# 탭 메뉴 구성
tab1, tab2, tab3, tab4 = st.tabs(["🏠 데일리 홈", "🥕 전국 당근검색", "⏰ 직원 출퇴근", "🏥 내 가게 진단"])

# =============================================================================
# [TAB 1] 데일리 홈 (후킹 요소 모음)
# =============================================================================
with tab1:
    # 1. 오늘의 운세 & 뉴스
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.subheader("🍀 오늘의 장사 운세")
        st.info(f"daily: {get_today_fortune()}")
        
        st.subheader("🥬 오늘 농산물 시세 (도매)")
        agri_data = get_agri_price()
        for item, val in agri_data.items():
            color = "red" if val['change'] > 0 else "blue"
            sign = "▲" if val['change'] > 0 else "▼"
            st.markdown(f"**{item}**: {val['price']:,}원 <span style='color:{color}'>({sign}{abs(val['change'])})</span>", unsafe_allow_html=True)

    with col2:
        st.subheader("📰 소상공인 주요 뉴스")
        news_list = get_news()
        if news_list:
            for news in news_list:
                st.markdown(f"""
                <div class='news-card'>
                <a href='{news.link}' target='_blank'>{news.title}</a><br>
                <small>{news.published[:16]}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.write("뉴스 로딩 중...")

    # 2. 일일 목표 매출 계산기
    st.markdown("---")
    st.subheader("🧮 오늘의 목표 매출 계산기")
    c1, c2, c3 = st.columns(3)
    fixed = c1.number_input("한 달 고정지출 (월세+인건비+기타)", value=4500000, step=10000)
    margin = c2.slider("내 가게 마진율 (%)", 10, 50, 25)
    days = c3.number_input("이번 달 영업일 수", 26)
    
    if days > 0 and margin > 0:
        target = (fixed / days) / (margin / 100)
        st.success(f"사장님, 오늘은 최소 **{int(target):,}원** 팔아야 본전입니다! 화이팅하세요!")

# =============================================================================
# [TAB 2] 당근마켓 전국 검색 (킬러 기능)
# =============================================================================
with tab2:
    st.markdown("### 🥕 당근마켓 전국 매물 찾기")
    st.markdown("""
    당근마켓 앱에서는 '내 동네'만 보이죠?  
    DOHA에서는 **전국에 올라온 모든 꿀매물**을 한 번에 찾을 수 있습니다.  
    (중고 주방기기, 인테리어 소품 구할 때 최고!)
    """)
    
    keyword = st.text_input("찾으시는 물건을 입력하세요 (예: 업소용 냉장고, 포스기)", "")
    
    if st.button("🔍 전국 당근 뒤지기"):
        if keyword:
            # 구글 검색 트릭 사용 (site:daangn.com)
            search_url = f"https://www.google.com/search?q=site:daangn.com/articles+{keyword}&tbs=qdr:m" # 최근 1달 내 검색
            st.markdown(f"""
            <div style='background-color:#fff3cd; padding:20px; border-radius:10px; text-align:center;'>
            <h3>👇 아래 링크를 클릭하세요!</h3>
            <a href="{search_url}" target="_blank" style="font-size:20px; font-weight:bold; color:#ff6f0f; text-decoration:none;">
            👉 '{keyword}' 전국 매물 보러가기 (클릭)
            </a>
            <br><br>
            <small>* 구글 검색 엔진을 통해 전국 당근마켓 게시글을 모아서 보여줍니다.</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("검색어를 입력해주세요.")

# =============================================================================
# [TAB 3] 직원 출퇴근부 (간편 기능)
# =============================================================================
with tab3:
    st.subheader("⏰ 직원 출퇴근 기록기")
    st.caption("※ 데이터는 임시 저장됩니다. (화면 새로고침 시 초기화)")
    
    if 'attendance' not in st.session_state:
        st.session_state.attendance = []

    c1, c2 = st.columns(2)
    emp_name = c1.text_input("직원 이름")
    action = c2.selectbox("구분", ["출근", "퇴근", "외출", "복귀"])
    
    if st.button("기록하기"):
        if emp_name:
            now = datetime.now().strftime("%H시 %M분")
            st.session_state.attendance.append(f"[{now}] {emp_name} : {action}")
            st.success("기록되었습니다.")
        else:
            st.warning("이름을 입력하세요.")
            
    # 기록 리스트 출력
    st.markdown("---")
    st.write("📝 **오늘의 기록**")
    for log in st.session_state.attendance[::-1]: # 최신순
        st.text(log)

# =============================================================================
# [TAB 4] 내 가게 진단 (수익 모델)
# =============================================================================
with tab4:
    st.header("🏥 사장님 고정비/보험 무료 진단")
    st.info("매일 계산기 두드리시죠? 줄일 수 있는 돈은 '보험료' 뿐입니다.")
    
    c1, c2 = st.columns(2)
    curr_fee = c1.number_input("현재 월 화재보험료", value=50000)
    py = c2.number_input("매장 평수", value=20)
    
    if st.button("💰 내 보험료 거품 확인"):
        std = py * 1000 + 10000
        diff = curr_fee - std
        
        if diff > 10000:
            st.error(f"🚨 진단: 매월 약 {diff:,}원을 더 내고 계십니다! (1년 {diff*12:,}원 손해)")
        else:
            st.success("✅ 진단: 적정하게 잘 내고 계십니다.")
            
    st.markdown("---")
    st.subheader("📉 보험료 다이어트 / 무료 견적 신청")
    with st.form("ins_form"):
        n = st.text_input("성명")
        p = st.text_input("연락처")
        req = st.text_area("요청사항 (예: 보험료가 너무 비싸요)")
        if st.form_submit_button("📨 무료 상담 신청"):
            s, m = send_email_safe(n, p, "미입력", req, "보험진단")
            if s: st.balloons(); st.success("신청 완료! 곧 연락드리겠습니다.")
            else: st.error(m)
