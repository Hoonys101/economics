import os
from typing import List

def search_log_file(file_path: str, keywords: List[str]) -> List[str]:
    """
    지정된 로그 파일에서 하나 이상의 키워드를 검색하고, 해당 키워드가 포함된 모든 줄을 반환합니다.
    """
    found_lines = []
    if not os.path.exists(file_path):
        print(f"Error: Log file not found at {file_path}")
        return found_lines

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                for keyword in keywords:
                    if keyword in line:
                        found_lines.append(line.strip())
                        break  # 한 줄에 여러 키워드가 있어도 한 번만 추가
    except Exception as e:
        print(f"Error reading log file {file_path}: {e}")

    return found_lines
