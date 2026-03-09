import streamlit as st
import requests
import time

# 1. 페이지 설정
st.set_page_config(page_title="초강력 AI 자동 매칭", layout="centered")
st.title("🛡️ 멀티 라우터 배당 시스템")
st.markdown("수많은 안내원 AI 중 **가장 먼저 응답하는 전문가**를 찾아 즉시 연결합니다.")

try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except KeyError:
    st.error("API 키를 등록해주세요.")
    st.stop()

API_URL = "https://openrouter.ai/api/v1/chat/completions"

# [전문가 군단]
EXPERTS = {
    "CODE": {"name": "Google Gemma 3 (27B)", "id": "google/gemma-3-27b-it:free", "icon": "💻", "desc": "코딩/기술"},
    "CREATIVE": {"name": "Arcee Trinity", "id": "arcee-ai/trinity-large-preview:free", "icon": "🎨", "desc": "창작/아이디어"},
    "LOGIC": {"name": "NVIDIA Nemotron", "id": "nvidia/nemotron-3-nano-30b-a3b:free", "icon": "🧠", "desc": "논리/수학"},
    "GENERAL": {"name": "StepFun 3.5 Flash", "id": "stepfun/step-3.5-flash:free", "icon": "💬", "desc": "일반 대화"}
}

# [안내원 풀 확장] - 안정성이 검증된 무료 모델 총집합
ROUTER_POOL = [
    "stepfun/step-3.5-flash:free",           # 1순위: 속도 최강
    "google/gemma-3-4b-it:free",            # 2순위: 구글 최신
    "meta-llama/llama-3.2-3b-instruct:free", # 3순위: 메타 대표
    "mistralai/mistral-7b-instruct:free",   # 4순위: 미스트랄
    "qwen/qwen-2-7b-instruct:free",         # 5순위: 큐원
    "microsoft/phi-3-mini-128k-instruct:free" # 6순위: 마이크로소프트
]

def call_openrouter(model_id, system_prompt, user_message, max_tokens=None):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    combined_message = f"{system_prompt}\n\n질문: {user_message}"
    data = {
        "model": model_id,
        "messages": [{"role": "user", "content": combined_message}],
        "temperature": 0.1
    }
    if max_tokens: data["max_tokens"] = max_tokens
        
    try:
        # 타임아웃을 짧게 잡아 안 대답하면 빨리 다음으로 넘김
        resp = requests.post(API_URL, headers=headers, json=data, timeout=10)
        if resp.status_code == 200:
            content = resp.json().get('choices', [{}])[0].get('message', {}).get('content')
            return (content.strip(), None) if content else (None, "빈 답변")
        return None, f"에러 {resp.status_code}"
    except Exception as e:
        return None, str(e)

user_input = st.text_input("질문을 입력하세요:", placeholder="무엇이든 물어보세요")

if st.button("질문하기") and user_input:
    status_container = st.empty()
    final_category = None
    
    with status_container.container():
        # --- 1단계: 무한 루프형 안내원 배당 ---
        for i, model in enumerate(ROUTER_POOL):
            model_short_name = model.split('/')[1]
            with st.spinner(f"🔍 {i+1}번 안내원({model_short_name})이 분석 중..."):
                router_prompt = "분류 카테고리 하나만 대답해: CODE, CREATIVE, LOGIC, GENERAL"
                category, err = call_openrouter(model, router_prompt, user_input, max_tokens=10)
                
                if category:
                    for key in EXPERTS.keys():
                        if key in category.upper():
                            final_category = key
                            break
                    if final_category: break
                
                st.warning(f"⚠️ {model_short_name} 응답 지연. 다음 안내원에게 이동합니다.")
                time.sleep(0.5)

        if not final_category:
            st.error("🚨 현재 모든 무료 안내원 AI가 과부하 상태입니다. 잠시 후 다시 시도해주세요.")
            st.stop()
            
        selected_ai = EXPERTS[final_category]
        
        # --- 2단계: 전문가 답변 생성 ---
        with st.spinner(f"🚀 {selected_ai['icon']} {selected_ai['name']} 전문가 연결 완료! 작성 중..."):
            answer, err = call_openrouter(selected_ai['id'], f"너는 {selected_ai['desc']} 전문가야.", user_input)
            
            if err:
                st.error(f"🚨 전문가 연결 실패: {err}")
                st.stop()

    status_container.empty()
    
    # 최종 결과
    st.subheader(f"{selected_ai['icon']} {selected_ai['name']}의 답변")
    st.markdown(answer)
    st.divider()
    st.caption("👇 복사하려면 아래 아이콘을 클릭하세요")
    st.code(answer, language="markdown")
