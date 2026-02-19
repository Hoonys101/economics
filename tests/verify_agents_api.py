import sys
import os
import time
import subprocess
import requests
import websocket
import json
import signal

def main():
    # Start server
    print("Starting server...")
    server_process = subprocess.Popen(
        [sys.executable, "server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        # Wait for server to be ready
        print("Waiting for server to be ready...")
        max_retries = 30
        server_ready = False
        for i in range(max_retries):
            try:
                resp = requests.get("http://localhost:8000/")
                if resp.status_code == 200:
                    server_ready = True
                    break
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(1)
            print(f"Retrying connection... {i+1}/{max_retries}")

        if not server_ready:
            print("Server failed to start.")
            stdout, stderr = server_process.communicate(timeout=5)
            print("STDOUT:", stdout)
            print("STDERR:", stderr)
            sys.exit(1)

        print("Server is ready.")

        # Test WebSocket
        print("Testing WebSocket /ws/agents...")
        ws = websocket.create_connection("ws://localhost:8000/ws/agents")
        result = ws.recv()
        data = json.loads(result)
        ws.close()

        print(f"Received {len(data)} agents from WebSocket.")
        if len(data) == 0:
            print("Warning: No agents received. Simulation might be empty or initializing.")
        else:
            first_agent = data[0]
            print("First Agent Basic DTO:", first_agent)

            # Test API
            agent_id = first_agent['id']
            print(f"Testing API /api/agents/{agent_id}...")
            resp = requests.get(f"http://localhost:8000/api/agents/{agent_id}")
            if resp.status_code == 200:
                detail = resp.json()
                print("Agent Detail DTO received successfully.")
                print("Keys:", detail.keys())
            else:
                print(f"Failed to fetch agent details. Status: {resp.status_code}")
                print(resp.text)
                sys.exit(1)

    except Exception as e:
        print(f"Verification failed: {e}")
        # Print server logs if possible
        # server_process.terminate()
        # stdout, stderr = server_process.communicate()
        # print("Server Output:\n", stdout)
        # print("Server Error:\n", stderr)
        sys.exit(1)
    finally:
        print("Stopping server...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    main()
