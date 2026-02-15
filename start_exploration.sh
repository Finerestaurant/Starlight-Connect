#!/bin/bash

# Python 가상 환경 활성화 (필수)
source backend/venv/bin/activate

BACKEND_URL="http://localhost:8000"
ENDPOINT="/import/explore-queue"
ARTIST_NAME="NAS"
MAX_DATA_GB=1 # 1GB 목표

# 백엔드 서버가 응답할 때까지 기다립니다.
echo "Waiting for backend server to be responsive..."
RETRY_COUNT=0
MAX_RETRIES=30 # 탐색은 단독으로 시작될 수 있으므로 재시도 횟수를 늘립니다.
until $(curl --output /dev/null --silent --fail $BACKEND_URL); do
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "Error: Backend server is not responsive after $MAX_RETRIES attempts."
        echo "Please ensure the backend is running (e.g., by running 'bash start_dev.sh' in another terminal)."
        exit 1
    fi
    printf '.'
    sleep 2 # 백엔드 시작을 위해 대기 시간을 늘립니다.
    RETRY_COUNT=$((RETRY_COUNT+1))
done
echo -e "\n✅ Backend is responsive!"


PAYLOAD=$(cat <<EOF
{
  "initial_artist_name": "${ARTIST_NAME}",
  "max_data_gb": ${MAX_DATA_GB}
}
EOF
)

echo "Calling Backend API: ${BACKEND_URL}${ENDPOINT}"
echo "Payload:"
echo "${PAYLOAD}"

# curl 명령어를 사용하여 POST 요청 전송
curl -X POST "${BACKEND_URL}${ENDPOINT}" \
     -H "Content-Type: application/json" \
     -d "${PAYLOAD}"

echo "" # 터미널 출력 정리를 위한 개행