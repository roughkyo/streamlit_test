import streamlit as st
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi

# — 1) API 키 로드 — 
#  a) 로컬 개발: .streamlit/secrets.toml 사용
#  b) 배포 환경: 환경변수 GEMINI_API_KEY 또는 Streamlit Cloud Secrets 사용
#  c) 또는 UI를 통한 직접 입력

# 1) 먼저 환경 변수에서 API 키 확인
gemini_api_key = os.environ.get("GEMINI_API_KEY", "")
api_key_source = "환경 변수"

# 2) 환경 변수에 없으면 secrets.toml에서 로드 시도
if not gemini_api_key:
    try:
        gemini_api_key = st.secrets["general"]["gemini_api_key"]
        # 기본 텍스트가 그대로 있는지 확인
        if gemini_api_key in ["여기에_실제_API_키_입력", "YOUR_API_KEY"]:
            gemini_api_key = ""  # 실제 키가 아니므로 비움
            raise ValueError("유효한 API 키가 아닙니다.")
        api_key_source = "Secrets 파일"
    except Exception as e:
        gemini_api_key = ""
        api_key_source = "오류"

# 3) UI에서 직접 API 키 입력 (환경 변수와 secrets.toml에서 모두 로드 실패했을 경우)
if not gemini_api_key:
    st.sidebar.warning("API 키를 찾을 수 없습니다. 아래 방법 중 하나로 설정해주세요.")
    st.sidebar.info("""
    API 키 설정 방법:
    1. 로컬 환경: .streamlit/secrets.toml 파일에 아래 내용 추가
       [general]
       gemini_api_key = "실제_API_키_값"
       
    2. 환경 변수: GEMINI_API_KEY 설정
    
    3. Streamlit Cloud: 앱 설정의 Secrets 메뉴에서 설정
    
    4. 또는 아래에 직접 입력 (일회성)
    """)
    
    # UI에서 직접 API 키 입력
    gemini_api_key = st.sidebar.text_input("Gemini API 키 입력:", type="password", key="api_key_input")
    
    if gemini_api_key:
        api_key_source = "직접 입력"
        st.sidebar.success("API 키가 입력되었습니다.")
    else:
        st.sidebar.error("API 키를 입력해주세요.")
        st.stop()

# API 키 로드 성공 시 표시
st.sidebar.success(f"API 키 로드 성공 (출처: {api_key_source})")

# 디버깅 도움이 될 경우 활성화 (API 키의 처음 5자만 표시)
# if gemini_api_key:
#     masked_key = gemini_api_key[:5] + "..." if len(gemini_api_key) > 5 else "유효하지 않음"
#     st.sidebar.info(f"API 키: {masked_key}")

# — 2) SDK 초기화 — 
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel("gemini-2.0-flash")

# — 3) 사이드바 UI — 
st.sidebar.header("설정")
yt_url = st.sidebar.text_input(
    "▶️ YouTube URL 붙여넣기",
    "https://www.youtube.com/watch?v=kTFWhKrjMRs"
)
n_sentences = st.sidebar.slider(
    "🔖 요약 문장 수 선택",
    min_value=1, max_value=10, value=3
)

# — 4) 유틸 함수 정의 — 
def get_ytid(url: str) -> str:
    return url.split("/")[-1] if "youtu.be" in url else url.split("=")[-1]

def fetch_transcript(ytid: str) -> str:
    try:
        lst = YouTubeTranscriptApi.get_transcript(ytid, languages=["ko","en"])
        return " ".join([e["text"] for e in lst])
    except Exception as e:
        st.error(f"자막 가져오기 실패: {e}")
        return ""

def chunk_text(text: str, max_chars: int = 3000) -> list[str]:
    return [text[i : i + max_chars] for i in range(0, len(text), max_chars)]

def summarize_chunks(chunks: list[str], n_sent: int) -> list[str]:
    summaries = []
    for idx, chunk in enumerate(chunks, start=1):
        st.write(f"⏳ 청크 {idx}/{len(chunks)} 요약 중…")
        prompt = (
            f"다음 내용을 한국어로 요약하되, 최대 {n_sent}문장 이내로 **요약 결과만** 반환하고 추가 설명은 하지 마세요:\n\n"
            + chunk
        )
        resp = model.generate_content(prompt)
        summaries.append(resp.text.strip())
    return summaries

def meta_summary(summaries: list[str], n_sent: int) -> str:
    combined = "\n\n".join(summaries)
    prompt = (
        f"여러 부분 요약을 합쳐 최대 {n_sent}문장 이내로 **최종 요약 결과만** 반환하고 추가 설명은 하지 마세요:\n\n"
        + combined
    )
    resp = model.generate_content(prompt)
    return resp.text.strip()

# — 5) ‘영상 요약하기’ 처리 — 
if st.sidebar.button("영상 요약하기") and yt_url:
    ytid = get_ytid(yt_url)
    transcript = fetch_transcript(ytid)
    if not transcript:
        st.stop()

    chunks = chunk_text(transcript)
    part_summaries = summarize_chunks(chunks, n_sentences)
    final_summary = meta_summary(part_summaries, n_sentences)

    st.subheader("📄 최종 영상 요약 결과")
    st.write(final_summary)

# — 6) 썸네일 표시 — 
if yt_url:
    thumb_url = f"http://img.youtube.com/vi/{get_ytid(yt_url)}/hqdefault.jpg"
    st.image(thumb_url)
    st.write("썸네일 URL:", thumb_url)
