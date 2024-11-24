import subprocess
import sys
import signal
import time


def run_server():
    process = None

    def signal_handler(signum, frame):
        if process:
            print("\nShutting down server...")
            process.terminate()
            process.wait()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    while True:
        try:
            process = subprocess.Popen([
                sys.executable, "-m", "uvicorn",
                "app.main:app",
                "--reload",
                "--log-level=debug",
                "--reload-exclude", "__pycache__",
                "--reload-exclude", "*.pyc"
            ])
            process.wait()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            if process:
                process.terminate()
                process.wait()
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)


if __name__ == "__main__":
    run_server()