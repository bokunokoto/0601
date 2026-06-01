import streamlit as st
from openai import OpenAI

st.title("📚 국립부경대학교 도서관 안내 챗봇")

api_key = st.session_state.get("openai_api_key", "")
if not api_key:
    st.warning("메인 페이지에서 OpenAI API Key를 등록해야 사용 가능합니다.")
    st.stop()

# 1. 교수님 요구사항: 국립부경대학교 도서관 규정을 문자열 변수로 보관
# (실제 과제 제출 시 부경대 규정집 페이지에서 텍스트를 일부 복사해 따옴표 안에 채우세요!)
LIBRARY_REGULATION = """
[국립부경대학교 도서관 규정 핵심 요약]
1. 휴관일: 일요일, 국정공휴일, 개교기념일, 기타 관장이 필요하다고 인정하여 지정한 날. (다만 열람실은 상황에 따라 개방 가능)
2. 대출 자격 및 권수/기간:
   - 학부생(대학생): 최대 5권, 대출 기간 10일
   - 대학원생: 최대 10권, 대출 기간 30일
   - 전임교원: 최대 30권, 대출 기간 90일
3. 반납 연기: 연체되지 않은 도서에 한하여 1회에 한해 10일 연장 가능.
"""

if "lib_messages" not in st.session_state:
    st.session_state.lib_messages = []

# 대화 리셋 기능
if st.button("대화 초기화"):
    st.session_state.lib_messages = []
    st.rerun()

# 기존 내역 표시
for msg in st.session_state.lib_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 질문 입력 및 처리
if prompt := st.chat_input("도서관 규정에 대해 물어보세요! (예: 학부생 책 대여는 몇 권까지인가요?)"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.lib_messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        try:
            client = OpenAI(api_key=api_key)
            
            # 💡 핵심 테크닉: System 메시지에 도서관 규정 컨텍스트를 강제로 주입!
            system_prompt = f"당신은 국립부경대학교 도서관 가이드입니다. 오직 아래 제공된 규정 내용에 기반하여 친절하게 답변하세요. 규정에 없는 내용은 모른다고 답하세요.\n\n{LIBRARY_REGULATION}"
            
            messages_payload = [{"role": "system", "content": system_prompt}] + [
                {"role": m["role"], "content": m["content"]} for m in st.session_state.lib_messages
            ]
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages_payload
            )
            answer = response.choices[0].message.content
            st.markdown(answer)
            st.session_state.lib_messages.append({"role": "assistant", "content": answer})
        except Exception as e:
            st.error(f"오류: {e}")
