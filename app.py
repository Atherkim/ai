import streamlit as st
import requests

st.set_page_config(page_title="AI 전문가 패널 토론", layout="wide")
st.title("⚖️ AI 전문가 패널 & 마스터 비평가")
st.markdown("4명의 전문가가 의견을 내고, 마스터 비평가가 합의점을 도출합니다.")

try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except KeyError:
    st.error("API 키를 등록해주세요.")
    st.stop()

API_URL = "https://openrouter.ai/api/v1/chat/completions"

# [안정성이 검증된 패널 4인방]
PANEL = [
    {"name": "Google Gemma 3", "id": "google/gemma-3-27b-it:free", "role": "논리/분석 전문가"},
    {"name": "NVIDIA Nemotron", "id": "nvidia/nemotron-3-nano-30b-a3b:free", "role": "기술/수학 전문가"},
    {"name": "Arcee Trinity", "id": "arcee-ai/trinity-large-preview:free", "role": "창의/인문 전문가"},
    {"name": "StepFun 3.5", "id": "stepfun/step-3.5-flash:free", "role": "실용/일반 전문가"}
]

def call_ai(model_id, prompt, user_msg):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": model_id,
        "messages": [{"role": "user", "content": f"{prompt}\n\n질문: {user_msg}"}],
        "temperature": 0.5
    }
    try:
        resp = requests.post(API_URL, headers=headers, json=data, timeout=30)
        if resp.status_code == 200:
            content = resp.json().get('choices', [{}])[0].get('message', {}).get('content')
            return content.strip() if content else "빈 답변이 도착했습니다."
        else:
            return f"에러코드 {resp.status_code}: 서버 지연"
    except Exception as e:
        return f"통신 장애: {str(e)}"

# 🚨 메모리(Session State) 사전 정의: 버튼을 눌러도 데이터가 날아가지 않게 꽉 잡아줍니다.
if "panel_answers" not in st.session_state:
    st.session_state.panel_answers = {}
if "master_summary" not in st.session_state:
    st.session_state.master_summary = None

user_input = st.text_input("토론 주제를 입력하세요:", placeholder="예: 무인 자동차의 도덕적 책임은 누구에게 있는가?")

# [1단계 버튼] 전문가 토론 시작
if st.button("전문가 패널 토론 시작") and user_input:
    # 새 질문을 던지면 기존 기억을 지웁니다.
    st.session_state.panel_answers = {}
    st.session_state.master_summary = None
    
    cols = st.columns(4)
    for i, ai in enumerate(PANEL):
        with cols[i]:
            with st.spinner(f"🎤 {ai['name']} 생각 중..."):
                answer = call_ai(ai['id'], f"너는 {ai['role']}야. 질문에 대해 너의 관점에서 깊이 있게 답변해줘.", user_input)
                # 에러가 나든 성공하든 무조건 메모리에 저장합니다.
                st.session_state.panel_answers[ai['name']] = answer
                st.success(f"**{ai['name']} 답변 완료**")

# 🚨 Streamlit 구조 최적화: 버튼 바깥으로 결과 화면을 빼내어 새로고침 에러를 방지합니다.
if st.session_state.panel_answers:
    st.markdown("### 💬 전문가 4인의 개별 의견")
    
    # 펼쳐보기(Expander) UI 적용
    cols = st.columns(4)
    for i, ai in enumerate(PANEL):
        with cols[i]:
            ans = st.session_state.panel_answers.get(ai['name'], "답변 없음")
            st.info(f"**{ai['role']}**\n\n{ai['name']}")
            # 사용자 아이디어 적용: 버튼을 누를 때만 내용이 펼쳐지도록 깔끔하게 정리
            with st.expander("전체 답변 읽기 ⬇️"):
                st.write(ans)
    
    st.divider()

    # [2단계 버튼] 마스터 비평가의 판단
    if st.button("✨ 마스터 비평가의 종합 판정 시작"):
        with st.spinner("🧠 답변들을 교차 분석하여 최적의 합의점을 도출 중입니다..."):
            
            critique_prompt = "너는 4명의 최고 전문가 의견을 조율하는 수석 비평가야. 아래 4개의 답변들을 읽고 다음 구조로 정리해.\n1. 핵심 공통점\n2. 주요 차이점\n3. 최종 결론 및 권고사항\n\n"
            for name, ans in st.session_state.panel_answers.items():
                critique_prompt += f"[{name}의 의견]: {ans}\n\n"
            
            summary = call_ai("google/gemma-3-27b-it:free", critique_prompt, f"주제: {user_input}\n위 내용들을 종합해줘.")
            st.session_state.master_summary = summary

    # 마스터 비평가의 결과가 메모리에 있다면 화면에 표시
    if st.session_state.master_summary:
        st.success("### 📝 마스터 비평가의 종합 분석 리포트")
        st.markdown(st.session_state.master_summary)
        
        # 클립보드 복사 기능
        full_text = f"주제: {user_input}\n\n[종합 분석 리포트]\n{st.session_state.master_summary}\n\n"
        for n, a in st.session_state.panel_answers.items():
            full_text += f"--- {n} ---\n{a}\n\n"
        
        st.caption("👇 전체 내용 한 번에 복사하기")
        st.code(full_text, language="markdown")
