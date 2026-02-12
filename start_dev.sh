#!/bin/bash

# Clear previous logs and pid files for a clean start
rm -f logs/*.log logs/*.err logs/*.pid

echo "Starting backend server in the background..."
cd backend
venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 > ../logs/backend.log 2> ../logs/backend.err &
UVICORN_BG_PID=$!
cd ..

echo "Waiting for backend server to respond..."
RETRY_COUNT=0
MAX_RETRIES=15
until $(curl --output /dev/null --silent --fail http://127.0.0.1:8000/); do # Use GET by default, not HEAD
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "Error: Backend server did not respond after $MAX_RETRIES attempts."
        echo "Please check 'logs/backend.err' and 'logs/backend.log' for errors."
        kill $UVICORN_BG_PID 2>/dev/null
        exit 1
    fi
    printf '.'
    sleep 1
    RETRY_COUNT=$((RETRY_COUNT+1))
done

echo -e "\n✅ Backend is responsive!"
BACKEND_PID=$(lsof -ti :8000)
if [ -z "$BACKEND_PID" ]; then
    echo "Error: Could not find PID for backend server even though it responded."
    exit 1
fi
echo $BACKEND_PID > logs/backend.pid
echo "Backend server running with PID(s): $BACKEND_PID"

echo "----------------------------------------------------"

echo "Starting frontend server in the background..."
cd frontend
npm run dev > ../logs/frontend.log 2> ../logs/frontend.err &
NPM_BG_PID=$!
cd ..

echo "Waiting for frontend server to respond..."
RETRY_COUNT=0
MAX_RETRIES=15
until $(curl --output /dev/null --silent --fail http://127.0.0.1:5173/); do # Use GET by default, not HEAD
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "Error: Frontend server did not respond after $MAX_RETRIES attempts."
        echo "Please check 'logs/frontend.err' and 'logs/frontend.log' for errors."
        kill $NPM_BG_PID 2>/dev/null
        kill $BACKEND_PID 2>/dev/null # Clean up backend as well
        exit 1
    fi
    printf '.'
    sleep 1
    RETRY_COUNT=$((RETRY_COUNT+1))
done

echo -e "\n✅ Frontend is responsive!"
FRONTEND_PID=$(lsof -ti :5173)
if [ -z "$FRONTEND_PID" ]; then
    echo "Error: Could not find PID for frontend server even though it responded."
    exit 1
fi
echo $FRONTEND_PID > logs/frontend.pid
echo "Frontend server running with PID: $FRONTEND_PID"


echo "----------------------------------------------------"
echo "✅ Both servers are running and responsive."
echo "   - Backend: PID $BACKEND_PID"
echo "   - Frontend: PID $FRONTEND_PID"
echo ""
echo "   To stop everything, run: ./stop_dev.sh"