import streamlit as st
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi

# — 1) API 키 로드 — 
# Streamlit Cloud에서는 앱 설정의 Secrets 메뉴에서 API 키를 설정하여 자동 적용

# API 키 로드 시도 순서:
# 1. Streamlit Secrets (배포 환경)
# 2. 환경 변수 (로컬 개발)

try:
    # 우선 Streamlit Secrets에서 API 키 로드 시도 (배포 환경용)
    gemini_api_key = st.secrets["general"]["gemini_api_key"]
    
    # 실제 API 키인지 확인 (기본 템플릿 텍스트 검사)
    if any(placeholder in gemini_api_key for placeholder in ["여기에_실제_API_키_입력", "YOUR_API_KEY", "AIzaSy"]):
        st.sidebar.warning("Streamlit Secrets에 유효한 API 키가 없습니다. 환경 변수를 확인합니다.")
        gemini_api_key = ""
    else:
        st.sidebar.success("✅ API 키가 자동으로 로드되었습니다.")
        
except Exception:
    # Secrets에서 로드 실패한 경우 환경 변수 확인
    gemini_api_key = os.environ.get("GEMINI_API_KEY", "")
    if gemini_api_key:
        st.sidebar.success("✅ 환경 변수에서 API 키를 로드했습니다.")

# API 키가 없는 경우에만 입력 필드 표시 (개발 환경용)
if not gemini_api_key:
    st.sidebar.warning("⚠️ API 키를 찾을 수 없습니다.")
    
    # 개발자용 안내 메시지 (축소 가능)
    with st.sidebar.expander("API 키 설정 방법 (개발자용)"):
        st.info("""
        **Streamlit Cloud 배포 시**:
        1. Streamlit Cloud의 앱 설정 → Secrets 메뉴에서 아래 내용 추가:
           ```
           [general]
           gemini_api_key = "실제_API_키_값"
           ```
        
        **로컬 개발 시**:
        1. .streamlit/secrets.toml 파일에 위와 동일한 내용 추가 또는
        2. 환경 변수 GEMINI_API_KEY 설정
        """)
    
    # 개발용으로만 직접 입력 필드 제공
    gemini_api_key = st.sidebar.text_input("Gemini API 키 입력:", type="password")
    if not gemini_api_key:
        st.sidebar.error("⚠️ API 키를 입력해야 앱을 사용할 수 있습니다.")
        st.stop()

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
