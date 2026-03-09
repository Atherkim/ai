import streamlit as st
import requests

# 1. 페이지 기본 설정
st.set_page_config(page_title="Top 4 무료 AI 비교", layout="wide")
st.title("🤖 안정성 최우선: Top 4 무료 AI 동시 비교 및 요약")

# 2. API 키 설정 확인
try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except KeyError:
    st.error("API 키 설정을 찾을 수 없습니다. Streamlit 설정의 'Secrets'에서 키를 입력해 주세요.")
    st.stop()

API_URL = "https://openrouter.ai/api/v1/chat/completions"

# 3. 메모리(Session State) 초기화: 답변이 날아가지 않도록 저장하는 공간
if "answers" not in st.session_state:
    st.session_state.answers = {}

# 4. 사용자 입력창
user_input = st.text_input("질문을 입력하세요:", placeholder="예: 미래의 인공지능은 어떤 모습일까?")

# 5. API 호출용 공통 함수
def fetch_ai_response(model_id, title):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model_id,
        "messages": [{"role": "user", "content": user_input}]
    }
    resp = requests.post(API_URL, headers=headers, json=data)
    if resp.status_code == 200:
        return resp.json()['choices'][0]['message']['content']
    else:
        return f"오류: {resp.status_code} - 일시적인 서버 지연입니다."

# 6. 답변 생성 버튼
if st.button("4개 AI 답변 듣기") and user_input:
    st.session_state.answers = {} # 기존 기억 지우기
    
    # 화면을 4칸으로 나누고 동시에 로딩 표시
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)
    
    with row1_col1:
        with st.spinner('Google Gemma 3 생각 중...'):
            st.session_state.answers["Google Gemma 3"] = fetch_ai_response("google/gemma-3-27b-it:free", "Google Gemma 3")
    with row1_col2:
        with st.spinner('NVIDIA Nemotron 생각 중...'):
            st.session_state.answers["NVIDIA Nemotron"] = fetch_ai_response("nvidia/nemotron-3-nano-30b-a3b:free", "NVIDIA Nemotron")
    with row2_col1:
        with st.spinner('StepFun 3.5 생각 중...'):
            st.session_state.answers["StepFun 3.5 Flash"] = fetch_ai_response("stepfun/step-3.5-flash:free", "StepFun 3.5 Flash")
    with row2_col2:
        with st.spinner('Arcee Trinity 생각 중...'):
            st.session_state.answers["Arcee Trinity"] = fetch_ai_response("arcee-ai/trinity-large-preview:free", "Arcee Trinity")

# 7. 생성된 답변 화면에 보여주기 (메모리에서 불러옴)
if st.session_state.answers:
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)
    
    with row1_col1:
        st.subheader("Google Gemma 3")
        st.write(st.session_state.answers.get("Google Gemma 3", ""))
    with row1_col2:
        st.subheader("NVIDIA Nemotron")
        st.write(st.session_state.answers.get("NVIDIA Nemotron", ""))
    with row2_col1:
        st.subheader("StepFun 3.5 Flash")
        st.write(st.session_state.answers.get("StepFun 3.5 Flash", ""))
    with row2_col2:
        st.subheader("Arcee Trinity")
        st.write(st.session_state.answers.get("Arcee Trinity", ""))
    
    st.divider() # 구분선 추가
    
    # 8. 가장 강력한 모델(Gemma 3)로 전체 요약하기
    if st.button("✨ 4개 답변 통합 요약하기 (by Google Gemma 3)"):
        # 요약을 위한 프롬프트(명령어) 조립
        summary_prompt = "다음은 동일한 질문에 대한 4가지 AI의 답변입니다. 이 내용들을 종합하여 가장 핵심적인 내용을 요약하고, 통찰력 있는 결론을 도출해주세요.\n\n"
        for ai_name, answer in st.session_state.answers.items():
            summary_prompt += f"[{ai_name}의 답변]\n{answer}\n\n"
            
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        data_summary = {
            "model": "google/gemma-3-27b-it:free", # 요약 담당 일타 모델
            "messages": [{"role": "user", "content": summary_prompt}]
        }
        
        with st.spinner('Gemma 3가 모든 답변을 읽고 요약 중입니다...'):
            resp_summary = requests.post(API_URL, headers=headers, json=data_summary)
            if resp_summary.status_code == 200:
                st.success("### 📝 통합 요약 결과")
                st.write(resp_summary.json()['choices'][0]['message']['content'])
            else:
                st.error("요약 중 오류가 발생했습니다.")
