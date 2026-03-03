import re
import os
import json

def analyze_file(filepath):
    leaks = []
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            lines = content.split('\n')

            # Check for direct asset/balance/cash mutations
            for i, line in enumerate(lines):
                if re.search(r'\b(self\.)?(assets|balance|cash|balance_pennies)\s*(\+=|-=|=)', line):
                    # Exceptions are okay in certain DTO init or engine resets, but we flag for review
                    leaks.append({"line": i + 1, "code": line.strip(), "type": "Direct State Mutation"})

                # Check for floating point conversions in monetary context
                if re.search(r'float\(.*\.(assets|balance|cash|balance_pennies|get_balance|total_pennies)\)', line):
                     leaks.append({"line": i + 1, "code": line.strip(), "type": "Float Cast on Monetary Value"})

                # Look for partial refunds without atomic rollback
                # if it's goods_handler.py
                if "goods_handler.py" in filepath and "def rollback" in line:
                    pass # We will check this specifically

    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return leaks

results = {}
for root, dirs, files in os.walk('simulation/'):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            leaks = analyze_file(filepath)
            if leaks:
                results[filepath] = leaks

with open('reports/audit/LEAK_REPORT.json', 'w') as f:
    json.dump(results, f, indent=4)
print("Audit analysis complete. Check reports/audit/LEAK_REPORT.json")
