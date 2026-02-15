import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# 전역 변수로 서비스 객체를 캐싱합니다.
_youtube_service = None

def get_youtube_service():
    """
    YouTube Data API v3 service 객체를 반환합니다.
    (현재 비활성화됨 - 할당량 문제)
    """
    return None

    # global _youtube_service
    if _youtube_service:
        return _youtube_service

    # API 클라이언트 시크릿 파일 경로
    CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'client_secret.json')
    
    # 필요한 API 범위
    SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
    API_SERVICE_NAME = 'youtube'
    API_VERSION = 'v3'

    # 인증 흐름 실행
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    credentials = flow.run_local_server(port=0)
    
    # API 서비스 객체 생성 및 캐싱
    _youtube_service = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
    return _youtube_service

def search_youtube_video(youtube_service, query, max_results=1):
    """
    주어진 쿼리로 YouTube를 검색하고 첫 번째 비디오의 링크를 반환합니다.
    """
    print(f"[LOG][YouTube] search_youtube_video 호출: query='{query}'")
    if not youtube_service:
        print(f"[LOG][YouTube] 서비스 객체 없음.")
        return None
        
    search_response = youtube_service.search().list(
        q=query,
        part='snippet',
        maxResults=max_results,
        type='video'
    ).execute()
    
    videos = search_response.get('items', [])
    
    if not videos:
        print(f"[LOG][YouTube] 검색 결과 없음.")
        return None
        
    # 첫 번째 비디오의 ID를 사용하여 링크 생성
    video_id = videos[0]['id']['videoId']
    link = f"https://www.youtube.com/watch?v={video_id}"
    print(f"[LOG][YouTube] 링크 반환: {link}")
    return link

if __name__ == '__main__':
    # 테스트를 위한 직접 실행
    # client_secret.json 파일이 필요합니다.
    youtube_service = get_youtube_service() # 서비스 객체를 먼저 얻음
    query = "NewJeans Hype Boy"
    video_link = search_youtube_video(youtube_service, query) # 서비스 객체를 전달
    if video_link:
        print(f"'{query}' 검색 결과: {video_link}")
    else:
        print(f"'{query}'에 대한 비디오를 찾을 수 없습니다.")
