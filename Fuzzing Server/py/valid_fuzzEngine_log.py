import os
import re

num_new_lines = []
first = True
last_new_line = 0
with open('fuzzEngineLog/log.txt', 'r') as f:
    lines = f.readlines()
    check_HWAddressSanitizer = False
    found_HWAddressSanitizer = False
    for i, line in enumerate(lines):
        if check_HWAddressSanitizer and 'ERROR: HWAddressSanitizer' in line:
            found_HWAddressSanitizer = True
            pass
        if '=============== NEW =================' in line or i == len(lines)-1:
            if not first and not found_HWAddressSanitizer:
                num_new_lines.append(last_new_line)
            check_HWAddressSanitizer = True
            found_HWAddressSanitizer = False
            if first:
                first = False
            last_new_line = i



    print('obj cannot reproduced (do not contain \'ERROR: HWAddressSanitizer\'): ', len(num_new_lines), num_new_lines)

    print_line = False
    for i, line in enumerate(lines):
        if '=============== NEW =================' in line:
            print_line = False
        if i in num_new_lines:
            print_line = True
            print('print from index:', i, 'line:', i+1)
        if print_line:
            print(line, end='')
