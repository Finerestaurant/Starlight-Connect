import requests
import re
import time
import random
from urllib.parse import quote_plus

def search_youtube_video_crawler(query: str) -> str | None:
    """
    YouTube 검색 페이지를 크롤링하여 첫 번째 동영상의 링크를 반환합니다.
    API 키를 사용하지 않으며, 할당량 제한이 없습니다.
    """
    encoded_query = quote_plus(query)
    url = f"https://www.youtube.com/results?search_query={encoded_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        # 랜덤 지연 (1~3초) - 차단 방지
        time.sleep(random.uniform(1.0, 3.0))
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # HTML 내에서 videoId 추출 (가장 먼저 나오는 videoId가 첫 번째 결과일 확률 높음)
        # "videoId":"VIDEO_ID" 패턴 찾기
        video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', response.text)
        
        if video_ids:
            # 중복 제거 및 첫 번째 유효 ID 반환
            # (가끔 광고나 플레이리스트 ID가 섞일 수 있으나, 상위 결과는 보통 정확함)
            first_video_id = video_ids[0]
            return f"https://www.youtube.com/watch?v={first_video_id}"
            
        return None

    except Exception as e:
        print(f"[LOG][YouTubeCrawler] 크롤링 중 오류 발생: {e}")
        return None

if __name__ == "__main__":
    # 테스트 코드
    test_query = "NewJeans Hype Boy"
    print(f"Testing query: {test_query}")
    result = search_youtube_video_crawler(test_query)
    print(f"Result: {result}")
