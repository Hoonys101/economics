
import importlib.metadata

packages = [
    "Flask", "numpy", "pandas", "python-dotenv", "joblib", 
    "scikit-learn", "pytest", "requests", "playwright", 
    "streamlit", "PyYAML", "matplotlib", "networkx", 
    "scipy", "statsmodels"
]

print("---BEGIN REQS---")
for p in packages:
    try:
        v = importlib.metadata.version(p)
        print(f"{p}=={v}")
    except importlib.metadata.PackageNotFoundError:
        print(f"# {p} not found")
print("---END REQS---")
