import os

original_cwd = os.getcwd()
script_dir = "C:/Users/Gram Pro/OneDrive/바탕 화면/coding/economics/design/"
os.chdir(script_dir)

files_to_rename = {
    "개발지침.md": "01_개발지침.md",
    "경제시뮬레이션_시장_및_상호작용_설계.md": "02_경제시뮬레이션_시장_및_상호작용_설계.md",
    "경제시뮬레이션_가계_재능_역량_설계.md": "03_경제시뮬레이션_가계_재능_역량_설계.md",
    "경제시뮬레이션_기업_재고_생산_개선_설계.md": "04_경제시뮬레이션_기업_재고_생산_개선_설계.md",
    "simulation_core.py": "05_simulation_core.py"
}

for old_name, new_name in files_to_rename.items():
    try:
        os.rename(old_name, new_name)
        print(f"Renamed '{old_name}' to '{new_name}'")
    except FileNotFoundError:
        print(f"File not found: '{old_name}'")
    except Exception as e:
        print(f"Error renaming '{old_name}': {e}")

os.chdir(original_cwd)