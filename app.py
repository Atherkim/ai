import streamlit as st
import requests

st.set_page_config(page_title="최적 AI 자동 매칭 서비스", layout="centered")
st.title("🎯 최적 AI 자동 매칭 서비스")
st.markdown("질문의 성격을 분석하여 **가장 전문적인 AI**를 연결해 드립니다.")

try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except KeyError:
    st.error("API 키를 찾을 수 없습니다. Streamlit Settings -> Secrets에 OPENROUTER_API_KEY를 등록해주세요.")
    st.stop()

API_URL = "https://openrouter.ai/api/v1/chat/completions"

EXPERTS = {
    "CODE": {"name": "Google Gemma 3 (27B)", "id": "google/gemma-3-27b-it:free", "icon": "💻", "desc": "코딩 및 기술 문제"},
    "CREATIVE": {"name": "Arcee Trinity", "id": "arcee-ai/trinity-large-preview:free", "icon": "🎨", "desc": "창의적 글쓰기 및 아이디어"},
    "LOGIC": {"name": "NVIDIA Nemotron", "id": "nvidia/nemotron-3-nano-30b-a3b:free", "icon": "🧠", "desc": "수학, 퍼즐 및 논리적 추론"},
    "GENERAL": {"name": "StepFun 3.5 Flash", "id": "stepfun/step-3.5-flash:free", "icon": "💬", "desc": "일반 상식 및 일상 대화"}
}

def call_openrouter(model_id, system_prompt, user_message, max_tokens=None):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    combined_message = f"{system_prompt}\n\n사용자 질문: {user_message}"
    
    data = {
        "model": model_id,
        "messages": [{"role": "user", "content": combined_message}],
        "temperature": 0.3
    }
    
    if max_tokens:
        data["max_tokens"] = max_tokens
        
    try:
        resp = requests.post(API_URL, headers=headers, json=data, timeout=30)
        if resp.status_code == 200:
            result = resp.json()
            # 🚨 핵심 수정: content가 None이거나 없을 경우를 대비해 기본값 "" 설정
            content = result.get('choices', [{}])[0].get('message', {}).get('content')
            
            if content is None:
                return None, f"[{model_id}] 서버가 빈 답변을 보냈습니다. 다시 시도해 주세요."
            
            return content.strip(), None
        else:
            return None, f"[{model_id}] 오류: {resp.status_code} - {resp.text}"
    except Exception as e:
        return None, f"통신 장애 발생: {str(e)}"

user_input = st.text_input("질문을 입력하세요:", placeholder="예: 파이썬으로 이메일 발송 코드 짜줘")

if st.button("질문하기") and user_input:
    status_container = st.empty()
    
    with status_container.container():
        # --- 1단계: 분류 ---
        with st.spinner("🕵️‍♂️ 1단계: 안내원 AI가 질문을 분석 중입니다..."):
            router_prompt = "질문의 카테고리를 분류해줘. 단어 하나로만 대답해: CODE, CREATIVE, LOGIC, GENERAL"
            
            category, error_msg1 = call_openrouter("stepfun/step-3.5-flash:free", router_prompt, user_input, max_tokens=10)
            
            if error_msg1:
                st.error(f"1단계 오류 발생: {error_msg1}")
                st.stop()
            
            # 🚨 2차 방어: category 자체가 비어있을 경우 예외 처리
            if not category:
                category = "GENERAL"
            
            matched_category = "GENERAL"
            for cat in EXPERTS.keys():
                if cat in category.upper():
                    matched_category = cat
                    break
            
            selected_ai = EXPERTS[matched_category]

        # --- 2단계: 답변 생성 ---
        with st.spinner(f"🚀 {selected_ai['icon']} 전문가 **{selected_ai['name']}**가 답변을 작성 중입니다..."):
            final_answer, error_msg2 = call_openrouter(
                selected_ai['id'], 
                f"너는 {selected_ai['desc']} 전문가야. 정확하게 답변해줘.", 
                user_input
            )
            
            if error_msg2:
                st.error(f"2단계 오류 발생: {error_msg2}")
                st.stop()
            
    status_container.empty()
    
    if final_answer:
        st.subheader(f"{selected_ai['icon']} {selected_ai['name']}의 답변")
        st.markdown(final_answer)
        st.divider()
        st.caption("👇 전체 답변 복사하기")
        st.code(final_answer, language="markdown")
