import io
import re

with io.open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Increase BUFFER_SIZE
text = re.sub(r'BUFFER_SIZE = 100', 'BUFFER_SIZE = 400', text)

# 2. Add EMA to TTF
old_ttf_calc = '''                        if time_to_failure <= 0:
                            danger_level = 100.0
                            time_to_failure = 0.0
                        else:
                            if time_to_failure <= 10:
                                danger_level = 100.0
                            elif time_to_failure >= 3600:
                                danger_level = 0.0
                            else:
                                val = math.log(time_to_failure / 10.0) / math.log(3600.0 / 10.0)
                                danger_level = max(0.0, min(100.0, 100.0 * (1 - val)))'''

new_ttf_calc = '''                        # Apply EMA smoothing to TTF
                        global smoothed_ttf
                        if 'smoothed_ttf' not in globals() or smoothed_ttf is None:
                            smoothed_ttf = time_to_failure
                        else:
                            smoothed_ttf = 0.9 * smoothed_ttf + 0.1 * time_to_failure
                        time_to_failure = smoothed_ttf
                        
                        if time_to_failure <= 0:
                            danger_level = 100.0
                            time_to_failure = 0.0
                        else:
                            if time_to_failure <= 10:
                                danger_level = 100.0
                            elif time_to_failure >= 3600:
                                danger_level = 0.0
                            else:
                                val = math.log(time_to_failure / 10.0) / math.log(3600.0 / 10.0)
                                danger_level = max(0.0, min(100.0, 100.0 * (1 - val)))'''

text = text.replace(old_ttf_calc, new_ttf_calc)

# 3. Constrain curve_fit bounds
old_bounds = "bounds = ([-np.inf, 0, 0], [np.inf, np.inf, np.inf])"
new_bounds = "bounds = ([0, 0, 0], [np.inf, np.inf, 0.5])  # Constrain k_opt to max 0.5 to prevent wild jumps"
text = text.replace(old_bounds, new_bounds)

# 4. Remove negative strain initial guess bound error
old_p0 = "p0 = [strain_data[0], 0.001, k_guess]"
new_p0 = "p0 = [max(0.0, strain_data[0]), 0.001, k_guess]"
text = text.replace(old_p0, new_p0)

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)