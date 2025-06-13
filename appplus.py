import streamlit as st
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi

# — 1) API 키 로드 — 
#  a) 로컬 개발: .streamlit/secrets.toml 사용
#  b) 배포 환경: 환경변수 GEMINI_API_KEY 또는 Streamlit Cloud Secrets 사용

# 1) 먼저 환경 변수에서 API 키 확인
gemini_api_key = os.environ.get("GEMINI_API_KEY", "")

# 2) 환경 변수에 없으면 secrets.toml에서 로드 시도
if not gemini_api_key:
    try:
        gemini_api_key = st.secrets["general"]["gemini_api_key"]
        st.sidebar.success("Secrets에서 API 키를 성공적으로 로드했습니다.")
    except Exception as e:
        st.sidebar.error(f"Secrets 로드 오류: {e}")
        st.sidebar.info("""
        API 키 설정 방법:
        1. 로컬 환경: .streamlit/secrets.toml 파일에 아래 내용 추가
           [general]
           gemini_api_key = "YOUR_API_KEY"
           
        2. 환경 변수: GEMINI_API_KEY 설정
        
        3. Streamlit Cloud: 앱 설정의 Secrets 메뉴에서 설정
        """)
        gemini_api_key = ""

# 하드코딩된 API 키 (개발용, 배포 시 제거하세요!)
if not gemini_api_key:
    # 여기에 개발 중 임시로 API 키를 입력할 수 있습니다.
    # 주의: 실제 코드 배포 시 이 부분은 반드시 제거하세요!
    gemini_api_key = st.text_input("Gemini API 키 입력:", type="password")
    if not gemini_api_key:
        st.stop()

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
