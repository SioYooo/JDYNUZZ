# coding=utf-8

import os
import re
from helper import find_command

def findAllFile(base, extension):
    for root, ds, fs in os.walk(base):
        for f in fs:
            if f.endswith('.' + extension) and 'tests/' not in root and 'test/' not in root and 'ndk/' not in root:
                    # and 'test/' not in root \
                    # and 'out/' not in root \
                    # and 'tests/' not in root \
                    # and 'development/' not in root \
                    # and 'packages/' not in root\
                    # and 'device/' not in root:
                # if not re.match(r'.*\d.*', f):
                    fullname = os.path.join(root, f)
                    yield fullname

def find_service_name(path, service_name):

    try:
        file = open(path, 'r', encoding='UTF-8')  # 转换编码以实现正确输出中文格式
        lines = file.readlines()
    except Exception as e:
        file = open(path, 'r', encoding='latin1')  # 转换编码以实现正确输出中文格式
        lines = file.readlines()
    finally:
        file.close()
    analyze_this_file = False
    for i, line in enumerate(lines):
        if '"' + service_name + '"' in line:
            analyze_this_file = True
    if not analyze_this_file:
        return False
    else:
        return True



def find_all(str, par):
    start = 0
    poses = []
    while True:
        index = str.find(par, start)
        start = index + 1

        if index!= -1:
            poses.append(index)
        else:
            break

    return poses

def extract_servicename_from_log(path):
    with open(path, 'r', encoding='UTF-8') as file:  # 转换编码以实现正确输出中文格式
        lines = file.readlines()

        analyze_this_file = False
        for i, line in enumerate(lines):
            if 'SEARCH FROM FUNCTION WHICH CONTAINS getService()' in line:
                # print(line.split("["))
                tem = line.split("[")[-1].strip()
                tem = tem[:-1]
                return tem

def find_in_h(service_name):
    base = '/Volumes/android/android-8.0.0_r34/frameworks/'
    # service_name = 'mount'
    h_files = findAllFile(base, 'h')
    for f in h_files:
        if find_service_name(f, service_name):
            c_cpp_list = find_command(f)
            if c_cpp_list is not None:
                source_file = '/Volumes/android/android-8.0.0_r34/' + c_cpp_list['source']
                print(source_file + '\n')
                return f
    return None

def find_in_cpp(service_name):
    base = '/Volumes/android/android-8.0.0_r34/frameworks/'
    # service_name = 'mount'
    h_files = findAllFile(base, 'cpp')
    for f in h_files:
        if find_service_name(f, service_name):
            return f
    return None

if __name__ == '__main__':
    paths = findAllFile('log/', 'txt')
    for path in paths:
        service_name = extract_servicename_from_log(path)
        if service_name != None and service_name != '':
            r = find_in_h(service_name)
            if(r != None):
                print()
                print('exist in *.h :::' + service_name)
                print(r)
            r = find_in_cpp(service_name)
            if (r != None):
                print()
                print('exist in *.cpp :::' + service_name)
                print(r)