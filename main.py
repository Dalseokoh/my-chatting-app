import streamlit as st
from openai import OpenAI

# ------------------------------------------------------------
# 1) 페이지 기본 설정
# ------------------------------------------------------------
st.set_page_config(page_title="AI 데이터 분석 선생님", page_icon="📊")
st.title("📊 AI 데이터 분석 선생님")

# ------------------------------------------------------------
# 2) Solar API 클라이언트 만들기
#    - API 키는 코드에 직접 쓰지 않고, 스트림릿 클라우드의
#      "Secrets"(비밀 금고)에 저장된 SOLAR_API_KEY 값을 읽어옵니다.
#    - 로컬(내 컴퓨터)에서 테스트할 때는 프로젝트 폴더에
#      .streamlit/secrets.toml 파일을 만들고 아래처럼 적어두면 됩니다.
#        SOLAR_API_KEY = "여기에_내_API_키"
# ------------------------------------------------------------
try:
    api_key = st.secrets["SOLAR_API_KEY"]
except Exception:
    st.error(
        "🔑 API 키를 찾을 수 없어요. 스트림릿 클라우드의 'Secrets' 설정에 "
        "SOLAR_API_KEY 값을 등록해 주세요."
    )
    st.stop()

# openai 라이브러리를 그대로 사용하되, 접속 주소만 Solar API 주소로 바꿔줍니다.
client = OpenAI(
    api_key=api_key,
    base_url="https://api.upstage.ai/v1",
)

# 사용할 모델 이름 (반드시 이 이름 그대로 사용)
MODEL_NAME = "solar-open2"

# AI에게 주는 성격(시스템 프롬프트)
SYSTEM_PROMPT = "너는 따뜻하고 친절한 데이터 분석 선생님이야. 반드시 순수 한국어로만 답해."

# ------------------------------------------------------------
# 3) 대화 기록 저장하기 (세션 상태 사용)
#    - st.session_state는 사용자가 페이지를 새로고침하지 않는 한
#      값이 계속 유지되는 "임시 저장 공간"입니다.
#    - 여기에 지금까지 주고받은 메시지들을 리스트로 쌓아둡니다.
# ------------------------------------------------------------
if "messages" not in st.session_state:
    # 화면에는 시스템 프롬프트를 보여주지 않고, 대화 내용만 저장합니다.
    st.session_state.messages = []

# ------------------------------------------------------------
# 4) 지금까지의 대화 내용을 화면에 말풍선으로 그려주기
# ------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ------------------------------------------------------------
# 5) 사용자 입력창 만들기
# ------------------------------------------------------------
user_input = st.chat_input("궁금한 내용을 물어보세요!")

if user_input:
    # 5-1) 사용자가 보낸 메시지를 대화 기록에 추가하고 화면에 표시
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 5-2) AI에게 보낼 전체 메시지 목록 만들기
    #      (시스템 프롬프트 + 지금까지의 모든 대화)
    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages

    # 5-3) AI의 답변을 말풍선 안에서 스트리밍(실시간 타이핑처럼)으로 보여주기
    with st.chat_message("assistant"):
        placeholder = st.empty()  # 실시간으로 글자를 채워 넣을 빈 공간
        full_answer = ""          # 지금까지 받은 답변 글자를 모아둘 변수

        try:
            # reasoning_effort="none" 으로 설정해서 생각(추론) 과정을 생략,
            # 답변이 더 빠르게 나오도록 합니다.
            stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=api_messages,
                reasoning_effort="none",
                stream=True,
            )

            # 스트림에서 조각(chunk)이 도착할 때마다 화면을 갱신
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    full_answer += delta
                    placeholder.markdown(full_answer + "▌")  # 커서 느낌 추가

            # 스트리밍이 끝나면 커서 없이 최종 답변만 표시
            placeholder.markdown(full_answer)

        except Exception:
            # 오류가 나면 개발자용 에러 메시지 대신, 친절한 한국어 안내를 보여줍니다.
            full_answer = (
                "😥 지금은 답변을 가져오는 데 문제가 생겼어요. "
                "잠시 후에 다시 시도해 주시겠어요? "
                "문제가 계속되면 API 키 설정이나 인터넷 연결을 확인해 보세요."
            )
            placeholder.markdown(full_answer)

    # 5-4) AI의 답변도 대화 기록에 저장해서, 다음 질문에서도 기억하게 함
    st.session_state.messages.append({"role": "assistant", "content": full_answer})
