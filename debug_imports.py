import sys
import time

modules = ["yaml", "joblib", "sklearn", "sklearn.linear_model", "sklearn.feature_extraction", "sklearn.preprocessing", "websockets", "streamlit", "pydantic", "fastapi", "fastapi.testclient", "uvicorn", "httpx", "starlette", "starlette.websockets", "starlette.status"]

for m in modules:
    print(f"Importing {m}...", end="", flush=True)
    start = time.time()
    try:
        __import__(m)
        print(f" DONE ({time.time() - start:.2f}s)")
    except ImportError:
        print(" FAILED (ImportError)")
    except Exception as e:
        print(f" FAILED ({e})")
