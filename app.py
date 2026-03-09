import streamlit as st
import requests

# 1. 페이지 기본 설정 및 디자인
st.set_page_config(page_title="최적 AI 자동 매칭 서비스", layout="centered")
st.title("🎯 최적 AI 자동 매칭 서비스")
st.markdown("질문의 성격을 분석하여 **가장 전문적인 AI**를 연결해 드립니다.")

# 2. API 키 보안 확인
try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except KeyError:
    st.error("API 키를 찾을 수 없습니다. Streamlit Settings -> Secrets에 OPENROUTER_API_KEY를 등록해주세요.")
    st.stop()

API_URL = "https://openrouter.ai/api/v1/chat/completions"

# 3. 전문가 AI 프로필 정의 (순서 중요: 함수나 버튼보다 위에 있어야 함)
EXPERTS = {
    "CODE": {"name": "Google Gemma 3 (27B)", "id": "google/gemma-3-27b-it:free", "icon": "💻", "desc": "코딩 및 기술 문제"},
    "CREATIVE": {"name": "Arcee Trinity", "id": "arcee-ai/trinity-large-preview:free", "icon": "🎨", "desc": "창의적 글쓰기 및 아이디어"},
    "LOGIC": {"name": "NVIDIA Nemotron", "id": "nvidia/nemotron-3-nano-30b-a3b:free", "icon": "🧠", "desc": "수학, 퍼즐 및 논리적 추론"},
    "GENERAL": {"name": "StepFun 3.5 Flash", "id": "stepfun/step-3.5-flash:free", "icon": "💬", "desc": "일반 상식 및 일상 대화"}
}

# 4. API 호출 함수 (max_tokens 지원)
def call_openrouter(model_id, system_prompt, user_message, max_tokens=None):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 모든 모델 호환성을 위해 메시지 통합
    combined_message = f"{system_prompt}\n\n사용자 질문: {user_message}"
    
    data = {
        "model": model_id,
        "messages": [{"role": "user", "content": combined_message}],
        "temperature": 0.3
    }
    
    if max_tokens:
        data["max_tokens"] = max_tokens
        
    try:
        resp = requests.post(API_URL, headers=headers, json=data)
        if resp.status_code == 200:
            return resp.json()['choices'][0]['message']['content'].strip(), None
        else:
            return None, f"[{model_id}] 오류: {resp.status_code} - {resp.text}"
    except Exception as e:
        return None, f"통신 장애: {str(e)}"

# 5. 사용자 입력창 (버튼보다 반드시 먼저 위치해야 NameError가 안 납니다)
user_input = st.text_input("질문을 입력하세요:", placeholder="예: 파이썬으로 이메일 발송 코드 짜줘")

# 6. 실행 로직
if st.button("질문하기") and user_input:
    
    # 진행 상황을 보여줄 빈 공간 확보
    status_container = st.empty()
    
    with status_container.container():
        # --- 1단계: 분류 (스피너 적용) ---
        with st.spinner("🕵️‍♂️ 1단계: 안내원 AI가 질문을 분석 중입니다..."):
            router_prompt = """
            질문의 카테고리를 분류해줘. 단어 하나로만 대답해: CODE, CREATIVE, LOGIC, GENERAL
            """
            # 1단계는 짧게 대답하도록 강제 (속도 향상)
            category, error_msg1 = call_openrouter("stepfun/step-3.5-flash:free", router_prompt, user_input, max_tokens=10)
            
            if error_msg1:
                st.error(f"1단계 오류 발생:\n{error_msg1}")
                st.stop()
            
            # 카테고리 매칭 (유연한 검색)
            matched_category = "GENERAL"
            for cat in EXPERTS.keys():
                if cat in category.upper():
                    matched_category = cat
                    break
            
            selected_ai = EXPERTS[matched_category]

        # --- 2단계: 답변 생성 (스피너 업데이트) ---
        with st.spinner(f"🚀 {selected_ai['icon']} 전문가 **{selected_ai['name']}**가 답변을 작성 중입니다..."):
            final_answer, error_msg2 = call_openrouter(
                selected_ai['id'], 
                f"너는 {selected_ai['desc']} 전문가야. 정확하게 답변해줘.", 
                user_input
            )
            
            if error_msg2:
                st.error(f"2단계 오류 발생:\n{error_msg2}")
                st.stop()
            
    # 모든 작업 완료 시 로딩 메시지 삭제
    status_container.empty()
    
    # 7. 최종 결과 출력
    st.subheader(f"{selected_ai['icon']} {selected_ai['name']}의 답변")
    st.markdown(final_answer)
    st.divider()
    
    # 8. 복사 기능 (코드 블록 활용)
    st.caption("👇 전체 답변 복사하기 (우측 상단 아이콘 클릭)")
    st.code(final_answer, language="markdown")
