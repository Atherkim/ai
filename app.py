import streamlit as st
import requests
import time

# 1. 페이지 설정
st.set_page_config(page_title="최적 AI 자동 매칭 서비스", layout="centered")
st.title("🎯 스마트 AI 자동 매칭 (무한 복구 버전)")
st.markdown("안내원 AI가 바쁘면 **예비 안내원**이 즉시 투입되어 중단 없이 작동합니다.")

# 2. 보안 및 설정
try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except KeyError:
    st.error("API 키를 등록해주세요.")
    st.stop()

API_URL = "https://openrouter.ai/api/v1/chat/completions"

# 전문가 군단
EXPERTS = {
    "CODE": {"name": "Google Gemma 3 (27B)", "id": "google/gemma-3-27b-it:free", "icon": "💻", "desc": "코딩 및 기술"},
    "CREATIVE": {"name": "Arcee Trinity", "id": "arcee-ai/trinity-large-preview:free", "icon": "🎨", "desc": "창작 및 아이디어"},
    "LOGIC": {"name": "NVIDIA Nemotron", "id": "nvidia/nemotron-3-nano-30b-a3b:free", "icon": "🧠", "desc": "논리 및 수학"},
    "GENERAL": {"name": "StepFun 3.5 Flash", "id": "stepfun/step-3.5-flash:free", "icon": "💬", "desc": "일반 대화"}
}

# 예비 안내원 리스트 (1번이 바쁘면 2번, 2번이 바쁘면 3번...)
ROUTER_MODELS = [
    "stepfun/step-3.5-flash:free",
    "google/gemma-3-4b-it:free",
    "meta-llama/llama-3.2-3b-instruct:free"
]

def call_openrouter(model_id, system_prompt, user_message, max_tokens=None):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    combined_message = f"{system_prompt}\n\n사용자 질문: {user_message}"
    data = {
        "model": model_id,
        "messages": [{"role": "user", "content": combined_message}],
        "temperature": 0.1 # 분류의 정확도를 위해 낮춤
    }
    if max_tokens: data["max_tokens"] = max_tokens
        
    try:
        resp = requests.post(API_URL, headers=headers, json=data, timeout=20)
        if resp.status_code == 200:
            content = resp.json().get('choices', [{}])[0].get('message', {}).get('content')
            return (content.strip(), None) if content else (None, "빈 답변")
        return None, f"에러 {resp.status_code}"
    except Exception as e:
        return None, str(e)

user_input = st.text_input("질문을 입력하세요:", placeholder="예: 파이썬으로 가계부 프로그램 짜줘")

if st.button("질문하기") and user_input:
    status_container = st.empty()
    final_category = None
    
    with status_container.container():
        # --- 1단계: 자동 복구형 분류 시스템 ---
        for i, model in enumerate(ROUTER_MODELS):
            with st.spinner(f"🕵️‍♂️ {i+1}번 안내원({model.split('/')[1]})에게 질문 분석을 요청 중..."):
                router_prompt = "질문을 딱 한 단어로만 분류해: CODE, CREATIVE, LOGIC, GENERAL"
                category, err = call_openrouter(model, router_prompt, user_input, max_tokens=10)
                
                if category:
                    # 유효성 검사
                    for key in EXPERTS.keys():
                        if key in category.upper():
                            final_category = key
                            break
                    if final_category: break # 분류 성공 시 루프 탈출
                
                st.warning(f"⚠️ {i+1}번 안내원이 바쁩니다. 다음 안내원을 호출합니다...")
                time.sleep(1) # 서버 과부하 방지를 위한 짧은 휴식

        if not final_category:
            st.error("🚨 모든 안내원 AI가 현재 응답 불가능 상태입니다. 잠시 후 다시 시도해주세요.")
            st.stop()
            
        selected_ai = EXPERTS[final_category]
        
        # --- 2단계: 전문가 답변 생성 ---
        with st.spinner(f"🚀 {selected_ai['icon']} 전문가 **{selected_ai['name']}**가 답변을 작성 중..."):
            answer, err = call_openrouter(selected_ai['id'], f"너는 {selected_ai['desc']} 전문가야.", user_input)
            
            if err:
                st.error(f"🚨 전문가 연결 실패: {err}")
                st.stop()

    status_container.empty()
    
    # 결과 출력
    st.subheader(f"{selected_ai['icon']} {selected_ai['name']}의 답변")
    st.markdown(answer)
    st.divider()
    st.caption("👇 복사하려면 아래 아이콘을 클릭하세요")
    st.code(answer, language="markdown")
