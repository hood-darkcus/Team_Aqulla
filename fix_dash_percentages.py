import io

with io.open('dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix JS path to use percentages instead of absolute 1000
old_js_path = '''beamPath.setAttribute("d", M 0 20 Q 500  1000 20);'''
new_js_path = '''beamPath.setAttribute("d", M 0 20 Q 50%  100% 20);'''
text = text.replace(old_js_path, new_js_path)

with io.open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)