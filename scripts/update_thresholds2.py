with open("run_real_injection.py", "r") as f:
    content = f.read()

old_thresh = 'if target == "0-1": threshold = 99.9'
new_thresh = 'if target == "0-1": threshold = 99.0'
content = content.replace(old_thresh, new_thresh)

with open("run_real_injection.py", "w") as f:
    f.write(content)
