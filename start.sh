#!/bin/bash

# Function to clean up the backend process when the script is closed
cleanup() {
    echo ""
    echo "🛑 Stopping FastAPI backend server..."
    kill $BACKEND_PID 2>/dev/null
    exit
}

# Run the cleanup function if user presses Ctrl+C
trap cleanup SIGINT SIGTERM

echo "🚀 Activating virtual environment..."
source venv/bin/activate

echo "⚙️ Starting FastAPI Backend on port 8005..."
# Run backend in the background (&) and save its Process ID (PID)
python backend/main.py &
BACKEND_PID=$!

# Wait a brief moment to let the backend initialize
sleep 2

echo "🖥️ Starting Streamlit Frontend..."
# Run the Streamlit chat app
streamlit run frontend/chat_app.py

# Wait for background jobs to finish (it keeps the script alive)
wait $BACKEND_PID
