import os
import requests
from dotenv import load_dotenv

# uvicorn이 실행되는 'backend' 디렉토리의 .env 파일을 자동으로 찾아서 로드합니다.
load_dotenv()

GENIUS_API_TOKEN = os.getenv("GENIUS_ACCESS_TOKEN")
API_BASE_URL = "https://api.genius.com"

if not GENIUS_API_TOKEN:
    # .env 파일이 없거나, 변수가 설정되지 않은 경우를 대비한 경고
    print("Warning: GENIUS_ACCESS_TOKEN not found. Please ensure a .env file exists in the 'backend' directory with the token.")
    # raise ValueError("GENIUS_ACCESS_TOKEN not found in environment variables.")

headers = {'Authorization': f'Bearer {GENIUS_API_TOKEN}'}

def search_song(query: str):
    """Genius API로 노래를 검색합니다."""
    if not GENIUS_API_TOKEN:
        return {"error": "Genius API token is not configured."}
        
    search_url = f"{API_BASE_URL}/search"
    params = {'q': query}
    try:
        response = requests.get(search_url, params=params, headers=headers, timeout=5)
        response.raise_for_status()  # 2xx 상태 코드가 아닐 경우 예외 발생
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error searching Genius API: {e}")
        return None

def get_song_details(song_id: int):
    """Genius API로 특정 노래의 상세 정보를 가져옵니다."""
    if not GENIUS_API_TOKEN:
        return {"error": "Genius API token is not configured."}

    song_url = f"{API_BASE_URL}/songs/{song_id}"
    params = {'text_format': 'dom'} # 'dom', 'html', 'plain'
    try:
        response = requests.get(song_url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting song details from Genius API: {e}")
        return None

def get_artist_songs(artist_id: int, page: int = 1):
    """Genius API로 특정 아티스트의 노래 목록을 가져옵니다."""
    if not GENIUS_API_TOKEN:
        return {"error": "Genius API token is not configured."}

    artist_songs_url = f"{API_BASE_URL}/artists/{artist_id}/songs"
    params = {'sort': 'popularity', 'per_page': 50, 'page': page} # 페이지 파라미터 추가
    try:
        response = requests.get(artist_songs_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting artist songs from Genius API: {e}")
        return None
