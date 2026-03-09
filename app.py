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

# 3. 사용자 입력창
user_input = st.text_input("질문을 입력하세요:", placeholder="예: 미래의 인공지능은 어떤 모습일까?")

# 4. 버튼 클릭 시 4개의 AI에게 동시 질문
if st.button("4개 AI 답변 듣기") and user_input:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 화면을 2줄 x 2칸으로 나눔
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)
    
    # AI 호출을 위한 공통 함수
    def fetch_ai_response(model_id, col, title):
        with col:
            st.subheader(title)
            data = {
                "model": model_id,
                "messages": [{"role": "user", "content": user_input}]
            }
            with st.spinner(f'{title} 생각 중...'):
                resp = requests.post(API_URL, headers=headers, json=data)
                if resp.status_code == 200:
                    st.write(resp.json()['choices'][0]['message']['content'])
                else:
                    st.error(f"오류: {resp.status_code} - 일시적인 서버 지연입니다. 다시 시도해주세요.")

    # [1칸] Google Gemma 3 27B
    fetch_ai_response("google/gemma-3-27b-it:free", row1_col1, "Google Gemma 3")
    
    # [2칸] NVIDIA Nemotron 3 Nano
    fetch_ai_response("nvidia/nemotron-3-nano-30b-a3b:free", row1_col2, "NVIDIA Nemotron")
    
    # [3칸] StepFun 3.5 Flash
    fetch_ai_response("stepfun/step-3.5-flash:free", row2_col1, "StepFun 3.5 Flash")
    
    # [4칸] Arcee Trinity Large
    fetch_ai_response("arcee-ai/trinity-large-preview:free", row2_col2, "Arcee Trinity")
