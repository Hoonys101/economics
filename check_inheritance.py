import os
import ast
import sys

def get_inheritance_depth(class_name, classes, depth=1):
    if class_name not in classes:
        return depth
    parents = classes[class_name]
    if not parents:
        return depth
    max_parent_depth = 0
    for parent in parents:
        max_parent_depth = max(max_parent_depth, get_inheritance_depth(parent, classes, depth + 1))
    return max_parent_depth

def analyze_file(filepath, classes_map):
    with open(filepath, 'r') as f:
        try:
            tree = ast.parse(f.read())
        except:
            return

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            parents = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    parents.append(base.id)
                elif isinstance(base, ast.Attribute):
                    parents.append(base.attr)
            classes_map[node.name] = parents

def main():
    classes_map = {}
    file_list = []
    for root, dirs, files in os.walk("simulation"):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                file_list.append(filepath)
                analyze_file(filepath, classes_map)

    print("High Inheritance Classes (Depth >= 4):")
    for cls in classes_map:
        depth = get_inheritance_depth(cls, classes_map)
        if depth >= 4:
            print(f"- {cls}: {depth}")

if __name__ == "__main__":
    main()
