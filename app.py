# 🚨 1. API 호출 함수 수정: max_tokens(글자 수 제한) 기능 추가
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
    
    # max_tokens가 설정되어 있으면 데이터에 추가
    if max_tokens:
        data["max_tokens"] = max_tokens
        
    resp = requests.post(API_URL, headers=headers, json=data)
    if resp.status_code == 200:
        return resp.json()['choices'][0]['message']['content'].strip(), None
    else:
        return None, f"[{model_id}] 오류 코드: {resp.status_code} \n상세 내용: {resp.text}"

# 🚨 2. 버튼 클릭 부분 수정: 애니메이션(spinner) 및 속도 향상 적용
if st.button("질문하기") and user_input:
    
    status_container = st.empty()
    
    with status_container.container():
        # 📌 정적인 텍스트 대신, 움직이는 로딩 애니메이션(spinner) 적용
        with st.spinner("🕵️‍♂️ 1단계: 안내원 AI가 질문을 분석 중입니다... (무료 서버 접속 대기 중 ⏳)"):
            
            router_prompt = """
            너는 질문의 카테고리를 분류하는 안내원이야. 사용자의 질문을 읽고 다음 4가지 카테고리 중 딱 하나만 골라서 영단어로만 대답해. 다른 말은 절대 금지.
            - CODE (프로그래밍, 코드 작성, 에러 해결, IT 기술)
            - CREATIVE (소설, 시, 기획안, 이메일, 마케팅 문구 등 창작)
            - LOGIC (수학 문제, 퍼즐, 논리적 증명)
            - GENERAL (위 3개에 해당하지 않는 일반적인 질문, 번역, 요약, 잡담)
            """
            
            # max_tokens=10을 주어 분류가 끝나면 즉시 통신을 끊어 속도 확보
            category, error_msg1 = call_openrouter("stepfun/step-3.5-flash:free", router_prompt, user_input, max_tokens=10)
            
            if error_msg1:
                st.error(f"🚨 1단계 분류 AI에서 통신 오류가 발생했습니다.\n\n{error_msg1}")
                st.stop()
                
            valid_categories = ["CODE", "CREATIVE", "LOGIC", "GENERAL"]
            matched_category = "GENERAL"
            
            for cat in valid_categories:
                if cat in category.upper():
                    matched_category = cat
                    break
                    
            selected_ai = EXPERTS[matched_category]
            
        # 📌 2단계 넘어갈 때 로딩 애니메이션 텍스트 변경
        with st.spinner(f"🚀 분류 완료! {selected_ai['icon']} 전문가 **{selected_ai['name']}**가 답변을 작성하고 있습니다... ✍️"):
            
            final_answer, error_msg2 = call_openrouter(
                selected_ai['id'], 
                f"너는 {selected_ai['desc']} 분야의 최고 전문가야. 아주 논리적이고 정확하게 답변해줘.", 
                user_input
                # 2단계는 긴 답변을 해야 하므로 max_tokens를 걸지 않습니다.
            )
            
            if error_msg2:
                st.error(f"🚨 2단계 전문가 AI({selected_ai['name']})에서 통신 오류가 발생했습니다.\n\n{error_msg2}")
                st.stop()
            
    # 에러 없이 완료되면 임시 공간 지우기
    status_container.empty()
    
    # 최종 결과 화면 출력
    st.subheader(f"{selected_ai['icon']} {selected_ai['name']}의 답변")
    st.markdown(final_answer)
    st.divider()
    
    st.caption("👇 전체 답변 복사하기")
    st.code(final_answer, language="markdown")
