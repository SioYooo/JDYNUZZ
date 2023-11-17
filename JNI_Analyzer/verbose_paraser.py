import os
import re
import json
import sys

if len(sys.argv) > 1:
    arg = sys.argv[1]
    print(arg)
    with open('/hci/chaoran_data/jni/tem/12.0compile_commands_full.json', 'r') as f:
        l = json.load(f)
        for t in l:
            if t['file'] == 'frameworks/native/libs/binder/IMemory.cpp':
                print(t['command'])
        # print(l[0])
    exit(0)


l = []

with open('verbose.log', 'r') as f:
    for i, line in enumerate(f):

        if 'prebuilts/clang/host/linux-x86/clang-r416183b1/bin/clang' in line:
            print(i)
            # print('---1---')
            cmd = line.replace('ANDROID_RUST_VERSION=1.51.0 ', '')
            cmd = re.sub(r'\[\d+/\d+\]', "", cmd)
            cmd = re.sub(r'\s+/bin/bash\s+-c\s+', "", cmd)
            cmd = cmd.strip()
            cmd = cmd.strip('"')
            # print(line)
            # print('---2---')
            # start_str = 'PWD=/proc/self/cwd'
            # cmd = line[line.index(start_str) + len(start_str):]
            cmd = re.sub(r'PWD=/proc/self/cwd\s+', "", cmd)
            # print(cmd)
            # print('---3---')
            cmd = re.sub(r'\s+-MD -MF\s+.+\.d', "", cmd)

            cmd = re.sub(r'\s+-o\s+.+\.o', "", cmd)
            # print(cmd)
            directory = '/hci/chaoran_data/android-12.0.0_r31'

            command = cmd.replace('\\', r'\\')
            file = cmd.split(' ')[-1]
            if not command.startswith('prebuilts/clang'):
                if command.startswith('rm') or command.startswith('prebuilts/rust/linux-x86/1.51.0/bin/rustc') \
                        or command.startswith('STD_ENV_ARCH') or 'link-args="' in command:
                    continue
                print('原始: ')
                print(line)
                print('处理后: ')
                print(cmd)
                exit(0)
            if not file.endswith('.c') and not file.endswith('.cpp') and not file.endswith('.S') and not file.endswith('.cc'):
                if not line.endswith('.c') and not line.endswith('.cpp') and not line.endswith('.S') and not line.endswith('.cc'):
                    continue
                print("file.endswith('.c') or file.endswith('.cpp')")
                print('原始: ')
                print(line)
                print('处理后: ')
                print(cmd)
                exit(0)
            l.append({"directory": directory, "command": command, "file": file, "arguments": command.split(' ')})
            # print(l)
            # python verbose_paraser.py "ssssssss(\\\"a\\\")sss"

            # aaa = r'ssssssss(\"a\")ssss'
            # print(aaa)
            # aaa = aaa.replace('\\', r'\\')
            # print(aaa)
            #
            # arg = sys.argv[1]
            # print('最终结果', arg)

            # mdmf = '-MD -MF'
            # print(cmd.index(mdmf))
            # i_mdmf = cmd.index(' ', start=cmd.index(mdmf))
            # print(mdmf[i_mdmf + len(mdmf):])
            # if re.match(r'prebuilts/clang/host/linux-x86/clang-r416183b1/bin/clang', line):
            #     print('*** pass ***')
            # exit(0)

with open('tem/12.0compile_commands_full.json', 'w') as f:
    json.dump(l, f)