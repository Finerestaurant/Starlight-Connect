from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from . import crud, models, schemas, genius_api
from .database import SessionLocal, engine
from .services import musicdata_service

# 데이터베이스 테이블 생성
models.Base.metadata.create_all(bind=engine)


app = FastAPI()

# --- CORS 미들웨어 설정 ---
origins = [
    "http://localhost:5173",  # React Frontend Origin
    "http://127.0.0.1:5173", # React Frontend Origin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메소드 허용
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)
# -------------------------


# 데이터베이스 세션을 얻기 위한 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# @app.post("/songs/", response_model=schemas.SongResponse)
# def create_song(song: schemas.SongCreate, db: Session = Depends(get_db)):
#     # 참고: 이미 존재하는 노래인지 확인하는 로직을 추가할 수 있습니다.
#     # 이 엔드포인트는 서비스 계층 도입으로 인해 비활성화되었습니다.
#     # return crud.create_song(db=db, song=song)


# --- MusicBrainz Service Endpoints ---
@app.post("/import/artist-by-name")
def import_artist_by_name(request: schemas.ArtistImportRequest, db: Session = Depends(get_db)):
    """
    아티스트 이름으로 MusicBrainz에서 모든 릴리즈를 가져와 데이터베이스에 저장합니다.
    """
    try:
        # artist_mbid가 제공되면 그걸 사용, 아니면 artist_name으로 검색
        artist_mbid_to_use = request.artist_mbid
        if not artist_mbid_to_use and request.artist_name:
            search_result_artist = musicdata_service.musicbrainz_api.search_artist(request.artist_name)
            if search_result_artist:
                artist_mbid_to_use = search_result_artist['id']
            else:
                raise HTTPException(status_code=404, detail=f"아티스트 '{request.artist_name}'를 찾을 수 없습니다.")

        if not artist_mbid_to_use:
            raise HTTPException(status_code=400, detail="아티스트 이름 또는 MBID가 필요합니다.")

        result = musicdata_service.import_artist_by_mbid(db=db, artist_mbid=artist_mbid_to_use, known_explored_mbids=set(), queue=[]) # 큐는 여기서 관리하지 않음
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"아티스트 데이터 임포트 중 오류 발생: {e}"
        )

# --- Exploration Queue Endpoints ---
@app.post("/import/explore-queue")
def start_exploration_queue(request: schemas.ExplorationQueueRequest):
    """
    MusicBrainz 데이터를 '연쇄 반응' 방식으로 탐색하여 DB에 저장합니다.
    """
    print(f"[LOG] start_exploration_queue 엔드포인트 호출됨.")
    print(f"[LOG] 요청 파라미터: initial_artist_name={request.initial_artist_name}, initial_artist_mbid={request.initial_artist_mbid}, max_data_gb={request.max_data_gb}")

    if not request.initial_artist_name and not request.initial_artist_mbid:
        print("[LOG] 오류: 초기 아티스트 이름 또는 MBID가 필요합니다.")
        raise HTTPException(status_code=400, detail="초기 아티스트 이름 또는 MBID가 필요합니다.")

    try:
        result = musicdata_service.run_exploration_queue(
            initial_artist_name=request.initial_artist_name,
            initial_artist_mbid=request.initial_artist_mbid,
            max_data_gb=request.max_data_gb
        )
        print(f"[LOG] start_exploration_queue 엔드포인트 완료. 결과: {result['status']}")
        return result
    except HTTPException as e:
        print(f"[LOG] 탐색 큐 실행 중 HTTPException 발생: {e.detail}")
        raise e
    except Exception as e:
        print(f"[LOG] 탐색 큐 실행 중 예상치 못한 오류 발생: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"탐색 큐 실행 중 오류 발생: {e}"
        )


@app.get("/songs/", response_model=List[schemas.SongResponse])
def read_songs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    songs = crud.get_songs(db, skip=skip, limit=limit)
    return songs


@app.get("/songs/mbid/{mbid}/graph-details")
def get_song_graph_details(mbid: str, db: Session = Depends(get_db)):
    """(NEW) 특정 곡의 mbid를 받아, 해당 곡과 참여 인물 리스트를 그래프 형식으로 반환합니다."""
    return crud.get_song_graph_details_by_mbid(db=db, mbid=mbid)


@app.get("/songs/{song_id}", response_model=schemas.SongResponse)
def read_song(song_id: int, db: Session = Depends(get_db)):
    db_song = crud.get_song(db, song_id=song_id)
    if db_song is None:
        raise HTTPException(status_code=404, detail="Song not found")
    return db_song


@app.get("/persons/", response_model=List[schemas.PersonResponse])
def read_persons(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    persons = crud.get_persons(db, skip=skip, limit=limit)
    return persons


@app.get("/persons/{person_id}", response_model=schemas.PersonResponse)
def read_person(person_id: int, db: Session = Depends(get_db)):
    db_person = crud.get_person(db, person_id=person_id)
    if db_person is None:
        raise HTTPException(status_code=404, detail="Person not found")
    return db_person

@app.get("/")
def read_root():
    return {"message": "K-POP 3D Graph API is running."}


# --- Genius API Endpoints ---

@app.get("/genius/search")
def search_genius_songs(q: str):
    """Genius API를 통해 노래를 검색하고 결과를 반환합니다."""
    if not genius_api.GENIUS_API_TOKEN:
        raise HTTPException(
            status_code=400, 
            detail="Genius API token is not configured on the server."
        )

    results = genius_api.search_song(q)
    if results is None:
        raise HTTPException(status_code=500, detail="Error communicating with Genius API.")
    
    if not results.get("response", {}).get("hits"):
        raise HTTPException(status_code=404, detail="No results found on Genius for the given query.")

    return results["response"]["hits"]


@app.post("/import/genius_song", response_model=schemas.SongResponse)
def import_genius_song(request: schemas.GeniusImportRequest, db: Session = Depends(get_db)):
    """Genius API에서 노래를 가져와 데이터베이스에 저장합니다."""
    db_song, _ = crud.import_genius_song_data(db=db, genius_song_id=request.genius_song_id)
    return db_song


@app.post("/import/batch/genius_songs", response_model=schemas.BatchImportResponse)
def import_batch_genius_songs(request: schemas.GeniusBatchImportRequest, db: Session = Depends(get_db)):
    """Genius 노래 ID 리스트를 받아 일괄적으로 데이터베이스에 저장합니다."""
    return crud.batch_import_genius_songs(db=db, genius_song_ids=request.genius_song_ids)


@app.get("/genius/artists/{artist_id}/songs")
def get_genius_artist_songs(artist_id: int, page: int = 1):
    """Genius API를 통해 특정 아티스트의 노래 목록을 가져옵니다."""
    if not genius_api.GENIUS_API_TOKEN:
        raise HTTPException(
            status_code=400,
            detail="Genius API token is not configured on the server."
        )
    
    results = genius_api.get_artist_songs(artist_id, page=page)
    if results is None:
        raise HTTPException(status_code=500, detail="Error communicating with Genius API.")
    
    # Genius API의 응답 구조에 따라 'songs' 키가 없을 수도 있음을 고려
    songs = results.get("response", {}).get("songs")
    if songs is None: # 'songs' 키가 없거나, 'songs'의 값이 None인 경우
        raise HTTPException(status_code=404, detail=f"No songs found or invalid response for artist ID {artist_id} on Genius.")
    
    # --- DEBUG LOGGING ---
    response_to_send = results["response"]
    print("--- DEBUG: get_genius_artist_songs ---")
    print(f"Type of response_to_send: {type(response_to_send)}")
    # To avoid flooding the log, print only keys or a small part of the data
    if isinstance(response_to_send, dict):
        print(f"Keys in response_to_send: {response_to_send.keys()}")
        print(f"Next page: {response_to_send.get('next_page')}")
    else:
        print(f"Data being sent (first 100 chars): {str(response_to_send)[:100]}")
    print("--- END DEBUG ---")
    # --- END DEBUG LOGGING ---

    return results["response"] # 'songs'와 'next_page' 정보를 모두 포함한 response 객체를 반환



@app.get("/artists/mbid/{mbid}/collaboration-details", response_model=schemas.CollaborationResponse)
def get_artist_collaboration_details_by_mbid(mbid: str, db: Session = Depends(get_db)):
    """(NEW) 특정 아티스트의 협업자 및 협업 곡 목록을 MBID 기준으로 상세히 반환합니다."""
    return crud.get_collaboration_details_by_mbid(db=db, mbid=mbid)


@app.get("/artists/genius/{genius_id}/collaboration-details", response_model=schemas.CollaborationResponse)
def get_artist_collaboration_details(genius_id: int, db: Session = Depends(get_db)):
    """특정 아티스트의 협업자 및 협업 곡 목록을 상세히 반환합니다."""
    return crud.get_collaboration_details(db=db, genius_id=genius_id)


@app.get("/search", response_model=schemas.SearchResponse)
def search_db(q: str, db: Session = Depends(get_db)):
    """
    내부 DB에서 아티스트와 곡을 검색합니다. (Autocomplete용)
    """
    if not q or len(q) < 1:
        return {"results": []}

    results = []
    
    # 1. 아티스트 검색
    artists = crud.search_persons_by_name(db, query=q, limit=5)
    for artist in artists:
        results.append(schemas.SearchResultItem(
            id=artist.id,
            name=artist.name,
            type="person", # 'artist' -> 'person'으로 변경 (프론트엔드 호환성)
            mbid=artist.mbid,
            image_url=artist.image_url,
            sub_text=None
        ))
        
    # 2. 곡 검색
    songs = crud.search_songs_by_title(db, query=q, limit=5)
    for song in songs:
        results.append(schemas.SearchResultItem(
            id=song.id,
            name=song.title,
            type="song",
            mbid=song.mbid,
            image_url=None, # 곡 이미지는 앨범 커버 등이 있다면 추가 가능
            sub_text=song.artist # 곡의 경우 아티스트 이름을 보조 텍스트로 표시
        ))
        
    return {"results": results}


