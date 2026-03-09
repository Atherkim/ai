import streamlit as st
import requests
import time

st.set_page_config(page_title="AI 전문가 패널 토론", layout="wide")
st.title("⚖️ AI 전문가 패널 & 마스터 비평가")
st.markdown("4개의 서로 다른 AI 전문가가 답변하고, 마스터 AI가 이를 종합 분석합니다.")

try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except KeyError:
    st.error("API 키를 등록해주세요.")
    st.stop()

API_URL = "https://openrouter.ai/api/v1/chat/completions"

# [패널 구성] 각기 다른 가문의 AI들을 배치하여 다양성 확보
PANEL = [
    {"name": "Google Gemma 3", "id": "google/gemma-3-27b-it:free", "role": "논리/분석 전문가"},
    {"name": "NVIDIA Nemotron", "id": "nvidia/nemotron-3-nano-30b-a3b:free", "role": "기술/수학 전문가"},
    {"name": "Arcee Trinity", "id": "arcee-ai/trinity-large-preview:free", "role": "창의/인문 전문가"},
    {"name": "Mistral 7B", "id": "mistralai/mistral-7b-instruct:free", "role": "실용/일반 전문가"}
]

def call_ai(model_id, prompt, user_msg):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": model_id,
        "messages": [{"role": "user", "content": f"{prompt}\n\n질문: {user_msg}"}],
        "temperature": 0.5
    }
    try:
        resp = requests.post(API_URL, headers=headers, json=data, timeout=25)
        if resp.status_code == 200:
            content = resp.json().get('choices', [{}])[0].get('message', {}).get('content')
            return content.strip() if content else None
    except: return None
    return None

# 메모리 초기화
if "panel_answers" not in st.session_state:
    st.session_state.panel_answers = {}

user_input = st.text_input("토론 주제를 입력하세요:", placeholder="예: 인공지능 시대에 인간의 가치는 무엇인가?")

if st.button("전문가 패널 토론 시작") and user_input:
    st.session_state.panel_answers = {}
    
    # 1단계: 4개의 AI에게 동시에 질문 던지기
    cols = st.columns(4)
    for i, ai in enumerate(PANEL):
        with cols[i]:
            with st.spinner(f"🎤 {ai['name']} 발언 중..."):
                answer = call_ai(ai['id'], f"너는 {ai['role']}야. 질문에 대해 너의 관점에서 답변해줘.", user_input)
                if answer:
                    st.session_state.panel_answers[ai['name']] = answer
                    st.success(f"**{ai['name']}**")
                    st.caption(ai['role'])
                    st.write(answer[:200] + "...") # 요약을 위해 앞부분만 살짝 노출
                else:
                    st.error(f"{ai['name']} 연결 실패")

# 2단계: 답변이 모두 모였을 때 마스터 비평가 등판
if st.session_state.panel_answers:
    st.divider()
    if st.button("✨ 마스터 비평가의 종합 판정 보기"):
        with st.spinner("🧠 모든 답변을 교차 분석하여 최적의 합의점을 도출 중입니다..."):
            
            # 비평가를 위한 특별 프롬프트 조립
            critique_prompt = "너는 4명의 전문가 의견을 조율하는 수석 비평가야. 아래 답변들을 읽고 1. 공통점, 2. 차이점, 3. 최종 결론을 정리해줘.\n\n"
            for name, ans in st.session_state.panel_answers.items():
                critique_prompt += f"[{name}의 의견]: {ans}\n\n"
            
            # 가장 성능이 좋은 모델에게 비평을 맡김
            master_summary = call_ai("google/gemma-3-27b-it:free", critique_prompt, "위 내용들을 종합해줘.")
            
            if master_summary:
                st.info("### 📝 마스터 비평가의 종합 분석 리포트")
                st.markdown(master_summary)
                
                # 전체 답변 복사 기능
                full_text = f"주제: {user_input}\n\n[종합 분석]\n{master_summary}\n\n"
                for n, a in st.session_state.panel_answers.items():
                    full_text += f"--- {n} ---\n{a}\n\n"
                st.code(full_text, language="markdown")
