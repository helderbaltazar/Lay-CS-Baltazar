with open('scheduler.py', 'r') as f:
    content = f.read()

bad_string = 'send_message("Bom dia! 🏆\nHoje não temos nenhum jogo seguro fora da Blacklist para o método Lay 0-1.")'
good_string = 'send_message("Bom dia! 🏆\\nHoje não temos nenhum jogo seguro fora da Blacklist para o método Lay 0-1.")'

if bad_string in content:
    content = content.replace(bad_string, good_string)
    with open('scheduler.py', 'w') as f:
        f.write(content)
    print("Syntax error 1 fixed.")

