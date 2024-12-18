from flask import Flask, send_file, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
from wordcloud import WordCloud
from collections import Counter
from PIL import Image
import numpy as np
import re
import random
import requests
import logging
import os

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
client_id = "1EMqh9I3E2bRjOi9G8M6"
client_secret = "A1flID3HVB"

# BASE_DIR 설정 (프로젝트 최상위 폴더)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.path.join(BASE_DIR, "font", "NotoSansKR-VariableFont_wght.ttf")
MASK_IMAGE_PATH = os.path.join(BASE_DIR, "image", "Tree.png")

# 워드클라우드 색상 설정
tree_colors = ["#008000", "#FF0000", "#8B4513"]  # 초록, 빨강, 갈색
def tree_colors_func(word, font_size, position, orientation, random_state=None, **kwargs):
    return random.choice(tree_colors)

# 네이버 검색 API를 사용하여 뉴스 가져오기
def fetch_naver_news(display=5):
    keyword = "분리수거"  # 검색 키워드 고정
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    params = {
        "query": keyword,
        "display": display,
        "sort": "date"
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        logging.info("네이버 뉴스 API에서 데이터를 성공적으로 가져왔습니다.")
        return [item["description"] for item in data["items"]]
    except requests.exceptions.RequestException as e:
        logging.error(f"네이버 뉴스 API 요청 실패: {e}")
        return []

# 텍스트 전처리 및 명사 추출
def preprocess_text(text):
    tokens = re.findall(r'\b[가-힣]{2,}\b', text)
    stop_words = {"것", "수", "있다", "하다", "의", "를", "이", "에", "가", "은", "들"}
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
            color_func=tree_colors_func
        ).generate_from_frequencies(word_freq)
        wordcloud.to_file(output_path)
        logging.info("워드클라우드 이미지 생성 완료")
    except Exception as e:
        logging.error(f"Failed to generate wordcloud: {e}")

@app.route("/", methods=["GET"])
def home():
    return """
    <h1>Word Cloud API Server</h1>
    <p>Welcome! Use the <code>/api/wordcloud</code> endpoint to view the word cloud image for '분리수거'.</p>
    """

@app.route("/api/wordcloud", methods=["GET"])
def wordcloud_endpoint():
    logging.info("네이버 뉴스 API를 사용하여 '분리수거' 키워드를 검색합니다.")
    descriptions = fetch_naver_news(display=5)

    # 기사 내용이 없을 경우
    if not descriptions:
        return jsonify({"error": "기사를 가져올 수 없습니다."}), 500

    # 텍스트 전처리 및 워드클라우드 생성
    combined_text = " ".join(descriptions)
    word_freq = preprocess_text(combined_text)
    output_path = "wordcloud.png"
    generate_wordcloud(word_freq, output_path)

    return send_file(output_path, mimetype="image/png")

# Flask 서버 실행
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)