import streamlit as st
import requests

# 1. 페이지 기본 설정
st.set_page_config(page_title="Top 4 무료 AI 비교", layout="wide")
st.title("🤖 안정성 최우선: Top 4 무료 AI 동시 비교")

# 2. API 키 설정 확인
try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except KeyError:
    st.error("API 키 설정을 찾을 수 없습니다. Streamlit 설정의 'Secrets'에서 키를 입력해 주세요.")
    st.stop()

API_URL = "https://openrouter.ai/api/v1/chat/completions"

# 3. 메모리(Session State) 초기화: 답변과 요약본이 날아가지 않도록 저장
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "summary" not in st.session_state:
    st.session_state.summary = ""

# 4. 사용자 입력창
user_input = st.text_input("질문을 입력하세요:", placeholder="예: 2026년 인공지능 트렌드는 어떻게 될까?")

# 5. API 호출용 공통 함수
def fetch_ai_response(model_id):
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
    # 새로운 질문을 던지면 기존 기억(답변, 요약)을 모두 지웁니다
    st.session_state.answers = {}
    st.session_state.summary = "" 
    
    # 화면을 4칸으로 나누고 동시에 로딩 표시 (데이터만 먼저 가져옴)
    col1, col2, col3, col4 = st.columns(4) # 로딩 스피너를 가로로 나란히 배치
    
    with col1:
        with st.spinner('Gemma 3 생각 중...'):
            st.session_state.answers["Google Gemma 3"] = fetch_ai_response("google/gemma-3-27b-it:free")
    with col2:
        with st.spinner('Nemotron 생각 중...'):
            st.session_state.answers["NVIDIA Nemotron"] = fetch_ai_response("nvidia/nemotron-3-nano-30b-a3b:free")
    with col3:
        with st.spinner('StepFun 생각 중...'):
            st.session_state.answers["StepFun 3.5 Flash"] = fetch_ai_response("stepfun/step-3.5-flash:free")
    with col4:
        with st.spinner('Trinity 생각 중...'):
            st.session_state.answers["Arcee Trinity"] = fetch_ai_response("arcee-ai/trinity-large-preview:free")

# 7. 생성된 답변이 있을 때 화면 렌더링 (요약 버튼을 최상단에 배치)
if st.session_state.answers:
    
    # --- [상단 영역] 통합 요약 ---
    st.markdown("### 💡 4대 AI 통합 핵심 요약")
    
    # 요약 버튼 (이미 요약본이 있다면 버튼을 숨기거나 비활성화할 수도 있지만, 우선 유지)
    if st.button("✨ 전체 답변 읽고 요약하기 (by Google Gemma 3)"):
        summary_prompt = "다음은 동일한 질문에 대한 4가지 AI의 답변입니다. 이 내용들을 종합하여 가장 핵심적인 내용을 요약하고, 통찰력 있는 결론을 도출해주세요.\n\n"
        for ai_name, answer in st.session_state.answers.items():
            summary_prompt += f"[{ai_name}의 답변]\n{answer}\n\n"
            
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        data_summary = {
            "model": "google/gemma-3-27b-it:free",
            "messages": [{"role": "user", "content": summary_prompt}]
        }
        
        with st.spinner('Gemma 3가 4개의 답변을 분석하여 요약 중입니다...'):
            resp_summary = requests.post(API_URL, headers=headers, json=data_summary)
            if resp_summary.status_code == 200:
                st.session_state.summary = resp_summary.json()['choices'][0]['message']['content']
            else:
                st.error("요약 중 오류가 발생했습니다.")
                
    # 요약 결과가 메모리에 있으면 화면에 눈에 띄게 표시
    if st.session_state.summary:
        st.success(st.session_state.summary)
        
    st.divider() # 구분선
    
    # --- [하단 영역] 개별 AI 상세 답변 ---
    st.markdown("### 💬 개별 AI 상세 답변")
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
