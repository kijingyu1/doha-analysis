import streamlit as st
import pandas as pd
import numpy as np
import requests
import feedparser
import yfinance as yf
import random
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import os

# -----------------------------------------------------------------------------
# [0] 페이지 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="사장님 비서",
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
        
        .finance-box { background-color: white; padding: 10px; border-radius: 10px; box-shadow: 1px 1px 3px rgba(0,0,0,0.1); text-align: center; margin-bottom: 8px; }
        .finance-title { font-size: 0.8rem; color: #666; font-weight: bold; }
        .finance-val { font-size: 1.1rem; font-weight: bold; color: #333; }
        .finance-change { font-size: 0.8rem; font-weight: bold; }
        
        .news-box { background-color: white; padding: 15px; border-radius: 10px; border-left: 5px solid #ff6f0f; margin-bottom: 20px; }
        .news-item { padding: 8px 0; border-bottom: 1px solid #eee; }
        .news-item a { text-decoration: none; color: #333; font-weight: bold; font-size: 1rem; }
        .news-date { font-size: 0.8rem; color: #ff6f0f; margin-left: 5px; }
        
        .stButton>button { background-color: #ff6f0f; color: white; border-radius: 8px; font-weight: bold; width: 100%; height: 45px; border: none; }
        .stButton>button:hover { background-color: #e65c00; }
        
        .event-box { background-color: #1e3932; color: white; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px; }
        .fire-info-box { background-color: #fff3cd; padding: 20px; border-radius: 10px; border: 2px solid #ffc107; text-align: center; margin-bottom: 20px; }
        .fire-emoji { font-size: 3rem; }
        .login-box { max-width: 400px; margin: 0 auto; padding: 40px; background-color: white; border-radius: 20px; text-align: center; }
        .install-guide { background-color: #e3f2fd; padding: 15px; border-radius: 10px; border: 1px solid #90caf9; margin-bottom: 15px; color: #0d47a1; font-size: 0.9rem; }
        .visitor-badge { background-color: #333; color: #00ff00; padding: 10px; border-radius: 5px; font-family: 'Courier New', monospace; text-align: center; font-weight: bold; margin-top: 20px; }
        
        /* 📻 방송국 스타일 */
        .dj-card { background-color: #2b2b2b; color: white; padding: 15px; border-radius: 10px; border-left: 5px solid #00ff00; margin-bottom: 10px; }
        .dj-name { color: #00ff00; font-weight: bold; font-size: 1.1rem; }
        .dj-comment { color: #ddd; font-size: 0.9rem; margin-top: 5px; }
        </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# [기능 2] 메일 전송
# -----------------------------------------------------------------------------
def send_email_safe(name, phone, client_email, req_text, type_tag):
    if "smtp" not in st.secrets: return False, "설정 오류"
    sender = st.secrets["smtp"].get("email", "")
    pw = st.secrets["smtp"].get("password", "")
    store = st.session_state.get('store_name', '미로그인')
    subject = f"📻 [라디오/비서] {name}님 {type_tag} ({store})"
    body = f"매장: {store}\n이름: {name}\n연락처: {phone}\n내용: {req_text}"
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = sender 
    try:
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
            server.starttls()
            server.login(sender, pw)
            server.sendmail(sender, sender, msg.as_string())
        return True, "성공"
    except Exception as e: return False, str(e)

# -----------------------------------------------------------------------------
# [기능 3] 데이터 엔진
# -----------------------------------------------------------------------------
@st.cache_data(ttl=1800)
def get_finance_data():
    try:
        tickers = {'KOSPI': '^KS11', 'NASDAQ': '^IXIC', 'USD/KRW': 'KRW=X'}
        data = {}
        for name, symbol in tickers.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d", timeout=10)
                if len(hist) >= 1:
                    current = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2] if len(hist) > 1 else current
                    change = current - prev
                    change_pct = (change / prev) * 100
                    data[name] = {"price": current, "change": change, "pct": change_pct}
            except: continue
        return data
    except: return {}

def get_real_google_news():
    keywords = ["소상공인", "자영업", "지원금", "정책", "세금", "창업", "폐업"]
    query = "+OR+".join(keywords)
    url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
    try:
        feed = feedparser.parse(url)
        if feed.bozo and feed.bozo_exception: return []
        return feed.entries[:10]
    except: return []

def get_today_affirmation():
    # 긍정의 말 (운세 대체)
    words = [
        "사장님, 오늘도 좋은 일이 생길 거예요!",
        "오늘 흘린 땀방울이 내일의 매출이 됩니다.",
        "사장님의 미소가 최고의 서비스입니다.",
        "위기는 기회입니다. 오늘도 화이팅!",
        "당신은 동네에서 가장 멋진 사장님입니다.",
        "걱정 마세요. 다 잘 될 겁니다!"
    ]
    random.seed(datetime.now().day)
    return random.choice(words)

VISITOR_FILE = "visitor_log.csv"
def track_visitor():
    if not os.path.exists(VISITOR_FILE):
        df = pd.DataFrame(columns=["timestamp", "date"])
        df.to_csv(VISITOR_FILE, index=False)
    if 'visitor_counted' not in st.session_state:
        st.session_state.visitor_counted = True
        now = datetime.now()
        new_row = {"timestamp": now.strftime("%Y-%m-%d %H:%M:%S"), "date": now.strftime("%Y-%m-%d")}
        try:
            df = pd.read_csv(VISITOR_FILE)
            df = pd.concat([pd.DataFrame([new_row]), df], ignore_index=True)
            df.to_csv(VISITOR_FILE, index=False)
        except: pass
def get_visitor_count():
    if os.path.exists(VISITOR_FILE):
        try:
            df = pd.read_csv(VISITOR_FILE)
            return len(df), df
        except: return 0, pd.DataFrame()
    return 0, pd.DataFrame()

STATION_FILE = "station_list.csv"
def load_stations():
    if os.path.exists(STATION_FILE): return pd.read_csv(STATION_FILE)
    return pd.DataFrame({
        "store_name": ["DOHA 공식 방송", "퇴근길 호프집"],
        "url": ["https://www.youtube.com/watch?v=TesYp2sO1IA", "https://www.youtube.com/watch?v=1b-3zbwgq1g"],
        "comment": ["활기찬 하루를 위한 트로트 믹스!", "오늘도 고생하셨습니다."]
    })
def save_station(url, comment):
    df = load_stations()
    new_row = {"store_name": st.session_state.store_name, "url": url, "comment": comment}
    df = pd.concat([pd.DataFrame([new_row]), df], ignore_index=True)
    df.to_csv(STATION_FILE, index=False)
    return df

def get_csv_filename():
    safe_name = "".join([c for c in st.session_state.store_name if c.isalnum()])
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
# [메인] 앱 실행
# -----------------------------------------------------------------------------
set_style()
track_visitor()
total_visitors, df_visitors = get_visitor_count()

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'store_name' not in st.session_state: st.session_state.store_name = ""

# 로그인
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<div class='login-box'><h1>🥕 사장님 비서</h1><p>로그인 (키오스크 방식)</p></div>", unsafe_allow_html=True)
        with st.expander("📲 카톡에서 들어오셨나요? (설치법)"):
            st.markdown("**우측 하단 점 3개 → [다른 브라우저로 열기] → [홈 화면에 추가]**")
        store_input = st.text_input("매장 이름")
        pw_input = st.text_input("비밀번호 (4자리)", type="password")
        if st.button("입장하기"):
            if store_input and pw_input:
                st.session_state.logged_in = True
                st.session_state.store_name = store_input
                st.rerun()
            else: st.warning("정보를 입력해주세요.")
    st.markdown(f"<div style='text-align:center; color:#888; margin-top:20px;'>👀 현재 <b>{total_visitors:,}명</b>의 사장님이 함께하고 계십니다.</div>", unsafe_allow_html=True)
    st.stop()

# 메인
with st.sidebar:
    st.write(f"👤 **{st.session_state.store_name}**님")
    st.markdown(f"<div class='visitor-badge'>VISITORS<br>{total_visitors:,}</div>", unsafe_allow_html=True)
    if st.button("로그아웃"):
        st.session_state.logged_in = False
        st.rerun()

# [수정] 타이틀 글씨 크기 조정 및 DOHA 삭제
st.title(f"🥕 사장님 비서 ({st.session_state.store_name})")
st.markdown("""<div class='install-guide'><b>💡 꿀팁:</b> 카톡 말고 <b>[다른 브라우저로 열기]</b> 후 <b>[홈 화면에 추가]</b> 하세요!</div>""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 데일리 홈", "🔍 전국 당근검색", "⏰ 직원 출퇴근", "🔥 화재보험 점검", "📻 우리들의 방송국"])

# [TAB 1] 데일리 홈
with tab1:
    st.subheader("📰 오늘의 사장님 필수 뉴스")
    news_list = get_real_google_news()
    if news_list:
        with st.container():
            st.markdown("<div class='news-box'>", unsafe_allow_html=True)
            for news in news_list:
                # [수정] 괄호 삭제하고 날짜만 표시
                date_str = f"{news.published_parsed.tm_mon}/{news.published_parsed.tm_mday}"
                st.markdown(f"<div class='news-item'><span style='color:#ff6f0f;'>●</span> <a href='{news.link}' target='_blank'>{news.title}</a> <span class='news-date'>{date_str}</span></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    col_left, col_right = st.columns(2)
    
    # [왼쪽] 긍정의 말 + 금융
    with col_left:
        # [수정] 운세 -> 긍정의 말
        st.subheader("🍀 긍정의 말 (Daily Affirmation)")
        st.success(get_today_affirmation())
        
        st.markdown("<br>", unsafe_allow_html=True)
        # [수정] 코스피 등 금융 지표 복구
        st.subheader("📉 주요 경제 지표")
        finance = get_finance_data()
        
        # 금융 데이터가 로딩 중이거나 실패해도 UI가 꺼지지 않도록 처리
        if finance:
            for name, data in finance.items():
                color = "red" if data['change'] > 0 else "blue"
                sign = "▲" if data['change'] > 0 else "▼"
                st.markdown(f"<div class='finance-box'><div class='finance-title'>{name}</div><div class='finance-val'>{data['price']:,.2f}</div><div class='finance-change' style='color:{color};'>{sign} {abs(data['change']):.2f} ({data['pct']:.2f}%)</div></div>", unsafe_allow_html=True)
        else:
            # 데이터 로딩 실패 시 보여줄 정적 UI (빈칸 방지)
            st.info("금융 정보를 불러오는 중입니다... (잠시 후 다시 시도)")

    with col_right:
        st.subheader("🧮 스마트 매출 계산기")
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
    # [수정] 글씨 크기 작게 (h3)
    st.markdown("### 🔍 당근마켓 전국 매물 찾기")
    keyword = st.text_input("찾으시는 물건", "")
    if st.button("전국 검색 시작"):
        if keyword:
            url = f"https://www.google.com/search?q=site:daangn.com {keyword}"
            st.markdown(f"<br><a href='{url}' target='_blank' style='background-color:#ff6f0f;color:white;padding:15px;display:block;text-decoration:none;border-radius:10px;font-weight:bold;text-align:center;'>👉 '{keyword}' 전국 매물 보기 (클릭)</a>", unsafe_allow_html=True)
        else: st.warning("검색어를 입력해주세요.")

# [TAB 3] 출퇴근부
with tab3:
    st.header(f"⏰ {st.session_state.store_name} 출퇴근부")
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
    if not df_log.empty: st.dataframe(df_log, use_container_width=True)

# [TAB 4] 화재보험
with tab4:
    # [수정] 스타벅스 글씨 크기 작게 (h3)
    st.markdown("""<div class='event-box'><h3>☕ 스타벅스 100% 증정</h3><b>"상담만 받아도 조건 없이 드립니다!"</b></div>""", unsafe_allow_html=True)
    st.header("🔥 우리 가게 안전 점검")
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown("""<div class='fire-info-box'><span class='fire-emoji'>🔥</span><div class='fire-title'>내 가게가 탈 때</div><div class='fire-desc'>건물주 보험은 보상해주지 않습니다.</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown("""<div class='fire-info-box'><span class='fire-emoji'>🏘️</span><div class='fire-title'>옆 가게 피해</div><div class='fire-desc'>옮겨붙은 불 피해도 다 물어줘야 합니다.</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown("""<div class='fire-info-box'><span class='fire-emoji'>🤕</span><div class='fire-title'>손님 부상</div><div class='fire-desc'>치료비, 합의금 모두 사장님 책임입니다.</div></div>""", unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("🏥 내 보험 & 배상책임 진단")
    c1, c2 = st.columns(2)
    curr = c1.number_input("현재 월 보험료", value=50000)
    size = c2.number_input("매장 평수", value=20)
    st.markdown("<br><b>'시설물배상책임보험' 가입 여부</b>", unsafe_allow_html=True)
    liab_check = st.radio("배상책임 여부", ["네, 가입했습니다.", "아니요 / 잘 모르겠습니다."], label_visibility="collapsed")
    if st.button("💰 종합 진단"):
        std = size * 1000 + 10000 
        diff = curr - std
        if diff > 15000: st.error(f"🚨 보험료 {diff:,}원 과다 지출 의심!")
        else: st.success("✅ 보험료는 적정합니다.")
        if liab_check == "아니요 / 잘 모르겠습니다.": st.markdown("""<div style='background-color:#fff3cd; padding:20px; border-radius:10px; border:2px solid red; margin-top:20px;'><h3 style='color:red;'>🚨 [긴급 경고] 배상책임 미가입 위험!</h3><b>손님이 매장에서 다치면 큰일 납니다.</b> 즉시 확인이 필요합니다.</div>""", unsafe_allow_html=True)
    st.markdown("---")
    with st.form("starbucks_form_fire"):
        c1, c2 = st.columns(2)
        name = c1.text_input("성명")
        phone = c2.text_input("연락처")
        agree = st.checkbox("(필수) 개인정보 동의")
        if st.form_submit_button("📨 상담 신청하고 스타벅스 받기"):
            if agree and name and phone:
                req_detail = f"화재보험 (배상책임: {liab_check})"
                s, m = send_email_safe(name, phone, "미입력", req_detail, "화재보험")
                if s: st.balloons(); st.success("신청 완료!")
                else: st.error(m)
            else: st.warning("정보를 입력하세요.")

# [TAB 5] 방송국
with tab5:
    st.header("📻 우리들의 방송국 (Open DJ)")
    st.info("누구나 **DJ**가 되어 음악을 틀 수 있습니다.")
    st.subheader("📡 현재 송출 중인 방송")
    df_stations = load_stations()
    station_names = df_stations['store_name'].tolist()
    choice = st.selectbox("어느 방송을 들을까요?", station_names)
    selected_row = df_stations[df_stations['store_name'] == choice].iloc[0]
    st.markdown(f"""<div class='dj-card'><div class='dj-name'>🎧 DJ: {selected_row['store_name']}</div><div class='dj-comment'>💬 {selected_row['comment']}</div></div>""", unsafe_allow_html=True)
    try: st.video(selected_row['url'])
    except: st.error("영상을 불러올 수 없습니다.")
    st.markdown("---")
    with st.expander("🎙️ 나도 DJ 신청하기"):
        with st.form("dj_form"):
            dj_url = st.text_input("유튜브 링크")
            dj_comment = st.text_input("청취자들에게 한마디")
            if st.form_submit_button("📡 내 방송국 등록"):
                if dj_url and dj_comment:
                    save_station(dj_url, dj_comment)
                    st.success("등록 완료!"); st.rerun()
                else: st.warning("내용을 입력해주세요.")
