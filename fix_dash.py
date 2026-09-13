import io
import re

with io.open('dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Fix CSS warning
text = text.replace('-webkit-background-clip: text;', 'background-clip: text;\n            -webkit-background-clip: text;')

# Fix SVG visibility: remove gradient and just use a solid color for testing, or fix the stroke.
# Let's just hardcode stroke='#d4a373' for now so it definitely renders.
text = re.sub(r'stroke="url\(#beamGrad\)"', 'stroke="#d4a373"', text)

with io.open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)