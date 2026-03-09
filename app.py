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

# 전문가 AI 리스트 정의
EXPERTS = {
    "CODE": {"name": "Google Gemma 3 (27B)", "id": "google/gemma-3-27b-it:free", "icon": "💻", "desc": "코딩 및 기술 문제"},
    "CREATIVE": {"name": "Arcee Trinity", "id": "arcee-ai/trinity-large-preview:free", "icon": "🎨", "desc": "창의적 글쓰기 및 아이디어"},
    "LOGIC": {"name": "NVIDIA Nemotron", "id": "nvidia/nemotron-3-nano-30b-a3b:free", "icon": "🧠", "desc": "수학, 퍼즐 및 논리적 추론"},
    "GENERAL": {"name": "StepFun 3.5 Flash", "id": "stepfun/step-3.5-flash:free", "icon": "💬", "desc": "일반 상식 및 일상 대화"}
}

user_input = st.text_input("질문을 입력하세요:", placeholder="예: 파이썬으로 테트리스 게임 만드는 코드 짜줘")

# API 호출 공통 함수
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
        "temperature": 0.3 # 분류의 정확도를 높이기 위해 창의성 낮춤
    }
    resp = requests.post(API_URL, headers=headers, json=data)
    if resp.status_code == 200:
        return resp.json()['choices'][0]['message']['content'].strip()
    else:
        return None

if st.button("질문하기") and user_input:
    
    # 처리 과정을 사용자에게 예쁘게 보여주는 UI
    with st.status("로봇이 질문을 분석하고 있습니다...", expanded=True) as status:
        
        # [1단계] 안내원 AI가 질문 성격 분류하기
        st.write("🕵️‍♂️ 안내원 AI가 질문의 의도를 파악하는 중...")
        router_prompt = """
        너는 질문의 카테고리를 분류하는 안내원이야. 사용자의 질문을 읽고 다음 4가지 카테고리 중 딱 하나만 골라서 영단어로만 대답해. 다른 말은 절대 금지.
        - CODE (프로그래밍, 코드 작성, 에러 해결, IT 기술)
        - CREATIVE (소설, 시, 기획안, 이메일, 마케팅 문구 등 창작)
        - LOGIC (수학 문제, 퍼즐, 논리적 증명)
        - GENERAL (위 3개에 해당하지 않는 일반적인 질문, 번역, 요약, 잡담)
        """
        category = call_openrouter("stepfun/step-3.5-flash:free", router_prompt, user_input)
        
        # 혹시 AI가 엉뚱한 대답을 하면 기본값(GENERAL)으로 설정
        if category not in EXPERTS:
            category = "GENERAL"
            
        selected_ai = EXPERTS[category]
        st.write(f"{selected_ai['icon']} **분류 완료!** 이 질문은 **[{selected_ai['desc']}]**에 해당합니다.")
        st.write(f"🚀 최적의 전문가 **{selected_ai['name']}**(에게 질문을 전달합니다...")
        
        # [2단계] 선택된 전문가 AI에게 답변 받아오기
        final_answer = call_openrouter(
            selected_ai['id'], 
            f"너는 {selected_ai['desc']} 분야의 최고 전문가야. 전문적이고 정확하게 답변해줘.", 
            user_input
        )
        
        status.update(label="답변 생성이 완료되었습니다!", state="complete", expanded=False)
        
    # [3단계]
