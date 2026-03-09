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

# [안정성이 검증된 튼튼한 패널 4인방으로 전면 교체]
PANEL = [
    {"name": "Google Gemma 3 (4B)", "id": "google/gemma-3-4b-it:free", "role": "논리/분석 전문가"},
    {"name": "Mistral 7B", "id": "mistralai/mistral-7b-instruct:free", "role": "기술/수학 전문가"},
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
            if content:
                return content.strip(), None
            else:
                return None, "빈 답변 도착"
        else:
            return None, f"에러 {resp.status_code}"
    except Exception as e:
        return None, f"통신 장애: {str(e)}"

if "panel_answers" not in st.session_state:
    st.session_state.panel_answers = {}
if "master_summary" not in st.session_state:
    st.session_state.master_summary = None

user_input = st.text_input("토론 주제를 입력하세요:", placeholder="예: 무인 자동차의 도덕적 책임은 누구에게 있는가?")

# [1단계 버튼] 전문가 토론 시작
if st.button("전문가 패널 토론 시작") and user_input:
    st.session_state.panel_answers = {}
    st.session_state.master_summary = None
    
    cols = st.columns(4)
    for i, ai in enumerate(PANEL):
        with cols[i]:
            with st.spinner(f"🎤 {ai['name']} 대기 중..."):
                answer, err = call_ai(ai['id'], f"너는 {ai['role']}야. 질문에 대해 너의 관점에서 깊이 있게 답변해줘.", user_input)
                
                if answer:
                    st.session_state.panel_answers[ai['name']] = answer
                    st.success(f"**{ai['name']} 완료**")
                else:
                    st.error(f"**{ai['name']} 실패**")
                    st.caption(err)

if st.session_state.panel_answers:
    st.markdown("### 💬 전문가 4인의 개별 의견")
    
    cols = st.columns(4)
    for i, ai in enumerate(PANEL):
        with cols[i]:
            if ai['name'] in st.session_state.panel_answers:
                st.info(f"**{ai['role']}**\n\n{ai['name']}")
                with st.expander("전체 답변 읽기 ⬇️"):
                    st.write(st.session_state.panel_answers[ai['name']])
            else:
                st.warning(f"**{ai['role']}**\n\n{ai['name']} (참여 실패)")
    
    st.divider()

    # [2단계 버튼] 마스터 비평가의 판단
    if st.button("✨ 마스터 비평가의 종합 판정 시작"):
        with st.spinner("🧠 성공적으로 도착한 답변들을 교차 분석 중입니다..."):
            
            critique_prompt = "너는 최고 전문가 의견을 조율하는 수석 비평가야. 아래 답변들을 읽고 다음 구조로 정리해.\n1. 핵심 공통점\n2. 주요 차이점\n3. 최종 결론 및 권고사항\n\n"
            for name, ans in st.session_state.panel_answers.items():
                critique_prompt += f"[{name}의 의견]: {ans}\n\n"
            
            # 🚨 비평가 전용 3중 자동 백업(Failover) 시스템 도입
            CRITIC_MODELS = [
                "google/gemma-3-4b-it:free",          # 1순위 비평가
                "mistralai/mistral-7b-instruct:free", # 2순위 비평가
                "stepfun/step-3.5-flash:free"         # 3순위 비평가
            ]
            
            summary_ans, summary_err = None, None
            
            for critic in CRITIC_MODELS:
                summary_ans, summary_err = call_ai(critic, critique_prompt, f"주제: {user_input}\n위 내용들을 종합해줘.")
                if summary_ans:
                    break # 성공하면 즉시 비평가 탐색 종료
                else:
                    # 실패할 경우 화면에 어떤 비평가가 실패했는지 짧게 안내하고 다음으로 넘어감
                    st.warning(f"⚠️ {critic.split('/')[1]} 서버 과부하. 다음 비평가에게 서류를 넘깁니다...")
            
            if summary_ans:
                st.session_state.master_summary = summary_ans
            else:
                st.error(f"🚨 모든 마스터 비평가 연결 실패: {summary_err}")

    if st.session_state.master_summary:
        st.success("### 📝 마스터 비평가의 종합 분석 리포트")
        st.markdown(st.session_state.master_summary)
        
        full_text = f"주제: {user_input}\n\n[종합 분석 리포트]\n{st.session_state.master_summary}\n\n"
        for n, a in st.session_state.panel_answers.items():
            full_text += f"--- {n} ---\n{a}\n\n"
        
        st.caption("👇 전체 내용 복사하기")
        st.code(full_text, language="markdown")
