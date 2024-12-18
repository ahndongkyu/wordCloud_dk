import requests

# 네이버 검색 API 인증 정보
client_id = "1EMqh9I3E2bRjOi9G8M6"
client_secret = "A1flID3HVB"

# 검색어 입력
search = input("검색할 키워드를 입력해주세요: ")

# API 요청 URL 생성
url = "https://openapi.naver.com/v1/search/news.json"
params = {
    "query": search,  # 검색어
    "display": 5,     # 가져올 결과 개수 (1~100)
    "start": 1,       # 검색 시작 위치
    "sort": "date"    # 정렬 기준: 최신순(date), 정확도순(sim)
}

# 헤더 설정
headers = {
    "X-Naver-Client-Id": client_id,
    "X-Naver-Client-Secret": client_secret
}

try:
    # API 요청
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()  # HTTP 오류 발생 시 예외 처리
    result = response.json()  # JSON 응답 처리

    # 뉴스 기사 데이터 출력
    print(f"\n{len(result['items'])}개의 기사를 가져왔습니다.")
    for idx, item in enumerate(result["items"], 1):
        # HTML 태그 제거 및 데이터 출력
        title = item["title"].replace("<b>", "").replace("</b>", "")
        link = item["link"]
        description = item["description"].replace("<b>", "").replace("</b>", "")
        print(f"\n[{idx}] 제목: {title}")
        print(f"링크: {link}")
except requests.exceptions.RequestException as e:
    print(f"API 요청 중 오류 발생: {e}")