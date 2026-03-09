import streamlit as st
import requests

# Streamlit의 안전한 비밀고에서 키를 불러옵니다.
API_KEY = st.secrets["OPENROUTER_API_KEY"]
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# ... (나머지 화면 및 챗봇 로직은 동일) ...
