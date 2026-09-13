import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_try = False
for i, line in enumerate(lines):
    if line.startswith("        try:") and lines[i-1].strip() == "await asyncio.sleep(0.2)":
        in_try = True
        new_lines.append(line)
        continue
    
    if in_try and line.startswith("        except Exception as e:"):
        in_try = False
    
    if in_try:
        # If the line has any text, indent it by 4 spaces
        if line.strip():
            new_lines.append("    " + line)
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write("".join(new_lines))