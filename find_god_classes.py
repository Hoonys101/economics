import os
import ast

def find_large_classes(root_dir, limit=800):
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".py"):
                filepath = os.path.join(dirpath, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                # Estimate lines by subtracting start line from end line
                                # Note: This is an approximation as it includes docstrings and whitespace within the class
                                start_line = node.lineno
                                end_line = getattr(node, 'end_lineno', start_line)
                                line_count = end_line - start_line + 1
                                if line_count > limit:
                                    print(f"{filepath}: Class '{node.name}' has {line_count} lines")
                except Exception as e:
                    print(f"Could not parse {filepath}: {e}")

if __name__ == "__main__":
    find_large_classes(".", 800)
