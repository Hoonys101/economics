
import os
import ast
import re

IGNORE_DIRS = {'venv', '.git', '__pycache__', 'design', 'docs', 'reports', 'results', 'scenarios', 'static', 'templates', 'tests', 'tools', 'utils', 'verification'}

class AuditScanner:
    def __init__(self, root_dir='.'):
        self.root_dir = root_dir
        self.god_classes = []
        self.leaky_abstractions = []
        self.suspicious_imports = []

    def scan(self):
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    self.process_file(filepath)

        self.report()

    def process_file(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content)

            # Check for God Classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    self.check_god_class(node, filepath)

            # Check for Leaky Abstractions (DecisionContext instantiation)
            self.check_leaky_abstractions(tree, filepath)

            # Check for imports
            self.check_imports(tree, filepath)

        except Exception as e:
            print(f"Error processing {filepath}: {e}")

    def check_god_class(self, node, filepath):
        # Rough line count based on line numbers
        if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
            line_count = node.end_lineno - node.lineno + 1
            if line_count > 800:
                self.god_classes.append({
                    'file': filepath,
                    'class': node.name,
                    'lines': line_count
                })

    def check_leaky_abstractions(self, tree, filepath):
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'DecisionContext':
                    self.analyze_decision_context_call(node, filepath)
                elif isinstance(node.func, ast.Attribute) and node.func.attr == 'DecisionContext': # e.g. dtos.DecisionContext
                    self.analyze_decision_context_call(node, filepath)

    def analyze_decision_context_call(self, call_node, filepath):
        # Check arguments for potential agent leaks (self being passed, or variable names like 'household', 'firm')
        # We are looking for: DecisionContext(household=self, ...) or similar
        for keyword in call_node.keywords:
            if isinstance(keyword.value, ast.Name):
                if keyword.value.id == 'self':
                    self.leaky_abstractions.append({
                        'file': filepath,
                        'line': call_node.lineno,
                        'type': 'Passing self to DecisionContext',
                        'arg': keyword.arg
                    })
                # Check for likely agent variable names if strict type checking isn't possible here
                elif keyword.value.id in ['household', 'firm', 'agent']:
                     self.leaky_abstractions.append({
                        'file': filepath,
                        'line': call_node.lineno,
                        'type': f'Passing potential agent "{keyword.value.id}" to DecisionContext',
                        'arg': keyword.arg
                    })

    def check_imports(self, tree, filepath):
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                # Check for tests import in non-test files
                module_name = None
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith('tests'):
                            self.suspicious_imports.append({'file': filepath, 'import': alias.name})
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith('tests'):
                        self.suspicious_imports.append({'file': filepath, 'import': node.module})

    def report(self):
        print("\n=== God Class Candidates (> 800 lines) ===")
        for item in self.god_classes:
            print(f"- {item['class']} in {item['file']} ({item['lines']} lines)")

        print("\n=== Potential Leaky Abstractions (DecisionContext) ===")
        for item in self.leaky_abstractions:
            print(f"- {item['type']} (arg: {item['arg']}) in {item['file']}:{item['line']}")

        print("\n=== Suspicious Imports (tests -> src) ===")
        for item in self.suspicious_imports:
            print(f"- {item['import']} in {item['file']}")

if __name__ == '__main__':
    scanner = AuditScanner()
    scanner.scan()
