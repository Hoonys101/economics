import ast
import astor
import os

def refactor_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())

    class OrderRefactor(ast.NodeTransformer):
        def visit_Call(self, node):
            # Target CanonicalOrderDTO or OrderDTO
            if isinstance(node.func, ast.Name) and node.func.id in ('CanonicalOrderDTO', 'OrderDTO'):
                # Filter out price_limit keyword
                node.keywords = [k for k in node.keywords if k.arg != 'price_limit']
            return self.generic_visit(node)

    new_tree = OrderRefactor().visit(tree)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(astor.to_source(new_tree))

# Target directory
test_dir = 'tests/market/'
for filename in os.listdir(test_dir):
    if filename.startswith('test_') and filename.endswith('.py'):
        print(f"Refactoring {filename}...")
        refactor_file(os.path.join(test_dir, filename))
