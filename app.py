import streamlit as st
import requests
import time

st.set_page_config(page_title="AI 전문가 패널 토론", layout="wide")
st.title("⚖️ AI 전문가 패널 & 마스터 비평가")
st.markdown("안정성을 위해 패널들이 **순서대로 하나씩** 발언합니다. (서버 과부하 방지)")

try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except KeyError:
    st.error("API 키를 등록해주세요.")
    st.stop()

API_URL = "https://openrouter.ai/api/v1/chat/completions"

# [현재 기준 404 에러가 없는 가장 대중적인 무료 모델 라인업]
PANEL = [
    {"name": "Mistral 7B", "id": "mistralai/mistral-7b-instruct:free", "role": "논리/분석 전문가"},
    {"name": "HuggingFace Zephyr", "id": "huggingfaceh4/zephyr-7b-beta:free", "role": "기술/수학 전문가"},
    {"name": "OpenChat 7B", "id": "openchat/openchat-7b:free", "role": "창의/인문 전문가"},
    {"name": "StepFun 3.5", "id": "stepfun/step-3.5-flash:free", "role": "실용/일반 전문가"}
]

def call_ai(model_id, prompt, user_msg):
    headers = {
        "Authorization": f"Bearer {API_KEY}", 
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "Multi-AI-Panel"
    }
    data = {
        "model": model_id,
        "messages": [{"role": "user", "content": f"{prompt}\n\n질문: {user_msg}"}],
        "temperature": 0.5
    }
    try:
        resp = requests.post(API_URL, headers=headers, json=data, timeout=30)
        if resp.status_code == 200:
            content = resp.json().get('choices', [{}])[0].get('message', {}).get('content')
            return content.strip() if content else None, "빈 답변"
        else:
            return None, f"에러 {resp.status_code}: {resp.text[:50]}"
    except Exception as e:
        return None, f"통신 장애: {str(e)}"

if "panel_answers" not in st.session_state:
    st.session_state.panel_answers = {}
if "master_summary" not in st.session_state:
    st.session_state.master_summary = None

user_input = st.text_input("토론 주제를 입력하세요:", placeholder="예: 무인 자동차의 도덕적 책임은?")

# [1단계] 순차적 토론 진행 (429 에러 방지)
if st.button("전문가 패널 토론 시작") and user_input:
    st.session_state.panel_answers = {}
    st.session_state.master_summary = None
    
    # 레이아웃을 미리 잡아둡니다.
    cols = st.columns(4)
    
    for i, ai in enumerate(PANEL):
        with cols[i]:
            with st.spinner(f"🎤 {ai['name']} 발언 준비 중..."):
                answer, err = call_ai(ai['id'], f"너는 {ai['role']}야. 질문에 대해 너의 관점에서 깊이 있게 답변해줘.", user_input)
                
                if answer:
                    st.session_state.panel_answers[ai['name']] = answer
                    st.success(f"**{ai['name']} 완료**")
                else:
                    st.error(f"**{ai['name']} 실패**")
                    st.caption(err)
                
                # 🚨 핵심: 429 에러를 피하기 위해 다음 AI 호출 전 강제로 3초를 멈춥니다.
                if i < len(PANEL) - 1:
                    time.sleep(3)

if st.session_state.panel_answers:
    st.markdown("### 💬 전문가 개별 의견")
    cols = st.columns(4)
    for i, ai in enumerate(PANEL):
        with cols[i]:
            if ai['name'] in st.session_state.panel_answers:
                st.info(f"**{ai['role']}**\n\n{ai['name']}")
                with st.expander("전체 답변 읽기 ⬇️"):
                    st.write(st.session_state.panel_answers[ai['name']])
    
    st.divider()

    # [2단계] 마스터 비평가
    if st.button("✨ 마스터 비평가의 종합 판정 시작"):
        with st.spinner("🧠 답변들을 교차 분석 중입니다..."):
            critique_prompt = "너는 최고 전문가 의견을 조율하는 수석 비평가야. 아래 답변들을 읽고 1. 핵심 공통점 2. 주요 차이점 3. 최종 결론으로 정리해.\n\n"
            for name, ans in st.session_state.panel_answers.items():
                critique_prompt += f"[{name}의 의견]: {ans}\n\n"
            
            # 비평가도 안 터지는 모델로 고정
            summary_ans, summary_err = call_ai("mistralai/mistral-7b-instruct:free", critique_prompt, f"주제: {user_input}\n위 내용들을 종합해줘.")
            
            if summary_ans:
                st.session_state.master_summary = summary_ans
            else:
                st.error(f"🚨 마스터 비평가 연결 실패: {summary_err}")

    if st.session_state.master_summary:
        st.success("### 📝 마스터 비평가의 종합 분석 리포트")
        st.markdown(st.session_state.master_summary)
        
        full_text = f"주제: {user_input}\n\n[종합 분석 리포트]\n{st.session_state.master_summary}\n\n"
        for n, a in st.session_state.panel_answers.items():
            full_text += f"--- {n} ---\n{a}\n\n"
        
        st.caption("👇 전체 내용 복사하기")
        st.code(full_text, language="markdown")
