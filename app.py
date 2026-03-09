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

PANEL = [
    {"name": "Google Gemma 3", "id": "google/gemma-3-27b-it:free", "role": "논리/분석 전문가"},
    {"name": "NVIDIA Nemotron", "id": "nvidia/nemotron-3-nano-30b-a3b:free", "role": "기술/수학 전문가"},
    {"name": "Arcee Trinity", "id": "arcee-ai/trinity-large-preview:free", "role": "창의/인문 전문가"},
    {"name": "StepFun 3.5", "id": "stepfun/step-3.5-flash:free", "role": "실용/일반 전문가"}
]

# 🚨 수정됨: 진짜 답변(content)과 에러 메시지(error_msg)를 확실하게 나누어 반환합니다.
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
            return None, f"에러 {resp.status_code}" # 429 등의 에러는 여기서 걸러집니다.
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
                
                # 🚨 수정됨: 에러가 없을 때만 성공 처리, 에러 시 붉은색 경고 출력
                if answer:
                    st.session_state.panel_answers[ai['name']] = answer
                    st.success(f"**{ai['name']} 완료**")
                else:
                    st.error(f"**{ai['name']} 실패**")
                    st.caption(err) # 실패 원인(예: 에러 429)을 작게 표시

# 결과 화면 렌더링 (성공한 데이터만 출력)
if st.session_state.panel_answers:
    st.markdown("### 💬 전문가 4인의 개별 의견")
    
    cols = st.columns(4)
    for i, ai in enumerate(PANEL):
        with cols[i]:
            # 성공해서 메모리에 데이터가 있는 AI만 펼쳐보기를 활성화합니다.
            if ai['name'] in st.session_state.panel_answers:
                st.info(f"**{ai['role']}**\n\n{ai['name']}")
                with st.expander("전체 답변 읽기 ⬇️"):
                    st.write(st.session_state.panel_answers[ai['name']])
            else:
                # 실패한 AI는 빈자리로 남겨두어 혼선을 방지합니다.
                st.warning(f"**{ai['role']}**\n\n{ai['name']} (참여 실패)")
    
    st.divider()

    # [2단계 버튼] 마스터 비평가의 판단
    if st.button("✨ 마스터 비평가의 종합 판정 시작"):
        with st.spinner("🧠 성공적으로 도착한 답변들을 교차 분석 중입니다..."):
            
            critique_prompt = "너는 최고 전문가 의견을 조율하는 수석 비평가야. 아래 답변들을 읽고 다음 구조로 정리해.\n1. 핵심 공통점\n2. 주요 차이점\n3. 최종 결론 및 권고사항\n\n"
            for name, ans in st.session_state.panel_answers.items():
                critique_prompt += f"[{name}의 의견]: {ans}\n\n"
            
            # 마스터 비평가 호출 (여기서도 에러 분리 로직 적용)
            summary_ans, summary_err = call_ai("google/gemma-3-27b-it:free", critique_prompt, f"주제: {user_input}\n위 내용들을 종합해줘.")
            
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
