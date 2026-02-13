import asyncio
import websockets
import json
import random
import time
from uuid import uuid4

async def handler(websocket):
    print("Client connected")
    tick = 0

    # State for On-Demand Telemetry
    active_mask = []

    try:
        while True:
            # 1. Generate Base Telemetry
            telemetry = {
                "tick": tick,
                "timestamp": time.time(),
                "status": "RUNNING",
                "integrity": {
                    "m2_leak": random.uniform(-0.1, 0.1),
                    "fps": random.uniform(55, 60)
                },
                "macro": {
                    "gdp": 1000000 + (tick * 1000) + random.uniform(-5000, 5000),
                    "cpi": 100 + (tick * 0.01) + random.uniform(-0.5, 0.5),
                    "unemploy": 0.05 + random.uniform(-0.01, 0.01),
                    "gini": 0.35
                },
                "finance": {
                    "rates": {
                        "base": 0.05,
                        "call": 0.045,
                        "loan": 0.07,
                        "savings": 0.03
                    },
                    "supply": {
                        "m0": 500000,
                        "m1": 1500000,
                        "m2": 3000000,
                        "velocity": 1.2
                    }
                },
                "politics": {
                    "approval": {
                         "total": 0.6,
                         "low": 0.5,
                         "mid": 0.6,
                         "high": 0.7
                    },
                    "status": {
                        "ruling_party": "Labor",
                        "cohesion": 0.8
                    },
                    "fiscal": {
                        "revenue": 200000,
                        "welfare": 50000,
                        "debt": 1000000
                    }
                },
                "population": {
                    "distribution": {
                        "q1": 0.1, "q2": 0.15, "q3": 0.2, "q4": 0.25, "q5": 0.3
                    },
                    "active_count": 1000 + int(tick * 0.1),
                    "metrics": {
                        "birth": 10,
                        "death": 8
                    }
                },
                "scenario_reports": [
                    {
                        "scenario_id": "SC-001: Female Labor Participation",
                        "status": "RUNNING",
                        "progress_pct": min(100.0, tick * 0.5),
                        "current_kpi_value": 0.45 + (tick * 0.0001),
                        "target_kpi_value": 0.6,
                        "message": "Participation rate increasing steadily."
                    }
                ],
                "custom_data": {}
            }

            # 2. Populate On-Demand Data
            if "population.distribution" in active_mask:
                # Mirroring population.distribution for test
                telemetry["custom_data"]["population.distribution"] = telemetry["population"]["distribution"]

            if "household_detailed_stats" in active_mask:
                # Generate fake agent list
                agents = []
                for i in range(50):
                    agents.append({
                        "id": i,
                        "age": random.randint(20, 80),
                        "wealth": random.randint(1000, 100000),
                        "satisfaction": random.uniform(0, 1),
                        "occupation": random.choice(["Farmer", "Worker", "Engineer"])
                    })
                telemetry["custom_data"]["household_detailed_stats"] = agents

            await websocket.send(json.dumps(telemetry))

            # 3. Check for Commands
            try:
                # Wait briefly for incoming messages
                message = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                data = json.loads(message)
                print(f"Received Command: {data}")

                # Verify it's a command
                if "command_type" in data:
                    if data["command_type"] == "UPDATE_TELEMETRY":
                        active_mask = data.get("new_value", [])
                        print(f"Updated Mask: {active_mask}")

                    # Echo back a response
                    response = {
                        "command_id": data.get("command_id", str(uuid4())),
                        "success": True,
                        "execution_tick": tick,
                        "failure_reason": None,
                        "audit_report": {
                            "details": f"Executed {data.get('parameter_key')} -> {data.get('new_value')}"
                        }
                    }
                    await websocket.send(json.dumps(response))

            except asyncio.TimeoutError:
                pass
            except Exception as e:
                print(f"Error processing command: {e}")

            tick += 1
            await asyncio.sleep(1) # 1 tick per second

    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("Mock Simulation Server running on ws://localhost:8765")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
