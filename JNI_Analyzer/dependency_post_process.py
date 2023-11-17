#!/usr/bin/env python3

from pprint import pprint
from clang_android12_r31.cindex import CursorKind, Index, CompilationDatabase, TypeKind, TokenKind, Cursor
from collections import defaultdict
import sys
import json
import os.path
from clang_android12_r31.cindex import Config
import ccsyspath
import numpy as np
# from helper_local import get_file, find_c_or_cpp, find_files, find_command, find_command_star_node, get_cpp_files_path
from helper import get_file, find_c_or_cpp, find_files, find_command, find_command_star_node, get_cpp_files_path, \
    find_command_all_cpp
import re
import pickle
import copy
from util import get_tu, get_cursor, get_cursors

pathname = '/hci/chaoran_data/jni/dependency/temp'
filelist = os.listdir(pathname)

dependency_unique = set()
dependency_full = []
jni_full = []
file_full = []
java_class = set()

def process_jni_methods(jni_methods):
    for tem in jni_methods:
        print('\njava_fun:', tem['java_fun'])
        print('java_sig:', tem['java_sig'])
        print('cpp_fun:', tem['cpp_fun'])
        print('java_fun_full:', tem['java_fun_full'])
        jni_full.append(tem['java_fun_full'])
        clazz = tem['java_fun_full'].split(' ')

        java_class.add(clazz[0])

def process_dependency(dependency, jni_methods):
    for tem in dependency:
        if tem[0] == tem[1]:
            continue
        print(tem[0], '=>', tem[1])
        jni0 = None
        jni1 = None
        for jni in jni_methods:
            if jni['cpp_fun'] in tem[0]:
                jni0 = jni['java_fun_full']
            if jni['cpp_fun'] in tem[1]:
                jni1 = jni['java_fun_full']
        if jni1 is None or jni0 is None:
            # raise Exception('jni1 is None or jni0 is None: '+file_full[-1])
            pass
        else:
            if jni0+jni1 not in dependency_unique and 'release' not in jni0:
                dependency_unique.add(jni0+jni1)
                dependency_full.append({'file': file_full[-1], 'cpp': tem, 'java': [jni0, jni1]})


def process_json(full_path):
    print()
    with open(full_path, 'r') as f:
        o = json.load(f)
        file = o['file']
        file_full.append(file)
        print('file', file)
        jni_methods = o['jni_methods']
        process_jni_methods(jni_methods)
        dependency = o['dependency']
        print()
        process_dependency(dependency, jni_methods)

        # print('jni_methods', jni_methods)
        # print('dependency', dependency)

for file in filelist:
    full_path = os.path.join(pathname, file)
    print(full_path)
    process_json(full_path)

for tem in dependency_full:
    print('\nfile:', tem['file'])
    print('cpp:', tem['cpp'])
    print('java:', tem['java'])
print('len(dependency_full):', len(dependency_full))

print('len(jni_full):', len(jni_full))

print('len(java_class)', len(java_class))
str = ''
for i, tem in enumerate(java_class):
    if i == 0:
        str = str + 'SootClass c = Scene.v().loadClassAndSupport("%s");ArrayList<String> supportClassList = new ArrayList<String>();' % tem
    else:
        str = str + 'supportClassList.add("%s");' % tem
print(str)