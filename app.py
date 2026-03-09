import streamlit as st
import requests

st.set_page_config(page_title="최적 AI 자동 매칭 서비스", layout="centered")
st.title("🎯 최적 AI 자동 매칭 서비스")
st.markdown("질문의 성격을 스스로 분석하여 **가장 잘하는 AI**가 알아서 답변합니다.")

try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except KeyError:
    st.error("API 키 설정을 찾을 수 없습니다. Streamlit 설정의 'Secrets'에서 키를 입력해 주세요.")
    st.stop()

API_URL = "https://openrouter.ai/api/v1/chat/completions"

EXPERTS = {
    "CODE": {"name": "Google Gemma 3 (27B)", "id": "google/gemma-3-27b-it:free", "icon": "💻", "desc": "코딩 및 기술 문제"},
    "CREATIVE": {"name": "Arcee Trinity", "id": "arcee-ai/trinity-large-preview:free", "icon": "🎨", "desc": "창의적 글쓰기 및 아이디어"},
    "LOGIC": {"name": "NVIDIA Nemotron", "id": "nvidia/nemotron-3-nano-30b-a3b:free", "icon": "🧠", "desc": "수학, 퍼즐 및 논리적 추론"},
    "GENERAL": {"name": "StepFun 3.5 Flash", "id": "stepfun/step-3.5-flash:free", "icon": "💬", "desc": "일반 상식 및 일상 대화"}
}

user_input = st.text_input("질문을 입력하세요:", placeholder="예: 파이썬으로 테트리스 게임 만드는 코드 짜줘")

# 에러 메시지까지 함께 반환하도록 함수 수정
def call_openrouter(model_id, system_prompt, user_message):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.3
    }
    resp = requests.post(API_URL, headers=headers, json=data)
    if resp.status_code == 200:
        return resp.json()['choices'][0]['message']['content'].strip(), None
    else:
        # 실패 시 에러 코드와 상세 내용을 반환
        return None, f"[{model_id}] 오류 코드: {resp.status_code} \n상세 내용: {resp.text}"

if st.button("질문하기") and user_input:
    
    status_container = st.empty()
    
    with status_container.container():
        st.info("🕵️‍♂️ 1단계: 안내원 AI가 질문의 의도를 파악하고 있습니다...")
        
        router_prompt = """
        너는 질문의 카테고리를 분류하는 안내원이야. 사용자의 질문을 읽고 다음 4가지 카테고리 중 딱 하나만 골라서 영단어로만 대답해. 다른 말은 절대 금지.
        - CODE (프로그래밍, 코드 작성, 에러 해결, IT 기술)
        - CREATIVE (소설, 시, 기획안, 이메일, 마케팅 문구 등 창작)
        - LOGIC (수학 문제, 퍼즐, 논리적 증명)
        - GENERAL (위 3개에 해당하지 않는 일반적인 질문, 번역, 요약, 잡담)
        """
        
        # 1단계 API 호출
        category, error_msg1 = call_openrouter("stepfun/step-3.5-flash:free", router_prompt, user_input)
        
        if error_msg1:
            st.error(f"🚨 1단계 분류 AI에서 통신 오류가 발생했습니다.\n\n{error_msg1}")
            st.stop() # 여기서 프로그램 즉시 정지
            
        if category not in EXPERTS:
            category = "GENERAL"
            
        selected_ai = EXPERTS[category]
        st.success(f"🚀 분류 완료! {selected_ai['icon']} 전문가 **{selected_ai['name']}**가 답변을 작성 중입니다...")
        
        # 2단계 API 호출
        final_answer, error_msg2 = call_openrouter(
            selected_ai['id'], 
            f"너는 {selected_ai['desc']} 분야의 최고 전문가야. 전문적이고 정확하게 답변해줘.", 
            user_input
        )
        
        if error_msg2:
            st.error(f"🚨 2단계 전문가 AI({selected_ai['name']})에서 통신 오류가 발생했습니다.\n\n{error_msg2}")
            st.stop() # 여기서 프로그램 즉시 정지
            
    # 에러 없이 무사히 통과했다면 임시 공간 지우고 결과 출력
    status_container.empty()
    
    st.subheader(f"{selected_ai['icon']} {selected_ai['name']}의 답변")
    st.markdown(final_answer)
    st.divider()
    st.caption("👇 전체 답변 복사하기")
    st.code(final_answer, language="markdown")
