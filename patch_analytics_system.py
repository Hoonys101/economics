import re

with open('simulation/systems/analytics_system.py', 'r') as f:
    content = f.read()

if 'from typing import ' in content and 'Optional' not in content:
    content = content.replace('from typing import ', 'from typing import Optional, ')
elif 'from typing import Optional' not in content:
    content = 'from typing import Optional\n' + content

with open('simulation/systems/analytics_system.py', 'w') as f:
    f.write(content)
