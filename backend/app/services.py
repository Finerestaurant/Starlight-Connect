import requests
import json
import time
import sys
import os
import os
from datetime import date 
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional, Set

from . import crud, models, schemas, musicbrainz_api

# Queue 파일 관리
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
QUEUE_FILE = os.path.join(CURRENT_DIR, "..", "..", "logs", "exploration_queue.json")

def _load_queue() -> List[str]:
    """큐 파일을 읽어 MBID 리스트를 반환합니다."""
    if not os.path.exists(QUEUE_FILE):
        return []
    with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def _save_queue(queue: List[str]):
    """MBID 리스트를 큐 파일에 저장합니다."""
    with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)

def _add_to_queue(mbid: str, current_queue: List[str], explored_mbids: Set[str]):
    """큐에 새로운 MBID를 추가합니다. 이미 탐색되었거나 큐에 있으면 추가하지 않습니다."""
    if mbid and mbid not in explored_mbids and mbid not in current_queue:
        current_queue.append(mbid)

class MusicDataService:
    def _parse_musicbrainz_recording_to_schema(self, recording_data: Dict[str, Any], artist_name_context: str = "Unknown") -> Optional[schemas.CrawledSongData]:
        """
        MusicBrainz의 Recording(곡) 데이터 하나를 CrawledSongData 스키마로 변환합니다.
        """
        song_mbid = recording_data.get('id')
        song_title = recording_data.get('title', 'Unknown Song')
        
        # 날짜 정보 (first-release-date 등)
        release_date_str = recording_data.get('first-release-date')
        release_date = None
        if release_date_str:
            try:
                # YYYY-MM-DD 형식이 아닐 수도 있음 (YYYY 등)
                if len(release_date_str) == 4:
                     release_date = date(int(release_date_str), 1, 1)
                else:
                    release_date = date.fromisoformat(release_date_str)
            except ValueError:
                pass 

        print(f"[LOG][Service]   곡 파싱 시작: Title='{song_title}', MBID='{song_mbid}'")

        contributions: List[schemas.ContributionData] = []
        
        # 1. 가창자 (Artist Credit)
        for ac in recording_data.get('artist-credit', []):
            artist_info = ac.get('artist', {})
            if artist_info.get('name'):
                contributor = schemas.ContributionData(
                    person_name=artist_info.get('name'),
                    person_mbid=artist_info.get('id'),
                    role="가창" 
                )
                contributions.append(contributor)

        # 2. 통합 관계 처리 (Direct Relations & Work Relations)
        relations = recording_data.get('relations', [])
        for rel in relations:
            target_type = rel.get('target-type')
            
            # 2-1. 아티스트와의 직접 관계
            if target_type == 'artist':
                artist_info = rel.get('artist', {})
                if artist_info.get('name') and rel.get('type'):
                    role = rel.get('type')
                    attributes = rel.get('attributes', [])
                    if attributes:
                        role += f" ({', '.join(attributes)})"
                        
                    contributor = schemas.ContributionData(
                        person_name=artist_info.get('name'),
                        person_mbid=artist_info.get('id'),
                        role=role
                    )
                    contributions.append(contributor)

            # 2-2. Work(작품)를 통한 관계 (작곡, 작사 등)
            elif target_type == 'work':
                work_data = rel.get('work', {})
                work_relations = work_data.get('relations', [])
                for work_rel in work_relations:
                    if work_rel.get('target-type') == 'artist':
                        artist_info = work_rel.get('artist', {})
                        if artist_info.get('name') and work_rel.get('type'):
                            role = work_rel.get('type')
                            contributor = schemas.ContributionData(
                                person_name=artist_info.get('name'),
                                person_mbid=artist_info.get('id'),
                                role=role
                            )
                            contributions.append(contributor)
                            
        # 앨범 정보는 Recording 단위 조회에서는 명확하지 않을 수 있음 (여러 앨범에 수록될 수 있음)
        # 일단은 대표 앨범을 찾거나 비워둠. 여기서는 비워둠.
        
        return schemas.CrawledSongData(
            title=song_title,
            artist=artist_name_context, # 컨텍스트로 받은 아티스트 이름 사용 (또는 artist-credit 조합)
            album=None, 
            release_date=release_date,
            source_url=f"https://musicbrainz.org/recording/{song_mbid}",
            mbid=song_mbid,
            contributions=contributions
        )

    def import_artist_by_mbid(self, db: Session, artist_mbid: str,
                              known_explored_mbids: Set[str], queue: List[str]) -> Dict[str, Any]:
        """아티스트 MBID로 검색하여, 해당 아티스트의 모든 Recording(곡)을 DB에 저장합니다."""
        print(f"[LOG][Service] import_artist_by_mbid 호출됨: artist_mbid={artist_mbid}")
        
        # 0. 탐색 여부 확인
        existing_artist_person = crud.get_person_by_mbid(db, mbid=artist_mbid)
        if existing_artist_person and existing_artist_person.is_explored:
            print(f"[LOG][Service] 아티스트 (MBID: {artist_mbid})는 이미 탐색되었습니다. 스킵.")
            return {"message": "Already explored"}

        # 아티스트 기본 정보 가져오기 (이름 확인용)
        artist_info_raw = musicbrainz_api.get_artist_by_mbid(artist_mbid) # 기존 함수 재사용 (releases inc 없이 호출하면 가벼움)
        artist_name = artist_info_raw.get('name', 'Unknown Artist') if artist_info_raw else "Unknown Artist"
        print(f"[LOG][Service] 아티스트 이름 식별: {artist_name}")

        imported_songs_count = 0
        offset = 0
        limit = 100
        
        while True:
            print(f"[LOG][Service] Recording 목록 가져오기 (Offset: {offset}, Limit: {limit})...")
            recordings_data = musicbrainz_api.get_artist_recordings(artist_mbid, limit=limit, offset=offset)
            
            if not recordings_data:
                print(f"[LOG][Service] 데이터를 가져오지 못했습니다. 루프 종료.")
                break
            
            recordings_list = recordings_data.get('recordings', [])
            if not recordings_list:
                print(f"[LOG][Service] 더 이상 가져올 곡이 없습니다. (총 {imported_songs_count}곡 처리됨)")
                break
                
            print(f"[LOG][Service]   {len(recordings_list)}개의 곡 데이터 수신.")
            
            for rec_data in recordings_list:
                parsed_song = self._parse_musicbrainz_recording_to_schema(rec_data, artist_name_context=artist_name)
                
                if not parsed_song: 
                    continue

                # --- DB 저장 로직 (기존 import_release와 유사하지만 단일 곡 처리) ---
                # 중복 확인
                existing_song = crud.get_song_by_mbid(db, mbid=parsed_song.mbid)
                if existing_song:
                     # 이미 있으면 건너뜀 (또는 업데이트? 일단은 스킵)
                     continue
                
                db_song = models.Song(
                    title=parsed_song.title,
                    artist=parsed_song.artist, # Main Artist Context
                    album=parsed_song.album,
                    release_date=parsed_song.release_date,
                    source_url=parsed_song.source_url,
                    mbid=parsed_song.mbid
                )
                
                for contribution in parsed_song.contributions:
                     # 인물 처리
                    db_person = None
                    if contribution.person_mbid:
                        db_person = crud.get_person_by_mbid(db, mbid=contribution.person_mbid)
                    
                    if not db_person:
                        db_person = crud.get_person_by_name(db, name=contribution.person_name)
                        
                    if not db_person:
                        new_person_schema = schemas.PersonCreate(
                            name=contribution.person_name,
                            mbid=contribution.person_mbid
                        )
                        db_person = crud.create_person(db, person=new_person_schema)
                    
                    # 큐 추가 (새로운 인물이거나, 기존 인물이지만 탐색 안 된 경우)
                    if db_person.mbid:
                        _add_to_queue(db_person.mbid, queue, known_explored_mbids)

                    # 기여 관계 생성
                    db_contribution = models.Contribution(song=db_song, person=db_person, role=contribution.role)
                    db_song.contributions.append(db_contribution)
                
                crud.create_song(db, song=db_song)
                imported_songs_count += 1
            
            db.commit() # 한 페이지(100곡) 단위로 커밋
            print(f"[LOG][Service]   현재까지 {imported_songs_count}곡 저장 완료. Offset 증가.")
            
            # 아티스트당 곡 수집 제한 (50곡)
            if imported_songs_count >= 50:
                print(f"Artist song limit reached ({imported_songs_count} songs). Moving to next artist.")
                break
            
            offset += limit

        # 아티스트 탐색 완료 처리
        if existing_artist_person:
            crud.update_person_explored_status(db, existing_artist_person.id, True)
        else: 
             # 만약 위에서 create_person으로 생성되었다면 여기서 다시 가져와서 업데이트
             db_person = crud.get_person_by_mbid(db, mbid=artist_mbid)
             if db_person:
                 crud.update_person_explored_status(db, db_person.id, True)

        db.commit()
        known_explored_mbids.add(artist_mbid)
        
        return {
            "artist_name": artist_name,
            "artist_mbid": artist_mbid,
            "imported_song_count": imported_songs_count
        }

    def run_exploration_queue(self, db: Session, initial_artist_name: str = None,
                              initial_artist_mbid: str = None, max_data_gb: float = 0.05): # 50MB로 조정
        """
        큐 파일에서 MBID를 가져와 아티스트 데이터를 탐색하고 DB에 저장합니다.
        max_data_gb: 목표 데이터베이스 크기 (GB)
        """
        print(f"[LOG][Service] run_exploration_queue 호출됨.")
        print(f"[LOG][Service] 초기 요청 파라미터: initial_artist_name={initial_artist_name}, initial_artist_mbid={initial_artist_mbid}, max_data_gb={max_data_gb}")
        
        target_db_size_bytes = max_data_gb * (1024 ** 3)
        print(f"[LOG][Service] 목표 DB 크기 (bytes): {target_db_size_bytes}")
        
        queue = _load_queue()
        print(f"[LOG][Service] 초기 큐 로드: {len(queue)}개 항목")

        # 이미 탐색된 아티스트 MBID를 DB에서 미리 로드 (중복 탐색 방지)
        explored_persons = db.query(models.Person).filter(models.Person.is_explored == True).all()
        known_explored_mbids: Set[str] = {p.mbid for p in explored_persons if p.mbid}
        print(f"[LOG][Service] 이미 탐색된 아티스트: {len(known_explored_mbids)}명 (MBIDs: {known_explored_mbids})")

        # 초기 아티스트 추가
        if initial_artist_name and not initial_artist_mbid:
            print(f"[LOG][Service] 초기 아티스트 '{initial_artist_name}' MBID 검색 중...")
            search_result_artist = musicbrainz_api.search_artist(initial_artist_name)
            if search_result_artist:
                initial_artist_mbid = search_result_artist['id']
                print(f"[LOG][Service] '{initial_artist_name}'의 MBID: {initial_artist_mbid} 발견.")
            else:
                print(f"[LOG][Service] 오류: 초기 아티스트 '{initial_artist_name}'를 MusicBrainz에서 찾을 수 없습니다.")
                return {"status": "failed", "message": "초기 아티티스트를 찾을 수 없습니다."}
        
        if initial_artist_mbid:
            _add_to_queue(initial_artist_mbid, queue, known_explored_mbids)
            _save_queue(queue) # 초기 큐 저장
            print(f"[LOG][Service] 큐에 초기 아티스트 '{initial_artist_mbid}' 추가됨. 현재 큐 크기: {len(queue)}")
        
        from fastapi import HTTPException
        
        results = []
        while queue:
            current_db_size = os.path.getsize(db.bind.url.database) if os.path.exists(db.bind.url.database) else 0
            print(f"[LOG][Service] 현재 DB 크기: {current_db_size} bytes. 목표: {target_db_size_bytes} bytes.")
            if current_db_size >= target_db_size_bytes:
                print(f"[LOG][Service] 목표 DB 크기({max_data_gb}GB)에 도달했습니다. 탐색을 종료합니다.")
                break

            artist_mbid_to_explore = queue.pop(0) # 큐에서 하나 꺼내기
            _save_queue(queue) # 큐 파일 업데이트
            print(f"[LOG][Service] 큐에서 '{artist_mbid_to_explore}' 꺼냄. 남은 큐 크기: {len(queue)}")

            if artist_mbid_to_explore in known_explored_mbids:
                print(f"[LOG][Service] 아티스트 (MBID: {artist_mbid_to_explore})는 이미 탐색되었습니다. 건너뜀.")
                continue
            
            print(f"\n--- 아티스트 (MBID: {artist_mbid_to_explore}) 탐색 시작 ---")
            try:
                result = self.import_artist_by_mbid(db, artist_mbid_to_explore, known_explored_mbids, queue)
                results.append(result)
                print(f"[LOG][Service] 아티스트 (MBID: {artist_mbid_to_explore}) 탐색 완료. 큐 크기: {len(queue)}")
                
            except HTTPException as e:
                print(f"[LOG][Service] API 호출 오류로 아티스트 (MBID: {artist_mbid_to_explore}) 탐색 실패: {e.detail}")
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"[LOG][Service] 예상치 못한 오류로 아티스트 (MBID: {artist_mbid_to_explore}) 탐색 실패: {e}")
            
            _save_queue(queue) # 매 탐색 후 큐 파일 저장 (진행 상황 저장)
        
        print(f"\n[LOG][Service] 데이터 탐색 완료! 최종 큐 크기: {len(queue)}")
        final_db_size_gb = (os.path.getsize(db.bind.url.database) / (1024 ** 3)) if os.path.exists(db.bind.url.database) else 0
        return {"status": "completed", "final_db_size_gb": f"{final_db_size_gb:.2f} GB", "processed_artists_count": len(results)}

musicdata_service = MusicDataService()
