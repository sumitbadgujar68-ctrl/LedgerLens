import re
import os

path = r"C:\Users\Sumit\Desktop\Hackathons\LedgerLens\LedgerLens\frontend\src\index.css"

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract colors inside @theme
theme_block_match = re.search(r'@theme\s*\{([\s\S]*?)\}', content)
theme_block = theme_block_match.group(1)

# Find all color variables in @theme
color_vars = []
non_color_vars = []

for line in theme_block.split('\n'):
    if line.strip().startswith('--color-'):
        color_vars.append(line)
    elif line.strip().startswith('/* Extej') or not line.strip():
        continue
    else:
        non_color_vars.append(line)

dark_colors = '\n'.join(color_vars)
non_colors = '\n'.join(non_color_vars)

light_colors = """
  --color-surface-dim: #f3f4f6;
  --color-surface-bright: #ffffff;
  --color-surface-container-lowest: #ffffff;
  --color-surface-container-low: #ffffff;
  --color-surface-container: #ffffff;
  --color-surface-container-high: #f9fafb;
  --color-surface-container-highest: #f3f4f6;
  --color-surface: #ffffff;
  --color-outline: #e5e7eb;
  --color-outline-variant: #d1d5db;
  --color-on-surface: #111827;
  --color-on-surface-variant: #6b7280;
  --color-primary: #ff9f43;
  --color-on-primary: #ffffff;
  --color-primary-container: #fff1e3;
  --color-on-primary-container: #ff9f43;
  --color-secondary: #28c76f;
  --color-on-secondary: #ffffff;
  --color-secondary-container: #e6f9f0;
  --color-on-secondary-container: #28c76f;
  --color-error: #ea5455;
  --color-on-error: #ffffff;
  --color-error-container: #fcebeb;
  --color-background: #f3f4f6;
  --color-on-background: #111827;
  
  --bg-app: #f3f4f6;
  --bg-sidebar: #ffffff;
  --bg-card: #ffffff;
  --bg-hover: #f9fafb;
  --border-color: #e5e7eb;
  --accent-orange: #ff9f43;
  --accent-orange-hover: #ff8800;
  --text-main: #111827;
  --text-muted: #6b7280;
"""

new_theme_block = f"""@theme {{
{non_colors}
}}

:root {{
  /* LIGHT MODE VARS */
{light_colors}
}}

html.dark {{
  /* DARK MODE VARS */
{dark_colors}
}}
"""

# Extract the fallback block (lines 72-83)
fallback_block_match = re.search(r'/\* Fallback CSS Variables for legacy parts \*/[\s\S]*?\}', content)
if fallback_block_match:
    fallback_block = fallback_block_match.group(0)
    # Remove it from content
    content = content.replace(fallback_block, '')

# Replace the old @theme with the new structure
content = content.replace(theme_block_match.group(0), new_theme_block)

# Remove any extra blank lines
content = re.sub(r'\n{3,}', '\n\n', content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("CSS updated successfully.")
