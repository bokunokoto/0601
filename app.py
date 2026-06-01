import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="AI 응용 앱", layout="centered")
st.title("🤖 내 첫 AI 웹 애플리케이션")

# 1. 세션 상태(session_state) 초기화하여 API Key가 다른 페이지 이동 시에도 유지되도록 함
if "openai_api_key" not in st.session_state:
    st.session_state["openai_api_key"] = ""

# 2. 사이드바에 암호 형태로 API Key 입력 창 배치
with st.sidebar:
    api_key_input = st.text_input(
        "OpenAI API Key를 입력하세요", 
        type="password", 
        value=st.session_state["openai_api_key"]
    )
    if api_key_input:
        st.session_state["openai_api_key"] = api_key_input
        st.success("API Key가 세션에 저장되었습니다!")

# 3. 입력 값이 캐싱되도록 비즈니스 로직 함수 분리
@st.cache_data(show_spinner="AI가 생각하는 중...")
def get_llm_response(api_key, question):
    if not api_key:
        return "오류: 사이드바에서 OpenAI API Key를 먼저 입력해 주세요."
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # 가성비 좋고 빠른 모델 추천
            messages=[{"role": "user", "content": question}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"API 에러 발생: {e}"

# 4. 사용자 질문 입력 화면 UI
user_question = st.text_input("질문을 던져보세요:")

if st.button("질문하기"):
    if user_question:
        # 캐싱된 함수 호출
        answer = get_llm_response(st.session_state["openai_api_key"], user_question)
        st.markdown("### 💬 AI 응답 결과")
        st.write(answer)
    else:
        st.warning("질문을 입력해 주세요.")
