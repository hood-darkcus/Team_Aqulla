import codecs

with codecs.open('dashboard.html', 'r', 'utf-8') as f:
    text = f.read()

css_old = """.cardboard-beam {
            width: calc(100% - 40px); /* spans between walls */
            height: 20px;
            background: linear-gradient(90deg, #d4a373, #faedcd);
            border-radius: 4px;
            position: absolute;
            top: 20px;
            transform-origin: center center;
            transition: border-radius 0.3s ease, height 0.3s ease, top 0.3s ease;
            box-shadow: inset 0 -4px 8px rgba(0,0,0,0.2);
        }"""
css_new = """.cardboard-beam-svg {
            width: calc(100% - 40px);
            height: 150px;
            position: absolute;
            top: 20px;
            overflow: visible;
        }"""
text = text.replace(css_old, css_new)

html_old = """<div class="cardboard-beam" id="beam"></div>"""
html_new = """<svg class="cardboard-beam-svg" id="beamSvg">
                    <defs>
                        <linearGradient id="beamGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stop-color="#d4a373" id="stop1"/>
                            <stop offset="100%" stop-color="#faedcd" id="stop2"/>
                        </linearGradient>
                    </defs>
                    <path id="beamPath" d="M 0 10 Q 50% 10 100% 10" stroke="url(#beamGrad)" stroke-width="20" fill="transparent" stroke-linecap="round"/>
                </svg>"""
text = text.replace(html_old, html_new)

text = text.replace("const beamEl = document.getElementById('beam');", 
"const beamPath = document.getElementById('beamPath');\n        const stop1 = document.getElementById('stop1');\n        const stop2 = document.getElementById('stop2');")

js_old = """// Apply a curve to the bottom of the div to simulate bending
            beamEl.style.height = (20 + currentDip) + "px";
            beamEl.style.borderBottomLeftRadius = (50 * bendIntensity) + "%";
            beamEl.style.borderBottomRightRadius = (50 * bendIntensity) + "%";
            
            // Change color to red as it fails
            if (bendIntensity > 0.8) {
                beamEl.style.background = linear-gradient(90deg, #d4a373, #ef4444, #faedcd);
            } else {
                beamEl.style.background = linear-gradient(90deg, #d4a373, #faedcd);
            }"""
js_new = """// Apply a quadratic bezier curve to the SVG path to simulate a true bend
            beamPath.setAttribute('d', M 0 10 Q 50%  100% 10);
            
            // Change color to red as it fails
            if (bendIntensity > 0.8) {
                stop1.setAttribute('stop-color', '#ef4444');
                stop2.setAttribute('stop-color', '#ef4444');
            } else {
                stop1.setAttribute('stop-color', '#d4a373');
                stop2.setAttribute('stop-color', '#faedcd');
            }"""
text = text.replace(js_old, js_new)

with codecs.open('dashboard.html', 'w', 'utf-8') as f:
    f.write(text)
print("SUCCESS!")
