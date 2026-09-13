import re
import io
with io.open('dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()
text = re.sub(r'statusEl\.textContent\s*=\s*".*?Connected to FastApi Brain";', 'statusEl.textContent = "Connected to FastApi Brain";', text)
text = re.sub(r'statusEl\.textContent\s*=\s*".*?Disconnected\. Is backend running\?";', 'statusEl.textContent = "Disconnected. Is backend running?";', text)
with io.open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)