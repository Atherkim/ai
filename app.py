import streamlit as st
import requests

# 1. 페이지 기본 설정
st.set_page_config(page_title="다중 AI 비교 테스트", layout="wide")
st.title("🤖 다중 AI 비교 테스트")

# 2. API 키 설정 확인
try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except KeyError:
    st.error("API 키 설정을 찾을 수 없습니다. Streamlit 화면 우측 하단의 'Manage app' -> 'Settings' -> 'Secrets'에서 키를 입력해 주세요.")
    st.stop()

API_URL = "https://openrouter.ai/api/v1/chat/completions"

# 3. 사용자 입력창
user_input = st.text_input("질문을 입력하세요:", placeholder="예: 양자역학을 5살 아이에게 설명해줘")

# 4. 버튼 클릭 시 두 AI에게 동시 질문
if st.button("답변 듣기") and user_input:
    col1, col2 = st.columns(2)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 첫 번째 AI: 최신 Google Gemma 3 (12B 모델)
    with col1:
        st.subheader("Google Gemma 3")
        data_gemma = {
            "model": "google/gemma-3-12b-it:free",
            "messages": [{"role": "user", "content": user_input}]
        }
        with st.spinner('Gemma가 생각 중...'):
            response1 = requests.post(API_URL, headers=headers, json=data_gemma)
            if response1.status_code == 200:
                st.info(response1.json()['choices'][0]['message']['content'])
            else:
                # 에러 발생 시 상세 원인 출력
                st.error(f"Gemma 응답 오류: {response1.status_code} - {response1.text}")
            
    # 두 번째 AI: 최신 Meta Llama 3.3 (70B 모델)
    with col2:
        st.subheader("Meta Llama 3.3")
        data_llama = {
            "model": "meta-llama/llama-3.3-70b-instruct:free",
            "messages": [{"role": "user", "content": user_input}]
        }
        with st.spinner('Llama가 생각 중...'):
            response2 = requests.post(API_URL, headers=headers, json=data_llama)
            if response2.status_code == 200:
                st.success(response2.json()['choices'][0]['message']['content'])
            else:
                # 에러 발생 시 상세 원인 출력
                st.error(f"Llama 응답 오류: {response2.status_code} - {response2.text}")
