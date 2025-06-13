import streamlit as st
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi

# 1) API 키 설정 및 초기화
gemini_api_key = st.sidebar.text_input(
    '🔑 Gemini API 키 입력', 
    value='AIzaSyDOTESWEgBjfYpkNsEeRQjSKgaVF_Y5D4Y', 
    type='password'  # ●●●로 마스킹함
)
if not gemini_api_key:
    gemini_api_key = os.getenv('GEMINI_API_KEY', '')
if not gemini_api_key:
    st.sidebar.error('API 키가 필요함. 입력하거나 환경변수에 설정하세요.')
    st.stop()

genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-2.0-flash')

# 2) 사이드바: URL 입력 + 슬라이더 설정
st.sidebar.header('설정')
yt_url = st.sidebar.text_input(
    '▶️ YouTube URL 붙여넣기', 
    'https://www.youtube.com/watch?v=kTFWhKrjMRs'
)
n_sentences = st.sidebar.slider(
    '🔖 요약 문장 수 선택', 
    min_value=1, 
    max_value=10, 
    value=3
)

# 3) 유틸 함수 정의
def get_ytid(url: str) -> str:
    """YouTube URL에서 영상 ID 추출함"""
    return url.split('/')[-1] if 'youtu.be' in url else url.split('=')[-1]

def fetch_transcript(ytid: str) -> str:
    """자막을 하나의 문자열로 합쳐 반환함"""
    try:
        lst = YouTubeTranscriptApi.get_transcript(ytid, languages=['ko','en'])
        return " ".join([entry['text'] for entry in lst])
    except Exception as e:
        st.error(f'자막 가져오기 실패: {e}')
        return ""

def chunk_text(text: str, max_chars: int = 3000) -> list[str]:
    """긴 텍스트를 max_chars 단위로 분할함"""
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

# 4) 요약 함수 (슬라이더 값 반영)
def summarize_chunks(chunks: list[str], n_sent: int) -> list[str]:
    """
    각 청크를 최대 n_sent 문장 이내로 요약함  
    - 부가 설명 없이 결과만 반환하도록 지시함
    """
    summaries = []
    for idx, chunk in enumerate(chunks, start=1):
        st.write(f'⏳ 청크 {idx}/{len(chunks)} 요약 중…')
        prompt = (
            f"다음 내용을 한국어로 요약하되, **최대 {n_sent}문장 이내**로 요약 결과만 반환하고 추가 설명은 하지 마세요:\n\n"
            + chunk
        )
        resp = model.generate_content(prompt)
        summaries.append(resp.text.strip())
    return summaries

def meta_summary(summaries: list[str], n_sent: int) -> str:
    """
    청크별 요약을 합쳐 최종적으로 최대 n_sent 문장 이내로 요약함  
    - 최종 결과만 반환하도록 지시함
    """
    combined = "\n\n".join(summaries)
    prompt = (
        f"여러 부분 요약을 합쳐 **최대 {n_sent}문장 이내**로 최종 요약 결과만 반환하고 추가 설명은 하지 마세요:\n\n"
        + combined
    )
    resp = model.generate_content(prompt)
    return resp.text.strip()

# 5) ‘영상 요약하기’ 버튼 처리
if st.sidebar.button('영상 요약하기') and yt_url:
    ytid = get_ytid(yt_url)
    transcript = fetch_transcript(ytid)
    if not transcript:
        st.stop()

    # 5-1) 자막 분할
    chunks = chunk_text(transcript)

    # 5-2) 청크별 요약 (슬라이더 반영)
    part_summaries = summarize_chunks(chunks, n_sentences)

    # 5-3) 메타 요약 (슬라이더 반영)
    final_summary = meta_summary(part_summaries, n_sentences)

    # 5-4) 결과 표시
    st.subheader('📄 최종 영상 요약 결과')
    st.write(final_summary)

# 6) 썸네일 추출 및 표시
if yt_url:
    thumb_url = f'http://img.youtube.com/vi/{get_ytid(yt_url)}/hqdefault.jpg'
    st.image(thumb_url)
    st.write('썸네일 URL:', thumb_url)
