import streamlit as st
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi

# — 1) API 키 로드 — 
# API 키 로드 시도 순서:
# 1. 하드코딩된 API 키 (배포 환경용, 실제 배포 시 여기에 API 키 입력)
# 2. Streamlit Secrets (중요: .gitignore에 등록하여 깃에 업로드되지 않도록 해야 함)
# 3. 환경 변수 (로컬 개발)
# 4. 사용자 입력 (UI)

# 배포 환경에서 사용할 API 키 (실제 배포 시에만 아래 값을 실제 API 키로 변경)
# 주의: 이 방법은 코드가 공개되는 경우 API 키가 노출될 수 있으니 주의하세요
GEMINI_API_KEY = "여기에_실제_API_키_입력"

# 1. 먼저 하드코딩된 API 키 확인
gemini_api_key = GEMINI_API_KEY if GEMINI_API_KEY and "여기에_실제_API_키_입력" not in GEMINI_API_KEY else ""
api_source = "하드코딩된 키" if gemini_api_key else ""

# 2. API 키가 없으면 Streamlit Secrets에서 로드 시도
if not gemini_api_key:
    try:
        # Secrets 정보 출력 (디버깅용)
        available_secrets = list(st.secrets.keys())
        if "general" in available_secrets:
            general_keys = list(st.secrets["general"].keys())
            st.sidebar.info(f"사용 가능한 Secrets: {available_secrets}, general 키: {general_keys}")
        else:
            st.sidebar.warning(f"사용 가능한 Secrets: {available_secrets}, 'general' 키가 없습니다.")
            
        # API 키 로드 시도
        gemini_api_key = st.secrets["general"]["gemini_api_key"]
        api_source = "Streamlit Secrets"
        
        # 유효한 키인지 확인 (예시 텍스트 검사)
        if any(placeholder in gemini_api_key for placeholder in [
            "여기에_실제_API_키_입력", "YOUR_API_KEY", "실제_API_키를_여기에_입력하세요"
        ]):
            gemini_api_key = ""
            st.sidebar.warning("Secrets에 실제 API 키가 아닌 예시 텍스트가 있습니다.")
    except Exception as e:
        st.sidebar.error(f"Secrets 로드 오류: {str(e)}")
        gemini_api_key = ""

# 3. 환경 변수에서 API 키 확인
if not gemini_api_key:
    gemini_api_key = os.environ.get("GEMINI_API_KEY", "")
    api_source = "환경 변수" if gemini_api_key else ""

# 4. API 키가 없는 경우 사용자 입력 필드 표시
if not gemini_api_key:
    st.sidebar.warning("API 키를 찾을 수 없습니다.")
    
    # 배포 안내 메시지
    st.sidebar.info("""
    ### Streamlit Cloud 배포 시
    
    1. **앱 비공개 설정**: 
       - 앱 설정 → Sharing → "Private" 선택
    
    2. **API 키 설정 방법**:
       - 앱 설정 → Secrets 메뉴에서 아래 내용 추가:
       ```
       [general]
       gemini_api_key = "실제_API_키_값"
       ```
       
    3. **또는 코드에 직접 API 키 입력**:
       - 코드 상단의 `GEMINI_API_KEY` 변수에 직접 API 키 입력
       - 단, 이 방법은 코드가 공개되면 API 키가 노출될 수 있음
    """)
    
    # 직접 입력 필드
    gemini_api_key = st.sidebar.text_input("Gemini API 키 입력:", type="password")
    api_source = "사용자 입력" if gemini_api_key else ""
    
    if not gemini_api_key:
        st.sidebar.error("API 키를 입력해주세요.")
        st.stop()

# API 키 로드 성공 시
if gemini_api_key:
    st.sidebar.success(f"✅ API 키 로드 성공! (출처: {api_source})")
    
    # API 키의 길이와 첫 4자리 마스킹하여 표시 (디버깅용)
    if len(gemini_api_key) > 8:
        masked_key = f"{gemini_api_key[:4]}...{gemini_api_key[-4:]}" 
        st.sidebar.info(f"API 키 확인: {masked_key} (총 {len(gemini_api_key)}자)")
    else:
        st.sidebar.warning("API 키가 너무 짧습니다. 유효한지 확인해주세요.")

# 디버깅 도움이 될 경우 활성화 (API 키의 처음 5자만 표시)
# if gemini_api_key:
#     masked_key = gemini_api_key[:5] + "..." if len(gemini_api_key) > 5 else "유효하지 않음"
#     st.sidebar.info(f"API 키: {masked_key}")

# — 2) SDK 초기화 — 
try:
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    # 모델이 제대로 로드되었는지 API 테스트 (선택 사항)
    try:
        # 간단한 API 테스트 (무거운 작업 방지를 위해 짧은 요청)
        test_response = model.generate_content("안녕하세요")
        if test_response:
            st.sidebar.success("✅ API 연결 테스트 성공!")
    except Exception as e:
        st.sidebar.warning(f"API 테스트 실패: {str(e)[:100]}...")
except Exception as e:
    st.sidebar.error(f"SDK 초기화 오류: {str(e)[:100]}...")
    st.stop()

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
