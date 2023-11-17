# 提取 JNI 函数签名及其 dependency 的脚本
import sys
import json
from clang_android12_r31.cindex import CursorKind, Index, CompilationDatabase, TypeKind, TokenKind
import os
import re
import os.path
from clang_android12_r31.cindex import Config
from collections import defaultdict

# aosp project path
project_path = '/data_ssd_1/siyu/aosp/'
# aosp clang path
Config.set_library_path('/data_ssd_1/siyu/aosp/prebuilts/clang/host/linux-x86/clang-stable/lib64/')
# initial arguments for clang
init_arg_config = [
    '-isystem/data_ssd_1/siyu/aosp/prebuilts/clang/host/linux-x86/clang-r416183b1/lib64/clang/12.0.7/include']
# initial header file list
h_list = []
cpp_list = []
# dictionary for check if the file is already parsed
file_tu = {}


# 查找所有的 header 文件
def find_all_headers(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.h'):
                h_list.append(os.path.join(root, file))


# 查找所有的 cpp 文件
def find_all_cpps(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.cpp'):
                cpp_list.append(os.path.join(root, file))


def parse_file(file_path, index, args):
    # tu 指的是 translation unit
    tu = index.parse(file_path, args=args)
    for cursor in tu.cursor.get_children():
        process_node(cursor)


def process_node(cursor):
    # print(cursor.spelling, cursor.kind, cursor.location)
    if is_jni_function(cursor):
        extract_jni_signature(cursor)
        exit(0)


def is_jni_function(cursor):
    return 'JNIEXPORT' in cursor.displayname and 'JNICALL' in cursor.displayname


def extract_jni_signature(cursor):
    function_name = cursor.spelling
    print(function_name)
    return_type = cursor.result_type.spelling
    print(return_type)


class file_analyser():
    def __init__(self):
        self.CALLGRAPH = defaultdict(list)
        self.FULLNAMES = {}
        self.pro_path = ''
        self.ENDNODE = []
        self.show_loc = False
        self.print_all_node = False

        self.html_log = []
        self.current_depth = 0

        self.found_permission_method = []

        self.node_start = {}
        self.file_tu = {}

        self.analyzed_cpp = set()


if __name__ == "__main__":
    find_all_headers(project_path)
    find_all_cpps(project_path)
    print("Found", len(h_list), "header files")
    print("Found", len(cpp_list), "cpp files")
    for file in h_list:
        print(file)
        index = Index.create()
        parse_file(file, index, init_arg_config)
    for file in cpp_list:
        index = Index.create()
        parse_file(file, index, init_arg_config)
