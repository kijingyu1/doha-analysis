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
        .stButton>button { 
            background-color: #ff6f0f; color: white; border-radius: 8px; 
            font-weight: bold; width: 100%; height: 45px; border: none;
        }
        .stButton>button:hover { background-color: #e65c00; }
        
        /* 스타벅스 이벤트 스타일 */
        .event-box {
            background-color: #1e3932; color: white; padding: 20px; border-radius: 10px;
            text-align: center; margin-bottom: 20px;
        }
        .small-text { font-size: 0.8rem; color: #666; margin-top: 5px; }
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
    -------------------------
    * 스타벅스 쿠폰 지급 대상자입니다.
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
# [기능 3] 데이터 유틸리티 (운세, 농산물, 출퇴근)
# -----------------------------------------------------------------------------
def get_agri_price():
    # 시뮬레이션 데이터
    items = ["배추(1포기)", "무(1개)", "양파(1kg)", "대파(1kg)", "청상추(100g)"]
    prices = {}
    for item in items:
        base = random.randint(1500, 5000)
        change = random.randint(-500, 500)
        prices[item] = {"price": base, "change": change}
    return prices

def get_today_fortune():
    fortunes = [
        "오늘은 귀인을 만날 운세입니다. 손님에게 밝게 인사하세요!",
        "재물운이 상승하는 날입니다. 재고 관리를 철저히 하세요.",
        "뜻밖의 지출이 생길 수 있으니 꼼꼼히 체크하세요.",
        "경쟁자보다 앞서 나가는 아이디어가 떠오를 겁니다.",
        "건강이 최고입니다. 바쁘더라도 식사는 챙기세요."
    ]
    return random.choice(fortunes)

# 출퇴근부 CSV 저장/로드 함수
CSV_FILE = "attendance_log.csv"

def load_attendance():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    return pd.DataFrame(columns=["일시", "직원명", "구분"])

def save_attendance(name, action):
    df = load_attendance()
    new_row = {
        "일시": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "직원명": name,
        "구분": action
    }
    # pandas concat 사용 (append는 구버전)
    df = pd.concat([pd.DataFrame([new_row]), df], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)
    return df

# -----------------------------------------------------------------------------
# [메인] 앱 실행
# -----------------------------------------------------------------------------
set_style()

st.title("🥕 DOHA 사장님 비서")
st.caption(f"오늘 날짜: {datetime.now().strftime('%Y년 %m월 %d일')}")

tab1, tab2, tab3, tab4 = st.tabs(["🏠 데일리 홈", "🔍 전국 당근검색", "⏰ 직원 출퇴근", "☕ 보험/고정비 진단"])

# =============================================================================
# [TAB 1] 데일리 홈 (좌우 분할)
# =============================================================================
with tab1:
    col_left, col_right = st.columns(2)
    
    # [왼쪽] 운세 + 농산물
    with col_left:
        st.subheader("🍀 오늘의 장사 운세")
        st.info(f"Today: {get_today_fortune()}")
        
        st.markdown("---")
        st.subheader("🥬 실시간 농산물 도매가")
        agri = get_agri_price()
        for item, val in agri.items():
            color = "red" if val['change'] > 0 else "blue"
            sign = "▲" if val['change'] > 0 else "▼"
            st.markdown(f"**{item}**: {val['price']:,}원 <span style='color:{color}'>({sign}{abs(val['change'])})</span>", unsafe_allow_html=True)

    # [오른쪽] 일일 목표 매출 계산기 (자동계산 기능 탑재)
    with col_right:
        st.subheader("🧮 스마트 매출 계산기")
        st.markdown("""<div class='metric-card'>월세/인건비를 입력하면 <b>오늘 목표치</b>를 계산해드립니다.</div>""", unsafe_allow_html=True)
        
        # 입력
        c1, c2 = st.columns(2)
        month_fixed = c1.number_input("월 고정비 합계 (월세+인건비 등)", value=4500000, step=10000, help="월세, 관리비, 인건비, 보험료 등을 모두 합친 금액")
        days = c2.number_input("영업 일수 (기준)", value=30, step=1)
        
        # 자동 계산: 일일 고정비
        daily_fixed = month_fixed / days
        st.markdown(f"👉 사장님은 숨만 쉬어도 하루에 **{int(daily_fixed):,}원**이 나갑니다.")
        
        margin = st.slider("내 가게 평균 마진율 (%)", 10, 50, 25)
        
        # 목표 매출 계산 (고정비 / 마진율)
        target_sales = daily_fixed / (margin / 100)
        
        st.success(f"💰 오늘 **최소 {int(target_sales):,}원** 팔아야 본전(BEP)입니다!")
        
        # 개선 항목 (영업이익 시뮬레이션)
        st.markdown("---")
        st.markdown("#### 📈 수익 개선 시뮬레이션")
        st.markdown("만약 화재보험 리모델링 등으로 **월 고정비를 10% 줄인다면?**")
        
        saved_cost = month_fixed * 0.1
        yearly_profit = saved_cost * 12
        
        st.markdown(f"""
        - 하루 부담금이 **{int(daily_fixed * 0.9):,}원**으로 줄어듭니다.
        - 같은 매출일 때, 연간 **{int(yearly_profit):,}원**의 추가 순이익이 생깁니다.
        """)
        st.caption("👉 고정비를 줄이는 가장 쉬운 방법은 '보험료 다이어트' 입니다. (4번 탭 확인)")

# =============================================================================
# [TAB 2] 전국 당근 검색 (오류 수정됨)
# =============================================================================
with tab2:
    st.header("🥕 당근마켓 전국 매물 찾기")
    st.markdown("우리 동네에 없는 물건, **전국 당근마켓**을 뒤져서 찾아드립니다.")
    
    keyword = st.text_input("찾으시는 물건 (예: 업소용 냉장고, 포스기)", "")
    
    if st.button("🔍 전국 검색 시작"):
        if keyword:
            # 구글 검색 URL 인코딩 문제 해결
            query = f"site:daangn.com {keyword}"
            url = f"https://www.google.com/search?q={query}"
            
            st.markdown(f"""
            <br>
            <a href="{url}" target="_blank" style="
                background-color: #ff6f0f; color: white; padding: 15px 30px; 
                text-decoration: none; border-radius: 10px; font-weight: bold; font-size: 1.2rem; display: block; text-align: center;">
                👉 '{keyword}' 검색 결과 보기 (새창)
            </a>
            <br>
            """, unsafe_allow_html=True)
            st.info("※ 위 버튼을 누르면 구글 검색 결과로 연결됩니다. (전국 당근마켓 게시글 표시)")
        else:
            st.warning("검색어를 입력해주세요.")

# =============================================================================
# [TAB 3] 직원 출퇴근 (CSV 장기 저장)
# =============================================================================
with tab3:
    st.header("⏰ 직원 출퇴근 기록부")
    st.info("이제 새로고침해도 지워지지 않고 **계속 저장**됩니다.")
    
    c1, c2 = st.columns(2)
    emp_name = c1.text_input("직원 이름")
    action = c2.selectbox("구분", ["출근", "퇴근", "외출", "복귀"])
    
    if st.button("💾 기록 저장"):
        if emp_name:
            save_attendance(emp_name, action)
            st.success(f"{emp_name}님 {action} 처리되었습니다.")
            st.rerun() # 화면 갱신
        else:
            st.warning("이름을 입력해주세요.")
            
    st.markdown("---")
    st.subheader("📝 최근 3개월 기록")
    
    # 기록 불러오기
    df_log = load_attendance()
    if not df_log.empty:
        st.dataframe(df_log, use_container_width=True)
        
        # 다운로드 버튼
        csv = df_log.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 엑셀(CSV)로 다운로드", csv, "attendance.csv", "text/csv")
    else:
        st.write("아직 기록이 없습니다.")

# =============================================================================
# [TAB 4] 보험 진단 (스타벅스 이벤트)
# =============================================================================
with tab4:
    st.markdown("""
    <div class='event-box'>
    <h2>☕ 스타벅스 커피 100% 증정 이벤트</h2>
    <b>"사장님, 화재보험 점검 받으시고 커피 한잔 하세요!"</b><br>
    상담만 받아도 조건 없이 드립니다. (선착순 진행 중)
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("🏥 왜 '화재보험 점검'이 필요할까요?")
    st.markdown("""
    1. **법이 바뀌었습니다:** 예전 보험으로는 과태료를 물거나 보상을 못 받을 수 있습니다.
    2. **줄줄 새는 돈:** 옆 가게보다 비싸게 내고 있다면, 그 차액만 모아도 1년에 50만 원입니다.
    3. **배상책임:** 손님이 넘어져서 다쳤을 때, 보험이 없다면 사장님 생돈으로 물어주셔야 합니다.
    """)
    
    st.markdown("---")
    st.subheader("📋 부담 없는 카카오톡 상담 신청")
    st.info("전화가 부담스러우신가요? **카카오톡으로 먼저 가볍게** 상담해드립니다.")
    
    with st.form("starbucks_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("성명 (필수)")
        phone = c2.text_input("연락처 (필수)")
        
        agree = st.checkbox("(필수) 개인정보 수집 및 이용에 동의합니다.")
        st.markdown("<div class='small-text'>* 수집된 정보는 상담 및 쿠폰 발송 목적으로만 사용됩니다.</div>", unsafe_allow_html=True)
        
        if st.form_submit_button("📨 상담 신청하고 스타벅스 받기"):
            if not agree:
                st.warning("개인정보 동의가 필요합니다.")
            elif not name or not phone:
                st.warning("성명과 연락처를 입력해주세요.")
            else:
                s, m = send_email_safe(name, phone, "미입력", "스타벅스 이벤트 참여", "화재보험 상담")
                if s:
                    st.balloons()
                    st.success("✅ 신청이 완료되었습니다!")
                    st.markdown("""
                    **[향후 절차 안내]**
                    1. 전문 상담사가 **카카오톡**으로 먼저 인사를 드립니다.
                    2. 간단한 **10분 진단 상담** (전화 또는 대면)을 진행합니다.
                    3. 상담 완료 후 **3일 이내** 기재하신 번호로 **스타벅스 쿠폰**을 발송해 드립니다.
                    """)
                else:
                    st.error(f"전송 오류: {m}")
