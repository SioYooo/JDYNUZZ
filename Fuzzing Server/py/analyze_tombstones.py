# coding=utf-8

import datetime
import os
import shutil
from shutil import copyfile, copytree
import re

def list(path):
    # if not os.path.exists(path):
    #     os.makedirs(path)

    fs = os.listdir(path)
    l = []
    for f in fs:
        if not f.startswith('.') and not f.endswith('.pb'):
            l.append(path + f)
    # print(l)
    return l

def process_tomb(path):
    with open(path, 'r') as f:
        lines = f.readlines()
        start_record = False
        str_sanitizer = ''
        objFileName = None
        separater = '--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---\n'
        for line in lines:
            if '>>>' in line and '<<<' in line:
                # 获取文本从>>>到<<<
                text = line.split('>>>')[1].split('<<<')[0]
                if text != ' com.example.fuzzer ':
                    print('crash from (not "com.example.fuzzer"): ' + text)


            if 'ERROR: HWAddressSanitizer' in line:
                start_record = True
                str_sanitizer = str_sanitizer + separater
            if separater in line:
                start_record = False
            if line.startswith("'"):
                start_record = False
            if start_record:
                str_sanitizer = str_sanitizer + line
            # objFileName: 1651563423839
            if 'objFileName: ' in line:
                objFileName = line.split('objFileName: ')[1].strip()
        if str_sanitizer != '':
            str_sanitizer = str_sanitizer.split(separater)
            # if str_sanitizer[1] == str_sanitizer[2]:
            #     print('objFileName', objFileName)
            #     print(str_sanitizer[1])
            # else:
            #     print('---------------str_sanitizer[1]----------------')
            #     print(str_sanitizer[1])
            #     print('---------------str_sanitizer[2]----------------')
            #     print(str_sanitizer[2])
            #     raise Exception('not equal: str_sanitizer[1] == str_sanitizer[2]')

            # if len(str_sanitizer) == 2:
            #     print(str_sanitizer[1])
            #     raise Exception('len(str_sanitizer) == 2')
            save_file_path = path.replace('tombstones/tombstone_', 'tombstones_sanitizer/tombstone_')
            # print(save_file_path+'.txt')
            with open(save_file_path+'.txt', 'w') as f2:
                f2.write('objFileName' + objFileName + '\n')
                f2.write(str_sanitizer[1])

if __name__ == '__main__':

    l = list('backup_tombstones/')
    fs = []
    for p in l:
        path = p + '/tombstones_sanitizer/'
        # print(path)
        if not os.path.exists(path):
            os.makedirs(path)
        l2 = list(p + '/tombstones/')
        # print(l2)
        for t in l2:
            # print(t)
            process_tomb(t)
