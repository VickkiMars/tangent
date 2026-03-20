import subprocess
import sys
import os
import time

import signal

def kill_port_process(port):
    """Kills any process currently using the specified port."""
    safe_pids = {os.getpid(), os.getppid()}
    try:
        # Use lsof to find the PID using the port
        result = subprocess.check_output(["lsof", "-t", f"-i:{port}"], stderr=subprocess.STDOUT)
        pids = result.decode().strip().split('\n')
        for pid in pids:
            if pid and int(pid) not in safe_pids:
                print(f"[*] Killing process {pid} using port {port}...")
                os.kill(int(pid), signal.SIGKILL)
                # Give it a tiny bit of time to release
                time.sleep(0.5)
    except (subprocess.CalledProcessError, ProcessLookupError, ValueError):
        # lsof returns non-zero if no process found, which is fine
        pass

def start_servers():
    """
    Starts the backend and frontend servers concurrently.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, "backend")
    frontend_dir = os.path.join(base_dir, "frontend")

    # Clean up ports before starting
    backend_port = os.getenv("PORT", "8000")
    kill_port_process(backend_port)
    kill_port_process("5173") # Standard Vite dev port

    # 1. Start the FastAPI backend
    # Use PORT from environment if available (Railway uses $PORT)
    print(f"[*] Starting backend server on port {backend_port}...")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", str(backend_port)],
        cwd=backend_dir
    )

    # 2. Start the Vite frontend
    # For local dev, we need to point the frontend to the backend URL
    # Vite pick up VITE_ prefixed variables at build/dev time
    print("[*] Starting frontend server...")
    frontend_env = os.environ.copy()
    frontend_env["VITE_API_URL"] = f"http://localhost:{backend_port}"
    frontend_env["VITE_WS_URL"] = f"ws://localhost:{backend_port}"
    
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        env=frontend_env
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
