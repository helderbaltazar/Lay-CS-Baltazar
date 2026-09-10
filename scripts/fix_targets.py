import re

with open("run_real_injection.py", "r") as f:
    content = f.read()

old_targets = '''    targets = [
        (LAY_0_1_BOT_ID, "bot_lay_0_1", "0-1"),
        (LAY_0_2_BOT_ID, "bot_lay_0_2", "0-2"),
        (LAY_0_3_BOT_ID, "bot_lay_0_3", "0-3"),
        (LAY_1_3_BOT_ID, LAY_U05_HT_BOT_ID, LAY_U15_HT_BOT_ID, LAY_U25_HT_BOT_ID, "bot_lay_1_3", "1-3"),
    ]'''
    
new_targets = '''    targets = [
        (LAY_0_1_BOT_ID, "bot_lay_0_1", "0-1"),
        (LAY_0_2_BOT_ID, "bot_lay_0_2", "0-2"),
        (LAY_0_3_BOT_ID, "bot_lay_0_3", "0-3"),
        (LAY_1_3_BOT_ID, "bot_lay_1_3", "1-3"),
        (LAY_U05_HT_BOT_ID, "bot_u05_ht", "UNDER_0.5_HT"),
        (LAY_U15_HT_BOT_ID, "bot_u15_ht", "UNDER_1.5_HT"),
        (LAY_U25_HT_BOT_ID, "bot_u25_ht", "UNDER_2.5_HT"),
    ]'''

content = content.replace(old_targets, new_targets)

with open("run_real_injection.py", "w") as f:
    f.write(content)

