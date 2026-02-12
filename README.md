# Starlight Connect

## 🎵 프로젝트 소개

**Starlight Connect**는 특정 K-POP 노래나 아티스트를 중심으로, 곡의 창작 과정에 참여한 모든 인물(작곡가, 작사가, 프로듀서, 연주자 등)들의 관계를 시각화하는 인터랙티브 웹 애플리케이션입니다.

"이 노래는 누가 만들었을까?" 혹은 "이 아티스트는 누구와 주로 협업했을까?"와 같은 궁금증을 직관적인 **2D 네트워크 그래프**를 통해 탐색할 수 있습니다.

## ✨ 주요 기능

-   **인터랙티브 2D 그래프**: [React Flow](https://reactflow.dev/)를 사용한 부드럽고 직관적인 관계도 시각화.
-   **동적 데이터 로딩**: 노드를 클릭하여 중심 인물/노래를 변경하고 관계망을 확장 탐색.
-   **협업 관계 시각화**: 아티스트를 중심으로 함께 작업한 다른 아티스트 및 관련 곡들을 한눈에 파악.
-   **자동화된 데이터 수집**: [MusicBrainz API](https://musicbrainz.org/)를 활용하여 방대한 음악 데이터를 수집하고 자동으로 관계망을 구축.

## 🛠️ 기술 스택

| 구분 | 기술 |
| :--- | :--- |
| **Frontend** | React, Vite, React Flow (`@xyflow/react`) |
| **Backend** | Python, FastAPI, SQLAlchemy |
| **Database** | SQLite |
| **Data Source**| MusicBrainz API |

## 🚀 시작하기

### 1. 저장소 복제

```bash
git clone <repository-url>
cd kpop
```

### 2. 백엔드 설정

```bash
# backend 디렉토리로 이동
cd backend

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. 프론트엔드 설정

```bash
# (프로젝트 루트에서) frontend 디렉토리로 이동
cd frontend

# 의존성 설치
npm install
```

### 4. 실행

프로젝트 루트 디렉토리에서 아래 스크립트를 실행하세요.

1.  **개발 서버 실행**: 백엔드와 프론트엔드 서버를 동시에 실행합니다.
    ```bash
    bash start_dev.sh
    ```
    -   Backend: `http://localhost:8000`
    -   Frontend: `http://localhost:5173`

2.  **데이터 수집 (필요 시)**: 초기 데이터를 수집합니다. (서버가 실행 중인 상태에서 별도의 터미널에서 실행)
    ```bash
    bash start_exploration.sh
    ```
    -   이 스크립트는 `NAS`를 시드 아티스트로 하여 MusicBrainz로부터 관련 데이터를 수집하기 시작합니다.
    -   수집 진행 상황은 `logs/backend.log`에서 확인할 수 있습니다.

## 📁 프로젝트 구조

```
.
├── backend/         # FastAPI 백엔드
│   ├── app/
│   └── venv/
├── frontend/        # React 프론트엔드
│   ├── src/
│   └── ...
├── agent_docs/      # 프로젝트 계획 및 로그
└── logs/            # 서버 및 데이터 수집 로그
```

## 🔮 향후 계획

-   **데이터베이스 고도화**: 더 복잡하고 깊은 관계 분석을 위해 그래프 데이터베이스(예: Neo4j)로의 전환을 고려하고 있습니다.
-   **UI/UX 개선**: '탐험 지도' 컨셉을 도입하여 더욱 몰입감 있는 사용자 경험을 제공할 계획입니다.
-   **검색 기능 강화**: 노래 및 아티스트를 쉽게 찾을 수 있는 검색 기능 구현.