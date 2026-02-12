#!/bin/bash

# Python 가상 환경 활성화 (필수)
source backend/venv/bin/activate

BACKEND_URL="http://localhost:8000"
ENDPOINT="/import/explore-queue"
ARTIST_NAME="NAS"
MAX_DATA_GB=1 # 1GB 목표

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

