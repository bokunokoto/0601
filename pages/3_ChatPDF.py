import streamlit as st
from openai import OpenAI
import time

st.title("📄 ChatPDF - 문서 기반 질의응답")

api_key = st.session_state.get("openai_api_key", "")
if not api_key:
    st.warning("메인 페이지에서 OpenAI API Key를 먼저 등록해 주세요.")
    st.stop()

client = OpenAI(api_key=api_key)

# 상태 관리를 위한 세션 상태 정의
if "pdf_messages" not in st.session_state:
    st.session_state.pdf_messages = []
if "assistant_id" not in st.session_state:
    st.session_state.assistant_id = None
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "vector_store_id" not in st.session_state:
    st.session_state.vector_store_id = None

# 리소스 해제용 리셋 버튼 구현 (Vector store 및 Assistant 제거)
if st.button("Clear: 문서 데이터 및 대화 완전히 지우기"):
    try:
        if st.session_state.assistant_id:
            client.beta.assistants.delete(st.session_state.assistant_id)
        if st.session_state.vector_store_id:
            client.beta.vector_stores.delete(st.session_state.vector_store_id)
    except Exception:
        pass
    st.session_state.pdf_messages = []
    st.session_state.assistant_id = None
    st.session_state.thread_id = None
    st.session_state.vector_store_id = None
    st.success("모든 파일 인덱싱과 대화 기록이 청소되었습니다.")
    st.rerun()

# 1. 파일 업로더 컴포넌트 배치
uploaded_file = st.file_uploader("분석할 PDF 파일을 업로드하세요 (1개만 지원)", type=["pdf"])

# 2. 파일이 업로드되었고, 아직 백엔드 세팅이 완료되지 않았다면 OpenAI File Search 파이프라인 가동
if uploaded_file and not st.session_state.assistant_id:
    with st.spinner("OpenAI 서버에 문서를 업로드하고 의미적 분석 벡터 데이터를 생성하는 중..."):
        try:
            # 임시 파일 저장 혹은 Bytes 바인딩하여 OpenAI에 전달
            uploaded_file_obj = client.files.create(
                file=(uploaded_file.name, uploaded_file.read(), "application/pdf"),
                purpose="assistants"
            )
            
            # Vector Store 생성 및 파일 링크 연결
            vector_store = client.beta.vector_stores.create(name=f"VS_{uploaded_file.name}")
            client.beta.vector_stores.files.create(
                vector_store_id=vector_store.id,
                file_id=uploaded_file_obj.id
            )
            
            # File Search 도구가 활성화된 Assistant 챗봇 에이전트 생성
            assistant = client.beta.assistants.create(
                name="PDF 분석 전문가",
                instructions="당신은 첨부된 문서를 완벽히 분석하여 사용자의 질문에 정확하게 대답하는 비서입니다. 문서에 명시된 사실에만 근거하여 답하세요.",
                model="gpt-4o-mini",
                tools=[{"type": "file_search"}],
                tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}}
            )
            
            # 개별 사용자와의 대화 세션 스트림을 위한 Thread 생성
            thread = client.beta.threads.create()
            
            # 추후 접근을 위해 세션 상태에 저장
            st.session_state.assistant_id = assistant.id
            st.session_state.thread_id = thread.id
            st.session_state.vector_store_id = vector_store.id
            st.success("문서 업로드 및 AI 챗봇 연결 완료! 대화를 시작하세요.")
        except Exception as e:
            st.error(f"초기 세팅 에러: {e}")

# 3. 기존 대화 기록 출력
for msg in st.session_state.pdf_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 4. 사용자의 문서 질문 채팅 핸들링
if prompt := st.chat_input("업로드한 문서에 관해 궁금한 점을 질문해 보세요."):
    if not st.session_state.assistant_id:
        st.error("먼저 PDF 문서를 상단에 업로드해 주세요.")
        st.stop()
        
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.pdf_messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        with st.spinner("문서 본문 탐색 및 답변 추론 중..."):
            try:
                # 사용자의 질문 메시지를 OpenAI Thread 대화방에 기록 전송
                client.beta.threads.messages.create(
                    thread_id=st.session_state.thread_id,
                    role="user",
                    content=prompt
                )
                
                # Assistant가 답을 구하도록 Run 실행 명령 요청
                run = client.beta.threads.runs.create(
                    thread_id=st.session_state.thread_id,
                    assistant_id=st.session_state.assistant_id
                )
                
                # 백엔드 계산 상태 폴링 완료 대기
                while run.status in ["queued", "in_progress"]:
                    time.sleep(0.5)
                    run = client.beta.threads.runs.retrieve(
                        thread_id=st.session_state.thread_id,
                        run_id=run.id
                    )
                
                # 최종 완료된 메시지 내역 정렬 후 가장 최근 AI 응답 추출
                messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
                assistant_reply = messages.data[0].content[0].text.value
                
                st.markdown(assistant_reply)
                st.session_state.pdf_messages.append({"role": "assistant", "content": assistant_reply})
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
