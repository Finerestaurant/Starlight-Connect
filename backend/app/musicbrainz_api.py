import requests
import json
import time
import sys
from typing import Dict, Any, List, Optional

from fastapi import HTTPException

BASE_URL = "https://musicbrainz.org/ws/2/"
HEADERS = {
    "User-Agent": "KpopGraphApp/0.1 (contact@kpopgraph.com)", # 실제 이메일 주소로 변경 필요
    "Accept": "application/json"
}
MAX_RETRIES = 5
RETRY_DELAY_SECONDS = 2
API_CALL_DELAY_SECONDS = 1 # MusicBrainz API Rate Limit (1 req/sec)

MAX_RAW_LOG_CHARS = 500 # 원본 JSON 응답의 최대 로깅 문자 수

def _make_api_call(url: str, entity_type: str = "데이터") -> Dict[str, Any]:
    """MusicBrainz API 호출을 수행하고, 실패 시 재시도 로직을 포함합니다."""
    response_data = None
    for attempt in range(MAX_RETRIES):
        try:
            print(f"[{entity_type}] API 호출 (시도 {attempt + 1}/{MAX_RETRIES}): {url}")
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status() # HTTP 오류 발생 시 예외 발생 (4xx, 5xx)
            response_data = response.json()
            print(f"[{entity_type}] API 호출 성공!")
            # 원본 JSON 응답의 일부를 로그에 기록
            print(f"[{entity_type}] 원본 응답 (일부): {json.dumps(response_data, ensure_ascii=False)[:MAX_RAW_LOG_CHARS]}...")
            break # 성공했으므로 루프 탈출
        except requests.exceptions.RequestException as e:
            print(f"[{entity_type}] API 요청 에러 발생: {e}")
            if attempt < MAX_RETRIES - 1:
                print(f"{RETRY_DELAY_SECONDS}초 후 재시도...")
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                print(f"[{entity_type}] 최대 재시도 횟수 {MAX_RETRIES}회를 초과했습니다. 종료합니다.")
                raise HTTPException(
                    status_code=503,
                    detail=f"MusicBrainz API 통신 중 에러 발생: {e}"
                )
        except json.JSONDecodeError as e:
            print(f"[{entity_type}] JSON 디코딩 에러 발생: {e}")
            if response:
                print(f"응답 내용: {response.text[:500]}")
            raise HTTPException(
                status_code=500,
                detail=f"MusicBrainz API 응답 파싱 중 에러 발생: {e}"
            )
        except Exception as e:
            print(f"[{entity_type}] 예상치 못한 에러 발생: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"MusicBrainz API 호출 중 예상치 못한 에러 발생: {e}"
            )
        finally:
            # API Rate Limit 준수 (성공 여부와 관계없이)
            time.sleep(API_CALL_DELAY_SECONDS) 
            
    if not response_data:
        raise HTTPException(
            status_code=500,
            detail=f"MusicBrainz API에서 {entity_type} 데이터를 가져오는 데 실패했습니다."
        )
    return response_data


def search_artist(query: str) -> Optional[Dict[str, Any]]:
    """
    아티스트 이름으로 MusicBrainz에서 검색하고, 가장 일치하는 아티스트 정보를 반환합니다.
    """
    print(f"[LOG][MusicBrainz] search_artist 호출: query='{query}'")
    url = f"{BASE_URL}artist/?query={query}&fmt=json"
    result = _make_api_call(url, entity_type="아티스트 검색")
    
    if result and result.get('artists'):
        # 가장 일치도가 높은 첫 번째 아티스트 선택
        artist = result['artists'][0]
        print(f"[LOG][MusicBrainz] search_artist 결과: {artist.get('name')} ({artist.get('id')})")
        return artist
    print(f"[LOG][MusicBrainz] search_artist 결과 없음.")
    return None

def get_artist_by_mbid(mbid: str) -> Optional[Dict[str, Any]]:
    """
    아티스트의 MBID로 상세 정보와 함께 모든 릴리즈(앨범 등) 정보를 가져옵니다.
    """
    print(f"[LOG][MusicBrainz] get_artist_by_mbid 호출: mbid='{mbid}'")
    # 'releases' 인자를 포함하여 해당 아티스트의 모든 릴리즈 정보를 함께 요청합니다.
    url = f"{BASE_URL}artist/{mbid}?inc=releases&fmt=json"
    result = _make_api_call(url, entity_type="아티스트 상세 정보")
    
    # 직접 API 호출 시 응답 자체가 artist 객체이므로, 'id' 존재 여부로 확인
    if result and result.get('id'):
        print(f"[LOG][MusicBrainz] get_artist_by_mbid 성공: {result.get('name')}")
        return result
    print(f"[LOG][MusicBrainz] get_artist_by_mbid 실패 (ID 없음)")
    return None

def get_artist_recordings(artist_mbid: str, limit: int = 100, offset: int = 0) -> Optional[Dict[str, Any]]:
    """
    아티스트의 모든 Recording(곡) 목록을 가져옵니다. (페이지네이션 지원)
    """
    print(f"[LOG][MusicBrainz] get_artist_recordings 호출: mbid='{artist_mbid}', offset={offset}, limit={limit}")
    # inc 파라미터에 필요한 정보를 모두 포함
    # artist-credits: 가창자 정보
    # artist-rels: 편곡, 프로듀서 등 아티스트 관계
    # work-rels: 작곡, 작사 등 작품(Work) 관계
    url = f"{BASE_URL}recording?artist={artist_mbid}&inc=artist-credits+work-rels+artist-rels&limit={limit}&offset={offset}&fmt=json"
    
    result = _make_api_call(url, entity_type=f"아티스트 곡 목록 (Offset: {offset})")
    
    count = len(result.get('recordings', [])) if result else 0
    print(f"[LOG][MusicBrainz] get_artist_recordings 반환: {count}곡")
    return result

def get_artist_image_from_relations(artist_mbid: str) -> Optional[str]:
    """
    아티스트의 관계(relations)에서 'image' 타입의 URL을 찾아 반환합니다.
    Wikimedia Commons URL을 우선적으로 찾습니다.
    """
    print(f"[LOG][MusicBrainz] get_artist_image_from_relations 호출: mbid='{artist_mbid}'")
    url = f"{BASE_URL}artist/{artist_mbid}?inc=url-rels&fmt=json"
    result = _make_api_call(url, entity_type=f"아티스트 이미지 관계 (MBID: {artist_mbid})")
    
    if not (result and result.get('relations')):
        print(f"[LOG][MusicBrainz] 관계 데이터 없음.")
        return None

    image_url = None
    for rel in result['relations']:
        if rel.get('type') == 'image':
            target_url = rel.get('url', {}).get('resource')
            if target_url:
                # 위키미디어 커먼스 URL을 우선적으로 선택
                if 'commons.wikimedia.org' in target_url:
                    print(f"[LOG][MusicBrainz] Wikimedia 이미지 찾음: {target_url}")
                    return target_url
                if not image_url: # 다른 이미지 URL이 아직 없으면 일단 저장
                    image_url = target_url
    
    print(f"[LOG][MusicBrainz] 이미지 URL 반환: {image_url}")
    return image_url


def get_release_details_by_mbid(mbid: str) -> Optional[Dict[str, Any]]:
    """
    릴리즈(앨범)의 MBID로 상세 정보, 포함된 곡(레코딩), 참여 아티스트 관계를 가져옵니다.
    """
    # 필요한 모든 includes 파라미터를 명시합니다.
    includes_params = [
        "recordings",       # 릴리즈 내의 곡(레코딩) 정보
        "artist-credits",   # 곡의 메인 아티스트 정보
        "artist-rels",      # 릴리즈 레벨 아티스트 관계 (프로듀서, 믹싱 엔지니어 등)
        "recording-rels",   # 레코딩 레벨 아티스트 관계 (프로듀서, 믹싱 엔지니어 등)
        "work-rels"         # 레코딩에 연결된 work(작품)의 아티스트 관계 (작곡, 작사 등)
    ]
    url = f"{BASE_URL}release/{mbid}?inc={'%2B'.join(includes_params)}&fmt=json"
    
    result = _make_api_call(url, entity_type="릴리즈 상세 정보")
    
    if result and result.get('release'):
        return result['release']
    return None

def get_recording_details_by_mbid(mbid: str) -> Optional[Dict[str, Any]]:
    """
    레코딩(곡)의 MBID로 상세 정보와 관계 정보를 가져옵니다.
    """
    includes_params = [
        "artist-credits",
        "artist-rels",
        "work-rels"
    ]
    url = f"{BASE_URL}recording/{mbid}?inc={'%2B'.join(includes_params)}&fmt=json"

    result = _make_api_call(url, entity_type="레코딩 상세 정보")

    if result and result.get('recording'):
        return result['recording']
    return None