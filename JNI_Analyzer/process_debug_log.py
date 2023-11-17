

save_str = ''

with open('debug.log', 'r') as f:
    lines = f.readlines()
    for line in lines:
        if '===============each cpp_jni==================' in line:
            save_str = ''
        save_str = save_str + line

with open('debug_.log', 'w') as f2:
    print(save_str.split('\n')[:5])
    f2.write(save_str)