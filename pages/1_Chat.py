import streamlit as st
from openai import OpenAI

st.title("💬 실시간 인공지능 채팅방")

# 메인 페이지에서 입력한 API Key 가져오기
api_key = st.session_state.get("openai_api_key", "")

if not api_key:
    st.warning("메인 페이지(app.py)의 사이드바에서 먼저 OpenAI API Key를 등록해 주세요.")
    st.stop()

# 1. 이 페이지의 대화 기록 세션초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 2. 대화 기록 초기화(Clear) 버튼 배치
if st.button("Clear: 대화 내용 초기화"):
    st.session_state.messages = []
    st.rerun()

# 3. 기존 대화 내용 화면에 렌더링
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 사용자로부터 실시간 채팅 입력 받기
if prompt := st.chat_input("메시지를 입력하세요..."):
    # 화면에 사용자 메시지 즉시 렌더링 후 저장
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # AI 응답 생성 및 렌더링
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ]
            )
            full_response = response.choices[0].message.content
            message_placeholder.markdown(full_response)
            # 대화 기록에 AI 응답 누적
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
