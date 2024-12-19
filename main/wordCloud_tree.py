from flask import Flask, send_file, jsonify
from flask_cors import CORS
from wordcloud import WordCloud
from collections import Counter
from PIL import Image
import numpy as np
import re
import random
import requests
import os
import html
import logging

# 로그 설정
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler()
    ]
)

# Flask 앱 생성 및 CORS 설정
app = Flask(__name__)
CORS(app)

# 네이버 검색 API 인증 정보
CLIENT_ID = "1EMqh9I3E2bRjOi9G8M6"
CLIENT_SECRET = "A1flID3HVB"

# BASE_DIR 설정 (프로젝트 최상위 폴더)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FONT_PATH = os.path.join(BASE_DIR, "font", "NotoSansKR-VariableFont_wght.ttf")
MASK_IMAGE_PATH = os.path.join(BASE_DIR, "image", "Recycle.png")  # Recycle.png로 변경

# 워드클라우드 색상 설정
recycle_colors = ["#008000", "#0000FF", "#FFAA00"]
def recycle_colors_func(word, font_size, position, orientation, random_state=None, **kwargs):
    return random.choice(recycle_colors)

# 네이버 뉴스 데이터 가져오기
def fetch_naver_news(display=5):
    keyword = "환경"
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET
    }
    params = {
        "query": keyword,
        "display": display,
        "start": 1,
        "sort": "date"
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        logging.info(f"네이버 뉴스 API 응답 데이터: {data}")
        return data["items"]
    except requests.exceptions.RequestException as e:
        logging.error(f"네이버 뉴스 API 요청 실패: {e}")
        return []

# 텍스트 전처리 및 명사 추출
def preprocess_text(text):
    tokens = re.findall(r'\b[가-힣]{2,}\b', text)
    stop_words = {"것", "수", "있다", "하다", "의", "를", "이", "에", "가", "은", "들", "에서"}
    word_freq = Counter([word for word in tokens if word not in stop_words])
    return word_freq

# 워드클라우드 생성 함수
def generate_wordcloud(word_freq, output_path):
    try:
        mask = np.array(Image.open(MASK_IMAGE_PATH))
        wordcloud = WordCloud(
            font_path=FONT_PATH,
            background_color="white",
            mask=mask,
            color_func=recycle_colors_func
        ).generate_from_frequencies(word_freq)
        wordcloud.to_file(output_path)
        logging.info("워드클라우드 이미지 생성 완료")
    except Exception as e:
        logging.error(f"Failed to generate wordcloud: {e}")

@app.route("/", methods=["GET"])
def home():
    return """
    <h1>API Server</h1>
    <p>Endpoints:</p>
    <ul>
        <li>/api/wordcloud - 워드클라우드 이미지</li>
        <li>/api/news - 뉴스 리스트</li>
    </ul>
    """

@app.route("/api/wordcloud", methods=["GET"])
def wordcloud_endpoint():
    logging.info("워드클라우드 생성 요청을 처리합니다.")
    descriptions = [item["description"] for item in fetch_naver_news(display=5)]

    if not descriptions:
        return jsonify({"error": "기사를 가져올 수 없습니다."}), 500

    combined_text = " ".join(descriptions)
    word_freq = preprocess_text(combined_text)
    output_path = "wordcloud.png"
    generate_wordcloud(word_freq, output_path)

    return send_file(output_path, mimetype="image/png")

@app.route("/api/news", methods=["GET"])
def news_endpoint():
    logging.info("뉴스 리스트 요청을 처리합니다.")
    articles = fetch_naver_news(display=10)  # 최대 6개의 기사 불러오기

    if not articles:
        return jsonify({"error": "기사를 가져올 수 없습니다."}), 500

    # 중복 제거를 위한 Set 사용
    seen_titles = set()
    news_list = []
    for item in articles:
        title = html.unescape(item["title"].replace("<b>", "").replace("</b>", ""))
        if title not in seen_titles:  # 제목이 이미 처리된 적이 없으면 추가
            seen_titles.add(title)
            news_list.append({
                "title": title,
                "link": item["link"]
            })

    return jsonify(news_list)

# Flask 서버 실행
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)