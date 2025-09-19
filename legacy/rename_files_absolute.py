
import os

base_path = "C:/Users/Gram Pro/OneDrive/바탕 화면/coding/economics/design/"

files_to_rename = {
    "개발지침.md": "01_개발지침.md",
    "경제시뮬레이션_시장_및_상호작용_설계.md": "02_경제시뮬레이션_시장_및_상호작용_설계.md",
    "경제시뮬레이션_가계_재능_역량_설계.md": "03_경제시뮬레이션_가계_재능_역량_설계.md",
    "경제시뮬레이션_기업_재고_생산_개선_설계.md": "04_경제시뮬레이션_기업_재고_생산_개선_설계.md",
    "simulation_core.py": "05_simulation_core.py"
}

for old_name, new_name in files_to_rename.items():
    old_path = os.path.join(base_path, old_name)
    new_path = os.path.join(base_path, new_name)
    try:
        os.rename(old_path, new_path)
        print(f"Renamed '{old_path}' to '{new_path}'")
    except FileNotFoundError:
        print(f"File not found: '{old_name}'")
    except Exception as e:
        print(f"Error renaming '{old_name}': {e}")
