from pydantic import BaseModel
from datetime import date
from typing import List, Optional


# --- Base Schemas ---
# 공통 필드를 정의하고, ORM 모델로부터 데이터를 읽어올 수 있도록 설정

class PersonBase(BaseModel):
    name: str
    genius_id: Optional[int] = None
    mbid: Optional[str] = None # MBID 필드 추가

class SongBase(BaseModel):
    title: str
    artist: str
    album: Optional[str] = None
    release_date: Optional[date] = None
    genius_id: Optional[int] = None
    mbid: Optional[str] = None # MBID 필드 추가


# --- Schemas for Data Creation (Input) ---

class PersonCreate(PersonBase):
    mbid: Optional[str] = None # MBID 필드 추가

class ContributionCreate(BaseModel):
    person_name: str
    person_genius_id: Optional[int] = None
    person_mbid: Optional[str] = None # MBID 필드 추가
    roles: List[str]

class SongCreate(SongBase):
    contributions: List[ContributionCreate]


# --- Schemas for Genius API Interaction ---
class GeniusSearchSong(BaseModel):
    id: int
    title: str
    artist_names: str
    api_path: str
    url: str

class GeniusImportRequest(BaseModel):
    genius_song_id: int

class GeniusBatchImportRequest(BaseModel):
    genius_song_ids: List[int]

class BatchImportResponse(BaseModel):
    imported_count: int
    skipped_count: int
    failed_ids: List[int]


# --- Schemas for Data Reading (Output) ---
# 순환 참조를 방지하며 API 응답에 사용될 모델들을 정의

class Person(PersonBase):
    id: int

    class Config:
        from_attributes = True

class R_Song(SongBase):
    id: int
    genius_id: Optional[int]
    mbid: Optional[str] # MBID 필드 추가

    class Config:
        from_attributes = True

class R_Contribution_For_Song(BaseModel):
    role: str
    person: Person

    class Config:
        from_attributes = True

class R_Contribution_For_Person(BaseModel):
    role: str
    song: R_Song

    class Config:
        from_attributes = True

class SongResponse(R_Song):
    contributions: List[R_Contribution_For_Song] = []

class PersonResponse(Person):

    contributions: List[R_Contribution_For_Person] = []



# --- Schemas for Collaboration Details ---



class CollaborationDetail(BaseModel):

    collaborator: Person

    songs: List[R_Song]



class CollaborationResponse(BaseModel):

    main_artist: Person

    collaborations: List[CollaborationDetail]


# --- Schemas for Crawled Data ---
class ContributionData(BaseModel):
    person_name: str
    person_mbid: Optional[str] = None # MBID 필드 추가
    role: str

class CrawledSongData(SongBase):
    source_url: str
    mbid: Optional[str] = None # MBID 필드 추가
    contributions: List[ContributionData]

# --- Schemas for Service Imports ---
class ArtistImportRequest(BaseModel):
    artist_name: str
    artist_mbid: Optional[str] = None # MBID 필드 추가

class ExplorationQueueRequest(BaseModel):
    initial_artist_name: Optional[str] = None
    initial_artist_mbid: Optional[str] = None
    max_data_gb: float = 0.05 # 기본 50MB