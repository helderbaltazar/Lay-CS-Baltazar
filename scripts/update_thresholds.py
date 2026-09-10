with open("run_real_injection.py", "r") as f:
    content = f.read()

old_thresh = '''        if target == "0-1": threshold = 94.0
        elif target == "0-2": threshold = 94.0
        elif target == "0-3": threshold = 99.20
        elif target == "1-3": threshold = 99.31'''

new_thresh = '''        if target == "0-1": threshold = 99.9
        elif target == "0-2": threshold = 91.0
        elif target == "0-3": threshold = 93.0
        elif target == "1-3": threshold = 98.0'''

content = content.replace(old_thresh, new_thresh)

with open("run_real_injection.py", "w") as f:
    f.write(content)

