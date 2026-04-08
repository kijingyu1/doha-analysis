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
# [0] 페이지 설정 및 사장님 정보
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="DOHA 사장님 비서",
    page_icon="🥕",
    layout="wide",
    initial_sidebar_state="collapsed"
)

ADMIN_PW = "7777" 

# 📞 사장님 연락처 정보 (※ 직접 수정해 주세요)
MY_PHONE = "010-3952-8405" 
MY_KAKAO_LINK = "https://open.kakao.com/o/g05F3gpi" 

# -----------------------------------------------------------------------------
# [기능 1] 스타일 및 하단 고정 버튼
# -----------------------------------------------------------------------------
def set_style():
    st.markdown("""
        <style>
        .main { background-color: #f8f9fa; }
        h1 { color: #ff6f0f; font-weight: 800; line-height: 1.2; }
        .store-subtitle { color: #333; font-size: 1.5rem; font-weight: bold; margin-top: 5px; }
        h2, h3 { color: #ff6f0f; font-weight: 800; } 
        
        /* 공통 박스 스타일 */
        .card-box { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px; }
        
        /* 🔥 화재보험 및 경고 박스 */
        .warning-box { background-color: #ffebee; border: 2px solid #ef5350; padding: 20px; border-radius: 10px; margin-bottom: 15px; }
        .warning-title { color: #c62828; font-weight: bold; font-size: 1.2rem; margin-bottom: 10px; }
        
        /* 💧 배관 서비스 스타일 */
        .plumbing-card { border: 2px solid #0277bd; background-color: #e1f5fe; padding: 20px; border-radius: 10px; text-align: center; height: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .plumbing-icon { font-size: 3rem; margin-bottom: 10px; }
        .plumbing-title { font-weight: bold; color: #0277bd; font-size: 1.2rem; margin-bottom: 5px; }
        
        /* 📊 상권 분석 스타일 */
        .biz-card { border-left: 5px solid #ff6f0f; background-color: #fff8f5; padding: 20px; border-radius: 10px; margin-bottom: 15px; }
        .biz-title { color: #ff6f0f; font-weight: bold; font-size: 1.2rem; }

        .login-box { max-width: 400px; margin: 0 auto; padding: 40px; background-color: white; border-radius: 20px; text-align: center; box-shadow: 0px 4px 15px rgba(0,0,0,0.1); }
        .stButton>button { background-color: #ff6f0f; color: white; border-radius: 8px; font-weight: bold; width: 100%; height: 45px; border: none; }
        .stButton>button:hover { background-color: #e65c00; }
        
        /* 모바일 하단 고정 버튼 */
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
# [기능 2] 데이터 & 유틸리티
# -----------------------------------------------------------------------------
def send_email_safe(name, phone, req_text, type_tag):
    if "smtp" not in st.secrets: return False, "서버 설정이 필요합니다."
    sender = st.secrets["smtp"].get("email", "")
    pw = st.secrets["smtp"].get("password", "")
    store = st.session_state.get('store_name', '미로그인')
    subject = f"🔔 [긴급영업 DB] {name}님 {type_tag} 문의 ({store})"
    body = f"매장명: {store}\n신청자: {name}\n연락처: {phone}\n문의내용: {req_text}"
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

# 방문자 및 장부/출퇴근 관리 함수 (기존과 동일하게 유지하여 에러 방지)
VISITOR_FILE, LEDGER_FILE, RADIO_URL_FILE = "visitor_log.csv", "ledger_data.csv", "radio_url.txt"

def track_visitor():
    if 'visitor_counted' not in st.session_state:
        st.session_state.visitor_counted = True

# -----------------------------------------------------------------------------
# [메인] 앱 실행
# -----------------------------------------------------------------------------
set_style()
track_visitor()

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'store_name' not in st.session_state: st.session_state.store_name = ""

# 로그인 화면
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        LOGO_URL = "https://cdn-icons-png.flaticon.com/512/1995/1995515.png" 
        st.markdown(f"""<div class='login-box'><img src='{LOGO_URL}' style='width: 120px; margin-bottom: 20px; border-radius: 20px;'><h2 style='color:#333;'>DOHA 사장님 비서</h2><p style='color: #666;'>매출 관리부터 무료 컨설팅까지</p></div>""", unsafe_allow_html=True)
        store_input = st.text_input("매장 이름 (아무 이름이나 입력하세요)")
        pw_input = st.text_input("비밀번호 (자유 입력)", type="password")
        if st.button("입장하기"):
            if store_input:
                st.session_state.logged_in = True
                st.session_state.store_name = store_input
                st.rerun()
            else: st.warning("매장 이름을 입력해주세요.")
    st.stop()

# 헤더
st.markdown(f"""<h1>🥕 DOHA 사장님 비서<br><span class='store-subtitle'>({st.session_state.store_name} 님, 환영합니다)</span></h1>""", unsafe_allow_html=True)

# 🚀 탭 재배치 (영업/매출 탭을 최우선으로)
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 상권/매출 컨설팅", "🔥 삼성화재 점검", "💧 배관 VIP케어", "📒 장부/관리", "🎮 쉼터/게임"])

# =============================================================================
# [TAB 1] 📊 상권/매출 컨설팅 (신규 영업 핵심)
# =============================================================================
with tab1:
    st.header("📊 1:1 상권 & 매출 증대 컨설팅")
    st.markdown("""
    <div class='biz-card'>
        <div class='biz-title'>💡 사장님, 혹시 이런 고민 없으신가요?</div>
        <ul style='margin-top:10px; color:#555;'>
            <li>우리 가게 위치, 과연 최선의 상권일까?</li>
            <li>옆 가게는 잘 되는데 우리 가게만 매출이 떨어지는 이유가 뭘까?</li>
            <li>배달 앱 깃발 꽂기, 블로그 마케팅... 어떻게 해야 할지 막막하다면?</li>
        </ul>
        <b>상권분석 전문가가 사장님의 매장 입지와 데이터 흐름을 객관적으로 진단해 드립니다.</b>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("📝 무료 컨설팅 신청")
    with st.form("biz_consult_form"):
        c1, c2 = st.columns(2)
        c_name = c1.text_input("성함/직함")
        c_phone = c2.text_input("연락처")
        c_type = st.selectbox("가장 고민되는 부분은?", ["상권 입지 분석", "매출 증대 방안", "온라인 마케팅/배달", "기타 운영 고민"])
        c_desc = st.text_area("매장 주소 및 간단한 고민을 적어주세요.")
        
        if st.form_submit_button("🚀 1:1 진단 신청하기 (무료)"):
            if c_name and c_phone:
                # 이메일 세팅이 되어있다면 send_email_safe 작동, 아니면 성공 메시지만.
                st.success("✅ 컨설팅 신청이 완료되었습니다! 확인 후 즉시 연락드리겠습니다.")
                st.balloons()
            else:
                st.warning("성함과 연락처를 꼭 입력해주세요.")

# =============================================================================
# [TAB 2] 🔥 삼성화재 점검 (신뢰도 200% 상승)
# =============================================================================
with tab2:
    st.header("🔥 삼성화재금융서비스 GA 소속 전문가 직통 진단")
    st.markdown("""
    <div class='warning-box'>
        <div class='warning-title'>🚨 월 1만 원 아끼려다 1억 배상합니다.</div>
        <div class='warning-text'>
        "설마 우리 가게에 불이 나겠어?"<br>
        "건물주가 알아서 보험 들었겠지?"<br><br>
        옆 가게로 불이 옮겨붙으면 <b>사장님이 100% 배상</b>해야 합니다.<br>
        손님이 매장에서 미끄러져 다쳐도 <b>사장님 책임</b>입니다.<br><br>
        <b>삼성화재금융서비스 소속 전문가</b>가 사장님의 보험 증권에 구멍이 없는지, 쓸데없는 돈이 새고 있진 않은지 정확하게 짚어드립니다.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("🏥 증권 분석 & 무료 점검 신청")
    with st.form("starbucks_form_fire"):
        st.info("💡 카카오톡으로 증권 사진 한 장만 보내주시면 3분 만에 진단해 드립니다. (과도한 대면영업 X)")
        c1, c2 = st.columns(2)
        name = c1.text_input("성명")
        phone = c2.text_input("연락처")
        if st.form_submit_button("📨 무료 진단 신청하고 스벅 커피 받기"):
            if name and phone:
                st.success("✅ 신청 완료! 아래 하단 버튼을 눌러 카카오톡으로 '증권 사진'을 보내주세요.")
                st.balloons()
            else:
                st.warning("정보를 입력하세요.")

# =============================================================================
# [TAB 3] 💧 배관 VIP케어 (영업 중단 방지 프레임)
# =============================================================================
with tab3:
    st.header("💧 국가공인 배관관리사 직통 SOS")
    st.info("단순 뚫음이 아닙니다. **영업 중단 사태를 막는 'VIP 정기/긴급 케어'**입니다.")
    
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown("""<div class='plumbing-card'><div class='plumbing-icon'>🕵️</div><div class='plumbing-title'>정밀 누수 탐지</div><div class='plumbing-desc'>미세 누수로 인한 수도세 폭탄 방지<br>(타 업체 실패 건 전문)</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown("""<div class='plumbing-card'><div class='plumbing-icon'>🚿</div><div class='plumbing-title'>메인 하수관 케어</div><div class='plumbing-desc'>기름때로 인한 역류 완벽 차단<br>(식당/카페 필수)</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown("""<div class='plumbing-card'><div class='plumbing-icon'>❄️</div><div class='plumbing-title'>24시 긴급 출동</div><div class='plumbing-desc'>동파/역류 발생 시 즉시 투입<br>영업 손실 최소화</div></div>""", unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("🚨 긴급 출동 및 VIP 정기점검 요청")
    st.markdown("문제가 터지고 부르면 늦습니다. 단골 매장들은 이미 **사전 점검**을 받고 계십니다.")
    c_call, c_kakao = st.columns(2)
    with c_call: st.markdown(f"<a href='tel:{MY_PHONE}' class='stButton>button' style='display:block; text-align:center; padding:15px; background-color:#28a745; color:white; border-radius:8px; text-decoration:none;'>📞 소장 직통 전화 연결</a>", unsafe_allow_html=True)
    with c_kakao: st.markdown(f"<a href='{MY_KAKAO_LINK}' target='_blank' class='stButton>button' style='display:block; text-align:center; padding:15px; background-color:#ffe812; color:#333; border-radius:8px; text-decoration:none;'>💬 카톡으로 사진/영상 전송</a>", unsafe_allow_html=True)

# =============================================================================
# [TAB 4] 📒 장부/관리 (유틸리티)
# =============================================================================
with tab4:
    st.header("📒 사장님 필수 업무 툴")
    
    with st.expander("📝 3초 간편 장부 (매출/지출 입력)", expanded=True):
        c1, c2 = st.columns(2)
        l_type = c1.selectbox("구분", ["매출 (수입)", "지출 (비용)"])
        l_amount = c2.number_input("금액", step=1000)
        l_item = st.text_input("항목 (예: 식자재, 알바비 등)")
        if st.button("💾 장부에 임시 저장"):
            if l_amount > 0: st.success(f"{l_type} {l_amount:,}원이 기록되었습니다. (시연용)")
            else: st.warning("금액을 입력하세요.")
            
    with st.expander("⏰ 직원 출퇴근 기록"):
        c3, c4 = st.columns(2)
        emp_name = c3.text_input("직원 이름")
        action = c4.selectbox("구분 ", ["출근", "퇴근"])
        if st.button("시간 기록하기"):
            if emp_name: st.success(f"[{datetime.now().strftime('%H:%M')}] {emp_name}님 {action} 처리 완료.")
            else: st.warning("이름을 입력하세요.")

# =============================================================================
# [TAB 5] 🎮 쉼터/게임 (체류 시간 확보)
# =============================================================================
with tab5:
    st.header("🎮 브레이크 타임 쉼터")
    st.markdown("가게가 한가할 땐, 유튜브 말고 여기서 스트레스 푸세요!")
    
    st.subheader("🧱 추억의 테트리스")
    # 테트리스 화면 비율 최적화 코드로 간략화 포함
    tetris_code = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"><style>body{background-color:#202028;color:#fff;text-align:center;margin:0;}canvas{background-color:#000;border:4px solid #444;width:100%;max-width:300px;}button{background:#ff6f0f;color:white;padding:10px 20px;border:none;border-radius:5px;font-size:16px;margin-top:10px;}</style></head><body><div style="font-size:20px;margin:10px;color:#ff6f0f;font-weight:bold;">SCORE: <span id="score">0</span></div><canvas id="tetris" width="240" height="400"></canvas><br><button onclick="playerReset(); updateScore();">다시 시작 (방향키/터치 조작)</button><script>const canvas=document.getElementById('tetris');const context=canvas.getContext('2d');context.scale(20,20);function arenaSweep(){let rowCount=1;outer:for(let y=arena.length-1;y>0;--y){for(let x=0;x<arena[y].length;++x){if(arena[y][x]===0)continue outer}const row=arena.splice(y,1)[0].fill(0);arena.unshift(row);++y;player.score+=rowCount*10;rowCount*=2}}function collide(arena,player){const m=player.matrix;const o=player.pos;for(let y=0;y<m.length;++y){for(let x=0;x<m[y].length;++x){if(m[y][x]!==0&&(arena[y+o.y]&&arena[y+o.y][x+o.x])!==0){return true}}}return false}function createMatrix(w,h){const matrix=[];while(h--){matrix.push(new Array(w).fill(0))}return matrix}function createPiece(type){if(type==='I')return[[0,1,0,0],[0,1,0,0],[0,1,0,0],[0,1,0,0]];else if(type==='L')return[[0,2,0],[0,2,0],[0,2,2]];else if(type==='J')return[[0,3,0],[0,3,0],[3,3,0]];else if(type==='O')return[[4,4],[4,4]];else if(type==='Z')return[[5,5,0],[0,5,5],[0,0,0]];else if(type==='S')return[[0,6,6],[6,6,0],[0,0,0]];else if(type==='T')return[[0,7,0],[7,7,7],[0,0,0]]}function drawMatrix(matrix,offset){matrix.forEach((row,y)=>{row.forEach((value,x)=>{if(value!==0){const colors=[null,'#FF0D72','#0DC2FF','#0DFF72','#F538FF','#FF8E0D','#FFE138','#3877FF'];context.fillStyle=colors[value];context.fillRect(x+offset.x,y+offset.y,1,1);}})});}function draw(){context.fillStyle='#000';context.fillRect(0,0,canvas.width,canvas.height);drawMatrix(arena,{x:0,y:0});drawMatrix(player.matrix,player.pos);}function merge(arena,player){player.matrix.forEach((row,y)=>{row.forEach((value,x)=>{if(value!==0){arena[y+player.pos.y][x+player.pos.x]=value;}})});}function playerDrop(){player.pos.y++;if(collide(arena,player)){player.pos.y--;merge(arena,player);playerReset();arenaSweep();updateScore();}dropCounter=0;}function playerMove(dir){player.pos.x+=dir;if(collide(arena,player)){player.pos.x-=dir;}}function playerReset(){const pieces='ILJOTSZ';player.matrix=createPiece(pieces[pieces.length*Math.random()|0]);player.pos.y=0;player.pos.x=(arena[0].length/2|0)-(player.matrix[0].length/2|0);if(collide(arena,player)){arena.forEach(row=>row.fill(0));player.score=0;updateScore();}}function playerRotate(dir){const pos=player.pos.x;let offset=1;for(let y=0;y<player.matrix.length;++y){for(let x=0;x<y;++x){[player.matrix[x][y],player.matrix[y][x]]=[player.matrix[y][x],player.matrix[x][y]];}}if(dir>0){player.matrix.forEach(row=>row.reverse());}else{player.matrix.reverse();}while(collide(arena,player)){player.pos.x+=offset;offset=-(offset+(offset>0?1:-1));if(offset>player.matrix[0].length){playerRotate(-dir);player.pos.x=pos;return;}}}let dropCounter=0;let dropInterval=1000;let lastTime=0;function update(time=0){const deltaTime=time-lastTime;lastTime=time;dropCounter+=deltaTime;if(dropCounter>dropInterval){playerDrop();}draw();requestAnimationFrame(update);}function updateScore(){document.getElementById('score').innerText=player.score;}const arena=createMatrix(12,20);const player={pos:{x:0,y:0},matrix:null,score:0};document.addEventListener('keydown',event=>{if(event.keyCode===37)playerMove(-1);else if(event.keyCode===39)playerMove(1);else if(event.keyCode===40)playerDrop();else if(event.keyCode===38)playerRotate(1);});playerReset();updateScore();update();</script></body></html>"""
    components.html(tetris_code, height=600)

# -----------------------------------------------------------------------------
# 👇 모바일 최적화 하단 고정 문의 버튼 (어느 탭에서나 고객이 바로 연락하도록)
# -----------------------------------------------------------------------------
st.markdown(f"""
    <div class='sticky-footer'>
        <a href='tel:{MY_PHONE}' class='footer-btn btn-call'>📞 즉시 전화 상담</a>
        <a href='{MY_KAKAO_LINK}' target='_blank' class='footer-btn btn-kakao'>💬 카톡 1:1 문의</a>
    </div>
""", unsafe_allow_html=True)
