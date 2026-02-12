from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from .database import Base


class Contribution(Base):
    __tablename__ = 'contributions'
    song_id = Column(Integer, ForeignKey('songs.id'), primary_key=True)
    person_id = Column(Integer, ForeignKey('persons.id'), primary_key=True)
    role = Column(String, primary_key=True)  # 역할(Role)을 복합 기본 키에 포함

    song = relationship("Song", back_populates="contributions")
    person = relationship("Person", back_populates="contributions")


class Song(Base):
    __tablename__ = 'songs'

    id = Column(Integer, primary_key=True, index=True)
    genius_id = Column(Integer, unique=True, index=True, nullable=True)
    mbid = Column(String, unique=True, index=True, nullable=True)
    title = Column(String, index=True)
    artist = Column(String, index=True)
    album = Column(String)
    release_date = Column(Date)
    source_url = Column(String, nullable=True)

    # Song이 Contribution 레코드들을 리스트로 가질 수 있도록 관계 설정
    contributions = relationship("Contribution", back_populates="song", cascade="all, delete-orphan")


class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    genius_id = Column(Integer, unique=True, index=True, nullable=True)
    mbid = Column(String, unique=True, index=True, nullable=True)
    source_url = Column(String, nullable=True)
    is_explored = Column(Boolean, default=False)

    # Person이 Contribution 레코드들을 리스트로 가질 수 있도록 관계 설정
    contributions = relationship("Contribution", back_populates="person", cascade="all, delete-orphan")
