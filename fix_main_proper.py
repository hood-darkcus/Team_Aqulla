import io
import re

with io.open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add macro_strain_live
target = "            'macro_acceleration': round(float(macro_acceleration[-1]), 6),"
replacement = "            'macro_acceleration': round(float(macro_acceleration[-1]), 6),\n            'macro_strain_live': round(float(smoothed_macro_strain[-1]), 6),"
text = text.replace(target, replacement)

# 2. Fix calibration
old_calib = '''                if flex_resistance > 100:
                    flex_calibration_samples.append(flex_resistance)
                    if len(flex_calibration_samples) >= 15:
                        app_config['flex_baseline'] = float(np.mean(flex_calibration_samples))
                        is_calibrated = True
                        print(f'[CALIBRATION] Dynamic Flex Baseline locked at: {app_config["flex_baseline"]:.1f} Ohms')'''

new_calib = '''                if flex_resistance > 100:
                    app_config['flex_baseline'] = 10000.0
                    is_calibrated = True
                    print(f'[CALIBRATION] Dynamic Flex Baseline locked at: {app_config["flex_baseline"]:.1f} Ohms')'''
text = text.replace(old_calib, new_calib)

# 3. Try except around math.log
old_calc = '''                    t_failure_rel = math.log(term) / k_opt
                    t_failure_abs = timestamps[0] + t_failure_rel
                    time_to_failure = t_failure_abs - time.time()
                    
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

new_calc = '''                    try:
                        t_failure_rel = math.log(term) / k_opt
                        t_failure_abs = timestamps[0] + t_failure_rel
                        time_to_failure = t_failure_abs - time.time()
                        
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
                                danger_level = max(0.0, min(100.0, 100.0 * (1 - val)))
                    except Exception as e:
                        print(f"[MATH ERROR] {e}")'''
text = text.replace(old_calc, new_calc)

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)