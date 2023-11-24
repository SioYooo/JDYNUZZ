from __future__ import print_function

import argparse
import json
import os
import re
import shlex
import sys

RULE_PATTERN = re.compile(r'^\s*rule\s+(\S+)$')
COMMAND_PATTERN = re.compile(r'^\s*command\s*=\s*(.+)$')
BUILD_PATTERN = re.compile(r'^\s*build\s+.*:\s*(?P<rule>\S+)\s+(?P<file>\S+)')
CAT_PATTERN = re.compile(r'\\\$\$\(\s*cat\s+([^\)]+)\)')
# SUBCOMMAND_PATTERN = re.compile(r'\(([^\)]*)\)')
SUBCOMMAND_PATTERN = re.compile(r'\(.*?cpp.\)')

rules = {}
compdb = []
directory = os.path.abspath(os.getcwd())
cat_cache = {}


def cat_expand(match):
    file_name = match.group(1).strip()

    if file_name in cat_cache:
        return cat_cache[file_name]

    try:
        with open(file_name) as cat_file:
            content = cat_file.read().replace('\n', ' ').strip()
    except IOError as ex:
        print(ex, file=sys.stderr)
        content = None

    cat_cache[file_name] = content
    return content

def parse_command(command, file):
    # stop = False
    while command:
        first_space = command.find(' ', 1)
        if (first_space == -1):
            first_space = len(command)
        # second_space = command.find(' ', first_space)
        # if (second_space == -1):
        #     second_space = len(command)
        # if stop:
        #     print(command)
        #     print('------------')
        #     print(command[first_space:first_space + 30])
        #     print('------------')
        #     print(command[0:first_space])
        #     print('------------')
        #     print(command[0:first_space].endswith('/arm-linux-androideabi-g++'))
        #     exit(2)
        # if 'prebuilts/gcc/linux-x86/arm/arm-linux-androideabi-4.9/bin/arm-linux-androideabi-g++' in command and '/bin/bash' not in command:
        #     stop = True
            # exit(2)
        if command[0:first_space].endswith('/clang') or command[0:first_space].endswith('/clang++') or command[0:first_space].endswith('/arm-linux-androideabi-g++'):
            break

        command = command[first_space:]
    # if 'android_hardware_Radio.cpp' in file:
        # print(command)
        # exit(2)
    command = command.strip()
    if command.startswith('"'):
        command = command[1:-1]

    if not command:
        return False

    compdb.append({
        'directory': directory,
        'command': command,
        'file': file
    })
    return True


parser = argparse.ArgumentParser(description='Generate compile_commands.json for AOSP')
target_product = os.getenv('TARGET_PRODUCT')
if target_product:
    parser.add_argument('ninja_file', nargs='?', default='out/build-{}.ninja'.format(target_product))
else:
    parser.add_argument('ninja_file')
args = parser.parse_args()

with open(args.ninja_file) as ninja_file:
    for line in ninja_file:
        rule_match = RULE_PATTERN.match(line)
        if rule_match:
            rule_name = rule_match.group(1)
            continue

        command_match = COMMAND_PATTERN.match(line)
        if command_match:
            rules[rule_name] = command_match.group(1)
            continue

        build_match = BUILD_PATTERN.match(line)
        if not build_match:
            continue

        command = rules.get(build_match.group('rule'))
        if not command:
            continue

        file = build_match.group('file')
        if file.endswith('.S'):  # Skip asm files
            continue

        command = CAT_PATTERN.sub(cat_expand, command)
        has_subcommands = False
        for subcommand in SUBCOMMAND_PATTERN.finditer(command):
            has_subcommands = True
            # print()
            # print(subcommand.group(0))
            if parse_command(subcommand.group(0)[1:-1], file):
                break

        if not has_subcommands:
            parse_command(command, file)

# 传入参数应该处于 out/soong/build.ninja 所在目录
# /data_ssd_1/siyu/aosp/out/build-aosp_blueline.ninja
with open('/home/siyu/tifs/JDYNUZZ/JNI_Analyzer/tem/10.0compile_commands.json', 'w') as compdb_file:
    json.dump(compdb, compdb_file, indent=1)
