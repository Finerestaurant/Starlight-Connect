from sqlalchemy.orm import Session
from sqlalchemy import Boolean
from . import models, schemas, genius_api
from fastapi import HTTPException
from datetime import date
from typing import List, Set, Tuple, Dict, Optional
from collections import Counter, defaultdict

# --- Person CRUD ---

def get_person(db: Session, person_id: int) -> Optional[models.Person]:
    print(f"[LOG][CRUD] get_person 호출: person_id={person_id}")
    result = db.query(models.Person).filter(models.Person.id == person_id).first()
    print(f"[LOG][CRUD] get_person 반환: {result.name if result else 'None'}")
    return result

def get_person_by_genius_id(db: Session, genius_id: int) -> Optional[models.Person]:
    """Helper function to get a person by their Genius ID."""
    print(f"[LOG][CRUD] get_person_by_genius_id 호출: genius_id={genius_id}")
    result = db.query(models.Person).filter(models.Person.genius_id == genius_id).first()
    print(f"[LOG][CRUD] get_person_by_genius_id 반환: {result.name if result else 'None'}")
    return result

def get_person_by_mbid(db: Session, mbid: str) -> Optional[models.Person]:
    """Helper function to get a person by their MusicBrainz ID."""
    print(f"[LOG][CRUD] get_person_by_mbid 호출: mbid={mbid}")
    result = db.query(models.Person).filter(models.Person.mbid == mbid).first()
    print(f"[LOG][CRUD] get_person_by_mbid 반환: {result.name if result else 'None'}")
    return result

def get_person_by_name(db: Session, name: str) -> Optional[models.Person]:
    """Helper function to get a person by their name."""
    print(f"[LOG][CRUD] get_person_by_name 호출: name='{name}'")
    result = db.query(models.Person).filter(models.Person.name == name).first()
    print(f"[LOG][CRUD] get_person_by_name 반환: {result.name if result else 'None'}")
    return result

def get_persons(db: Session, skip: int = 0, limit: int = 100) -> List[models.Person]:
    print(f"[LOG][CRUD] get_persons 호출: skip={skip}, limit={limit}")
    results = db.query(models.Person).offset(skip).limit(limit).all()
    print(f"[LOG][CRUD] get_persons 반환: 총 {len(results)}명")
    return results

def create_person(db: Session, person: schemas.PersonCreate) -> models.Person:
    """Creates a new Person instance from a schema, adds it to the session, but does not commit."""
    print(f"[LOG][CRUD] create_person 호출: name='{person.name}', mbid={person.mbid}")
    db_person = models.Person(
        name=person.name,
        genius_id=person.genius_id,
        mbid=person.mbid,
        image_url=person.image_url,
        is_explored=False
    )
    db.add(db_person)
    # db.flush() # REMOVED
    # db.refresh(db_person) # REMOVED
    print(f"[LOG][CRUD] create_person 생성됨: name='{db_person.name}' (ID는 flush/commit 후에만 얻을 수 있음)")
    return db_person

def update_person_explored_status(db: Session, person_id: int, status: bool) -> Optional[models.Person]:
    """Updates the is_explored status for a given person."""
    print(f"[LOG][CRUD] update_person_explored_status 호출: person_id={person_id}, status={status}")
    db_person = db.query(models.Person).filter(models.Person.id == person_id).first()
    if db_person:
        db_person.is_explored = status
        db.add(db_person)
        # db.flush() # REMOVED
        # db.refresh(db_person) # REMOVED
        print(f"[LOG][CRUD] update_person_explored_status 업데이트됨: id={db_person.id}, is_explored={db_person.is_explored}")
    else:
        print(f"[LOG][CRUD] update_person_explored_status: person_id={person_id} 찾을 수 없음.")
    return db_person

def search_persons_by_name(db: Session, query: str, limit: int = 10) -> List[models.Person]:
    """Search for persons by name (partial match)."""
    return db.query(models.Person).filter(models.Person.name.ilike(f"%{query}%")).limit(limit).all()


# --- Song CRUD ---

def get_song(db: Session, song_id: int) -> Optional[models.Song]:
    print(f"[LOG][CRUD] get_song 호출: song_id={song_id}")
    result = db.query(models.Song).filter(models.Song.id == song_id).first()
    print(f"[LOG][CRUD] get_song 반환: {result.title if result else 'None'}")
    return result

def get_song_by_genius_id(db: Session, genius_id: int) -> Optional[models.Song]:
    print(f"[LOG][CRUD] get_song_by_genius_id 호출: genius_id={genius_id}")
    result = db.query(models.Song).filter(models.Song.genius_id == genius_id).first()
    print(f"[LOG][CRUD] get_song_by_genius_id 반환: {result.title if result else 'None'}")
    return result

def get_song_by_mbid(db: Session, mbid: str) -> Optional[models.Song]:
    """Helper function to get a song by its MusicBrainz ID."""
    print(f"[LOG][CRUD] get_song_by_mbid 호출: mbid='{mbid}' (type: {type(mbid)}, len: {len(mbid)})")
    result = db.query(models.Song).filter(models.Song.mbid == mbid).first()
    if not result:
        print(f"[LOG][CRUD]  >> Song with mbid='{mbid}' NOT FOUND!")
    print(f"[LOG][CRUD] get_song_by_mbid 반환: {result.title if result else 'None'}")
    return result

def get_song_by_source_url(db: Session, source_url: str) -> Optional[models.Song]:
    print(f"[LOG][CRUD] get_song_by_source_url 호출: source_url='{source_url}'")
    result = db.query(models.Song).filter(models.Song.source_url == source_url).first()
    print(f"[LOG][CRUD] get_song_by_source_url 반환: {result.title if result else 'None'}")
    return result

def get_songs(db: Session, skip: int = 0, limit: int = 100) -> List[models.Song]:
    print(f"[LOG][CRUD] get_songs 호출: skip={skip}, limit={limit}")
    results = db.query(models.Song).offset(skip).limit(limit).all()
    print(f"[LOG] crud.get_songs 반환: 총 {len(results)}곡")
    return results

def create_song(db: Session, song: models.Song) -> models.Song:
    """단순히 준비된 Song 모델 객체를 데이터베이스에 추가합니다."""
    print(f"[LOG][CRUD] create_song 호출: title='{song.title}', mbid={song.mbid}")
    db.add(song)
    # db.flush() # REMOVED
    # db.refresh(song) # REMOVED
    print(f"[LOG][CRUD] create_song 생성됨: title='{song.title}' (ID는 flush/commit 후에만 얻을 수 있음)")
    return song

def search_songs_by_title(db: Session, query: str, limit: int = 10) -> List[models.Song]:
    """Search for songs by title (partial match)."""
    return db.query(models.Song).filter(models.Song.title.ilike(f"%{query}%")).limit(limit).all()



def import_genius_song_data(db: Session, genius_song_id: int) -> (models.Song, bool):
    """
    Genius API에서 노래 상세 정보를 가져와 데이터베이스에 저장합니다.
    (ID 기반, 생성 여부 반환)
    """
    existing_song = get_song_by_genius_id(db, genius_id=genius_song_id)
    if existing_song:
        return existing_song, False

    song_details_data = genius_api.get_song_details(genius_song_id)
    if not (song_details_data and song_details_data.get("response", {}).get("song")):
        raise HTTPException(status_code=500, detail="Failed to retrieve valid song details from Genius API.")

    song = song_details_data["response"]["song"]

    title = song.get("title")
    artist_display = song.get("artist_names")
    album_name = song.get("album", {}).get("name") if song.get("album") else None

    release_date = None
    if release_date_str := song.get("release_date"):
        try:
            release_date = date.fromisoformat(release_date_str)
        except (ValueError, TypeError):
            pass
    
    ROLE_MAP = { "Composer": "작곡", "Lyricist": "작사", "Arranger": "편곡", "Producer": "프로듀싱", "Mixing Engineer": "믹싱 엔지니어", "Mastering Engineer": "마스터링 엔지니어", "Recording Engineer": "레코딩 엔지니어" }
    
    person_roles_temp: Dict[int, Dict[str, any]] = {}

    def add_roles_to_person(artist: Dict, roles: List[str]):
        if not (artist and artist.get("id") and artist.get("name")):
            return
        
        genius_id = artist["id"]
        name = artist["name"]

        if genius_id not in person_roles_temp:
            person_roles_temp[genius_id] = {"name": name, "roles": set()}
        
        person_roles_temp[genius_id]["roles"].update(roles)

    add_roles_to_person(song.get("primary_artist"), ["가창"])
    for artist in song.get("featured_artists", []):
        add_roles_to_person(artist, ["피처링"])
    for performance in song.get("custom_performances", []):
        if korean_role := ROLE_MAP.get(performance.get("label")):
            for artist in performance.get("artists", []):
                add_roles_to_person(artist, [korean_role])
    
    final_contributions: List[schemas.ContributionCreate] = [
        schemas.ContributionCreate(
            person_name=data["name"],
            person_genius_id=genius_id,
            roles=list(data["roles"])
        )
        for genius_id, data in person_roles_temp.items()
    ]
    
    if not title or not artist_display:
        raise HTTPException(status_code=400, detail=f"Song title or artist is missing for ID {genius_song_id}.")

    song_create_schema = schemas.SongCreate(
        title=title, artist=artist_display, album=album_name, release_date=release_date,
        genius_id=genius_song_id, contributions=final_contributions
    )

    db_song = create_song(db, song=song_create_schema)
    return db_song, True

def batch_import_genius_songs(db: Session, genius_song_ids: List[int]) -> schemas.BatchImportResponse:
    """주어진 Genius 노래 ID 리스트를 일괄적으로 임포트합니다."""
    # ... (rest of the function is unchanged)
    imported_count = 0
    skipped_count = 0
    failed_ids = []

    for song_id in genius_song_ids:
        try:
            _, was_created = import_genius_song_data(db, genius_song_id=song_id)
            if was_created:
                imported_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            print(f"Failed to import song ID {song_id}: {e}")
            failed_ids.append(song_id)
            db.rollback()

    return schemas.BatchImportResponse(
        imported_count=imported_count,
        skipped_count=skipped_count,
        failed_ids=failed_ids
    )

# --- Collaboration Details ---


def get_song_graph_details_by_mbid(db: Session, mbid: str):
    """
    특정 곡의 mbid를 받아, 해당 곡(main)과 참여 인물 리스트(related)를 반환합니다.
    프론트엔드의 `getLayoutedElements(data, 'song')` 형식에 맞춘 응답입니다.
    """
    song = get_song_by_mbid(db, mbid=mbid)
    if not song:
        raise HTTPException(status_code=404, detail="Song with given MBID not found in DB.")

    # 각 기여자의 역할을 수집
    person_roles_map = defaultdict(lambda: {"person": None, "roles": []})
    for contribution in song.contributions:
        person = contribution.person
        if person:
            person_roles_map[person.id]["person"] = person
            person_roles_map[person.id]["roles"].append(contribution.role)
    
    # 최종 related 리스트 생성
    related_persons = []
    for person_id, data in person_roles_map.items():
        person_obj = data["person"]
        # Pydantic 모델로 변환하여 역할 정보 추가
        person_with_roles = schemas.Person.model_validate(person_obj).model_dump()
        person_with_roles["roles"] = data["roles"]
        related_persons.append(person_with_roles)

    return {"main": song, "related": related_persons}


def get_collaboration_details_by_mbid(db: Session, mbid: str) -> schemas.CollaborationResponse:
    """특정 아티스트의 협업자 및 협업 곡 목록을 MBID 기준으로 상세히 반환합니다."""
    main_artist = get_person_by_mbid(db, mbid=mbid)
    if not main_artist:
        raise HTTPException(status_code=404, detail="Main artist not found in DB with the given MBID.")

    collaborations = defaultdict(list)
    collaborator_objects: Dict[str, models.Person] = {}

    # 1. 메인 아티스트가 참여한 모든 곡을 찾습니다.
    for main_artist_contrib in main_artist.contributions:
        song = main_artist_contrib.song
        
        # 2. 해당 곡에 참여한 다른 모든 사람들을 찾습니다.
        for song_contrib in song.contributions:
            collaborator = song_contrib.person
            
            # 3. 메인 아티스트 본인은 제외하고, mbid가 있는 협업자만 집계합니다.
            if collaborator.id != main_artist.id and collaborator.mbid:
                # 이전에 추가되지 않은 곡만 추가
                if not any(s.id == song.id for s in collaborations[collaborator.mbid]):
                    collaborations[collaborator.mbid].append(song)

                if collaborator.mbid not in collaborator_objects:
                    collaborator_objects[collaborator.mbid] = collaborator

    # 4. 집계된 결과를 CollaborationDetail 스키마 리스트로 변환합니다.
    collaboration_details_list = []
    for col_mbid, song_list in collaborations.items():
        person_obj = collaborator_objects[col_mbid]
        
        collaboration_details_list.append(
            schemas.CollaborationDetail(
                collaborator=person_obj,
                songs=[schemas.R_Song.model_validate(s) for s in song_list]
            )
        )
    
    # 협업 횟수 순으로 정렬
    collaboration_details_list.sort(key=lambda x: len(x.songs), reverse=True)

    return schemas.CollaborationResponse(
        main_artist=main_artist,
        collaborations=collaboration_details_list
    )


def get_collaboration_details(db: Session, genius_id: int) -> schemas.CollaborationResponse:
    """특정 아티스트의 협업자 및 협업 곡 목록을 상세히 반환합니다."""
    main_artist = get_person_by_genius_id(db, genius_id=genius_id)
    if not main_artist:
        raise HTTPException(status_code=404, detail="Main artist not found in DB.")

    collaborations = defaultdict(list)
    collaborator_objects: Dict[int, models.Person] = {}

    # 1. 메인 아티스트가 참여한 모든 곡을 찾습니다.
    for main_artist_contrib in main_artist.contributions:
        song = main_artist_contrib.song
        
        # 2. 해당 곡에 참여한 다른 모든 사람들을 찾습니다.
        for song_contrib in song.contributions:
            collaborator = song_contrib.person
            
            # 3. 메인 아티스트 본인은 제외하고, genius_id가 있는 협업자만 집계합니다.
            if collaborator.id != main_artist.id and collaborator.genius_id:
                # 이전에 추가되지 않은 곡만 추가
                if not any(s.id == song.id for s in collaborations[collaborator.genius_id]):
                    collaborations[collaborator.genius_id].append(song)

                if collaborator.genius_id not in collaborator_objects:
                    collaborator_objects[collaborator.genius_id] = collaborator

    # 4. 집계된 결과를 CollaborationDetail 스키마 리스트로 변환합니다.
    collaboration_details_list = []
    for col_genius_id, song_list in collaborations.items():
        person_obj = collaborator_objects[col_genius_id]
        
        collaboration_details_list.append(
            schemas.CollaborationDetail(
                collaborator=person_obj,
                songs=[schemas.R_Song.model_validate(s) for s in song_list]
            )
        )
    
    # 협업 횟수 순으로 정렬
    collaboration_details_list.sort(key=lambda x: len(x.songs), reverse=True)

    return schemas.CollaborationResponse(
        main_artist=main_artist,
        collaborations=collaboration_details_list
    )