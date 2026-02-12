#!/bin/bash

BACKEND_PID_FILE=logs/backend.pid
FRONTEND_PID_FILE=logs/frontend.pid

if [ -f "$BACKEND_PID_FILE" ]; then
    BACKEND_PID=$(cat $BACKEND_PID_FILE)
    echo "Stopping backend server with PID: $BACKEND_PID"
    # Use kill -9 for forceful stop if a graceful kill doesn't work
    kill $BACKEND_PID
    rm $BACKEND_PID_FILE
    echo "Backend server stopped."
else
    echo "Backend PID file not found. Server may not be running or was already stopped."
fi

echo ""

if [ -f "$FRONTEND_PID_FILE" ]; then
    FRONTEND_PID=$(cat $FRONTEND_PID_FILE)
    echo "Stopping frontend server with PID: $FRONTEND_PID"
    kill $FRONTEND_PID
    rm $FRONTEND_PID_FILE
    echo "Frontend server stopped."
else
    echo "Frontend PID file not found. Server may not be running or was already stopped."
fi
