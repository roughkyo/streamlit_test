import streamlit as st
st.title('🖼️ yt-img-app')
st.header('YouTube 썸네일 이미지 추출기 앱')

with st.expander('이 앱에 대하여'):
    st.write('이 앱은 YouTube 동영상의 썸네일 이미지를 추출해 제공함')
    st.write('사용법: 유튜브 주소가 https://www.youtube.com/watch?v=p2EGFTsXbyM&ab_channel=YTN 라면? ')
    st.write('✅ab_channel 전주소까지만 추출 ➡️ "https://youtu.be/p2EGFTsXbyM"  까지만 입력')


st.sidebar.header('설정')
img_dict = {'Max': 'maxresdefault', 'High': 'hqdefault', 'Medium': 'mqdefault', 'Standard': 'sddefault'}
selected_img_quality = st.sidebar.selectbox('이미지 품질 선택', ['Max', 'High', 'Medium', 'Standard'])
img_quality = img_dict[selected_img_quality]

yt_url = st.text_input('YouTube URL 붙여넣기', 'https://www.youtube.com/watch?v=kTFWhKrjMRs')


def get_ytid(input_url):
  if 'youtu.be' in input_url:
    ytid = input_url.split('/')[-1]
  if 'youtube.com' in input_url:
    ytid = input_url.split('=')[-1]
  return ytid


# YouTube 썸네일 이미지 표시
if yt_url != '':
  ytid = get_ytid(yt_url) # yt or yt_url

  yt_img = f'http://img.youtube.com/vi/{ytid}/{img_quality}.jpg'
  st.image(yt_img)
  st.write('YouTube 동영상 썸네일 이미지 URL: ', yt_img)
else:
  st.write('☝️ URL을 입력해 계속하세요 ...')
