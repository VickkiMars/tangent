import subprocess
import sys
import os
import time

def start_servers():
    """
    Starts the backend and frontend servers concurrently.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, "backend")
    frontend_dir = os.path.join(base_dir, "nagent")

    print("[*] Starting backend server...")
    # Start the FastAPI backend
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--port", "8000"],
        cwd=backend_dir
    )

    print("[*] Starting frontend server...")
    # Start the Vite frontend
    # Note: shell=True is typically beneficial on Windows, but this relies on array-format on Unix.
    # We'll use npx or npm directly.
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir
    )

    try:
        # Keep the script running to hold the processes
        print("[*] Both servers are starting. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Shutting down servers...")
        backend_process.terminate()
        frontend_process.terminate()
        
        backend_process.wait()
        frontend_process.wait()
        print("[*] Servers stopped successfully.")

if __name__ == "__main__":
    start_servers()
