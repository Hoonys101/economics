
with open('tree_audit.txt', 'r') as f:
    lines = f.readlines()
    for line in lines:
        if 'economic' in line.lower():
            print(line.strip())
