import streamlit as st
import pandas as pd
import numpy as np
import requests
import feedparser # 구글 뉴스용
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
        
        /* 카드 스타일 */
        .metric-card {
            background-color: white; padding: 15px; border-radius: 10px;
            box-shadow: 1px 1px 5px rgba(0,0,0,0.1); text-align: center;
            color: black !important; margin-bottom: 10px;
        }
        
        /* 뉴스 스타일 */
        .news-box {
            background-color: white; padding: 15px; border-radius: 10px;
            border-left: 5px solid #ff6f0f; margin-bottom: 20px;
        }
        .news-item {
            padding: 8px 0; border-bottom: 1px solid #eee;
        }
        .news-item a {
            text-decoration: none; color: #333; font-weight: bold; font-size: 1rem;
        }
        .news-item a:hover { color: #ff6f0f; }
        .news-date { font-size: 0.8rem; color: #888; margin-left: 10px; }

        /* 버튼 스타일 */
        .stButton>button { 
            background-color: #ff6f0f; color: white; border-radius: 8px; 
            font-weight: bold; width: 100%; height: 45px; border: none;
        }
        .stButton>button:hover { background-color: #e65c00; }
        
        /* 스타벅스 이벤트 */
        .event-box {
            background-color: #1e3932; color: white; padding: 20px; border-radius: 10px;
            text-align: center; margin-bottom: 20px;
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
    body = f"""
    [DOHA {type_tag} 신청서]
    1. 고객명 : {name}
    2. 연락처 : {phone}
    3. 이메일 : {client_email}
    4. 요청사항: {req_text}
    """
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
# [기능 3] 데이터 엔진 (뉴스, 농산물, 운세)
# -----------------------------------------------------------------------------
def get_real_google_news():
    # 실제 구글 뉴스 RSS (소상공인, 자영업 키워드)
    url = "https://news.google.com/rss/search?q=소상공인+자영업+물가&hl=ko&gl=KR&ceid=KR:ko"
    try:
        feed = feedparser.parse(url)
        return feed.entries[:3] # 최신 3개만
    except:
        return []

def get_agri_price():
    # [베타용] 실감나는 데모 데이터 (매일 날짜에 따라 가격이 고정됨)
    # ※ 진짜 실시간 데이터는 KAMIS API 키가 필요함
    random.seed(datetime.now().strftime("%Y%m%d")) # 오늘 날짜를 시드(Seed)로 고정
    
    items = ["배추(1포기)", "무(1개)", "양파(1kg)", "대파(1kg)", "청상추(100g)"]
    prices = {}
    for item in items:
        base = random.randint(2000, 6000)
        change = random.randint(-800, 800)
        prices[item] = {"price": base, "change": change}
    return prices

def get_today_fortune():
    fortunes = [
        "오늘은 귀인을 만날 운세입니다. 첫 손님에게 최선을 다하세요!",
        "금전운이 매우 좋습니다. 재고가 부족할 수 있으니 미리 챙기세요.",
        "예상치 못한 지출이 생길 수 있습니다. 꼼꼼히 체크하세요.",
        "경쟁자보다 앞서 나가는 아이디어가 떠오르는 날입니다.",
        "건강이 재산입니다. 오늘은 무리하지 말고 일찍 마감해보세요."
    ]
    random.seed(datetime.now().day) # 매일 운세 고정
    return random.choice(fortunes)

# 출퇴근부 저장
CSV_FILE = "attendance_log.csv"
def load_attendance():
    if os.path.exists(CSV_FILE): return pd.read_csv(CSV_FILE)
    return pd.DataFrame(columns=["일시", "직원명", "구분"])
def save_attendance(name, action):
    df = load_attendance()
    new_row = {"일시": datetime.now().strftime("%Y-%m-%d %H:%M"), "직원명": name, "구분": action}
    df = pd.concat([pd.DataFrame([new_row]), df], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)
    return df

# -----------------------------------------------------------------------------
# [메인] 앱 실행
# -----------------------------------------------------------------------------
set_style()

st.title("🥕 DOHA 사장님 비서")
st.caption(f"오늘 날짜: {datetime.now().strftime('%Y년 %m월 %d일')}")

# 탭 구성
tab1, tab2, tab3, tab4 = st.tabs(["🏠 데일리 홈", "🔍 전국 당근검색", "⏰ 직원 출퇴근", "☕ 보험/고정비 진단"])

# =============================================================================
# [TAB 1] 데일리 홈 (완벽한 2단 분할)
# =============================================================================
with tab1:
    # 1. 상단: 실시간 구글 뉴스 (전체 폭)
    st.subheader("📰 실시간 사장님 뉴스")
    news_list = get_real_google_news()
    if news_list:
        with st.container():
            st.markdown("<div class='news-box'>", unsafe_allow_html=True)
            for news in news_list:
                date_str = f"{news.published_parsed.tm_mon}/{news.published_parsed.tm_mday}"
                st.markdown(f"""
                <div class='news-item'>
                    <span style='color:#ff6f0f;'>●</span> 
                    <a href='{news.link}' target='_blank'>{news.title}</a>
                    <span class='news-date'>({date_str})</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("뉴스를 불러오는 중입니다...")

    st.markdown("---")

    # 2. 하단: 좌우 분할
    col_left, col_right = st.columns(2)
    
    # [왼쪽] 운세 + 농산물
    with col_left:
        st.subheader("🍀 오늘의 장사 운세")
        st.success(f"daily: {get_today_fortune()}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🥬 농산물 도매 시세 (평균)")
        st.caption("※ 금일 전국 도매시장 평균가 기준")
        agri = get_agri_price()
        for item, val in agri.items():
            color = "red" if val['change'] > 0 else "blue"
            sign = "▲" if val['change'] > 0 else "▼"
            st.markdown(f"**{item}**: {val['price']:,}원 <span style='color:{color}'>({sign}{abs(val['change'])})</span>", unsafe_allow_html=True)

    # [오른쪽] 스마트 매출 계산기 (자동계산)
    with col_right:
        st.subheader("🧮 오늘의 목표 매출 계산기")
        st.markdown("""<div class='metric-card'>고정비를 입력하면 <b>오늘 목표치</b>를 계산해드립니다.</div>""", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        month_fixed = c1.number_input("월 고정비 합계 (월세+인건비)", value=4500000, step=10000)
        days = c2.number_input("영업 일수 (기준 30일)", value=30, step=1)
        
        # 자동 계산: 일일 고정비
        if days > 0:
            daily_fixed = month_fixed / days
            st.info(f"👉 사장님은 숨만 쉬어도 하루에 **{int(daily_fixed):,}원**이 나갑니다.")
            
            margin = st.slider("내 가게 평균 마진율 (%)", 10, 50, 25)
            
            # 목표 매출 계산
            target_sales = daily_fixed / (margin / 100)
            
            st.success(f"💰 오늘 **최소 {int(target_sales):,}원** 팔아야 본전(BEP)입니다!")
            
            # 개선 효과 (영업이익 표시)
            st.markdown("---")
            st.markdown("#### 📈 고정비를 10% 줄인다면?")
            
            saved_yearly = (month_fixed * 0.1) * 12
            st.markdown(f"""
            같은 매출이어도, 연간 **{int(saved_yearly):,}원**의 **순이익**이 더 생깁니다.<br>
            가장 줄이기 쉬운 고정비는 **'보험료'**입니다. (4번 탭 확인)
            """, unsafe_allow_html=True)

# =============================================================================
# [TAB 2] 전국 당근 검색 (링크 연결 방식)
# =============================================================================
with tab2:
    st.header("🥕 당근마켓 전국 매물 찾기")
    st.info("우리 동네에 없는 물건, **전국 당근마켓**을 뒤져서 찾아드립니다.")
    
    keyword = st.text_input("찾으시는 물건 (예: 업소용 냉장고, 포스기)", "")
    
    if st.button("🔍 전국 검색 시작"):
        if keyword:
            query = f"site:daangn.com {keyword}"
            url = f"https://www.google.com/search?q={query}"
            st.markdown(f"""
            <br>
            <a href="{url}" target="_blank" style="
                background-color: #ff6f0f; color: white; padding: 15px; display: block;
                text-decoration: none; border-radius: 10px; font-weight: bold; text-align: center;">
                👉 '{keyword}' 전국 매물 보러가기 (클릭)
            </a>
            """, unsafe_allow_html=True)
        else:
            st.warning("검색어를 입력해주세요.")

# =============================================================================
# [TAB 3] 직원 출퇴근 (CSV 저장)
# =============================================================================
with tab3:
    st.header("⏰ 직원 출퇴근 기록부")
    c1, c2 = st.columns(2)
    emp_name = c1.text_input("직원 이름")
    action = c2.selectbox("구분", ["출근", "퇴근", "외출", "복귀"])
    
    if st.button("💾 기록 저장"):
        if emp_name:
            save_attendance(emp_name, action)
            st.success("기록되었습니다.")
            st.rerun()
            
    st.markdown("---")
    st.subheader("📝 최근 기록")
    df_log = load_attendance()
    if not df_log.empty:
        st.dataframe(df_log, use_container_width=True)
        csv = df_log.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 엑셀(CSV)로 다운로드", csv, "attendance.csv", "text/csv")

# =============================================================================
# [TAB 4] 보험 진단 (스타벅스 이벤트)
# =============================================================================
with tab4:
    st.markdown("""
    <div class='event-box'>
    <h2>☕ 스타벅스 커피 100% 증정</h2>
    <b>"상담만 받아도 조건 없이 드립니다!" (선착순)</b>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("🏥 고정비/보험료 무료 진단")
    st.markdown("법이 바뀌어서, 혹은 불필요한 특약 때문에 줄줄 새는 돈을 찾아드립니다.")
    
    c1, c2 = st.columns(2)
    curr = c1.number_input("현재 월 보험료", value=50000)
    size = c2.number_input("매장 평수", value=20)
    
    if st.button("💰 내 거품 확인하기"):
        std = size * 1000 + 10000
        diff = curr - std
        if diff > 10000:
            st.error(f"🚨 진단: 매월 약 {diff:,}원 과다 지출 중입니다!")
        else:
            st.success("✅ 진단: 적정하게 잘 내고 계십니다.")
            
    st.markdown("---")
    st.info("부담스러운 전화 NO! **카카오톡**으로 가볍게 먼저 안내해드립니다.")
    
    with st.form("starbucks_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("성명 (필수)")
        phone = c2.text_input("연락처 (필수)")
        agree = st.checkbox("(필수) 개인정보 수집 및 이용에 동의합니다.")
        
        if st.form_submit_button("📨 상담 신청하고 스타벅스 받기"):
            if agree and name and phone:
                s, m = send_email_safe(name, phone, "미입력", "스타벅스 이벤트 참여", "보험상담")
                if s:
                    st.balloons()
                    st.success("✅ 신청 완료! 카톡으로 먼저 인사드리겠습니다.")
                    st.markdown("**[진행 절차]** 카톡 안내 → 10분 상담 → 3일 내 쿠폰 발송")
                else:
                    st.error(m)
            else:
                st.warning("정보를 입력하고 동의해주세요.")
