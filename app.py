import streamlit as st
import pandas as pd
import numpy as np
import requests
import feedparser
import yfinance as yf
import random
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import os
import streamlit.components.v1 as components

# -----------------------------------------------------------------------------
# [0] 페이지 설정 및 관리자 비밀번호
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="사장님 비서",
    page_icon="🥕",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 🔐 관리자 비밀번호
ADMIN_PW = "7777" 

# -----------------------------------------------------------------------------
# [기능 1] 스타일
# -----------------------------------------------------------------------------
def set_style():
    st.markdown("""
        <style>
        .main { background-color: #f8f9fa; }
        h1 { color: #ff6f0f; font-weight: 800; line-height: 1.2; }
        .store-subtitle { color: #333; font-size: 1.5rem; font-weight: bold; margin-top: 5px; }
        h2, h3 { color: #ff6f0f; font-weight: 800; } 
        
        .finance-box { background-color: white; padding: 10px; border-radius: 10px; box-shadow: 1px 1px 3px rgba(0,0,0,0.1); text-align: center; margin-bottom: 8px; }
        .finance-title { font-size: 0.8rem; color: #666; font-weight: bold; }
        .finance-val { font-size: 1.1rem; font-weight: bold; color: #333; }
        .finance-change { font-size: 0.8rem; font-weight: bold; }
        
        .news-box { background-color: white; padding: 15px; border-radius: 10px; border-left: 5px solid #ff6f0f; margin-bottom: 20px; }
        .news-item { padding: 8px 0; border-bottom: 1px solid #eee; }
        .news-item a { text-decoration: none; color: #333; font-weight: bold; font-size: 1rem; }
        .news-date { font-size: 0.8rem; color: #ff6f0f; margin-left: 5px; }
        .news-update-time { font-size: 0.8rem; color: #888; text-align: right; margin-top: 5px; }
        
        .stButton>button { background-color: #ff6f0f; color: white; border-radius: 8px; font-weight: bold; width: 100%; height: 45px; border: none; }
        .stButton>button:hover { background-color: #e65c00; }
        
        .event-box { background-color: #1e3932; color: white; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px; }
        
        /* 🔥 화재보험 경고 박스 */
        .warning-box { background-color: #ffebee; border: 2px solid #ef5350; padding: 15px; border-radius: 10px; margin-bottom: 15px; }
        .warning-title { color: #c62828; font-weight: bold; font-size: 1.1rem; margin-bottom: 5px; }
        .warning-text { color: #333; font-size: 0.95rem; }
        
        .login-box { max-width: 400px; margin: 0 auto; padding: 40px; background-color: white; border-radius: 20px; text-align: center; box-shadow: 0px 4px 15px rgba(0,0,0,0.1); }
        .install-guide { background-color: #e3f2fd; padding: 15px; border-radius: 10px; border: 1px solid #90caf9; margin-bottom: 15px; color: #0d47a1; font-size: 0.9rem; }
        .visitor-badge { background-color: #333; color: #00ff00; padding: 10px; border-radius: 5px; font-family: 'Courier New', monospace; text-align: center; font-weight: bold; margin-top: 20px; }
        
        .notice-box { background-color: #fff3cd; color: #856404; padding: 15px; border-radius: 10px; border: 1px solid #ffeeba; margin-bottom: 20px; }
        
        .ledger-summary { background-color: white; padding: 15px; border-radius: 10px; border: 1px solid #ddd; text-align: center; }
        .ledger-val { font-size: 1.3rem; font-weight: bold; color: #333; }
        .ledger-label { font-size: 0.9rem; color: #666; }
        
        /* 🎮 랭킹 스타일 */
        .rank-card { background-color: #fff; border: 2px solid #ff6f0f; border-radius: 10px; padding: 10px; margin-bottom: 5px; display: flex; justify-content: space-between; align-items: center; }
        .rank-medal { font-size: 1.5rem; margin-right: 10px; }
        .rank-name { font-weight: bold; color: #333; }
        .rank-score { font-weight: bold; color: #ff6f0f; }

        /* 🛠️ 전문가 카드 스타일 */
        .expert-card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 15px; border-left: 5px solid #ff6f0f; }
        .expert-cat { display: inline-block; background-color: #eee; padding: 3px 8px; border-radius: 5px; font-size: 0.8rem; color: #555; margin-bottom: 5px; }
        .expert-name { font-size: 1.2rem; font-weight: bold; color: #333; }
        .expert-desc { font-size: 0.95rem; color: #666; margin: 5px 0 10px 0; }
        .expert-contact { background-color: #ff6f0f; color: white; padding: 8px; text-align: center; border-radius: 8px; text-decoration: none; display: block; font-weight: bold; }
        
        /* 💧 배관 서비스 스타일 */
        .plumbing-card { border: 1px solid #29b6f6; background-color: #e1f5fe; padding: 15px; border-radius: 10px; text-align: center; height: 100%; }
        .plumbing-icon { font-size: 2.5rem; margin-bottom: 10px; }
        .plumbing-title { font-weight: bold; color: #0277bd; margin-bottom: 5px; }
        .plumbing-desc { font-size: 0.9rem; color: #555; }
        
        /* 👇 모바일 최적화 하단 고정 문의 버튼 */
        .sticky-footer {
            position: fixed; bottom: 0; left: 0; width: 100%; background-color: white;
            box-shadow: 0px -2px 10px rgba(0,0,0,0.1); display: flex; justify-content: space-around;
            padding: 10px 5px; z-index: 9999; border-top: 1px solid #eee;
        }
        .footer-btn {
            flex: 1; margin: 0 5px; padding: 12px 0; border-radius: 8px; text-align: center;
            font-weight: bold; text-decoration: none; font-size: 1rem; display: flex; align-items: center; justify-content: center;
        }
        .btn-call { background-color: #28a745; color: white !important; }
        .btn-kakao { background-color: #ffe812; color: #381e1f !important; }
        .block-container { padding-bottom: 80px; }
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
    subject = f"🔔 [사장님 비서] {name}님 {type_tag} ({store})"
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

@st.cache_data(ttl=3600)
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
    words = ["사장님, 오늘도 대박 나세요!", "오늘 흘린 땀방울이 내일의 매출이 됩니다.", "위기는 기회입니다. 화이팅!", "당신은 최고의 CEO입니다."]
    random.seed(datetime.now().day)
    return random.choice(words)

# 방문자 로그
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
            return len(df), df, df 
        except: return 0, pd.DataFrame(), pd.DataFrame()
    return 0, pd.DataFrame(), pd.DataFrame()

# 공지사항
NOTICE_FILE = "notice.txt"
def load_notice():
    if os.path.exists(NOTICE_FILE):
        with open(NOTICE_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return "사장님들 힘내세요! 공지사항이 여기에 표시됩니다."
def save_notice(text):
    with open(NOTICE_FILE, "w", encoding="utf-8") as f:
        f.write(text)

# 라디오 URL
RADIO_URL_FILE = "radio_url.txt"
def load_radio_url():
    if os.path.exists(RADIO_URL_FILE):
        with open(RADIO_URL_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "https://www.youtube.com/watch?v=5qap5aO4i9A"
def save_radio_url(url):
    with open(RADIO_URL_FILE, "w", encoding="utf-8") as f:
        f.write(url)

# 장부
LEDGER_FILE = "ledger_data.csv"
def load_ledger():
    if os.path.exists(LEDGER_FILE): return pd.read_csv(LEDGER_FILE)
    return pd.DataFrame(columns=["날짜", "구분", "항목", "금액", "메모"]) 
def save_ledger(date, type_, item, amount, memo):
    df = load_ledger()
    new_row = {"날짜": date, "구분": type_, "항목": item, "금액": amount, "메모": memo}
    df = pd.concat([pd.DataFrame([new_row]), df], ignore_index=True)
    df.to_csv(LEDGER_FILE, index=False)
    return df

# 출퇴근부
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

# 게임 랭킹
GAME_FILE = "game_rank.csv"
def load_rank():
    if os.path.exists(GAME_FILE): return pd.read_csv(GAME_FILE)
    return pd.DataFrame(columns=["name", "score", "date"])
def save_score(name, score):
    df = load_rank()
    if name in df['name'].values:
        idx = df.index[df['name'] == name].tolist()[0]
        if score > df.at[idx, 'score']:
            df.at[idx, 'score'] = score
            df.at[idx, 'date'] = datetime.now().strftime("%Y-%m-%d")
    else:
        new_row = {"name": name, "score": score, "date": datetime.now().strftime("%Y-%m-%d")}
        df = pd.concat([pd.DataFrame([new_row]), df], ignore_index=True)
    df.to_csv(GAME_FILE, index=False)
    return df

# 전문가 DB
EXPERT_FILE = "experts.csv"
def load_experts():
    if os.path.exists(EXPERT_FILE): return pd.read_csv(EXPERT_FILE)
    return pd.DataFrame({
        "category": ["인테리어", "철거/원상복구", "세무/회계", "마케팅/블로그"],
        "name": ["김목수 디자인", "깔끔 철거", "성실 세무", "대박 마케팅"],
        "desc": ["카페, 식당 인테리어 10년 경력", "폐업 지원금 신청까지 도와드려요", "소상공인 절세 전문", "블로그 상위노출 보장"],
        "contact": ["010-1234-5678", "010-9876-5432", "010-1111-2222", "010-3333-4444"],
        "location": ["서울/경기", "전국", "인천", "서울"]
    })
def save_expert(category, name, desc, contact, location):
    df = load_experts()
    new_row = {"category": category, "name": name, "desc": desc, "contact": contact, "location": location}
    df = pd.concat([pd.DataFrame([new_row]), df], ignore_index=True)
    df.to_csv(EXPERT_FILE, index=False)
    return df

# -----------------------------------------------------------------------------
# [메인] 앱 실행
# -----------------------------------------------------------------------------
set_style()
track_visitor()
total_visitors, _, df_visitors_all = get_visitor_count()

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'store_name' not in st.session_state: st.session_state.store_name = ""

# 로그인 화면
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        LOGO_URL = "https://cdn-icons-png.flaticon.com/512/1995/1995515.png" 
        st.markdown(f"""<div class='login-box'><img src='{LOGO_URL}' style='width: 150px; margin-bottom: 20px; border-radius: 20px;'><p style='font-size: 1.1rem; font-weight: bold; color: #555;'>로그인</p></div>""", unsafe_allow_html=True)
        with st.expander("📲 카톡에서 들어오셨나요?"):
            st.markdown("**우측 하단 점 3개 → [다른 브라우저로 열기]**")
        store_input = st.text_input("매장 이름")
        pw_input = st.text_input("비밀번호 (4자리)", type="password")
        if st.button("입장하기"):
            if store_input in ["admin", "관리자"]:
                if pw_input == ADMIN_PW:
                    st.session_state.logged_in = True
                    st.session_state.store_name = store_input
                    st.rerun()
                else: st.error("❌ 관리자 비밀번호가 틀렸습니다.")
            elif store_input and pw_input:
                st.session_state.logged_in = True
                st.session_state.store_name = store_input
                st.rerun()
            else: st.warning("정보를 입력해주세요.")
    st.markdown(f"<div style='text-align:center; color:#888; margin-top:20px;'>👀 현재 <b>{total_visitors:,}명</b>의 사장님이 함께하고 계십니다.</div>", unsafe_allow_html=True)
    st.stop()

# 메인 화면
with st.sidebar:
    st.write(f"👤 **{st.session_state.store_name}**님")
    st.markdown(f"<div class='visitor-badge'>VISITORS<br>{total_visitors:,}</div>", unsafe_allow_html=True)
    with st.expander("🕵️‍♂️ 접속 로그 (상세)"):
        if not df_visitors_all.empty:
            st.dataframe(df_visitors_all.sort_values("timestamp", ascending=False).head(10), hide_index=True)
        else: st.write("기록 없음")
    if st.button("로그아웃"):
        st.session_state.logged_in = False
        st.rerun()

st.markdown(f"""<h1>🥕 사장님 비서<br><span class='store-subtitle'>({st.session_state.store_name})</span></h1>""", unsafe_allow_html=True)
st.markdown("""<div class='install-guide'><b>💡 꿀팁:</b> 카톡 말고 <b>[다른 브라우저로 열기]</b> 후 <b>[홈 화면에 추가]</b> 하세요!</div>""", unsafe_allow_html=True)

# 공지사항
current_notice = load_notice()
if st.session_state.store_name in ["admin", "관리자"]:
    with st.expander("📢 공지사항 수정 (관리자용)"):
        new_notice = st.text_area("공지 내용", current_notice)
        if st.button("공지 업데이트"):
            save_notice(new_notice)
            st.success("수정 완료!")
            st.rerun()

st.markdown(f"""<div class='notice-box'><b>📢 필독 공지:</b> {current_notice}</div>""", unsafe_allow_html=True)

# 탭 설정 (Tab 9 추가됨)
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(["🏠 홈", "🔍 당근", "⏰ 근태", "🔥 보험점검", "📻 라디오", "📒 장부", "💰 쉼터", "🛠️ 전문가", "💧 배관/누수"])

# ... (Tab 1 ~ 3 기존 코드) ...
with tab1:
    st.subheader("📰 오늘의 사장님 필수 뉴스")
    st.caption("※ 매일 09시, 12시, 18시, 21시 자동 업데이트")
    news_list = get_real_google_news()
    if news_list:
        with st.container():
            st.markdown("<div class='news-box'>", unsafe_allow_html=True)
            for news in news_list:
                date_str = f"{news.published_parsed.tm_mon}/{news.published_parsed.tm_mday}"
                st.markdown(f"<div class='news-item'><span style='color:#ff6f0f;'>●</span> <a href='{news.link}' target='_blank'>{news.title}</a> <span class='news-date'>{date_str}</span></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            now_str = datetime.now().strftime("%H시 %M분")
            st.markdown(f"<div class='news-update-time'>최근 갱신: {now_str} 기준</div>", unsafe_allow_html=True)
    st.markdown("---")
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("🍀 긍정의 말")
        st.success(get_today_affirmation())
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📉 주요 경제 지표")
        finance = get_finance_data()
        if finance:
            for name, data in finance.items():
                color = "red" if data['change'] > 0 else "blue"
                sign = "▲" if data['change'] > 0 else "▼"
                st.markdown(f"<div class='finance-box'><div class='finance-title'>{name}</div><div class='finance-val'>{data['price']:,.2f}</div><div class='finance-change' style='color:{color};'>{sign} {abs(data['change']):.2f} ({data['pct']:.2f}%)</div></div>", unsafe_allow_html=True)
        else: st.info("정보 로딩 중...")
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

with tab2:
    st.markdown("### 🔍 당근마켓 전국 매물 찾기")
    keyword = st.text_input("찾으시는 물건", "")
    if st.button("전국 검색 시작"):
        if keyword:
            url = f"https://www.google.com/search?q=site:daangn.com {keyword}"
            st.markdown(f"<br><a href='{url}' target='_blank' style='background-color:#ff6f0f;color:white;padding:15px;display:block;text-decoration:none;border-radius:10px;font-weight:bold;text-align:center;'>👉 '{keyword}' 전국 매물 보기 (클릭)</a>", unsafe_allow_html=True)

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

# =============================================================================
# [TAB 4] 🔥 화재보험 점검 (매운맛 리뉴얼)
# =============================================================================
with tab4:
    st.markdown("""<div class='event-box'><h3>☕ 스타벅스 100% 증정</h3><b>"상담만 받아도 조건 없이 드립니다!"</b></div>""", unsafe_allow_html=True)
    
    st.header("🔥 사장님, 보험료 1만 원 아끼려다 1억 날립니다.")
    st.markdown("""
    <div class='warning-box'>
        <div class='warning-title'>🚨 혹시 이렇게 생각하시나요?</div>
        <div class='warning-text'>
        "설마 우리 가게에 불이 나겠어?"<br>
        "건물주가 보험 들었으니 괜찮겠지?"<br>
        <br>
        <b>절대 아닙니다.</b><br>
        옆 가게로 불이 옮겨붙으면 <b>사장님이 100% 배상</b>해야 하고,<br>
        손님이 매장에서 미끄러져 다쳐도 <b>사장님 책임</b>입니다.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("📋 [3초 자가진단] 하나라도 해당되면 위험합니다!")
    check1 = st.checkbox("내가 가입한 화재보험에 '시설소유관리자 배상책임'이 있는지 모른다.")
    check2 = st.checkbox("보험 가입한 지 3년이 넘었는데, 한 번도 점검받은 적 없다.")
    check3 = st.checkbox("월 보험료가 5만 원 이상 나가는데, 보장 내용은 잘 모른다.")
    
    if check1 or check2 or check3:
        st.error("🚨 경고: 지금 당장 '보험 증권' 확인이 필요합니다! 불필요한 돈이 새고 있거나, 정작 필요한 보장이 빠져있을 수 있습니다.")
    
    st.markdown("---")
    st.subheader("🏥 무료 점검 신청 (대면 강요 X)")
    
    with st.form("starbucks_form_fire"):
        st.info("💡 **기본 상담은 카카오톡으로 진행**되며, **대면 상담은 희망하실 때만** 방문합니다. (부담 0%)")
        c1, c2 = st.columns(2)
        name = c1.text_input("성명")
        phone = c2.text_input("연락처")
        agree = st.checkbox("(필수) 개인정보 동의")
        
        if st.form_submit_button("📨 무료 진단받고 스타벅스 받기"):
            if agree and name and phone:
                req_detail = f"화재보험 점검 요청 (위험체크: {check1 or check2 or check3})"
                s, m = send_email_safe(name, phone, "미입력", req_detail, "화재보험")
                if s: st.balloons(); st.success("신청 완료! 담당자가 카톡으로 연락드립니다.")
                else: st.error(m)
            else: st.warning("정보를 입력하세요.")

# ... (Tab 5 ~ 8 기존 코드) ...
with tab5:
    st.header("📻 사장님 힐링 라디오")
    st.caption("오늘도 수고 많으셨습니다. 노래 들으면서 힘내세요! 💪")
    current_radio_url = load_radio_url()
    try:
        st.video(current_radio_url)
    except:
        st.error("영상을 재생할 수 없습니다.")
    st.info("💡 위 영상은 **유튜브 조회수**에 그대로 반영됩니다!")
    if st.session_state.store_name in ["admin", "관리자"]:
        st.markdown("---")
        with st.expander("🛠️ [관리자] 방송 영상 바꾸기"):
            st.markdown("**유튜브 영상 URL이나 플레이리스트 주소를 입력하세요.**")
            new_url = st.text_input("새로운 유튜브 주소", current_radio_url)
            if st.button("방송 송출 주소 변경"):
                save_radio_url(new_url)
                st.success("방송이 변경되었습니다! 모든 사장님들에게 이 영상이 송출됩니다."); st.rerun()

with tab6:
    st.header("📒 사장님 간편 장부")
    st.caption("복잡한 기능은 뺐습니다. **입력하고, 조회하고, 엑셀로 받으세요.**")
    with st.expander("✏️ 수입/지출 입력하기 (클릭)", expanded=False):
        with st.form("ledger_input"):
            c1, c2 = st.columns(2)
            l_date = c1.date_input("날짜", datetime.now())
            l_type = c2.selectbox("구분", ["매출 (수입)", "지출 (비용)"])
            c3, c4 = st.columns(2)
            l_item = c3.text_input("항목 (예: 식자재)", placeholder="직접 입력")
            l_amount = c4.number_input("금액", step=1000)
            l_memo = st.text_input("메모", placeholder="특이사항")
            if st.form_submit_button("💾 장부에 저장"):
                if l_item and l_amount > 0:
                    save_ledger(l_date, l_type, l_item, l_amount, l_memo)
                    st.success("저장되었습니다."); st.rerun()
                else: st.warning("항목과 금액을 확인해주세요.")
    st.markdown("---")
    st.subheader("🔍 장부 조회 & 엑셀 다운로드")
    df_ledger = load_ledger()
    if not df_ledger.empty:
        c1, c2, c3 = st.columns([2, 1, 1])
        search_txt = c1.text_input("검색어 (항목, 메모)", placeholder="예: 식자재")
        mask = df_ledger.apply(lambda x: search_txt in str(x['항목']) or search_txt in str(x['메모']), axis=1)
        df_filtered = df_ledger[mask]
        total_income = df_filtered[df_filtered['구분'] == "매출 (수입)"]['금액'].sum()
        total_expense = df_filtered[df_filtered['구분'] == "지출 (비용)"]['금액'].sum()
        net_profit = total_income - total_expense
        c_a, c_b, c_c = st.columns(3)
        c_a.markdown(f"<div class='ledger-summary'><div class='ledger-label'>총 매출</div><div class='ledger-val' style='color:blue;'>{total_income:,}원</div></div>", unsafe_allow_html=True)
        c_b.markdown(f"<div class='ledger-summary'><div class='ledger-label'>총 지출</div><div class='ledger-val' style='color:red;'>{total_expense:,}원</div></div>", unsafe_allow_html=True)
        c_c.markdown(f"<div class='ledger-summary'><div class='ledger-label'>순이익</div><div class='ledger-val'>{net_profit:,}원</div></div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(df_filtered, use_container_width=True, hide_index=True)
        csv = df_filtered.to_csv(index=False).encode('utf-8-sig')
        st.download_button(label="📥 엑셀(CSV)로 내보내기", data=csv, file_name=f"사장님장부_{datetime.now().strftime('%Y%m%d')}.csv", mime='text/csv')
    else: st.info("작성된 장부가 없습니다.")

with tab7:
    st.header("💰 소상공인 정책자금 센터")
    st.markdown("""<div style='background-color:#e8f5e9; padding:20px; border-radius:15px; border:2px solid #4caf50; text-align:center;'><h3 style='color:#2e7d32; margin-bottom:10px;'>🏛️ 정책자금/대출 공식 신청 사이트</h3><p style='color:#333; margin-bottom:15px;'>소상공인시장진흥공단에서 제공하는 <b>저금리 정책자금</b>을 확인하세요.</p><a href='https://ols.semas.or.kr/ols/man/SMAN010M/page.do' target='_blank' style='background-color:#4caf50; color:white; padding:12px 25px; border-radius:30px; text-decoration:none; font-weight:bold; font-size:1.1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>🚀 정책자금 신청하러 가기 (클릭)</a></div>""", unsafe_allow_html=True)
    st.markdown("---")
    st.header("🎮 테트리스 챔피언십 (모바일용)")
    st.caption("레벨 20까지 도전하세요! 500점마다 속도가 빨라집니다.")
    tetris_code = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"><style>body{background-color:#202028;color:#fff;font-family:'Courier New',Courier,monospace;text-align:center;margin:0;padding:0;touch-action:manipulation}#game-container{position:relative;width:100%;max-width:350px;margin:0 auto}.hud{display:flex;justify-content:space-between;padding:10px;font-weight:bold;font-size:18px;color:#ff6f0f}canvas{display:block;background-color:#000;border:4px solid #444;margin:0 auto;box-shadow:0 0 20px rgba(0,0,0,0.5);width:100%;height:auto;image-rendering:pixelated}#overlay{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);background:rgba(0,0,0,0.85);width:80%;padding:20px;border-radius:10px;border:2px solid #ff6f0f;display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:10}.btn-start{background:#ff6f0f;color:white;border:none;padding:15px 30px;font-size:20px;font-weight:bold;border-radius:50px;cursor:pointer;margin-top:10px;box-shadow:0 4px 0 #b34e0a}.btn-start:active{transform:translateY(4px);box-shadow:none}.controls-area{margin-top:15px;display:flex;flex-direction:column;align-items:center;gap:10px;padding-bottom:20px}.d-pad{display:flex;gap:10px}.ctrl-btn{width:70px;height:70px;background:#444;border-radius:15px;border:none;color:white;font-size:30px;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 0 #222;touch-action:manipulation;-webkit-tap-highlight-color:transparent}.ctrl-btn:active{background:#666;transform:translateY(4px);box-shadow:none}.rotate-btn{background:#2e7d32;width:80px;height:80px;border-radius:50%}.hidden{display:none!important}</style></head><body><div id="game-container"><div class="hud"><span>LV:<span id="level">1</span></span><span>SCORE:<span id="score">0</span></span></div><canvas id="tetris" width="240" height="400"></canvas><div id="overlay"><h2 id="msg-title" style="margin:0 0 10px 0;color:#fff">TETRIS</h2><p id="msg-sub" style="color:#aaa">사장님, 준비되셨나요?</p><div id="final-score-display" style="display:none;font-size:24px;color:#ff6f0f;margin:10px 0;font-weight:bold">0점</div><button class="btn-start" onclick="startGame()">GAME START</button></div></div><div class="controls-area"><button class="ctrl-btn rotate-btn" ontouchstart="playerRotate(1);return false;" onmousedown="playerRotate(1)">↻</button><div class="d-pad"><button class="ctrl-btn" ontouchstart="playerMove(-1);return false;" onmousedown="playerMove(-1)">⬅️</button><button class="ctrl-btn" ontouchstart="playerDrop();return false;" onmousedown="playerDrop()">⬇️</button><button class="ctrl-btn" ontouchstart="playerMove(1);return false;" onmousedown="playerMove(1)">➡️</button></div><div style="font-size:12px;color:#666;margin-top:5px">(PC는 방향키 사용 가능)</div></div><script>const canvas=document.getElementById('tetris');const context=canvas.getContext('2d');context.scale(20,20);let isGameOver=false;let isPaused=true;let dropInterval=1000;let lastTime=0;let dropCounter=0;let level=1;function arenaSweep(){let rowCount=1;outer:for(let y=arena.length-1;y>0;--y){for(let x=0;x<arena[y].length;++x){if(arena[y][x]===0)continue outer}const row=arena.splice(y,1)[0].fill(0);arena.unshift(row);++y;player.score+=rowCount*10;rowCount*=2}updateLevel()}function updateLevel(){const newLevel=Math.min(20,Math.floor(player.score/500)+1);if(newLevel!==level){level=newLevel;dropInterval=Math.max(100,1000-(level-1)*45)}document.getElementById('level').innerText=level;document.getElementById('score').innerText=player.score}function collide(arena,player){const m=player.matrix;const o=player.pos;for(let y=0;y<m.length;++y){for(let x=0;x<m[y].length;++x){if(m[y][x]!==0&&(arena[y+o.y]&&arena[y+o.y][x+o.x])!==0){return true}}}return false}function createMatrix(w,h){const matrix=[];while(h--){matrix.push(new Array(w).fill(0))}return matrix}function createPiece(type){if(type==='I')return[[0,1,0,0],[0,1,0,0],[0,1,0,0],[0,1,0,0]];else if(type==='L')return[[0,2,0],[0,2,0],[0,2,2]];else if(type==='J')return[[0,3,0],[0,3,0],[3,3,0]];else if(type==='O')return[[4,4],[4,4]];else if(type==='Z')return[[5,5,0],[0,5,5],[0,0,0]];else if(type==='S')return[[0,6,6],[6,6,0],[0,0,0]];else if(type==='T')return[[0,7,0],[7,7,7],[0,0,0]]}function drawMatrix(matrix,offset){matrix.forEach((row,y)=>{row.forEach((value,x)=>{if(value!==0){const colors=[null,'#FF0D72','#0DC2FF','#0DFF72','#F538FF','#FF8E0D','#FFE138','#3877FF'];context.fillStyle=colors[value];context.fillRect(x+offset.x,y+offset.y,1,1);context.lineWidth=0.05;context.strokeStyle='white';context.strokeRect(x+offset.x,y+offset.y,1,1)}})})}function draw(){context.fillStyle='#000';context.fillRect(0,0,canvas.width,canvas.height);drawMatrix(arena,{x:0,y:0});drawMatrix(player.matrix,player.pos)}function merge(arena,player){player.matrix.forEach((row,y)=>{row.forEach((value,x)=>{if(value!==0){arena[y+player.pos.y][x+player.pos.x]=value}})});if(player.pos.y===0)gameOver()}function rotate(matrix,dir){for(let y=0;y<matrix.length;++y){for(let x=0;x<y;++x){[matrix[x][y],matrix[y][x]]=[matrix[y][x],matrix[x][y]]}}if(dir>0)matrix.forEach(row=>row.reverse());else matrix.reverse()}function playerDrop(){if(isPaused||isGameOver)return;player.pos.y++;if(collide(arena,player)){player.pos.y--;merge(arena,player);playerReset();arenaSweep()}dropCounter=0}function playerMove(offset){if(isPaused||isGameOver)return;player.pos.x+=offset;if(collide(arena,player)){player.pos.x-=offset}}function playerReset(){const pieces='ILJOTSZ';player.matrix=createPiece(pieces[pieces.length*Math.random()|0]);player.pos.y=0;player.pos.x=(arena[0].length/2|0)-(player.matrix[0].length/2|0);if(collide(arena,player)){gameOver()}}function playerRotate(dir){if(isPaused||isGameOver)return;const pos=player.pos.x;let offset=1;rotate(player.matrix,dir);while(collide(arena,player)){player.pos.x+=offset;offset=-(offset+(offset>0?1:-1));if(offset>player.matrix[0].length){rotate(player.matrix,-dir);player.pos.x=pos;return}}}function update(time=0){if(!isPaused&&!isGameOver){const deltaTime=time-lastTime;lastTime=time;dropCounter+=deltaTime;if(dropCounter>dropInterval){playerDrop()}draw()}requestAnimationFrame(update)}function startGame(){arena.forEach(row=>row.fill(0));player.score=0;level=1;dropInterval=1000;isGameOver=false;isPaused=false;updateLevel();playerReset();document.getElementById('overlay').classList.add('hidden');update()}function gameOver(){isGameOver=true;document.getElementById('overlay').classList.remove('hidden');document.getElementById('msg-title').innerText="GAME OVER";document.getElementById('msg-sub').innerText="사장님의 최종 점수는?";const scoreEl=document.getElementById('final-score-display');scoreEl.style.display="block";scoreEl.innerText=player.score+" 점";document.querySelector('.btn-start').innerText="다시 시작하기"}const arena=createMatrix(12,20);const player={pos:{x:0,y:0},matrix:null,score:0};document.addEventListener('keydown',event=>{if(event.keyCode===37)playerMove(-1);else if(event.keyCode===39)playerMove(1);else if(event.keyCode===40)playerDrop();else if(event.keyCode===38)playerRotate(1)});playerReset();updateLevel();draw();</script></body></html>"""
    components.html(tetris_code, height=850)
    st.markdown("---")
    st.subheader("🏆 랭킹 등록하기")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.info("👆 위 게임이 끝나면 **'GAME OVER'** 화면에 나온 점수를 아래에 입력해주세요.")
        with st.form("game_score_submit"):
            my_score = st.number_input("내 최종 점수", min_value=0, step=100)
            if st.form_submit_button("🥇 점수 등록 및 랭킹 확인"):
                if my_score > 0:
                    save_score(st.session_state.store_name, my_score)
                    st.success(f"축하합니다! {my_score}점 등록 완료!"); st.rerun()
    with c2:
        st.markdown("##### 🏅 명예의 전당 (Top 5)")
        df_rank = load_rank()
        if not df_rank.empty:
            df_rank = df_rank.sort_values(by='score', ascending=False).head(5).reset_index(drop=True)
            for i, row in df_rank.iterrows():
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}위"
                st.markdown(f"<div class='rank-card'><div><span class='rank-medal'>{medal}</span> <span class='rank-name'>{row['name']}</span></div><div class='rank-score'>{row['score']:,} 점</div></div>", unsafe_allow_html=True)
        else: st.info("아직 랭커가 없습니다. 1등을 노리세요!")

with tab8:
    st.header("🛠️ 우리 동네 전문가 (숨고보다 싸다!)")
    st.markdown("견적 비용? 수수료? 없습니다. **사장님들끼리 직거래하세요!**")
    st.subheader("🔎 전문가 찾기")
    df_experts = load_experts()
    categories = ["전체"] + list(df_experts['category'].unique())
    selected_cat = st.selectbox("어떤 전문가가 필요하신가요?", categories)
    if selected_cat != "전체": df_show = df_experts[df_experts['category'] == selected_cat]
    else: df_show = df_experts
    if not df_show.empty:
        for idx, row in df_show.iterrows():
            st.markdown(f"""<div class='expert-card'><div class='expert-cat'>{row['category']} | {row['location']}</div><div class='expert-name'>{row['name']}</div><div class='expert-desc'>{row['desc']}</div><a href='tel:{row['contact']}' class='expert-contact'>📞 {row['contact']} (전화 걸기)</a></div>""", unsafe_allow_html=True)
    else: st.info("아직 등록된 전문가가 없습니다.")
    st.markdown("---")
    with st.expander("🙋‍♂️ 나도 전문가로 등록하기 (무료)"):
        with st.form("expert_register"):
            e_cat = st.selectbox("분야", ["인테리어", "철거/원상복구", "용달/이사", "세무/회계", "마케팅/블로그", "기타"])
            e_name = st.text_input("업체명")
            e_loc = st.text_input("활동 지역")
            e_contact = st.text_input("연락처")
            e_desc = st.text_area("소개글")
            if st.form_submit_button("등록 신청하기"):
                if e_name and e_contact:
                    save_expert(e_cat, e_name, e_desc, e_contact, e_loc)
                    st.success("등록되었습니다!"); st.rerun()
                else: st.warning("정보를 입력하세요.")

# =============================================================================
# [TAB 9] 💧 배관/누수 (NEW! 전문가 모드)
# =============================================================================
with tab9:
    st.header("💧 배관지킴이 (국가공인 배관관리사)")
    st.info("🧑‍🔧 **공인 배관관리사 직접 출동!** 타 업체가 못 잡은 누수, 꼭 잡아드립니다.")
    
    # 서비스 메뉴 (그리드)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class='plumbing-card'><div class='plumbing-icon'>🕵️</div><div class='plumbing-title'>누수 정밀탐지</div><div class='plumbing-desc'>못 찾으면 0원!<br>최첨단 장비 보유</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class='plumbing-card'><div class='plumbing-icon'>🚿</div><div class='plumbing-title'>하수구 막힘</div><div class='plumbing-desc'>고압 세척으로<br>속 시원하게 뻥!</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""<div class='plumbing-card'><div class='plumbing-icon'>❄️</div><div class='plumbing-title'>언 수도 녹임</div><div class='plumbing-desc'>동파 해빙 전문<br>긴급 출동</div></div>""", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 긴급 출동 요청
    st.subheader("🚨 긴급 출동 요청 (24시)")
    st.markdown("배관 문제는 **골든타임**이 중요합니다. 지금 바로 연락 주세요.")
    
    c_call, c_kakao = st.columns(2)
    with c_call:
        st.markdown(f"<a href='tel:{010-3952-8405}' class='footer-btn btn-call' style='width:100%; display:block;'>📞 지금 바로 전화하기</a>", unsafe_allow_html=True)
    with c_kakao:
        st.markdown(f"<a href='{https://open.kakao.com/o/seWGDKVh}' target='_blank' class='footer-btn btn-kakao' style='width:100%; display:block;'>💬 카톡으로 사진 보내기</a>", unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # 신뢰 포인트
    st.success("✅ **국가공인 자격 보유** | ✅ **배상책임보험 가입 업체** | ✅ **카드 결제 환영**")


# 👇 [하단 고정 버튼]
st.markdown(f"""
    <div class='sticky-footer'>
        <a href='tel:{010-3952-8405}' class='footer-btn btn-call'>📞 전화 상담</a>
        <a href='{https://open.kakao.com/o/seWGDKVh}' target='_blank' class='footer-btn btn-kakao'>💬 카톡 문의</a>
    </div>
""", unsafe_allow_html=True)
