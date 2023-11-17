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

# import shelve
"""
Dumps a callgraph of a function in a codebase
usage: callgraph.py file.cpp|compile_commands.json [-x exclude-list] [extra clang args...]
The easiest way to generate the file compile_commands.json for any make based
compilation chain is to use Bear and recompile with `bear make`.

When running the python script, after parsing all the codebase, you are
prompted to type in the function's name for which you wan to obtain the
callgraph

- 'new' means the version supports clear/restoreCallingIdentity
"""
# project_path = '/hci/chaoran_data/android-12.0.0_r31/'
# clang_prepath = 'prebuilts/clang/host/linux-x86/clang-r353983c1/'
# clang_lib_path = project_path + clang_prepath + 'lib64/libc++.so'
# clang_lib_path = '/hci/chaoran_data/android-10.0.0_r45/out/host/linux-x86/lib64/libclang_android.so'
# clang_lib_path = '/hci/chaoran_data/android-10.0.0_r45/prebuilts/clang/host/linux-x86/clang-r353983c1/lib64/libclang.so.9svn'
# # clang_lib_path = '/hci/chaoran_data/pythonProject/clang_api24/libclang.so'
# print(clang_lib_path)
# Config.set_library_file(clang_lib_path)
# init_arg_config = ['-isystem/hci/chaoran_data/android-10.0.0_r45/prebuilts/clang/host/linux-x86/clang-r353983c1/lib64/clang/9.0.3/include']
# init_arg_config = ['-x', 'c++', '-isystem/hci/chaoran_data/android-10.0.0_r45/prebuilts/clang/host/linux-x86/clang-r353983c1/lib64/clang/9.0.3/include']

project_path = '/hci/chaoran_data/android-12.0.0_r31/'
Config.set_library_path('/hci/chaoran_data/android-12.0.0_r31/prebuilts/clang/host/linux-x86/clang-r416183b1/lib64/')
init_arg_config = [
    '-isystem/hci/chaoran_data/android-12.0.0_r31/prebuilts/clang/host/linux-x86/clang-r416183b1/lib64/clang/12.0.7/include']

h_list = None

CursorKind.IF_CONDITION = CursorKind(8625)


# class Condition:
#     def __init__(self, spelling, displayname, location):
#         self.kind = CursorKind.IF_CONDITION
#         self.spelling = spelling
#         self.displayname = displayname
#         self.location = location
#         self.referenced = self
#
#     def set_ref(self, referenced):
#         self.referenced = referenced

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

        self.assign = {}
        self.add_self_assign('root')
        self.var = {}
        self.add_self_var('root')
        self.jni_methods = []
        self.structure_var = {}

        self.fist_lvl_funs = []

    def save(self):
        obj1 = pickle.dumps(self.CALLGRAPH)
        with open("tem/save/self.CALLGRAPH", "ab")as f:
            f.write(obj1)

    def load(self):
        f = open("tem/save/self.CALLGRAPH", "rb")
        while 1:
            try:
                obj = pickle.load(f)
                self.CALLGRAPH = obj
            except:
                break
        f.close()

    def get_diag_info(self, diag):
        return {
            'severity': diag.severity,
            'location': diag.location,
            'spelling': diag.spelling,
            'ranges': diag.ranges,
            'fixits': diag.fixits
        }

    def fully_qualified(self, c):
        if c is None:
            return ''
        elif c.kind == CursorKind.TRANSLATION_UNIT or c.kind == CursorKind.IF_CONDITION:
            return ''
        else:
            res = self.fully_qualified(c.semantic_parent)
            if res != '':
                return res + '::' + c.spelling
            return c.spelling

    def fully_qualified_pretty(self, c):
        if c is None:
            return ''
        elif c.kind == CursorKind.TRANSLATION_UNIT or c.kind == CursorKind.IF_CONDITION:
            return ''
        else:
            res = self.fully_qualified(c.semantic_parent)
            return_name = c.displayname
            # 需要处理模板函数
            # 去除函数名后的<>
            # '^[a-zA-Z0-9_^\(]+(::[a-zA-Z0-9_^\(]+)+<>\(' 全函数名匹配
            # 无类名匹配
            for tem in re.findall('^[a-zA-Z0-9_^\(]+<>\(', return_name):
                return_name = return_name.replace(tem, tem.replace('<>(', '('))
            # 去除参数列表中的<XXXX>
            for tem in re.findall('<[^\(]+?>', return_name):
                return_name = return_name.replace(tem, '<>')

            if res != '':
                return res + '::' + return_name
            # 防止更换Binder方法 但是参数中有漏掉const 导致匹配不到
            return return_name

    def is_excluded(self, node, xfiles, xprefs):
        if not node.extent.start.file:
            return False

        for xf in xfiles:
            if node.extent.start.file.name.startswith(xf):
                return True

        fqp = self.fully_qualified_pretty(node)

        for xp in xprefs:
            if fqp.startswith(xp):
                return True

        return False

    def is_template(self, node):
        return hasattr(node, 'type') and node.type.get_num_template_arguments() != -1

    def get_all_children(self, node, list=[], level=0, so_far=[]):
        for child in node.get_children():
            list.append([level, child])
            self.get_all_children(child, list, level + 1)

    def get_all_children_ref(self, node, list=[], level=0, so_far=[]):
        print('159 | ' + ' ' * level, node.kind, node.displayname)
        if node.kind == CursorKind.CALL_EXPR:
            print(node.displayname, node.referenced)
        if node.kind == CursorKind.CALL_EXPR and node.referenced:
            node = node.referenced

        if node in so_far:
            return
        so_far.append(node)

        if (node.location.file is not None and self.pro_path in node.location.file.name):

            for child in node.get_children():
                list.append([level, child])
                self.get_all_children_ref(child, list, level + 1, so_far)

    def get_para_index(self, para, method_index, children):
        para_index = -1
        for i in range(method_index, len(children)):
            if children[i][1].kind == CursorKind.PARM_DECL:
                para_index = para_index + 1
                if children[i][1].displayname == para:
                    return para_index
        print('未找到参数')

    def get_para_class_by_name(self, para, node):
        para_index = -1
        children = []
        self.get_all_children(node, children, level=0)
        found = False
        for i in range(len(children)):
            if children[i][1].kind == CursorKind.PARM_DECL:
                para_index = para_index + 1
                if found:
                    print('found|', children[i][1].kind, children[i][1].displayname)
                if found and children[i][1].kind == CursorKind.TYPE_REF and children[i][1].displayname != '':
                    return children[i][1].displayname
                if children[i][1].displayname == para:
                    found = True
        return None

    def get_method_index(self, index, children):
        print('*** get_method_index ***')
        # print(range(index, 0, -1))
        for i in range(index, 0, -1):
            # print(children[i][1].kind, children[i][1].displayname)
            if children[i][1].kind == CursorKind.FUNCTION_TEMPLATE or \
                    children[i][1].kind == CursorKind.CONSTRUCTOR or \
                    children[i][1].kind == CursorKind.CXX_METHOD or \
                    children[i][1].kind == CursorKind.FUNCTION_DECL:
                return i
        print('未找到函数')

    def get_method_index_var(self, index, method, children):
        method_str = self.fully_qualified_pretty(method.referenced)
        print('寻找', method_str, '的第', index, '个参数')
        last_level = 10e10
        para_index = -1
        for i, tem in enumerate(children):
            if tem[1].kind == CursorKind.CALL_EXPR and tem[1].displayname in method_str:
                if self.fully_qualified_pretty(tem[1].referenced) == method_str:
                    last_level = tem[0]

            if tem[0] < last_level:
                last_level = 10e10
                para_index = -1

            if tem[0] > last_level:
                if tem[1].kind == CursorKind.DECL_REF_EXPR:
                    para_index = para_index + 1
                    if para_index == index:
                        return tem[1].displayname, 'local', i
                if tem[1].kind == CursorKind.MEMBER_REF_EXPR:
                    para_index = para_index + 1
                    if para_index == index:
                        return tem[1].displayname, 'global', i
        print('未找到调用改函数传入的变量')
        return None, 'no_caller', -1

    def method_inner_para_class(self, index, node):
        children = []
        self.get_all_children(node, children, level=0)

        para_index = -1
        for i, tem in enumerate(children):
            print(tem[0], ' ' * tem[0], tem[1].kind, tem[1].displayname)
            if tem[1].kind == CursorKind.PARM_DECL:
                para_index = para_index + 1
                if para_index == index:
                    local_var = tem[1].displayname
                    return_class = self.find_var_local(local_var, children, node)
                    return return_class

    def find_var(self, var, file, DEBUG=False):
        print('\n*** var ***')
        print('在', file, '中寻找', var)
        # 头文件里面没有变量赋值 所以将.h文件中分析替换为.cpp文件中分析 (也许有潜在的问题，最好两处都分析)
        if file.endswith('.h'):
            file = file[:-1] + 'cpp'
        node = self.node_start[file]
        children = []
        self.get_all_children(node, children, level=0)
        last_level = 10e10
        assign_mode = False
        assign_stmt = []
        call_mode_last_level = 10e10
        call_node = None
        call_mode_para_index = -1
        current_fun_node = None
        for i, tem in enumerate(children):
            if DEBUG:
                print(tem[0], 'line 213|', ' ' * tem[0], tem[1].kind, tem[1].displayname)
            if tem[1].kind == CursorKind.CXX_METHOD:
                current_fun_node = tem[1]
            '''
            NativeRemoteDisplay(const sp<IRemoteDisplay>& display,
            const sp<NativeRemoteDisplayClient>& client) :
            mDisplay(display), mClient(client) {
            }

            ===
            mDisplay 由display决定
            display 是这个方法的第0个参数
            找这个方法第0个参数的类型
            '''
            if last_level == 10e10 and call_mode_last_level == 10e10:
                if DEBUG:
                    print(tem[0], 'line 226|', ' ' * tem[0], tem[1].kind, tem[1].displayname)
                if tem[1].kind == CursorKind.MEMBER_REF and tem[1].displayname == var:
                    if children[i + 2][1].kind == CursorKind.DECL_REF_EXPR:
                        para = children[i + 2][1].displayname
                        member_sp_mode = False
                        print('找到通过参数', para, '传入, index', i)
                        method_index = self.get_method_index(i, children)
                        para_index = self.get_para_index(para, method_index, children)
                        print('参数为第几个', para_index, '参数')
                        # 找到调用这个函数 的第x个参数 的变量名
                        method = children[method_index][1]
                        r, scope, var_index = self.get_method_index_var(para_index, method, children)
                        if scope == 'global':
                            print('.line 211')
                            return_class = self.find_var(r, file)
                        elif scope == 'local':
                            parent_method_index = self.get_method_index(var_index, children)
                            parent_method = children[parent_method_index][1]
                            print('.line 216')
                            return_class = self.find_var_local(r, children, parent_method)
                        elif scope == 'no_caller':
                            print('no caller, does not analyze')
                            return 'no_caller'
                        else:
                            print('unhandled scope.')
                        return return_class

            # 赋值
            if call_mode_last_level == 10e10:
                if DEBUG:
                    print(tem[0], 'line 254|', ' ' * tem[0], tem[1].kind, tem[1].displayname)
                # if tem[1].kind == CursorKind.UNARY_OPERATOR:
                #     # print(self._is_secure_condition(node))
                #     ooo = tem[1].get_tokens()
                #     for temm in ooo:
                #         print('/', temm.kind, temm.spelling, end=' ')
                # print()
                if var == tem[1].displayname:
                    # CursorKind.MEMBER_REF_EXPR mDrm
                    print('.line 236')
                    print('*** found var ***')
                    last_level = tem[0]
                    print(tem[0], 'var|', ' ' * tem[0], tem[1].kind, tem[1].displayname, tem[1].location)
                    # print(tem[0], 'var|', ' ' * tem[0], tem[1].kind, tem[1].displayname)
                if tem[0] > last_level:
                    print(tem[0], 'var|', ' ' * tem[0], tem[1].kind, tem[1].displayname, tem[1].location)
                    # print(tem[0], 'var|', ' ' * tem[0], tem[1].kind, tem[1].displayname)
                    # if assign_mode:
                    #     print(tem[0], 'line 306|', ' ' * tem[0], tem[1].kind, tem[1].displayname)
                    if 'operator=' in tem[1].displayname:
                        print('assign_mode = True')
                        # 赋值
                        assign_mode = True
                        print()
                    elif assign_mode and tem[1].kind == CursorKind.CALL_EXPR:
                        # get return var class
                        print('invoke method: get return class |||', tem[1].kind)
                        fun_str = self.fully_qualified_pretty(tem[1].referenced)
                        print('DEBUG ', fun_str)
                        if 'interface_cast' in fun_str:
                            # gAudioFlinger = interface_cast<IAudioFlinger>(binder);
                            for tem_i in range(i + 1, len(children)):
                                print(children[tem_i][0], 'interface_cast|', ' ' * children[tem_i][0],
                                      children[tem_i][1].kind, children[tem_i][1].displayname,
                                      children[tem_i][1].location)
                            return 'no_caller'
                            # exit(2)
                        print(fun_str, tem[1].location)
                        strinfo = re.compile('<.{0,}?>')
                        fun_str_revised = strinfo.sub('<>', fun_str)
                        print('fun_str_revised(去掉<...>模板内容):', fun_str_revised)
                        if self.has_no_ignore_fun(fun_str_revised):
                            entry_funs, entry_fun_vs = self.search_fun(fun_str_revised)
                        else:
                            return 'END'
                        # entry_funs, entry_fun_vs = self.search_fun(fun_str_revised)
                        # print(entry_fun_vs[0].location)
                        assert len(entry_fun_vs) == 1, '没找到函数或函数过多 ' + tem[1].referenced.displayname
                        print('.line 170')
                        return_class = self.get_return(entry_fun_vs[0], node)
                        print(return_class)
                        # exit(2)

                        # assign_mode = False
                        if return_class != None:
                            return return_class
                        pass
                    elif assign_mode and tem[1].kind == CursorKind.DECL_REF_EXPR:
                        print('line 323 被右边变量赋值了', tem[1].displayname)
                        # return self.find_var(tem[1].displayname, file)
                        print('变量所在函数:', current_fun_node.displayname)
                        children_current_fun_node = []
                        self.get_all_children(current_fun_node, children_current_fun_node, level=0)
                        return self.find_var_local(tem[1].displayname, children, current_fun_node)

                if tem[0] < last_level:
                    last_level = 10e10

            # 成员变量未找到 寻找通过传参方式赋值的变量
            '''
            3     CursorKind.CALL_EXPR waitForSensorService
            4      CursorKind.UNEXPOSED_EXPR waitForSensorService
            5       CursorKind.DECL_REF_EXPR waitForSensorService
            4      CursorKind.UNARY_OPERATOR 
            5       CursorKind.MEMBER_REF_EXPR mSensorServer
            '''
            '''
            这个变量被传入一个函数(传引用)
            在这个函数内这个变量被赋值
            '''
            if last_level == 10e10:
                if DEBUG:
                    print(tem[0], 'line 317|', ' ' * tem[0], tem[1].kind, tem[1].displayname)
                if tem[1].kind == CursorKind.CALL_EXPR and ('operator->' in tem[1].displayname or
                                                            'operator!=' in tem[1].displayname or
                                                            'operator==' in tem[1].displayname or
                                                            'operator=' in tem[1].displayname or
                                                            'sp' in tem[1].displayname or
                                                            'asBinder' in tem[1].displayname):
                    call_mode_last_level = 10e10
                    call_node = None
                    call_mode_para_index = -1

                if tem[1].kind == CursorKind.CALL_EXPR and 'operator->' not in tem[
                    1].displayname and 'operator!=' not in tem[1].displayname and 'operator==' not in tem[
                    1].displayname and 'operator=' not in tem[1].displayname and 'sp' not in tem[
                    1].displayname and 'asBinder' not in tem[1].displayname:
                    # 获取参数index BUGBUGBUG
                    # print(tem[0], 'line 308|', ' ' * tem[0], tem[1].kind, tem[1].displayname)
                    call_mode_last_level = tem[0]
                    call_node = tem[1]
                    call_mode_para_index = -1

                # 不需要第一个的子树 不然会将 var.method() 中的method作为第一个参数，实际并不是
                if tem[0] == call_mode_last_level + 1:
                    if tem[1].displayname == call_node.displayname or tem[1].displayname == 'operator==':
                        children_ignore = True
                    else:
                        children_ignore = False
                if tem[0] > call_mode_last_level and not children_ignore and (
                        tem[1].kind == CursorKind.MEMBER_REF_EXPR or tem[1].kind == CursorKind.DECL_REF_EXPR):
                    # print(tem[0], 'line 322|', ' ' * tem[0], tem[1].kind, tem[1].displayname)
                    if tem[1].displayname != call_node.displayname and 'operator->' not in tem[1].displayname and \
                            children[i - 1][1].kind != CursorKind.CALL_EXPR and 'operator->' not in children[i - 1][
                        1].displayname \
                            :
                        call_mode_para_index = call_mode_para_index + 1
                        if tem[1].displayname == var:
                            # 进入某个方法 第几个参数 在方法中被赋值
                            print('.line 318')
                            print('进入某个方法 第几个参数 在方法中被赋值')
                            print('FUN:', call_node.kind, call_node.displayname, call_node.location)
                            print('Para index:', call_mode_para_index)
                            if 'getService' in call_node.displayname:
                                print('找到传入的str， 去函数中查表')
                                service_names = []
                                self.print_childrens(call_node, service_names, 0)
                                print(service_names)
                                service_name = None
                                for tem in service_names:
                                    if tem[0] != '' and service_names != 'None' and 'permisson.' not in service_names:
                                        service_name = tem[0]
                                print(service_name)
                                class_str = self.service_str_trans(service_name)
                                print(class_str)
                                # exit(0)
                                return class_str
                            call_node_referenced = call_node.referenced
                            print(call_node_referenced.kind, call_node_referenced.displayname,
                                  call_node_referenced.location)
                            method_full = self.fully_qualified_pretty(call_node.referenced)
                            print(call_node.referenced.kind, method_full)
                            # 直接返回变量类名
                            if call_node.referenced.kind == CursorKind.CONSTRUCTOR:
                                return_class = self.fully_qualified(call_node.referenced.semantic_parent)
                                print(return_class)
                                return return_class
                            # 将IxxxService::直接替换为xxxService::
                            if 'AudioPolicyService::createAudioPatch' in method_full:
                                print('.line 421')
                                exit(0)
                            tema = re.findall(r'I[a-zA-Z]+?Service::', method_full)
                            for temb in tema:
                                print(temb)
                                method_full = method_full.replace(temb, temb[1:])
                            print(method_full)
                            if (call_node.displayname != 'GetLongField'):
                                entry_funs, entry_fun_vs = self.search_fun(method_full)
                                print('.lin3 325')
                                # 进入某个方法 第几个参数 在方法中被赋值
                                return_class = self.method_inner_para_class(call_mode_para_index, entry_fun_vs[0])
                                print('\n', return_class)
                                # exit(4)
                                return return_class
                            exit(7)
                            call_node_referenced = call_node.referenced

                # if tem[0] > call_mode_last_level and tem[1].kind == CursorKind.MEMBER_REF_EXPR and tem[1].displayname == var:
                #     # 传入的参数 method: call_node | para:tem[1].displayname
                #     fun_str = self.fully_qualified_pretty(call_node)
                #     if 'sp::' not in fun_str:
                #         print('.line 206')
                #         print('函数', fun_str, '调用', tem[1].displayname)
                if tem[0] < call_mode_last_level:
                    call_mode_last_level = 10e10
                    call_node = None
                    call_mode_para_index = -1

    def service_str_trans(self, str):
        if str == None:
            return str
        str = str.strip('"')
        if str == 'sensorservice':
            return 'android::SensorService'
        elif str == 'permission':
            return 'android::PermissionService'
        elif str == 'SurfaceFlinger':
            # SurfaceFlinger.h
            self.extend_h_analysis('frameworks/SurfaceFlinger_hwc1.cpp', '12.0', True, project_path, fuzzy=True)
            return 'android::SurfaceFlinger'
        else:
            return str

    def getService(self, index, children):
        print('*** getService ***')
        var = None
        start2find_var = False
        print(children[index][1].location)
        for i in range(index, index + 30):
            tem = children[i]
            print(tem[0], ' ' * tem[0], tem[1].kind, tem[1].displayname)
        ignore = False
        ini_level = children[index][0]
        for i in range(index, len(children)):
            if children[i][0] == ini_level + 1:
                if children[i][1].displayname == 'getService':
                    ignore = True
                else:
                    ignore = False
            if not ignore and children[i][1].kind == CursorKind.DECL_REF_EXPR and children[i][
                1].displayname != 'getService':
                var = children[i][1].displayname
                print('.line 396 ')
                print('var:', var)
                break
            if children[i][1].kind == CursorKind.STRING_LITERAL:
                print('.line 399 ')
                print('service_string', children[i][1].displayname)
                return_class = self.service_str_trans(children[i][1].displayname)
                print('return_class:', return_class)
                return return_class
        for i in range(0, index):
            if children[i][1].kind == CursorKind.VAR_DECL and children[i][1].displayname == var:
                print('.line 404 ')
                print('found var', var)
                start2find_var = True
            if start2find_var and children[i][1].kind == CursorKind.STRING_LITERAL:
                print('.line 407 ')
                print('service_string', children[i][1].displayname)
                return_class = self.service_str_trans(children[i][1].displayname)
                print('return_class:', return_class)
                return return_class

    def find_var_local(self, str, children, parent_node, so_far=None, DEBUG=True):
        print('\n****** find_var_local ******')
        if str == 'player':
            print('sssss')
        print('find var:', str, '| at', self.fully_qualified_pretty(parent_node), parent_node.location)
        if 'instance' in str:
            return 'END'
        declare_mode = False
        assign_left = False
        assign_mode = False
        last_level = 10e10
        assign_mode_last_level = 10e10
        for i, tem in enumerate(children):

            if DEBUG:
                print(tem[0], 'full|', ' ' * tem[0], tem[1].kind, tem[1].displayname)

            # if tem[1].kind == CursorKind.PARM_DECL and tem[1].displayname == str:
            #     for i2 in range(i, len(children)):
            #         if DEBUG:
            #             print(tem[0], '539 |', ' ' * children[i2][0], children[i2][1].kind, children[i2][1].displayname)
            #         # 知道第几个参数，找到传入这个参数的方法，获取那个参数赋值的类型
            #
            #         if children[i2][1].kind == CursorKind.TYPE_REF and children[i2][1].displayname.startswith('class '):
            #             return_class = children[i2][1].displayname
            #             return_class = return_class.replace('class ', '')
            #             return_class = return_class.replace('::I', '::')
            #             print('.line 490')
            #             print('return_class:', return_class)
            #             # return_class = self.service_str_trans(return_class)
            #             return return_class
            #             # return 'END'

            if tem[1].kind == CursorKind.CALL_EXPR and tem[1].displayname == 'getService':
                # 如果函数传入参数有要找的变量
                tem_level = tem[0]
                print('getService tem_level =', tem_level)
                for tem_i in range(i + 1, len(children)):
                    print('getService|', ' ' * children[tem_i][0], children[tem_i][1].kind,
                          children[tem_i][1].displayname)
                    if children[tem_i][0] <= tem_level:
                        break
                    if children[tem_i][1].kind == CursorKind.DECL_REF_EXPR and children[tem_i][1].displayname == str:
                        print('.line 458 参数获取了一个服务类')
                        return_class = self.getService(i, children)
                        return return_class

            if tem[1].displayname == str:
                if tem[1].kind == CursorKind.VAR_DECL:
                    declare_mode = True
                    last_level = tem[0]
                elif tem[1].kind == CursorKind.DECL_REF_EXPR:
                    # 找到等号左边
                    assign_left = True
                    '''
                    7 full|         CursorKind.COMPOUND_STMT 
                    8 full|          CursorKind.CALL_EXPR operator=
                    9 full|           CursorKind.UNARY_OPERATOR 
                    10 full|            CursorKind.UNEXPOSED_EXPR server
                    11 full|             CursorKind.DECL_REF_EXPR server
                    9 full|           CursorKind.UNEXPOSED_EXPR operator=
                    10 full|            CursorKind.DECL_REF_EXPR operator=
                    9 full|           CursorKind.UNEXPOSED_EXPR s
                    10 full|            CursorKind.DECL_REF_EXPR s
                    '''
                    for tem_i in range(i - 1, 0, -1):
                        if children[tem_i][1].kind == CursorKind.CALL_EXPR and children[tem_i][
                            1].displayname == 'operator=':
                            assign_mode_last_level = children[tem_i][0]
                            break
                    print('assign_mode_last_level =', assign_mode_last_level)
                    print('*** found var ***')
                    # print(tem[0], 'var|', ' ' * tem[0], tem[1].kind, tem[1].displayname, tem[1].location)
                    print(tem[0], 'var 468|', ' ' * tem[0], tem[1].kind, tem[1].displayname)

            if declare_mode and tem[0] < last_level:
                declare_mode = False
                last_level = 10e10
            if declare_mode and tem[0] > last_level:
                if tem[1].kind == CursorKind.CALL_EXPR and declare_mode and tem[1].displayname != '' and tem[
                    1].displayname != 'sp':
                    print('****** CursorKind.CALL_EXPR ******')
                    print(tem[1].referenced.displayname)
                    method_full = self.fully_qualified_pretty(tem[1].referenced)
                    print(tem[1].referenced.kind, method_full)
                    if tem[1].referenced.kind == CursorKind.CONSTRUCTOR:
                        return_class = self.fully_qualified(tem[1].referenced.semantic_parent)
                        print(return_class)
                        return return_class
                    # 将IxxxService::直接替换为xxxService::
                    # tema = re.findall(r'I[a-zA-Z]+?Service::', method_full)
                    print('.line 575 将IxxxService::直接替换为xxxService::')
                    if 'AudioPolicyService::createAudioPatch' in method_full:
                        print('.line 580')
                        # self.extend_h_analysis(hfile, '0.7', True, project_path)
                        exit(0)
                    tema = re.findall(r'I[A-Z][a-z][a-zA-Z]+?::', method_full)
                    for temb in tema:
                        print(temb)
                        method_full = method_full.replace(temb, temb[1:])
                    print(method_full)
                    print(tem[1].displayname, tem[1].displayname != 'GetLongField')
                    if (tem[1].displayname != 'GetLongField'):
                        entry_funs, entry_fun_vs = self.search_fun(method_full)
                        print('.line 237')
                        # *** search for fun android::SurfaceComposer::createConnection() ***
                        if len(entry_funs) == 0:
                            print('.line 614 未处理屏蔽掉')
                            return 'END'
                        return_class = self.get_return(entry_fun_vs[0], parent_node, level=tem[0] + 1)
                        # return_class = 'DrmHal'
                        print('\n', return_class)
                        # exit(4)
                        return return_class
                    # 在children里找到这个变量的类型

            # 找到左边时 非子tree 退出
            if assign_left and tem[0] < assign_mode_last_level:
                assign_left = False
                assign_mode_last_level = 10e10

            # 找到左边时 看是否找到右边
            if assign_left and tem[0] >= assign_mode_last_level:
                print(tem[0], 'var(find right)|', ' ' * tem[0], tem[1].kind, tem[1].displayname)
                # if tem[1].kind == CursorKind.BINARY_OPERATOR and children[i-1][1].kind != CursorKind.IF_STMT:
                #     l, op, r = self._get_binop_operator(tem[1], get_left_right=True)
                #     print(l, op, r)
                #     if l == str:
                #         print('返回right的函数')
                #         exit(2)
                #         return self.find_var_local()

                if 'operator=' in tem[1].displayname:
                    # 赋值
                    assign_mode = True

                elif assign_mode and tem[1].kind == CursorKind.CXX_NEW_EXPR:
                    print('.line 424')
                    print(children[i + 1][1].kind)
                    if children[i + 1][1].kind == CursorKind.TYPE_REF:
                        assert children[i + 1][1].displayname.startswith('class ')
                        return_class = children[i + 1][1].displayname[6:]
                        print('.line 429')
                        print(return_class)
                        # exit(6)
                        return return_class
                elif assign_mode and tem[1].kind == CursorKind.CALL_EXPR:
                    print('.line 434')
                    print('invoke method: get return class |||', tem[1].kind)
                    fun_str = self.fully_qualified_pretty(tem[1].referenced)
                    print('DEBUG ', fun_str)
                    print(fun_str, tem[1].location)
                    if 'interface_cast' in fun_str:
                        # gAudioFlinger = interface_cast<IAudioFlinger>(binder);
                        for tem_i in range(i + 1, len(children)):
                            print(children[tem_i][0], 'interface_cast|', ' ' * children[tem_i][0],
                                  children[tem_i][1].kind, children[tem_i][1].displayname)
                            if children[tem_i][1].kind == CursorKind.TYPE_REF:
                                return_class = children[tem_i][1].displayname
                                return_class = return_class.replace('class ', '')
                                return_class = return_class.replace('::I', '::')
                                print('.line 574')
                                print(return_class)
                                return return_class
                    strinfo = re.compile('<.{0,}?>')
                    fun_str_revised = strinfo.sub('<>', fun_str)
                    print('fun_str_revised(去掉<...>模板内容):', fun_str_revised)
                    print('.line 437')
                    if self.has_no_ignore_fun(fun_str_revised):
                        entry_funs, entry_fun_vs = self.search_fun(fun_str_revised)
                    else:
                        return 'END'
                    # print(entry_fun_vs[0].location)
                    assert len(entry_fun_vs) == 1, '没找到函数或函数过多 ' + tem[1].referenced.displayname
                    print('.line 444')
                    return_class = self.get_return(entry_fun_vs[0], parent_node)
                    print(return_class)
                    # exit(2)

                    # assign_mode = False
                    if return_class != None:
                        return return_class
                    pass

                elif assign_mode and tem[1].kind == CursorKind.DECL_REF_EXPR:
                    print('被右边变量赋值了', tem[1].displayname)
                    return self.find_var_local(tem[1].displayname, children, parent_node)

        for i, tem in enumerate(children):

            if DEBUG:
                print(tem[0], 'full|', ' ' * tem[0], tem[1].kind, tem[1].displayname)

            if tem[1].kind == CursorKind.PARM_DECL and tem[1].displayname == str:
                for i2 in range(i, len(children)):
                    if DEBUG:
                        print(tem[0], '539 |', ' ' * children[i2][0], children[i2][1].kind, children[i2][1].displayname)
                    # 知道第几个参数，找到传入这个参数的方法，获取那个参数赋值的类型

                    if children[i2][1].kind == CursorKind.TYPE_REF and children[i2][1].displayname.startswith('class '):
                        return_class = children[i2][1].displayname
                        return_class = return_class.replace('class ', '')
                        return_class = return_class.replace('::I', '::')
                        print('.line 490')
                        print('return_class:', return_class)
                        # return_class = self.service_str_trans(return_class)
                        # return return_class
                        return 'END'

    def get_return(self, node, parent_node, level=0, debug=False):
        # node = node.referenced
        print('\n*** get_return ***\n', node.kind, self.fully_qualified_pretty(node), node.location)

        # 如果函数指向Binder，修正为真正的函数
        method_full = self.fully_qualified_pretty(node)
        # print('original TO:', method_full, node.location)
        if 'android::hardware::' in method_full or '::asInterface' in method_full:
            return

        # TO如果为IxxxService:: 直接替换
        # 将IxxxService::直接替换为xxxService::
        # ::IDrm:: YES  ::IPCThreadState:: NO
        r_final = re.findall(r'::I[A-Z][a-z].+?::', method_full)
        if len(r_final) > 0 and self.has_no_ignore_fun(method_full):
            if 'AudioPolicyService::createAudioPatch' in method_full:
                print('.line 690')
                exit(0)
            tema = re.findall(r'I[a-zA-Z]+?Service::', method_full)
            if self.has_ignore_fun_Ixx(method_full) and len(tema) > 0:
                print('替换前', method_full)
                if 'createAudioPatch' in method_full:
                    print('.line 684 FOUND createAudioPatch:', method_full)
                for temb in tema:
                    print(temb)
                    method_full = method_full.replace(temb, temb[1:])
                print('替换后', method_full)
                k_list, v_list = self.search_fun_list_full(method_full)
                print('.line 267')
                print('LINK到下一个方法:')
                print(method_full)
                print('.line 733 更改为', k_list[0], v_list[0].location)
                print('.line 548')
                print('*** 继续正常打印call graph****')
                # self.print_calls(k_list[0], so_far, v_list[0], permission_strs, depth + 1)
                node = v_list[0]
            elif self.has_ignore_fun_Ixx(self.fully_qualified_pretty(node)):
                print('.line 269')
                return_class = self.link_binder(parent_node, node)
                if return_class == 'no_caller':
                    print('no_caller，返回sp中的类')
                    exit(8)
                print('.line 277')
                print('LINK到下一个方法:')
                print(self.fully_qualified_pretty(parent_node), '=>')
                print(self.fully_qualified_pretty(node))
                fun_str = return_class + '::' + node.displayname
                print('.line 749 更改为', fun_str)
                strinfo = re.compile('<.{0,}?>')
                fun_str_revised = strinfo.sub('<>', fun_str)
                print('fun_str_revised(去掉<...>模板内容):', fun_str_revised)
                print('function in self.CALLGRAPH:', fun_str_revised in self.CALLGRAPH)
                if self.has_no_ignore_fun(fun_str_revised) and 'END' not in return_class:
                    k_list, v_list = self.search_fun_list_full(fun_str_revised)
                else:
                    return 'END'
                # k_list, v_list = self.search_fun_list_full(fun_str_revised)
                print('.line 573')
                print('*** 继续正常打印call graph****')
                print(k_list[0], v_list[0].location, '=> ...')
                # self.print_calls(k_list[0], so_far, v_list[0], permission_strs, depth + 1)
                node = v_list[0]
            elif '::getService' in self.fully_qualified_pretty(node):
                print('暂时忽略掉隐式Service的Binder')
                return 'END'
            else:
                print('*** ignore IServiceManager:: method ****', self.fully_qualified_pretty(node))

        children = []
        self.get_all_children(node, children, level=level)
        TEMPLATE_REF_list = []

        return_mode = False
        last_return_level = 10e10
        single_var_return = True

        for tem in children:
            if debug:
                print(tem[0], ' ' * tem[0], tem[1].kind, tem[1].displayname, end='')
            type = tem[1].type
            if debug:
                print('|type:', type.kind, end='')
            # if node.kind.is_reference():
            #     ref_node = node.get_definition()
            #     print(ref_node.spelling)

            # 测试搜索变量指向的实际类命
            # if tem[1].displayname == 'mDrm' and tem[1].kind == CursorKind.MEMBER_REF_EXPR:
            #     self.find_var(tem[1])

            # 返回
            if tem[1].kind == CursorKind.RETURN_STMT:
                return_mode = True
                last_return_level = tem[0]

            if tem[0] < last_return_level:
                return_mode = False
                last_return_level = 10e10
            if tem[0] > last_return_level:
                if tem[1].kind == CursorKind.MEMBER_REF_EXPR:
                    # return [tem[1].kind, tem[1].displayname]
                    print('.line 325')
                    print('*** return CursorKind.MEMBER_REF_EXPR ***')
                    return_class = self.find_var(tem[1].displayname, tem[1].location.file.name)
                    assert return_class is not None
                    return return_class
                elif tem[1].kind == CursorKind.CONDITIONAL_OPERATOR:
                    single_var_return = False
                elif tem[1].kind == CursorKind.DECL_REF_EXPR and single_var_return:
                    print('\n****** CursorKind.DECL_REF_EXPR ******')
                    print(tem[1].displayname)
                    print('.line 343')
                    if tem[1].displayname:
                        return_class = self.find_var_local(tem[1].displayname, children, node)
                    else:
                        return_class = 'END'
                    assert return_class is not None
                    # 在children里找到这个变量的类型
                    return return_class
            # 不要sp这种模板函数的call_expr
            if tem[1].kind == CursorKind.TEMPLATE_REF:
                if tem[1].displayname not in TEMPLATE_REF_list:
                    TEMPLATE_REF_list.append(tem[1].displayname)
            # if tem[1].kind == CursorKind.DECL_REF_EXPR and tem[1].displayname not in TEMPLATE_REF_list:
            #     if tem[1].referenced is not None:
            #         print('11111111111111111')
            #         print(tem[1].referenced.kind, tem[1].referenced.displayname)
            #         if tem[1].referenced.kind== CursorKind.CXX_METHOD:
            #             return_class = self.get_return(tem[1].referenced, level=tem[0] + 1)
            #             if return_class != None:
            #                 return return_class
            #             print('\n*** END END END analyze_fun ***')
            if tem[1].kind == CursorKind.CALL_EXPR and tem[1].displayname not in TEMPLATE_REF_list:
                if tem[1].referenced is not None and return_mode:
                    return_mode = False
                    last_return_level = 10e10
                    print('.line 347')
                    return_class = self.get_return(tem[1].referenced, parent_node, level=tem[0] + 1)
                    print('\n*** END END END analyze_fun ***')
                    if return_class != None:
                        return return_class

            elif tem[1].kind == CursorKind.INTEGER_LITERAL:
                value = tem[1].get_tokens()
                if debug:
                    for v in value:
                        print('', v.spelling, end='')
                # value = value.__next__().spelling
                # print('',value, end='')
            elif type.kind == TypeKind.RECORD:
                value = type.spelling
                if debug:
                    print('', value, end='')
                if return_mode:
                    return type.spelling
            # and type.kind == TypeKind.DEPENDENT
            # elif (tem[1].kind == CursorKind.DECL_REF_EXPR ):
            #     ooo = node.get_tokens()
            #     for tem in ooo:
            #         print('|', tem.kind, tem.spelling, end=' ')
            #     # iii = type.get_pointee()
            #     # print(iii)
            #     o=0
            elif (tem[1].kind == CursorKind.TYPE_REF and type.kind == TypeKind.UNEXPOSED):
                if debug:
                    print(type.spelling, end='')
            # print(node.type.get_typedef_name())
            # if node.kind == CursorKind.TYPE_REF:
            #     num = node.get_num_template_arguments()
            #     print(num)
            # print(self.fully_qualified_pretty(node))
            if debug:
                print()
        # print('\n*** ENDENDEND analyze_fun ***')

    def get_caller(self, last, current, so_far=None, debug=True):
        # if 'getMediaPlayerService' in current.displayname:
        #     return 'service', 'var_init'
        # node = node.referenced
        print('\n*** get_caller ***\nsearch in method:', last.kind, last.displayname, last.location)
        print('to find', current.displayname)
        children = []
        self.get_all_children(last, children, level=0)
        TEMPLATE_REF_list = []

        found_CALL_EXPR = False
        found_operator = False
        CALL_EXPR = ''
        last_level = 10e10
        for tem in children:
            if debug:
                print(tem[0], ' ' * tem[0], tem[1].kind, tem[1].displayname, end='')
            # if tem[1].kind == CursorKind.CALL_EXPR:
            #     # debug
            #     print('|', tem[1].referenced.displayname)
            if tem[1].kind == CursorKind.CALL_EXPR and tem[1].referenced is not None and tem[
                1].referenced.displayname == current.displayname:
                found_CALL_EXPR = True
                CALL_EXPR = tem[1].displayname
                print('found_CALL_EXPR = True')
                last_level = tem[0]
            if tem[0] < last_level:
                found_CALL_EXPR = False
                found_operator = False
                last_level = 10e10
            if tem[0] > last_level and found_CALL_EXPR and not found_operator and tem[1].displayname == 'operator->':
                print('found_operator = True')
                found_operator = True
            if tem[0] > last_level and found_operator and tem[1].kind == CursorKind.MEMBER_REF_EXPR:
                return tem[1].displayname, 'global'
            if tem[0] > last_level and found_operator and tem[1].kind == CursorKind.DECL_REF_EXPR:
                if tem[1].displayname == CALL_EXPR:
                    '''
                    6        CursorKind.CALL_EXPR getBuiltInDisplay
                    7         CursorKind.MEMBER_REF_EXPR getBuiltInDisplay
                    8          CursorKind.CALL_EXPR operator->
                    9           CursorKind.UNEXPOSED_EXPR 
                    10            CursorKind.UNEXPOSED_EXPR 
                    11             CursorKind.CALL_EXPR getComposerService
                    12              CursorKind.UNEXPOSED_EXPR getComposerService
                    13               CursorKind.DECL_REF_EXPR getComposerService
                    '''
                    print('.line 864')
                    return '', 'no_caller'
                if tem[1].displayname != 'interface_cast':
                    print('.line 862')
                    return tem[1].displayname, 'local'
                else:
                    print('\t 不终止忽略interface_cast')
                    continue
            if debug:
                print()

        # 没有找到 var -> xxx 格式的调用
        # const sp<IMediaPlayerService> service(getMediaPlayerService());
        return None, 'no_caller'

    def link_binder(self, last, current, so_far=None):
        '''
        用来找到Bind实际指向的函数
        '''
        print('\n******* link_binder ******')
        print('|last:', last.kind, last.displayname)
        # print('original TO:', current.kind, current.displayname)
        print('.line 426')
        r, scope = self.get_caller(last, current, so_far)
        print('\nr, scope:', r, scope)
        print('\n******* link_binder children ENDENDEND******')
        file = last.location.file.name
        # file = os.path.basename(path)
        return_class = None
        if scope == 'global':
            print('.line 432')
            return_class = self.find_var(r, file)
        elif scope == 'local':
            children = []
            print('.line 436')
            self.get_all_children(last, children)
            return_class = self.find_var_local(r, children, last, so_far)
        elif scope == 'no_caller':
            print('no caller, does not analyze')
            return 'no_caller'
        # elif scope == 'var_init':
        #     return_class = 'android::MediaPlayerService'
        else:
            print('unhandled scope.')
        print('.line 447')
        print('link_binder:', return_class)
        # assert return_class is not None, '没有找到Binder的函数'
        if return_class is None:
            return 'no_caller'
        return return_class
        # exit(3)

    def _get_num_comparision_operator(self, cursor):
        count = 0
        tem = ''
        for token in cursor.get_tokens():
            tem = tem + token.spelling + ' '
        tem = tem[:-1]
        COMPARISION_OPERATORS = ['==', '<=', '>=', '<', '>', '!=', '&&', '||']
        for temCOMPARISION_OPERATORS in COMPARISION_OPERATORS:
            tem = tem.replace(temCOMPARISION_OPERATORS, temCOMPARISION_OPERATORS + '@@')
        ori_tem = tem.split('@@')
        for tem in ori_tem:
            if '(' in tem and ')' in tem:
                count = count + 1
        return count

    def _contain_comparision_operator(self, cursor):
        COMPARISION_OPERATORS = ['==', '<=', '>=', '<', '>', '!=', '&&', '||']
        for token in cursor.get_tokens():
            if token.spelling in COMPARISION_OPERATORS:
                return True
        return False

        # tokens = []
        # for token in cursor.get_tokens():
        #     tokens.append(token)

        # if tokens[-1].spelling in COMPARISION_OPERATORS:
        #     return tokens[-1].spelling
        # else:
        #     return None

    def _return_condition(self, cursor, debug=True):
        ooo = cursor.get_tokens()
        str = ''
        for tem in ooo:
            if debug:
                print('|', tem.kind, tem.spelling, end=' ')
            str = str + tem.spelling + ' '

        return str[:-1]

    def _get_binop_operator(self, cursor, get_left_right=False):
        """
        https://github.com/coala/coala-bears/blob/master/bears/c_languages/codeclone_detection/ClangCountingConditions.py
        Returns the operator token of a binary operator cursor.
        :param cursor: A cursor of kind BINARY_OPERATOR.
        :return:       The token object containing the actual operator or None.
        """
        children = list(cursor.get_children())
        # print('\n\n%%%\n%%%\n', end='')
        # for child in children:
        #     print(' ', child.displayname, end='')
        # print('\n%%%\n%%%')
        operator_min_begin = (children[0].location.line,
                              children[0].location.column)
        operator_max_end = (children[1].location.line,
                            children[1].location.column)
        left = children[0].displayname
        if children[0].kind == CursorKind.CALL_EXPR:
            left = left + ' ( )'
        right = children[1].displayname
        if children[1].kind == CursorKind.CALL_EXPR:
            right = right + ' ( )'

        for token in cursor.get_tokens():
            if (operator_min_begin < (token.extent.start.line,
                                      token.extent.start.column) and
                    operator_max_end >= (token.extent.end.line,
                                         token.extent.end.column)):
                if get_left_right:
                    return left, token.spelling, right
                else:
                    return token.spelling
        if get_left_right:
            return None, None, None
        else:
            return None  # pragma: no cover

    def _analyze_switch(self, cursor, debug=True):
        case_flag = False
        return_flag = False
        switch_flag = False
        switch_var = None
        cond = {}
        tokens = cursor.get_tokens()
        for tem in tokens:
            if debug:
                print('|', tem.kind, tem.spelling, end=' ')

            if tem.kind == TokenKind.KEYWORD and tem.spelling == 'switch':
                switch_flag = True
            elif tem.kind == TokenKind.IDENTIFIER and switch_flag:
                switch_flag = False
                switch_var = tem.spelling
            elif tem.kind == TokenKind.KEYWORD and tem.spelling == 'case':
                case_flag = True
            elif tem.kind == TokenKind.IDENTIFIER and case_flag:
                case_flag = False
                cond[tem.spelling] = None
            elif tem.kind == TokenKind.KEYWORD and tem.spelling == 'return':
                return_flag = True
            elif tem.kind == TokenKind.IDENTIFIER and return_flag:
                return_flag = False
                keys = cond.keys()
                for key in keys:
                    if cond[key] == None:
                        cond[key] = tem.spelling
            elif tem.kind == TokenKind.KEYWORD and tem.spelling == 'default':
                cond[tem.spelling] = None

        if debug:
            print()
            print('=============cond======\n', cond)
        # exit(0)
        return switch_var, cond

    def _get_fun_con(self, cursor, debug=True):
        print('|||||||||||cursor|||', cursor.kind, cursor.displayname, cursor.location)
        ori_cursor = cursor
        cursor = cursor.referenced
        fun_str = self.fully_qualified_pretty(cursor)
        str_return_cond = fun_str
        print(fun_str)
        return_cond = []
        print('.line 1060', cursor.location.file.name)
        # if 'std::__1' in fun_str:
        #     str_return_cond = ori_cursor.displayname
        #     print('std::__1|||' + str_return_cond)
        #     return str_return_cond
        tem_head = cursor.location.file.name
        if tem_head.endswith('.h'):
            print('.line 1066 方法在.h中定义 需要扩展分析cpp', tem_head)
            c_cpp_list = find_command(tem_head, version_prefix='12.0', compdb=True, project_path=project_path)
            # for i_c_cpp_lists, c_cpp_list in enumerate(c_cpp_lists):
            #     print('.line 2293 ', i_c_cpp_lists, '/', len(c_cpp_lists))
            if c_cpp_list is not None and project_path + c_cpp_list['file'] not in self.analyzed_cpp:
                # next_file = '/Volumes/android/android-7.0.0_r33/' + c_cpp_list['source']
                next_file = project_path + c_cpp_list['file']
                self.analyzed_cpp.add(next_file)
                print('.line 1074', next_file)
                '''
                        /Volumes/android/android-7.0.0_r33/frameworks/av/media/libstagefright/MediaClock.cpp:93:5: error: use of undeclared identifier 'GE'
                        /Volumes/android/android-7.0.0_r33/frameworks/av/media/libstagefright/foundation/AString.cpp:170:5: error: use of undeclared identifier 'LT'
                        /Volumes/android/android-7.0.0_r33/frameworks/av/media/libstagefright/MediaSync.cpp:502:9: error: use of undeclared identifier 'EQ'         
                        /Volumes/android/android-7.0.0_r33/frameworks/av/media/libstagefright/foundation/MediaBuffer.cpp:109:9: error: use of undeclared identifier 'EQ'

                '''
                if not (
                        'MediaClock.cpp' in next_file or 'AString.cpp' in next_file or 'MediaSync.cpp' in next_file or 'MediaBuffer.cpp' in next_file):
                    print('pass: ', next_file)

                    # ninja_args = c_cpp_list['content']['flags']
                    # ninja_args = c_cpp_list['command'].split()[1:]
                    ninja_args = c_cpp_list['arguments'][1:]
                    ninja_args = self.parse_ninja_args(ninja_args)
                    # print(next_file)
                    # print(ninja_args)
                    # self.load_cfg(index, c_cpp_list['content']['compiler'], next_file, ninja_args)

                    # if 'clang++' in c_cpp_list['command'].split()[0]:
                    if 'clang++' in c_cpp_list['arguments'][0]:
                        self.load_cfg(self.index, 'clang++', next_file, ninja_args)
                    else:
                        self.load_cfg(self.index, 'clang', next_file, ninja_args)

            k_list, v_list = self.search_fun_list_full(self.fully_qualified_pretty(cursor))
            found = False
            for v_list_tem in v_list:
                if not v_list_tem.location.file.name.endswith('.h'):
                    print(k_list)
                    print(v_list[0].displayname)
                    print(v_list[0].kind)
                    print(v_list[0].location)
                    cursor = v_list[0]
                    found = True
                    break
            if not found:
                print('_get_fun_con||无cpp中的方法')
                print(str_return_cond)
                return str_return_cond

        if debug:
            print('.line 1079 |||||||||||cursor.referenced|||', cursor.kind, cursor.displayname, cursor.location)
        children = []
        self.get_all_children_ref(cursor, children, level=0)
        print('.line 1082 len(children):', len(children))
        mode = None
        # 不能处理嵌套的
        # 例 bool recordingAllowed(const String16& opPackageName, pid_t pid, uid_t uid) {
        #     return checkRecordingInternal(opPackageName, pid, uid, /*start*/ false,
        #             /*is_hotword_source*/ false);
        #       }
        for child in children:
            node = child[1]
            print('.line 1199 |||||||||||', node.kind, node.displayname, node.location)
            if node.kind == CursorKind.SWITCH_STMT:
                mode = 'switch'
                break
            if 'checkCallingPermission' in node.displayname or 'checkPermission' in node.displayname:
                mode = 'permission'
                break

        if mode == 'switch':
            for child in children:
                node = child[1]
                if debug:
                    print('.line 1096 |||||||||||', node.kind, node.displayname, node.location)

                if node.kind == CursorKind.SWITCH_STMT:
                    var, conds = self._analyze_switch(node)
                    for key in conds.keys():
                        if conds[key] == 'true':
                            return_cond.append(key)

            str_return_cond = ''
            for tem in return_cond:
                str_return_cond = str_return_cond + var + ' == ' + tem + ' || '
            str_return_cond = str_return_cond[:-4]
        elif mode == 'permission':
            for child in children:
                node = child[1]
                if debug:
                    print('.line 1112|||||||permission||||', node.kind, node.displayname)
                if (
                        'checkCallingPermission' in node.displayname or 'checkPermission' in node.displayname) and node.kind == CursorKind.CALL_EXPR:
                    str_return_cond = self.getPermission(node)

        if debug:
            print('.line 1117 ', str_return_cond)
        # if 'settingsAllowed' in cursor.displayname:
        #     exit(2)
        # if 'recordingAllowed' in cursor.displayname:
        #     exit(0)
        return str_return_cond

    def _get_fun_in_condition(self, cursor, num=1, debug=False):
        '''
        返回所有的方法
        :param cursor:
        :param num:
        :param debug:
        :return:
        '''
        children = []
        self.get_all_children(cursor, children, level=0)
        funs = []
        for child in children:
            level = child[0]
            node = child[1]
            if debug:
                print('|', level, ' ' * level, node.kind, node.displayname)
            if node.kind == CursorKind.CALL_EXPR:
                method = node.referenced
                # fun_str = self.fully_qualified_pretty(method)
                # funs.append(fun_str)
                funs.append(node)
                if debug:
                    print('&&& 添加了一个node', node.kind, node.displayname, node.location)
                    print('&&& node.referenced', method.kind, method.displayname, method.location)
                    children = []
                    self.get_all_children(method, children, level=0)
                    print('len(children)', len(children))
                    # if 'operator' not in node.displayname:
                    #     exit(2)
                if len(funs) >= num:
                    return funs
        return funs
        # raise ValueError('len(funs) < num | num:', num)

    def _if_contains_elif(self, cursor, debug=False):
        if cursor is None:
            return False
        children = []
        self.get_all_children(cursor, children, level=0)
        for child in children:
            level = child[0]
            node = child[1]
            if node.kind == CursorKind.IF_STMT:
                return True
        return False

    def _is_secure_condition(self, cursor, debug=False):
        if cursor is None:
            return False
        children = []
        self.get_all_children(cursor, children, level=0)
        for child in children:
            level = child[0]
            node = child[1]
            # if node.kind == CursorKind.IF_STMT:
            #     return False
            if debug:
                print('|', level, ' ' * level, node.kind, node.displayname)
            if 'PERMISSION_DENIED' in node.displayname:
                return True
            if 'checkPermission' in node.displayname:
                return True
        return False

    def _get_unaryop_operator(self, cursor, debug=True):
        """
        https://github.com/coala/coala-bears/blob/master/bears/c_languages/codeclone_detection/ClangCountingConditions.py
        Returns the operator token of a binary operator cursor.
        :param cursor: A cursor of kind BINARY_OPERATOR.
        :return:       The token object containing the actual operator or None.
        """
        for tem in cursor.get_tokens():
            if debug:
                print('|', tem.kind, tem.spelling, end=' ')

        children = list(cursor.get_children())
        operator_min_begin = (children[0].location.line,
                              children[0].location.column)

        left = children[0].displayname
        if children[0].kind == CursorKind.CALL_EXPR:
            left = left + ' ( )'

        for token in cursor.get_tokens():
            if operator_min_begin > (token.extent.start.line,
                                     token.extent.start.column):
                return left, token.spelling

        return None, None  # pragma: no cover

    # def dump_children(node):
    #     for c in node.get_children():
    #         print(c.kind, c.type.spelling)
    #         dump_children(c)

    def parse_literal(self, cursor):
        value = ''.join([str(t.spelling) for t in cursor.get_tokens()])
        if cursor.kind == CursorKind.STRING_LITERAL:
            value = "'" + value[1:-1] + "'"  # prefer single quotes
            # value = 'b' + value  # Ensure byte string for compatibility
        return value

    def parse_assign(self, node, var, prt, pos=None, level=0):
        if level == 0:
            child = list(node.get_children())
            self.parse_assign(child[0], var, prt, pos='left', level=level+1)
            self.parse_assign(child[1], var, prt, pos='right', level=level+1)
        elif node.kind == CursorKind.CXX_THIS_EXPR:
            node._spelling = 'this'
            print(CursorKind.CXX_THIS_EXPR, node._spelling)
            if pos == 'left':
                prt['left'].append(node)
                print('\n### %s | %s %s %s' % (var, node.kind, node.spelling, '='), end='')
            elif pos == 'right':
                prt['right'].append(node)
                print('\n### %s | %s %s %s' % (var, '=', node.kind, node.spelling), end='')
        elif node.kind == CursorKind.CXX_UNARY_EXPR:
            tokens = ''.join([t.spelling for t in node.get_tokens()])
            node._spelling = tokens
            print(CursorKind.CXX_UNARY_EXPR, tokens)
            if pos == 'left':
                prt['left'].append(node)
                print('\n### %s | %s %s %s' % (var, node.kind, node.spelling, '='), end='')
            elif pos == 'right':
                prt['right'].append(node)
                print('\n### %s | %s %s %s' % (var, '=', node.kind, node.spelling), end='')
        elif node.kind == CursorKind.INTEGER_LITERAL:
            int_val = self.parse_literal(node)
            node._spelling = int_val
            print(CursorKind.INTEGER_LITERAL, int_val)
            if pos == 'left':
                prt['left'].append(node)
                print('\n### %s | %s %s %s' % (var, node.kind, node.spelling, '='), end='')
            elif pos == 'right':
                prt['right'].append(node)
                print('\n### %s | %s %s %s' % (var, '=', node.kind, node.spelling), end='')
        elif node.kind == CursorKind.CXX_BOOL_LITERAL_EXPR:
            bool_val = str(next(node.get_tokens()).spelling)
            node._spelling = bool_val
            print(CursorKind.CXX_BOOL_LITERAL_EXPR, bool_val)
            if pos == 'left':
                prt['left'].append(node)
                print('\n### %s | %s %s %s' % (var, node.kind, node.spelling, '='), end='')
            elif pos == 'right':
                prt['right'].append(node)
                print('\n### %s | %s %s %s' % (var, '=', node.kind, node.spelling), end='')
        elif node.kind == CursorKind.FLOATING_LITERAL:
            val = str(next(node.get_tokens()).spelling)
            node._spelling = val
            print(CursorKind.FLOATING_LITERAL, val)
            if pos == 'left':
                prt['left'].append(node)
                print('\n### %s | %s %s %s' % (var, node.kind, node.spelling, '='), end='')
            elif pos == 'right':
                prt['right'].append(node)
                print('\n### %s | %s %s %s' % (var, '=', node.kind, node.spelling), end='')
        elif node.kind == CursorKind.GNU_NULL_EXPR:
            node._spelling = 'NULL'
            if pos == 'left':
                prt['left'].append(node)
                print('\n### %s | %s %s %s' % (var, node.kind, node.spelling, '='), end='')
            elif pos == 'right':
                prt['right'].append(node)
                print('\n### %s | %s %s %s' % (var, '=', node.kind, node.spelling), end='')
        elif node.kind == CursorKind.CXX_NULL_PTR_LITERAL_EXPR:
            node._spelling = 'nullptr'
            if pos == 'left':
                prt['left'].append(node)
                print('\n### %s | %s %s %s' % (var, node.kind, node.spelling, '='), end='')
            elif pos == 'right':
                prt['right'].append(node)
                print('\n### %s | %s %s %s' % (var, '=', node.kind, node.spelling), end='')
        elif node.kind == CursorKind.STRING_LITERAL:
            if pos == 'left':
                prt['left'].append(node)
                print('\n### %s | %s %s %s' % (var, node.kind, node.spelling, '='), end='')
            elif pos == 'right':
                prt['right'].append(node)
                print('\n### %s | %s %s %s' % (var, '=', node.kind, node.spelling), end='')
        elif node.kind == CursorKind.MEMBER_REF_EXPR:
            child = list(node.get_children())
            if len(child) == 0:
                # like 'name = ' => node
                if pos == 'left':
                    prt['left'].append(node)
                    print('\n### %s | %s %s' % (var, node.spelling, '='), end='')
                elif pos == 'right':
                    prt['right'].append(node)
                    print('\n### %s | %s %s' % (var, '=', node.spelling), end='')
            else:
                # like 'student.name = ' => node.child[0]
                if child[0].kind == CursorKind.DECL_REF_EXPR:
                    if pos == 'left':
                        prt['left'].append([child[0], node])
                        print('\n### %s | %s %s' % (var, [child[0].spelling, node.spelling], '='), end='')
                    elif pos =='right':
                        prt['right'].append([child[0], node])
                        print('\n### %s | %s %s' % (var, '=', [child[0].spelling, node.spelling]), end='')

            '''
            1358| 4      CursorKind.CALL_EXPR GetMethodID                                               frameworks/base/core/jni/android_hardware_Camera.cpp', line 1196, column 32>
            ### found used memberVar: GetMethodID
            1358| 5       CursorKind.MEMBER_REF_EXPR GetMethodID             0                           frameworks/base/core/jni/android_hardware_Camera.cpp', line 1196, column 37>
            1358| 6        CursorKind.UNEXPOSED_EXPR env                                                frameworks/base/core/jni/android_hardware_Camera.cpp', line 1196, column 32>
            1358| 7         CursorKind.DECL_REF_EXPR env                                                frameworks/base/core/jni/android_hardware_Camera.cpp', line 1196, column 32>
            1358| 5       CursorKind.UNEXPOSED_EXPR clazz                    1                           frameworks/base/core/jni/android_hardware_Camera.cpp', line 1196, column 49>
            1358| 6        CursorKind.DECL_REF_EXPR clazz                                               frameworks/base/core/jni/android_hardware_Camera.cpp', line 1196, column 49>
            1358| 5       CursorKind.UNEXPOSED_EXPR                          2                           frameworks/base/core/jni/android_hardware_Camera.cpp', line 1196, column 56>
            1358| 6        CursorKind.STRING_LITERAL "<init>"                                           frameworks/base/core/jni/android_hardware_Camera.cpp', line 1196, column 56>
            1358| 5       CursorKind.UNEXPOSED_EXPR                          3                           frameworks/base/core/jni/android_hardware_Camera.cpp', line 1196, column 66>
            1358| 6        CursorKind.STRING_LITERAL "()V"  
            fields.point_constructor = env->GetMethodID(clazz, "<init>", "()V");
            '''

        elif node.kind == CursorKind.DECL_REF_EXPR:
            if pos == 'left':
                prt['left'].append(node)
                print('\n### %s | %s %s' % (var, node.spelling, '='), end='')
            elif pos == 'right':
                prt['right'].append(node)
                print('\n### %s | %s %s' % (var, '=', node.spelling), end='')

        if node.kind == CursorKind.CALL_EXPR:
            children = list(node.get_children())

            if pos == 'left':
                prt['left'].append(node)
                print('\n### %s | %s %s' % (var, node.spelling, '='), end='')
            elif pos == 'right':
                prt['right'].append(node)
                print('\n### %s | %s %s' % (var, '=', node.spelling), end='')

            # fun
            if len(children) > 0: # make sure fun has pars
                if children[0].kind == CursorKind.MEMBER_REF_EXPR and children[0].spelling == node.spelling:
                    children2 = list(children[0].get_children())

                    if len(children2)>0 and children2[0].kind == CursorKind.UNEXPOSED_EXPR:
                        # mFaceClass = (jclass) env->NewGlobalRef(faceClazz);
                        #                      child2[0]  node
                        child2 = list(children2[0].get_children())
                        if child2[0].kind == CursorKind.DECL_REF_EXPR:
                            if pos == 'left':
                                prt['left'].append([child2[0], node])
                                print('\n### %s | %s %s' % (var, [child2[0].spelling, node.spelling], '='), end='')
                            elif pos == 'right':
                                prt['right'].append([child2[0], node])
                                print('\n### %s | %s %s' % (var, '=', [child2[0].spelling, node.spelling]), end='')
                    else:
                        if pos == 'left':
                            prt['left'].append(node)
                            print('\n### %s | %s %s %s' % (var, node.kind, node.spelling, '='), end='')
                        elif pos == 'right':
                            prt['right'].append(node)
                            print('\n### %s | %s %s %s' % (var, '=', node.kind, node.spelling), end='')
                # par
                for child in children[1:]:
                    self.parse_assign(child, var, prt, pos=pos, level=level+1)
        else:
            for child in node.get_children():
                self.parse_assign(child, var, prt, pos=pos, level=level+1)


    def add_self_assign(self, node_str):
        # self.assign[node_str] = {'left': [], 'right': [], 'field': []}
        self.assign[node_str] = []
        return node_str

    def add_self_var(self, node_str):
        # self.assign[node_str] = {'left': [], 'right': [], 'field': []}
        self.var[node_str] = []
        return node_str

    def show_children(self, node, depth=0):
        print('show_children|%2d' % depth, ' ' * depth, node.kind, (node.spelling or node.displayname),
              ' ' * (120 - depth - len(str(node.kind)) - len(str(node.spelling))), '-',
              str(node.location).replace('<SourceLocation file \'/hci/chaoran_data/android-12.0.0_r31/', ''))
        for tem in node.get_children():
            self.show_children(tem, depth=depth+1)

    def parse_fun(self, node, var, fun, level=0, type=None):
        if level == 0:
            # self.show_children(node)
            # exit(0)

            child = list(node.get_children())
            if child[0].kind == CursorKind.UNEXPOSED_EXPR:
                # env->NewGlobalRef(faceClazz);
                # child2[0]  node
                child2 = list(child[0].get_children())
                if child2[0].kind == CursorKind.DECL_REF_EXPR:
                    # self.var[var]['left'].append([child3[0], node])
                    print('\n%s | FUN = %s' % (var, child2[0].spelling), end='')
                    fun['fun'] = [child2[0]]

            elif child[0].kind == CursorKind.MEMBER_REF_EXPR and child[0].spelling == node.spelling:
                child2 = list(child[0].get_children())

                if len(child2) > 0 and child2[0].kind == CursorKind.UNEXPOSED_EXPR:
                    # env->NewGlobalRef(faceClazz);
                    # child2[0]  node
                    child3 = list(child2[0].get_children())
                    if child3[0].kind == CursorKind.DECL_REF_EXPR or child3[0].kind == CursorKind.MEMBER_REF_EXPR:
                        # self.var[var]['left'].append([child3[0], node])
                        print('\n%s | FUN = %s' % (var, [child3[0].spelling, node.spelling]), end='')
                        fun['fun'] = [child3[0], node]
                    elif child3[0].kind == CursorKind.CALL_EXPR or child3[0].kind == CursorKind.UNEXPOSED_EXPR:
                        child4 = list(child3[0].get_children())
                        if child4[0].kind == CursorKind.DECL_REF_EXPR or child4[0].kind == CursorKind.MEMBER_REF_EXPR:
                            print('\n%s | FUN = %s' % (var, [child4[0].spelling, node.spelling]), end='')
                            fun['fun'] = [child4[0], node]
                        #font->typeface()->GetFontExtent(&extent, minikinPaint, layout.getFakery(i));
                        else:
                            print('got something like:       #font->typeface()->GetFontExtent(&extent, minikinPaint, layout.getFakery(i));')
                            print('ignore it to miake it simple:')
                            print('\n%s | FUN = %s' % (var, [child4[0].spelling, node.spelling]), end='')
                            fun['fun'] = [child4[0], node]

                else:
                    print('\n%s | FUN = %s %s' % (var, node.kind, node.spelling), end='')
                    fun['fun'] = [node]
            #par
            for tem in child[1:]:
                self.parse_fun(tem, var, level=level + 1, fun=fun)
        else:
            children = list(node.get_children())
            if len(children) == 0:
                fun['input'].append(node)
                print('\n%s | INPUT = %s' % (var, (node.spelling or node.kind)), end='')
            else:
                for tem in children:
                    self.parse_fun(tem, var, level=level + 1, fun=fun)

    def get_var_s_string(self, n):
        if n.kind == CursorKind.STRING_LITERAL:
            return n.spelling
        else:
            for c in n.get_children():
                return self.get_var_s_string(c)

    def parse_JNImethod(self, node, name, level=0):
        if level == 0:
            for c in list(node.get_children()):
                self.parse_JNImethod(c, name, level=level+1)
        elif level == 1:
            cs = list(node.get_children())
            java_fun = cs[0].spelling
            java_sig = None
            print('\n1602 |', cs[1].kind, cs[1].spelling, cs[1].location)
            if cs[1].kind == CursorKind.DECL_REF_EXPR:
                ref = cs[1].referenced
                print('\n1605 |', ref.kind, ref.spelling, ref.location)
                java_sig = self.get_var_s_string(ref)
                print('java_sig', java_sig)
            else:
                java_sig = cs[1].spelling
            cpp_fun = list(list(cs[2].get_children())[0].get_children())[0].spelling
            print('var_name: ' + name +' java_fun: ' + java_fun + ' java_sig: ' + java_sig + ' cpp_fun: ' + cpp_fun)
            self.var[name].append({'java_fun':java_fun,'java_sig': java_sig, 'cpp_fun': cpp_fun})


    def parse_RegisterNatives(self, node, type=None, index=1, level=0, parent= None):
        print('\n1587 *** | %2d' % level, ' ' * level, node.kind, (node.spelling or node.displayname), type,
              ' ' * (120 - level - len(str(node.kind)) - len(str(node.spelling))), '', '-',
              str(node.location).replace('<SourceLocation file \'/hci/chaoran_data/android-12.0.0_r31/', ''), end='')
        if level == 0:
            total = len(list(node.get_children()))
            print('\n1603 | num of par list:', total)
            index = total - 3
            class_n = list(node.get_children())[index:][0]
            self.parse_RegisterNatives(class_n, type='class', index=index, level=level+1, parent=node)
            method_var_n = list(node.get_children())[index:][1]
            self.parse_RegisterNatives(method_var_n, type='method_var', index=index, level=level + 1, parent=node)
        else:
            if node.kind == CursorKind.STRING_LITERAL:
                # 在list中
                if parent.kind == CursorKind.INIT_LIST_EXPR:
                    self.jni_methods.append({})
                    self.jni_methods[-1]['type'] = 'list'
                    self.jni_methods[-1]['class'] = node.spelling
                    print('\nself.jni_methods[\'class\']', node.spelling)
                    pass
                elif re.match(r'"[0-9a-zA-Z_]+(/[0-9a-zA-Z$_]+)+"', node.spelling) and parent.kind != CursorKind.INIT_LIST_EXPR:
                    self.jni_methods.append({})
                    self.jni_methods[-1]['class'] = node.spelling
                    print('\nself.jni_methods[\'class\']', node.spelling)
                    pass
                else:
                    print('\n', node.spelling, '\'miss match, not assign\'')
            # 是列    没var
            if 'type' in self.jni_methods[-1].keys() and 'method_var' not in self.jni_methods[-1].keys(): # no method var
                if node.kind == CursorKind.DECL_REF_EXPR:
                    print('\nself.jni_methods[\'method_var\']', node.spelling)
                    self.jni_methods[-1]['method_var'] = node.spelling
            # 找到类    没var
            elif 'class' in self.jni_methods[-1].keys() and 'method_var' not in self.jni_methods[-1].keys(): # no method var
                if node.referenced is not None and node.referenced.kind == CursorKind.FIELD_DECL:
                    # 不一定是要的那个parent node
                    parent = node.referenced.semantic_parent
                    print('\n1636 |', parent.kind, parent.spelling, parent.location)
                    # if parent.kind == CursorKind.STRUCT_DECL:
                    #     raise Exception('found CursorKind.STRUCT_DECL')
                    # parent node 是 structure ，则找structure的变量
                    for k in self.structure_var.keys():
                        if parent.spelling in k:
                            for c in self.structure_var[k].get_children():
                                self.parse_RegisterNatives(c, type=self.jni_methods[-1]['class'], index=index,
                                                           level=level + 1,
                                                           parent=self.structure_var[k])
                elif node.kind == CursorKind.DECL_REF_EXPR:
                    if node.spelling in self.var.keys():
                        print('\nself.jni_methods[\'method_var\']', node.spelling)
                        self.jni_methods[-1]['method_var'] = node.spelling
            # 没找到类 继续找类
            elif type == 'class' and 'class' not in self.jni_methods[-1].keys() and node.kind == CursorKind.DECL_REF_EXPR:
                node = node.referenced
                print('\n1650 |', node.kind, node.spelling, node.location)

            #     #
            #     # # java class
            #     # self.jni_methods.append({})
            #     # print('\nself.jni_methods[\'class\']', node.spelling)
            #     # if re.match(r'"[0-9a-zA-Z_]+(/[0-9a-zA-Z$_]+)+"', node.spelling) and parent.kind==CursorKind.INIT_LIST_EXPR:
            #     #     self.jni_methods[-1]['type'] = 'list'
            #     #     self.jni_methods[-1]['class'] = node.spelling
            #     # elif type != 'class' and type != 'method_var' and re.match(r'"[0-9a-zA-Z_]+(/[0-9a-zA-Z$_]+)*"', node.spelling):
            #     #     self.jni_methods[-1]['class'] = type.strip('"')+'$'+node.spelling.strip('"')
            #     # elif re.match(r'"[0-9a-zA-Z_]+(/[0-9a-zA-Z$_]+)"', node.spelling):
            #     #         self.jni_methods[-1]['class'] = node.spelling
            #     # else:
            #     #     print('miss match, not assign')
            # # do not have class
            # elif (node.kind == CursorKind.DECL_REF_EXPR) and 'class' not in self.jni_methods[-1].keys():
            #     print(node.referenced.kind)
            #     print(node.referenced.spelling)
            #     print(node.referenced.location)
            #     node = node.referenced
            #     pass
            # # has class no method_var
            # # or node.kind == CursorKind.MEMBER_REF_EXPR
            # elif (node.kind == CursorKind.DECL_REF_EXPR or node.kind == CursorKind.MEMBER_REF_EXPR) and 'class' in self.jni_methods[-1].keys() \
            #         and 'method_var' not in self.jni_methods[-1].keys() and type!='class':
            #     # jni methods
            #     print('\n1619')
            #     print(node)
            #     aa = node.referenced
            #     print(aa.kind)
            #     print(aa.spelling)
            #     print(aa.location)
            #     if aa.kind == CursorKind.FIELD_DECL:
            #         aa = aa.semantic_parent
            #         # if aa.kind ==CursorKind.STRUCT_DECL:
            #         #     aa = aa.semantic_parent
            #         print(aa.kind, aa.spelling, aa.location)
            #         for k in self.structure_var.keys():
            #             if aa.spelling in k:
            #                 print('\n1633', self.structure_var[k].kind, self.structure_var[k].spelling, self.structure_var[k].location)
            #                 for c in self.structure_var[k].get_children():
            #                     self.parse_RegisterNatives(c, type=self.jni_methods[-1]['class'], index=index, level=level + 1, parent=self.structure_var[k])
            #     else:
            #         print('\nself.jni_methods[\'method_var\']', node.spelling)
            #         self.jni_methods[-1]['method_var'] = node.spelling
            # elif (node.kind == CursorKind.DECL_REF_EXPR or node.kind == CursorKind.MEMBER_REF_EXPR) and 'type' in self.jni_methods[-1].keys():
            #     print('\nself.jni_methods[\'method_var\']', node.spelling)
            #     self.jni_methods[-1]['method_var'] = node.spelling

            for c in node.get_children():
                self.parse_RegisterNatives(c, type=type, index=index, level=level+1, parent=node)


    def show_single_assign(self, assign):
        print()
        str = ''
        for tem in assign['left']:
            if isinstance(tem, list):
                for i, temm in enumerate(tem):
                    if i!=len(tem)-1:
                        print((temm.spelling or temm.kind), end='. ')
                    else:
                        print((temm.spelling or temm.kind), end=' ')
            else:
                print((tem.spelling or tem.kind), end=' ')
        print('=', end=' ')
        for tem in assign['right']:
            if isinstance(tem, list):
                for i, temm in enumerate(tem):
                    if i != len(tem) - 1:
                        print((temm.spelling or temm.kind), end='. ')
                    else:
                        print((temm.spelling or temm.kind), end=' ')
            else:
                print((tem.spelling or tem.kind), end=' ')
        print()


    def show_info(self, node, cur_fun=None, depth=0, print_node=False, if_stmt=None, last_node=None, case_identifier=[],
                  case_mode=[False], case_level=[10e10], var='root'):
        print_node = True

        # debug 显示制定node
        if node.location.file and (self.print_all_node or print_node) and self.pro_path + 'frameworks' in node.location.file.name:
            # print('\n1358|%2d' % depth + ' ' * depth, node.kind, node.spelling, '|current case_identifier:',
            #       case_identifier, end='')
            print('\n1358|%2d' % depth, ' ' * depth, node.kind, (node.spelling or node.displayname), ' ' * (120-depth-len(str(node.kind))-len(str(node.spelling))-len(var)), var, '-', str(node.location).replace('<SourceLocation file \'/hci/chaoran_data/android-12.0.0_r31/',''), end='')

            # if('GetDrm' in node.displayname and str(node.kind)=='CursorKind.CALL_EXPR'):
            #     if node.referenced is not None:
            #         node = node.referenced
            #         return_class = self.get_return(node)
            #         print(return_class[0], return_class[1])
            #         if return_class[0] == CursorKind.MEMBER_REF_EXPR:
            #             self.find_var(return_class[1])
            #         exit(2)
            # # type = node.type
            # # print('|type:', type.kind, end='')
            # # # if node.kind.is_reference():
            # # #     ref_node = node.get_definition()
            # # #     print(ref_node.spelling)
            # # if node.kind == CursorKind.CALL_EXPR:
            # #     o=0
            # # elif node.kind == CursorKind.INTEGER_LITERAL:
            # #     value = node.get_tokens()
            # #     for v in value:
            # #         print('', v.spelling, end='')
            # #     # value = value.__next__().spelling
            # #     # print('',value, end='')
            # # elif type.kind == TypeKind.RECORD:
            # #     value = type.spelling
            # #     print('', value, end='')
            # # # and type.kind == TypeKind.DEPENDENT
            # # elif (node.kind == CursorKind.DECL_REF_EXPR ):
            # #     ooo = node.get_tokens()
            # #     for tem in ooo:
            # #         print('|', tem.kind, tem.spelling, end=' ')
            # #     # iii = type.get_pointee()
            # #     # print(iii)
            # #     o=0
            # # elif (node.kind == CursorKind.TYPE_REF and type.kind == TypeKind.UNEXPOSED):
            # #     print(type.spelling, end='')
            # #     # print(type.get_align())
            # #     o=0
            # # # print(node.type.get_typedef_name())
            # # # if node.kind == CursorKind.TYPE_REF:
            # # #     num = node.get_num_template_arguments()
            # # #     print(num)
            # #     # print(self.fully_qualified_pretty(node))
            # print()

            # assign spelling if BINARY_OPERATOR
        if node.kind == CursorKind.BINARY_OPERATOR:
            operator = self._get_binop_operator(node)
            node._spelling = operator

            if operator == '=' or operator == 'operator=':
                self.assign[var].append({"left": [], "right": []})
                self.parse_assign(node, var, self.assign[var][-1])
                print()
                self.show_single_assign(self.assign[var][-1])

        if node.kind == CursorKind.CLASS_DECL:
            # class
            node_str = (node.spelling or node.displayname)
            print('\n--------', 'class:', node_str, end='')
            var = self.add_self_assign(node_str)
            var = self.add_self_var(node_str)
            pass

        if node.kind == CursorKind.FIELD_DECL:
            # class member var
            node_str = (node.spelling or node.displayname)
            print('\n***', 'memberVar:', node_str, var, end='')
            self.var[var].append(node)
            pass

            # if node.kind == CursorKind.MEMBER_REF_EXPR:
            #     # use member var/fun
            #     node_str = (node.spelling or node.displayname)
            #     if node_str in self.var['root']:
            #         print('\n###', 'found used memberVar:', node_str, end='')
            #     pass

        if node.kind == CursorKind.VAR_DECL:
            children = list(node.get_children())
            if len(children)>0 and children[0].kind == CursorKind.TYPE_REF and children[0].spelling == 'JNINativeMethod':
                self.var[node.spelling] = []
                print()
                self.parse_JNImethod(children[1], node.spelling)
            elif len(children)>0:
                print('\n1859 self.structure_var', node.spelling, node.location)
                print('\n1859 self.structure_var', children[0].spelling, children[0].spelling != '')
                if children[0].spelling != '':
                    self.structure_var[children[0].spelling] = node
                else:
                    self.structure_var[node.spelling] = node
            # elif len(children)>0 and children[0].kind == CursorKind.TYPE_REF:
            #     children2 = list(children[0].get_children())
            #     if len(children2)>0 and children2[0].kind == CursorKind.INIT_LIST_EXPR:
            #         children3 = list(children2[0].get_children())
            #         if len(children3)>0 and children3[0].kind == CursorKind.INIT_LIST_EXPR:
            #             children4 = list(children3[0].get_children())
            #             if len(children4) == 3:
            #                 self.var[node.spelling] = []
            #                 print()
            #                 self.parse_JNImethod(children[1], node.spelling)

        if node.kind == CursorKind.IF_STMT:
            if_stmt = node



        if node.kind == CursorKind.CALL_EXPR:
            print('\n', node.spelling)
            print('RegisterMethods' in node.spelling)
            if node.spelling.startswith('Set'):
                fun = {'fun': None, 'input': [], 'pos': 'left'}
                self.parse_fun(node, var, fun=fun, type='Set')
                if fun['fun'] is None:
                    print('\n1722 | fun[\'fun\'] is None')
                    # raise Exception('\n1722 | fun[\'fun\'] is None')
                self.assign[var].append(fun)
            elif node.spelling.startswith('Get'):
                fun = {'fun': None, 'input': [], 'pos': 'right'}
                self.parse_fun(node, var, fun=fun, type='Get')
                if fun['fun'] is None:
                    print('\n1722 | fun[\'fun\'] is None')
                    # raise Exception('\n1722 | fun[\'fun\'] is None')
                self.assign[var].append(fun)

            # 2nd par
            # jniRegisterNativeMethods
            elif ('Register' in node.spelling or 'register' in node.spelling) and 'Methods' in node.spelling:
                # avoid registerNativeMethods(env)
                if len(list(node.get_children())) > 2:
                    print('\n1709 |')
                    old_len = len(self.jni_methods)
                    self.jni_methods.append({})
                    print('\nself.parse_RegisterNatives(node, 1)')
                    self.parse_RegisterNatives(node, 1)
                    delete_k = []
                    for i, v in enumerate(self.jni_methods):
                        if 'method_var' not in v.keys() or 'class' not in v.keys():
                            delete_k.append(v)
                    for v in delete_k:
                        self.jni_methods.remove(v)
                    print('\nself.jni_methods', self.jni_methods)
                    print(len(self.jni_methods), old_len)
                    if len(self.jni_methods) - old_len == 0:
                        raise Exception('len(self.jni_methods) - old_len = 0')
            # 1st par
            # RegisterNatives
            elif 'Register' in node.spelling and 'Natives' in node.spelling:
                # avoid registerNativeMethods(env)
                if len(list(node.get_children())) > 2:
                    print('\n1709 |')
                    self.jni_methods.append({})
                    print('\nself.parse_RegisterNatives(node, 0)')
                    self.parse_RegisterNatives(node, 0)
                    delete_k = []
                    for i, v in enumerate(self.jni_methods):
                        if 'method_var' not in v.keys() or 'class' not in v.keys():
                            delete_k.append(v)
                    for v in delete_k:
                        self.jni_methods.remove(v)
                    print('\nself.jni_methods', self.jni_methods)
                    if len(self.jni_methods) == 0:
                        Exception(self.jni_methods)

        if node.kind == CursorKind.CXX_METHOD or node.kind == CursorKind.FUNCTION_DECL:
            cur_fun = node
            fun_str = self.fully_qualified_pretty(cur_fun)
            var = self.add_self_assign(fun_str)
            var = self.add_self_var(fun_str)
            # 没有或者location在cpp中
            if cur_fun.location.file.name.endswith('.cpp'):
                self.fist_lvl_funs.append(fun_str)

        # path start
        if node.kind == CursorKind.FUNCTION_TEMPLATE or node.kind == CursorKind.CONSTRUCTOR:
            # if not is_excluded(node, xfiles, xprefs):
            cur_fun = node
            fun_str = self.fully_qualified_pretty(cur_fun)
            var = self.add_self_assign(fun_str)
            var = self.add_self_var(fun_str)
            # 没有或者location在cpp中
            if fun_str not in self.FULLNAMES.keys() or cur_fun.location.file.name.endswith('.cpp'):
                # ::RadioService::attach
                # ::MediaRecorderClient::MediaRecorderClient(
                # if '::RadioService::attach(' in fun_str:
                #     print('添加', fun_str, cur_fun.location.file.name)
                self.FULLNAMES[fun_str] = cur_fun
            # if self.print_all_node and self.pro_path in cur_fun.location.file.name:
            #     print('%2d' % depth + ' ' * depth, '|||' + fun_str)

        if node.kind == CursorKind.CXX_METHOD or node.kind == CursorKind.FUNCTION_DECL:
            cur_fun = node
            fun_str = self.fully_qualified_pretty(cur_fun)
            var = self.add_self_assign(fun_str)
            var = self.add_self_var(fun_str)
            if fun_str not in self.FULLNAMES.keys() or cur_fun.location.file.name.endswith('.cpp'):
                self.FULLNAMES[fun_str] = cur_fun

        # 在某函数中发现了调用，那么把这个函数->调用函数的mapping，加入call graph
        if node.kind == CursorKind.CALL_EXPR:
            if node.referenced:
                fun_str = self.fully_qualified_pretty(cur_fun)
                if cur_fun is not None and self.pro_path in cur_fun.location.file.name:
                    # self.CALLGRAPH[fun_str].append(node.referenced)
                    # 在一个函数(fun_str)中找到了函数调用(node)，加入call graph
                    self.CALLGRAPH[fun_str].append(node)
                    # 打印的是起点/父节点
                    # if self.print_all_node:
                    #     print('%2d' % depth + ' ' * depth, '|||' + self.fully_qualified_pretty(cur_fun))



        # case 加进 call graph
        if node.kind == CursorKind.CASE_STMT and depth <= case_level[0]:
            case_identifier = []
            case_mode[0] = True
            case_level[0] = depth
            # print('\ncase_mode:', case_mode[0])
            # print('case_level:', case_level[0])
        elif case_mode[0] and depth <= case_level[0]:
            case_mode[0] = False
            case_level[0] = 10e10
            # print('\ncase_mode:', case_mode[0])
            # print('case_level:', case_level[0])
        elif case_mode[0] and depth > case_level[0] and node.kind == CursorKind.UNEXPOSED_EXPR:
            # case_mode[0] = False
            # case_level[0] = depth
            if node.spelling != '' and re.sub(r'[A-Z][A-Z_]+', "", node.spelling) == '':
                case_identifier.append(node.spelling)
                print('\n当前case_identifier:', case_identifier)
                # print('case_mode:', case_mode[0])
                # print('case_level:', case_level[0])
                # node._displayname = '==CONDITION==identifier*' + case_identifier[0] + '*'
                # node._spelling = node._displayname
                # fun_str = self.fully_qualified_pretty(node)
                # if self.pro_path in node.location.file.name:
                #     # self.CALLGRAPH[fun_str].append(node.referenced)
                #     # 在一个函数(fun_str)中找到了函数调用(node)，加入call graph
                #     self.CALLGRAPH[fun_str].append(node)

        # if 加进 call graph
        if node.kind == CursorKind.BINARY_OPERATOR and self._is_secure_condition(if_stmt):
            if self._contain_comparision_operator(node):
                # CursorKind.IF_STMT
                # print(self._is_secure_condition(if_stmt))
                # print(self._is_secure_condition(node))
                condition = self._return_condition(node)
                print('\n***', condition, '*** CursorKind.BINARY_OPERATOR')
                print(self._if_contains_elif(if_stmt))
                # ===== 改造node 作为条件分支存在 =======
                confition_funs = self._get_fun_in_condition(node, self._get_num_comparision_operator(node))
                # confition_funs_str = ''
                # for confition_fun in confition_funs:
                #     confition_funs_str = confition_funs_str + confition_fun + '|'
                # confition_funs_str = confition_funs_str[:-1]
                if self._if_contains_elif(if_stmt):
                    # if confition_funs_str!='':
                    #     node._displayname = '==CONDITION==|[' + confition_funs_str + ']|!(' + condition + ') &&'
                    # else:
                    node._if_contain_functions = confition_funs
                    print('\n添加case_identifier:', case_identifier)
                    if len(case_identifier) == 0:
                        node._displayname = '==CONDITION==' + '' + '*!(' + condition + ') &&'
                    else:
                        node._displayname = '==CONDITION==' + str(case_identifier) + '*!(' + condition + ') &&'
                    print(node._displayname)
                    # exit(0)
                else:
                    # if confition_funs_str != '':
                    #     node._displayname = '==CONDITION==|[' + confition_funs_str + ']|' + condition
                    # else:
                    node._if_contain_functions = confition_funs
                    print('\n添加case_identifier:', case_identifier)
                    if len(case_identifier) == 0:
                        node._displayname = '==CONDITION==' + '' + '*' + condition
                    else:
                        node._displayname = '==CONDITION==' + str(case_identifier) + '*' + condition
                    print(node._displayname)
                    # exit(0)
                node._spelling = node._displayname
                node._referenced = node
                # node._kind_id = 8625
                # ============
                # comparisionop = self._get_binop_comparision_operator(node)
                # if comparisionop: print('\n*** COMPARISION:', comparisionop, '***')

                # 添加条件在call sequence中
                fun_str = self.fully_qualified_pretty(cur_fun)
                if cur_fun is not None and self.pro_path in cur_fun.location.file.name:
                    # self.CALLGRAPH[fun_str].append(node.referenced)
                    # 在一个函数(fun_str)中找到了函数调用(node)，加入call graph
                    self.CALLGRAPH[fun_str].append(node)

                if_stmt = None


        elif node.kind == CursorKind.UNARY_OPERATOR and self._is_secure_condition(if_stmt):
            # print(self._is_secure_condition(if_stmt))
            # ooo = node.get_tokens()
            # for tem in ooo:
            #     print('/', tem.kind, tem.spelling, end=' ')

            # 获取函数中
            # 获取操作符
            left, binop = self._get_unaryop_operator(node)
            if left and binop:
                condition = binop + ' ' + left
                print('\n***', condition, '*** CursorKind.UNARY_OPERATOR')
                # ===== 改造node 作为条件分支存在 =======
                confition_funs = self._get_fun_in_condition(node)
                # confition_funs_str = ''
                # for confition_fun in confition_funs:
                #     confition_funs_str = confition_funs_str + confition_fun + '|'
                # confition_funs_str = confition_funs_str[:-1]
                # if confition_funs_str != '':
                #     node._displayname = '==CONDITION==|[' + confition_funs_str + ']|' + condition
                # else:
                node._if_contain_functions = confition_funs
                if len(case_identifier) == 0:
                    node._displayname = '==CONDITION==' + '' + '*' + condition
                else:
                    node._displayname = '==CONDITION==' + str(case_identifier) + '*' + condition
                node._spelling = node._displayname
                print(node._displayname)
                # exit(0)
                node._referenced = node
                # comparisionop = self._get_binop_comparision_operator(node)
                # if comparisionop: print('\n*** COMPARISION:', comparisionop, '***')
                fun_str = self.fully_qualified_pretty(cur_fun)
                if cur_fun is not None and self.pro_path in cur_fun.location.file.name:
                    # self.CALLGRAPH[fun_str].append(node.referenced)
                    # 在一个函数(fun_str)中找到了函数调用(node)，加入call graph
                    self.CALLGRAPH[fun_str].append(node)

            if_stmt = None
        # elif self._is_secure_condition(if_stmt):
        #     print('line 1403')
        #     exit(2)
        # ============== IF  END  TEST================

        for c in node.get_children():
            self.show_info(c, cur_fun, var=var, depth=depth + 1, print_node=print_node, if_stmt=if_stmt, last_node=node,
                           case_identifier=case_identifier, case_mode=case_mode, case_level=case_level)

    def pretty_print(self, n):
        v = ''
        if self.show_loc:
            return self.fully_qualified_pretty(n) + v + "|" + str(n.location)
        else:
            return self.fully_qualified_pretty(n) + v

    def search_fun(self, fun_name):
        return self.search_fun_list_full(fun_name)

    def search_fun_list_full(self, fun_name):
        fun_name = fun_name.replace('const ', '')
        fun_name = fun_name.replace('struct ', '')
        fun_name = fun_name.replace('_t', '')
        fun_names = fun_name.split('(')
        fun_names[1] = re.sub('([a-zA-Z0-9]+?)([a-zA-Z0-9]+?::)+', '', fun_names[1])
        fun_name = fun_names[0] + '(' + fun_names[1]
        print('*** search for fun %s ***\n' % fun_name)
        full_fun_name = re.sub('\(.+?\)', r'', fun_name)
        print(full_fun_name)
        k_list = []
        v_list = []
        for k, v in self.FULLNAMES.items():
            k4match = k
            k4match = k4match.replace('const ', '')
            k4match = k4match.replace('struct ', '')
            k4match = k4match.replace('_t', '')
            k4matchs = k4match.split('(')
            k4matchs[1] = re.sub('([a-zA-Z0-9]+?)([a-zA-Z0-9]+?::)+', '', k4matchs[1])
            k4match = k4matchs[0] + '(' + k4matchs[1]
            if full_fun_name in k4match:
                print('Found similar fun -> \n' + k4match)
                print(v.location)
                print('判断方法对不对|', fun_name in k4match)
                print('判断方法对不对|', fun_name)
                print('判断方法对不对|', k4match)
            if fun_name in k4match:
                print('Found fun -> ' + k)
                print(v.location)
                k_list.append(k)
                v_list.append(v)
        # if len(k_list) == 0:
        #     print('.line 1564')
        #     exit(0)
        return k_list, v_list

    def search_fun_precise(self, fun_name):
        fun_name = fun_name.replace('const ', '')
        fun_name = fun_name.replace('struct ', '')
        fun_name = fun_name.replace('_t', '')
        fun_names = fun_name.split('(')
        fun_names[1] = re.sub('([a-zA-Z0-9]+?)([a-zA-Z0-9]+?::)+', '', fun_names[1])
        fun_name = fun_names[0] + '(' + fun_names[1]
        print('*** search for fun %s ***\n' % fun_name)
        full_fun_name = re.sub('\(.+?\)', r'', fun_name)
        print(full_fun_name)
        k_list = []
        v_list = []
        for k, v in self.FULLNAMES.items():
            k4match = k
            k4match = k4match.replace('const ', '')
            k4match = k4match.replace('struct ', '')
            k4match = k4match.replace('_t', '')
            k4matchs = k4match.split('(')
            k4matchs[1] = re.sub('([a-zA-Z0-9]+?)([a-zA-Z0-9]+?::)+', '', k4matchs[1])
            k4match = k4matchs[0] + '(' + k4matchs[1]
            if full_fun_name in k4match:
                print('Found similar fun -> \n' + k4match)
                print(v.location)
                print('精确判断方法对不对|', fun_name in k4match)
                print('精确判断方法对不对|', fun_name)
                print('精确判断方法对不对|', k4match)
            if fun_name in k4match:
                print('Found fun -> ' + k)
                print(v.location)
                k_list.append(k)
                v_list.append(v)
        # if len(k_list) == 0:
        #     print('.line 1564')
        #     exit(0)
        return k_list, v_list

    def search_fun_list(self, fun_name):
        list = []
        for k, v in self.FULLNAMES.items():
            if fun_name in k:
                print('Found fun -> ' + k)
                list.append(v)
        return list

    def getPermission(self, node):
        print(node.kind, node.spelling)
        if node is None:
            return None

        # get_tokens
        for tem in node.get_tokens():
            # print(tem.spelling)
            if 'permission.' in tem.spelling:
                return tem.spelling

        if self.pro_path in node.location.file.name:
            if node.kind == CursorKind.DECL_REF_EXPR:
                node = node.referenced

            if node is None:
                return None

            if node.kind == CursorKind.STRING_LITERAL:
                if 'permission.' in node.spelling:
                    # print(node.spelling)
                    return node.spelling

            for n in node.get_children():
                if n is not None:
                    print('.line 1564 子', node.kind, node.spelling)
                    return_str = self.getPermission(n)
                    if return_str:
                        return return_str
        return None

    def get_para(self, node):
        if node is None:
            return 'None'

        if self.pro_path in node.location.file.name:
            if node.kind == CursorKind.DECL_REF_EXPR:
                node = node.referenced

            if node is None:
                return 'None'

            if node.kind == CursorKind.STRING_LITERAL:
                if node.spelling != '""':
                    return node.spelling

            # if node.kind == CursorKind.INTEGER_LITERAL:
            #     value = node.get_tokens()
            #     for v in value:
            #         return v.spelling

            for n in node.get_children():
                return_str = self.get_para(n)
                if return_str is not None:
                    return return_str
        return 'None'

    def print_childrens(self, node, service_names, depth, DEBUG=False):
        if node is not None and node.location.file is not None and self.pro_path in node.location.file.name:
            for n in node.get_children():
                if DEBUG:
                    print('1664| %2d' % depth + ' ' * depth, n.kind, n.spelling, end=' | ')
                ooo = n.get_tokens()
                tokens_key = []
                tokens_val = []
                for tem in ooo:
                    tokens_key.append(tem.spelling)
                    tokens_val.append(tem)
                for token in tokens_key:
                    if DEBUG:
                        print(token, end='')

                if n.kind == CursorKind.DECL_REF_EXPR and 'getServiceName' in tokens_key:
                    key_name = ''
                    for tem in self.FULLNAMES.keys():
                        if 'getServiceName' in tem:
                            key_name = tem
                    tem_node = self.FULLNAMES[key_name]
                    service_name = self.get_para(tem_node)
                    # 这个binder的字符和cpp文件绑定即所需
                    if DEBUG:
                        print(" " + service_name, end='')
                    service_names.append([service_name, n.location.file.name])
                elif n.kind == CursorKind.DECL_REF_EXPR and 'getService' in tokens_key:
                    key_name = ''
                    for tem in self.FULLNAMES.keys():
                        if 'getService' in tem:
                            key_name = tem
                    tem_node = self.FULLNAMES[key_name]
                    service_name = self.get_para(tem_node)
                    # 这个binder的字符和cpp文件绑定即所需
                    if DEBUG:
                        print(" " + service_name, end='')
                    service_names.append([service_name, n.location.file.name])
                # elif n.kind == CursorKind.ENUM_CONSTANT_DECL:
                #     print('!!!!!!!!CursorKind.ENUM_CONSTANT_DECL', node.spelling)
                #     service_names.append([node.spelling, n.location.file.name])
                if DEBUG:
                    print()

                if n.kind == CursorKind.STRING_LITERAL:
                    service_name = n.spelling
                    service_names.append([n.spelling, n.location.file.name])

                if n.kind == CursorKind.DECL_REF_EXPR:
                    n = n.referenced
                    # print(n is not None)
                    if n is not None:
                        if DEBUG:
                            print('%2d' % depth + ' ' * depth, n.kind, n.spelling, end=' | ')
                        if n.kind == CursorKind.ENUM_CONSTANT_DECL:
                            if DEBUG:
                                print('!!!!!!!!CursorKind.ENUM_CONSTANT_DECL', node.spelling)
                            service_names.append([node.spelling, n.location.file.name])
                        ooo = n.get_tokens()
                        for tem in ooo:
                            if DEBUG:
                                print(tem.spelling, end=' ')

                        if DEBUG:
                            print()
                if n is not None:
                    self.print_childrens(n, service_names, depth=depth + 1)

    def get_print_ndoe(self, fun_name, so_far, graphs, depth=0):
        found = False
        for k, v in self.CALLGRAPH.items():
            for f in v:
                f = f.referenced
                # 找到了子节点
                if self.fully_qualified_pretty(f) == fun_name or self.fully_qualified(f) == fun_name:
                    if k in so_far:
                        continue
                    so_far.append(k)
                    # 返回父节点
                    found = True
                    self.get_print_ndoe(k, so_far, graphs, depth + 1)
        if found == False:
            graphs.append(so_far)

    def has_no_ignore_fun(self, str):
        # 列表都不存在 返回True
        # 存在一个返回False
        # 忽略系统底层的Binder相关类
        ignore_fun_list = ['Binder', 'IInterface', 'setListener', 'sp', 'IServiceManager', 'IPermissionController']
        for tem_ignore in ignore_fun_list:
            if tem_ignore + '::' in str:
                return False
        return True

    def has_ignore_fun_Ixx(self, str):
        # 列表都不存在 返回True
        # 存在一个返回False
        # 忽略系统底层的Ixxx系统相关类
        ignore_fun_list = ['IServiceManager', 'IMemory', 'asInterface']
        for tem_ignore in ignore_fun_list:
            if tem_ignore + '::' in str:
                return False
        ignore_fun_list2 = ['asInterface']
        for tem_ignore in ignore_fun_list2:
            if tem_ignore in str:
                return False
        return True

    def _replace_condition_fun(self, ori, replace):
        COMPARISION_OPERATORS = ['==', '<=', '>=', '<', '>', '!=', '&&', '||']
        tem = ori
        for temCOMPARISION_OPERATORS in COMPARISION_OPERATORS:
            tem = tem.replace(temCOMPARISION_OPERATORS, temCOMPARISION_OPERATORS + '@@')
        ori_tem = tem.split('@@')
        print('++++++++++')
        print('ori_tem', ori_tem)
        ori_tem_only_fun = []
        tem = ''
        for k, v in enumerate(ori_tem):
            tem = tem + v
            if '(' in v and ')' in v:
                ori_tem_only_fun.append(tem)
                tem = ''

        print(ori)
        print(ori_tem)
        print(len(replace))
        print(replace)
        print(len(ori_tem_only_fun))
        print(ori_tem_only_fun)

        return_str = ''
        assert len(replace) == len(ori_tem_only_fun), len(replace) + len(ori_tem_only_fun)
        for k, v in enumerate(replace):
            if v:
                print('第', k, '项， ', '要被替换为', v)
                print('替换前', ori_tem_only_fun[k])
                if 'strncmp' in ori_tem_only_fun[k]:
                    print('截获', ori_tem_only_fun[k])
                elif 'std::__1' not in v:
                    ori_tem_only_fun[k] = re.sub(r'[a-zA-Z0-9_]+ \(.+\)', '(' + v + ')', ori_tem_only_fun[k])
                print('替换后', ori_tem_only_fun[k])
            return_str = return_str + ori_tem_only_fun[k]
        print('最终采用的条件', return_str)
        print('======')
        # exit(2)
        return return_str

    def I_find_no_I(self, h):
        # 找没I的文件的头文件位置
        # 去掉完整目录中的I 找无I的cpp完整路径 在无I的cpp头找h路径
        temmm = re.findall(r'I[a-zA-Z]+?Service', h)
        h = h.replace(temmm[0], temmm[0][1:])
        f = os.path.basename(h).replace('.h', '.cpp')
        print('要找的cpp文件', f)
        h_no_I = ''
        for tem in self.file_tu.keys():
            if f in tem:
                print(tem)
                for temm in self.file_tu[tem].get_includes():
                    include_path = temm.include.name
                    print(include_path)
                    if '/' + f.replace('.cpp', '.h') in include_path:
                        h_no_I = include_path
        print(h_no_I)
        # exit(0)
        return h_no_I

    def extract_onTransact(self, node, identifier, conditions, depth=0, case_mode=False, case_level=10e10):
        if node is not None and node.location.file is not None and self.pro_path in node.location.file.name:
            for n in node.get_children():
                print('1818| %2d' % depth + ' ' * depth, n.kind, n.spelling, end=' | ')
                print()
                print(
                    'case_mode and depth > case_level and n.kind == CursorKind.DECL_REF_EXPR and n.spelling == identifier',
                    case_mode and depth > case_level and n.kind == CursorKind.DECL_REF_EXPR and n.spelling == identifier)
                print('case_mode and depth > case_level', case_mode and depth > case_level)
                print('n.kind == CursorKind.DECL_REF_EXPR', n.kind == CursorKind.DECL_REF_EXPR)
                print('n.spelling == identifier', n.spelling == identifier)
                if n.kind == CursorKind.CASE_STMT:
                    case_mode = True
                    case_level = depth
                    print('case_mode changed', case_mode)
                    print('case_level changed', case_level)
                elif case_mode and depth <= case_level:
                    case_mode = False
                    case_level = 10e10
                    print('case_mode changed', case_mode)
                    print('case_level changed', case_level)
                elif case_mode and depth > case_level and n.kind == CursorKind.DECL_REF_EXPR and n.spelling == identifier:
                    print('.line 1831 找case中的conditions')
                    self.print_childrens(node, conditions, depth + 2)
                    so_far = []
                    self.print_calls(self.fully_qualified_pretty(node), so_far, node, conditions, depth=depth + 1)

                if n is not None:
                    self.extract_onTransact(n, identifier, conditions, case_mode=case_mode, case_level=case_level,
                                            depth=depth + 1)

    def onTransact(self, identifier, onTransact_class):
        print(identifier)
        print(onTransact_class)
        k_list, v_list = self.search_fun_list_full(onTransact_class + '::onTransact(')
        node = None
        for tem_v_list in v_list:
            print(tem_v_list.location.file.name)
            if tem_v_list.location.file.name.endswith('.cpp'):
                print('找到onTransact方法：', tem_v_list.kind, self.fully_qualified_pretty(tem_v_list),
                      tem_v_list.location.file.name)
                node = tem_v_list
        if node:
            print('=============查找onTransact中的conditions====')
            print('.line 1837', node.kind, self.fully_qualified_pretty(node), node.location)
            conditions = []
            # self.extract_onTransact(node, identifier, conditions)
            so_far = []
            self.print_calls(self.fully_qualified_pretty(node), so_far, node, conditions, depth=0)
            print('conditions', conditions)
            conditions_new = []
            print(identifier + '*')
            for tem in conditions:
                print(tem)
                if identifier in tem and 'err' not in tem:
                    # tem = tem.replace(identifier + '*', '')
                    tem = re.sub(r'', '', tem)
                    tem = tem.replace('PermissionCache :: ', '')
                    conditions_new.append(tem)
            print('conditions_new', conditions_new)
            # exit(0)
            return conditions_new

    def print_calls(self, fun_name, so_far, last_node, permission_strs, depth=0, DEBUG=False):
        if fun_name in self.CALLGRAPH:
            for f in self.CALLGRAPH[fun_name]:
                node = f
                f = f.referenced
                # string被忽略了
                if (f.location.file is not None and self.pro_path in f.location.file.name):
                    log = self.pretty_print(f)
                    current_depth = depth
                    if '==CONDITION==' in log:
                        if DEBUG:
                            print('.line 1932', log)
                        speci_conds = []
                        str_con = log.replace('==CONDITION==', '')
                        for fun in node._if_contain_functions:
                            if 'check' in log and 'Permission' in self.pretty_print(fun):
                                speci_conds_tem = self.getPermission(fun)
                                if DEBUG:
                                    print('.line 1938', speci_conds_tem)
                                speci_conds_tem = speci_conds_tem.replace(' PermissionCache :: ', '')
                                speci_conds.append(speci_conds_tem)
                                if DEBUG:
                                    print('******* permission check', speci_conds_tem)
                            # elif 'UserId' in log:
                            #     speci_conds_tem =
                            #     speci_conds.append(speci_conds_tem)
                            #     print('******* UserId', speci_conds_tem)
                            # elif 'pid' not in self.pretty_print(fun) and 'Pid' not in self.pretty_print(fun) and 'user' not in self.pretty_print(fun) and 'User' not in self.pretty_print(fun) :
                            #     # speci_conds_tem = self._get_fun_con(fun)
                            #     speci_conds_tem = self.getPermission(fun)
                            #     speci_conds.append(speci_conds_tem)
                            #     print('******* speci_conds_tem', speci_conds_tem)
                            #     exit(2)
                            # elif 'modifyAudioRoutingAllowed' in self.pretty_print(fun):
                            #     print(self.pretty_print(fun))
                            #     exit(0)
                            # elif 'recordingAllowed' in self.pretty_print(fun):
                            # print(self.pretty_print(fun))
                            # speci_conds_tem = self._get_fun_con(fun)
                            # print('******* permission check', speci_conds_tem)
                            # exit(0)
                            # speci_conds.append('!(android.permission.RECORD_AUDIO)')
                            else:
                                speci_conds_tem = self._get_fun_con(fun)
                                speci_conds_tem = speci_conds_tem.replace(' PermissionCache :: ', '')
                                speci_conds.append(speci_conds_tem)
                                if DEBUG:
                                    print('******* speci_conds_tem', speci_conds_tem)

                        # if str_con == '!':
                        #     str_con = speci_conds
                        # else:
                        if len(speci_conds) > 0:
                            # str_con = str_con + '(' + str(speci_conds) + ')'
                            str_con = self._replace_condition_fun(str_con, speci_conds)
                        if DEBUG:
                            print('|||[%s]' % str_con)
                        permission_strs.append(str_con)
                    # elif 'check' in log and 'Permission' in log:
                    #     print('%2d' % current_depth, ' ' * (depth + 1) + log, end='')
                    #     permission_str = self.getPermission(node)
                    #     print('|||[%s]' % permission_str)
                    #     log = log + '|||[%s]' % permission_str
                    #     permission_strs.append(permission_str)
                    elif 'addService' in log:
                        if DEBUG:
                            print('%2d' % current_depth, ' ' * (depth + 1) + log)
                        if DEBUG:
                            print('***')
                        self.print_childrens(node, permission_strs, current_depth + 2)
                        if DEBUG:
                            print('***')
                    elif 'getService' in log:
                        if DEBUG:
                            print('%2d' % current_depth, ' ' * (depth + 1) + log)
                        if DEBUG:
                            print('***')
                        self.print_childrens(node, permission_strs, current_depth + 2)
                        if DEBUG:
                            print('***')
                    elif 'writeInterfaceToken' in log:
                        if DEBUG:
                            print('%2d' % current_depth, ' ' * (depth + 1) + log)
                            print('***')
                        self.print_childrens(node, permission_strs, current_depth + 2)
                        if DEBUG:
                            print('***')
                    else:
                        if DEBUG:
                            print('%2d' % current_depth, ' ' * (depth + 1) + log)

                    self.html_log.append([depth, log])

                    if f in so_far:
                        continue
                    so_far.append(f)

                    # ::IDrm:: YES  ::IPCThreadState:: NO
                    r_final = re.findall(r'::I[A-Z][a-z].+?::', log)
                    print(log)

                    if len(r_final) > 0 and self.has_no_ignore_fun(
                            self.fully_qualified_pretty(last_node)) and self.has_no_ignore_fun(
                            self.fully_qualified_pretty(f)):
                        print('\n\n###### binder start ######')
                        # if 'frameworks/native/lib' in last_node.location.file.name:
                        #     print('*** END OF CALL because go to native lib')
                        #     continue
                        print('original FROM:', self.fully_qualified_pretty(last_node), last_node.location)
                        print(last_node.location.file.name)
                        print('last_node.location.file.name.endswith(\'.h\')',
                              last_node.location.file.name.endswith('.h'))
                        # 如果函数是从.h来的，需要检查有无同名cpp文件，同名cpp文件中是否有这个函数，有的话以cpp中分析为准
                        if last_node.location.file.name.endswith('.h'):
                            print('方法为 .h中的方法，将其替换为cpp中的方法')
                            k_list, v_list = self.search_fun_list_full(self.fully_qualified_pretty(last_node))
                            for tem_v_list in v_list:
                                print(tem_v_list.location.file.name)
                                if tem_v_list.location.file.name.endswith('.cpp'):
                                    print('last_node 替换为 cpp中的方法：', tem_v_list.kind,
                                          self.fully_qualified_pretty(tem_v_list), tem_v_list.location.file.name)
                                    last_node = tem_v_list
                            # exit(2)
                        method_full = self.fully_qualified_pretty(f)
                        print('original TO:', method_full, f.location)

                        if 'android::hardware::' in method_full:
                            print('*** END OF CALL because found android::hardware:: TOO DEEP***')
                            continue
                        elif 'checkPermission' in method_full:
                            print('*** END OF CALL because found checkPermission()')
                            continue
                        elif 'getMediaPlayerService' in method_full:
                            print('*** END OF CALL because found IMediaDeathNotifier::getMediaPlayerService')
                            continue
                        # TO如果为IxxxService:: 直接替换
                        # 将IxxxService::直接替换为xxxService::
                        tema = re.findall(r'I[a-zA-Z]+?Service::', method_full)

                        if 'AudioPolicyService::createAudioPatch' in method_full:
                            head_file_re = f.location.file.name
                            print(head_file_re)
                            h_no_I = self.I_find_no_I(head_file_re)
                            self.extend_h_analysis(h_no_I, '12.0', True, project_path)
                            print('.line 1903')
                            # exit(0)

                        if self.has_ignore_fun_Ixx(method_full) and len(tema) > 0:
                            print('.line 1983')
                            print('替换前', method_full)
                            # if 'AudioPolicyService::createAudioPatch' in method_full:
                            #     print('.line 1908')
                            #     head_file_re = f.location.file.name
                            #     print(head_file_re)
                            #     h_no_I = self.I_find_no_I(head_file_re)
                            #     self.extend_h_analysis(h_no_I, '7.0', True, project_path)
                            # exit(0)
                            for temb in tema:
                                print(temb)
                                method_full = method_full.replace(temb, temb[1:])
                            print('替换后', method_full)
                            k_list, v_list = self.search_fun_list_full(method_full)
                            if len(v_list) != 1:
                                print(len(v_list))
                                print(k_list)
                            assert len(v_list) == 1, '没有找到或找到多个方法，请检查'
                            print('.line 806')
                            print('LINK到下一个方法:')
                            print(self.fully_qualified_pretty(last_node), '=>')
                            print(method_full)
                            print('.line 2091 更改为', k_list[0], v_list[0].location)
                            if v_list[0] in so_far:
                                continue
                            so_far.append(v_list[0])
                            print('.line 1233')
                            print('*** 继续正常打印call graph****')
                            self.print_calls(k_list[0], so_far, v_list[0], permission_strs, depth + 1)
                        elif self.has_ignore_fun_Ixx(self.fully_qualified_pretty(f)):
                            print('.line 2010')
                            return_class = self.link_binder(last_node, f, so_far)
                            print('.line 2012')
                            print('return_class', return_class)

                            print('==========找到Ixxx::xx中的transact 第一个参数的变量名===========')
                            if 'ISurfaceComposer::captureScreen' in self.fully_qualified_pretty(
                                    f) and return_class != 'no_caller':
                                print('解析', f.location.file.name)
                                self.extend_h_analysis(f.location.file.name, '12.0', True, project_path, fuzzy=True)
                                # exit(8)
                                # 找到Ixxx::xx中的transact 第一个参数的变量名
                                # method_full = method_full.replace('android::ISurfaceComposer::', '')
                                # print(method_full)
                                Ixx_method_cpp_k = None
                                Ixx_method_cpp_v = None
                                function_transact = self.fully_qualified_pretty(f)
                                print('line2136', function_transact)
                                # function_transact = function_transact.split('(')[0].split('::')[-1]
                                function_transact = function_transact.split('(')[0].split('::')[-1] + '(' + \
                                                    function_transact.split('(')[1]
                                print('现在开始搜索', function_transact)
                                k_list, v_list = self.search_fun_list_full(function_transact + '(')
                                for i, tem_v_list in enumerate(v_list):
                                    print(tem_v_list.location.file.name)
                                    if tem_v_list.location.file.name.endswith(
                                            '.cpp') and 'BpSurfaceComposer::captureScreen(' in k_list[i]:
                                        print('.line 2121 更改为', k_list[i], v_list[i].location)
                                        Ixx_method_cpp_k = k_list[i]
                                        Ixx_method_cpp_v = v_list[i]
                                if Ixx_method_cpp_k:
                                    transacts = []
                                    self.print_childrens(Ixx_method_cpp_v, transacts, 0)
                                    print('.line 2015', transacts)
                                    transact = transacts[0][0]
                                    print('.line 2017', transact)
                                    # exit(0)
                                    conditions = self.onTransact(transact, return_class)
                                    if conditions is not None:
                                        permission_strs.extend(conditions)
                                        print('提取的permission', conditions)
                                    # exit(8)
                            print('2134==========END===========')

                            if return_class == 'no_caller':
                                print('no_caller，无需分析')
                                continue
                            print('查找结束，LINK到下一个方法:')
                            print(self.fully_qualified_pretty(last_node), '=>')
                            print(self.fully_qualified_pretty(f))
                            fun_str = return_class + '::' + f.displayname
                            print('.line 2143 更改为', fun_str)
                            strinfo = re.compile('<.{0,}?>')
                            fun_str_revised = strinfo.sub('<>', fun_str)
                            # fun_str_revised = fun_str_revised.replace('android::SensorServer', 'android::SensorService')
                            print('.line 2147 fun_str_revised(去掉<...>模板内容):', fun_str_revised)
                            print('function in self.CALLGRAPH:', fun_str_revised in self.CALLGRAPH)
                            k_list, v_list = self.search_fun_list_full(fun_str_revised)
                            if len(k_list) <= 0:
                                # self.search_fun(fun_str_revised)
                                print('找不到这个方法 跳过！')
                                continue
                            if self.has_no_ignore_fun(fun_str_revised) and 'END' not in return_class:
                                k_list, v_list = self.search_fun_list_full(fun_str_revised)
                            else:
                                continue
                            # k_list, v_list = self.search_fun_list_full(fun_str_revised)
                            if v_list[0] in so_far:
                                continue
                            so_far.append(v_list[0])
                            print('.line 1260')
                            print('*** 继续正常打印call graph****')
                            print(k_list[0], v_list[0].location, '=> ...')
                            # 调试
                            # k_list, v_list = self.search_fun_list_full('setOperationParameter(')
                            # for i in range(len(k_list)):
                            #     print(v_list[i].kind, k_list[i], v_list[i].kind, v_list[i].location)
                            self.print_calls(k_list[0], so_far, v_list[0], permission_strs, depth + 1)
                        else:
                            print('*** ignore IServiceManager:: method ****', self.fully_qualified_pretty(f))
                        # if self.fully_qualified_pretty(f) in self.CALLGRAPH:
                        #     self.print_calls(self.fully_qualified_pretty(f), so_far, f, permission_strs, depth + 1)
                        # else:
                        #     self.print_calls(self.fully_qualified(f), so_far, f, permission_strs,
                        #                      depth + 1)
                    #     # f.displayname 'destroyPlugin()'
                    #     print(f.location)
                    #     # last_node = 'android::JDrm::disconnect()'
                    #     # next_fun_name = log[:log.index('(') + 1]
                    #     k_list, v_list = self.search_fun_list_full('::'+f.spelling+'(')
                    #     next_fun_notshown_list_k = []
                    #     next_fun_notshown_list_v = []
                    #     for i in range(len(k_list)):
                    #         exist = False
                    #         for so_far_single in so_far:
                    #             if k_list[i] == self.pretty_print(so_far_single):
                    #                 exist = True
                    #         if not exist and '::Bp' not in k_list[i] and '::Bn' not in k_list[i] and '::__' not in k_list[i]:
                    #             next_fun_notshown_list_k.append(k_list[i])
                    #             next_fun_notshown_list_v.append(v_list[i])
                    #
                    #     print(next_fun_notshown_list_k)
                    #     print('###### binder end ######')
                    #     if len(next_fun_notshown_list_k) > 0:
                    #         so_far.append(next_fun_notshown_list_v[-1])
                    #         print(next_fun_notshown_list_k[-1])
                    #         print(next_fun_notshown_list_k[-1] in self.CALLGRAPH)
                    #         if 'android::DrmHal::signRSA' in next_fun_notshown_list_k[-1]:
                    #             ppp=0
                    #         # self.print_calls(next_fun_notshown_list_k[-1], so_far, self.pretty_print(f), permission_strs,
                    #         #                  depth + 1)
                    #         self.print_calls(next_fun_notshown_list_k[-1], so_far, f, permission_strs, depth + 1)
                    #     else:
                    #         # self.print_calls(next_fun_notshown_list[0], so_far, self.pretty_print(f), permission_strs,
                    #         #                  depth + 1)
                    #         if self.fully_qualified_pretty(f) in self.CALLGRAPH:
                    #             # self.print_calls(self.fully_qualified_pretty(f), so_far, self.pretty_print(f),
                    #             #                  permission_strs, depth + 1)
                    #             self.print_calls(self.fully_qualified_pretty(f), so_far, f, permission_strs, depth + 1)
                    #         else:
                    #             # self.print_calls(self.fully_qualified(f), so_far, self.pretty_print(f), permission_strs,
                    #             #                  depth + 1)
                    #             self.print_calls(self.fully_qualified(f), so_far, f, permission_strs,
                    #                              depth + 1)
                    #
                    #     # android::IRadio::tune(unsigned int, unsigned int)
                    #     # 'android::IServiceManager::getService(const class android::String16 &)'
                    #     # next_fun_name = log.replace(r1[0], r1[0][1:])
                    #     # print('%2d' % current_depth, ' ' * (depth + 1) + next_fun_name, '%%% AIDL JUMP')
                    #     # self.print_calls(next_fun_name, so_far, self.pretty_print(f), permission_strs,
                    #     #                  depth + 1)
                    # # link for AIDL============
                    elif self.fully_qualified_pretty(f) in self.CALLGRAPH:
                        # self.print_calls(self.fully_qualified_pretty(f), so_far, self.pretty_print(f), permission_strs, depth + 1)
                        self.print_calls(self.fully_qualified_pretty(f), so_far, f, permission_strs,
                                         depth + 1)
                    else:
                        # self.print_calls(self.fully_qualified(f), so_far, self.pretty_print(f), permission_strs, depth + 1)
                        self.print_calls(self.fully_qualified(f), so_far, f, permission_strs,
                                         depth + 1)
                # else:
                #     # print('  ' * (depth + 1) + 'ENDNODE|' + fun_name)
                #     if last_node is not None and last_node not in self.ENDNODE:
                #         self.ENDNODE.append(last_node)
        else:
            # print('  ' * (depth + 1) + 'ENDNODE|'+ fun_name)
            # aaa= self.CALLGRAPH[fun_name]
            if last_node is not None and last_node not in self.ENDNODE:
                self.ENDNODE.append(last_node)

    def extend_h_analysis(self, file, version_prefix, compdb=False, project_path='/Volumes/android/android-8.0.0_r34/',
                          fuzzy=False):

        if fuzzy:
            c_cpp_lists = [find_command(file, version_prefix=version_prefix, compdb=compdb, project_path=project_path)]
        else:
            c_cpp_lists = find_command_all_cpp(file, version_prefix=version_prefix, compdb=compdb,
                                               project_path=project_path)
        for i, c_cpp_list in enumerate(c_cpp_lists):
            # self.print_all_node = True
            print('额外分析', i, '/', len(c_cpp_lists))
            if c_cpp_list is not None and project_path + c_cpp_list['file'] not in self.analyzed_cpp:
                # next_file = '/Volumes/android/android-7.0.0_r33/' + c_cpp_list['source']
                next_file = project_path + c_cpp_list['file']
                self.analyzed_cpp.add(next_file)
                print('.line 2039', next_file)
                '''
                        /Volumes/android/android-7.0.0_r33/frameworks/av/media/libstagefright/MediaClock.cpp:93:5: error: use of undeclared identifier 'GE'
                        /Volumes/android/android-7.0.0_r33/frameworks/av/media/libstagefright/foundation/AString.cpp:170:5: error: use of undeclared identifier 'LT'
                        /Volumes/android/android-7.0.0_r33/frameworks/av/media/libstagefright/MediaSync.cpp:502:9: error: use of undeclared identifier 'EQ'         
                        /Volumes/android/android-7.0.0_r33/frameworks/av/media/libstagefright/foundation/MediaBuffer.cpp:109:9: error: use of undeclared identifier 'EQ'
                '''
                if 'MediaClock.cpp' in next_file or 'AString.cpp' in next_file or 'MediaSync.cpp' in next_file or 'MediaBuffer.cpp' in next_file:
                    print('pass: ', next_file)
                    continue
                # ninja_args = c_cpp_list['content']['flags']
                # ninja_args = c_cpp_list['command'].split()[1:]
                ninja_args = c_cpp_list['arguments'][1:]
                ninja_args = self.parse_ninja_args(ninja_args)
                # print(next_file)
                # print(ninja_args)
                # self.load_cfg(index, c_cpp_list['content']['compiler'], next_file, ninja_args)
                if 'clang++' in c_cpp_list['arguments'][0]:
                    self.load_cfg(self.index, 'clang++', next_file, ninja_args)
                else:
                    self.load_cfg(self.index, 'clang', next_file, ninja_args)
                # self.print_all_node = False
            else:
                print(file, '*.h has implement or *.cpp name is different')

    def read_compile_commands(self, filename):
        if filename.endswith('.json'):
            with open(filename) as compdb:
                return json.load(compdb)
        else:
            return [{'arguments': '', 'file': filename}]

    def read_args(self, args):
        db = None
        clang_args = []
        excluded_prefixes = []
        excluded_paths = ['/usr']
        i = 0
        while i < len(args):
            if args[i] == '-x':
                i += 1
                excluded_prefixes = args[i].split(',')
            elif args[i] == '-p':
                i += 1
                excluded_paths = args[i].split(',')
            elif args[i][0] == '-':
                clang_args.append(args[i])
            else:
                db = args[i]
            i += 1
        return {
            'db': db,
            'clang_args': clang_args,
            'excluded_prefixes': excluded_prefixes,
            'excluded_paths': excluded_paths
        }

    def check_file(self, file):
        if not os.path.exists(file):
            raise Exception("FILE DOES NOT EXIST: \"" + file + "\"")
        return file

    def check_path(self, path):
        if not os.path.exists(path):
            raise Exception("PATH DOES NOT EXIST: \"" + path + "\"")
        return path

    def is_include_in_set(self, path, set):
        for tem in set:
            print(str(tem, encoding="utf-8"), path)
            if path not in str(tem):
                return True
        return False

    def collect_cfg(self, index, file, args):
        tu = index.parse(file, args)
        for d in tu.diagnostics:
            if d.severity == d.Error or d.severity == d.Fatal:
                print(d)
            else:
                print(d)
        print('Analyzing:', file)
        self.node_start = tu.cursor
        self.file_tu = tu
        self.show_info(tu.cursor)

    def parse_ninja_args(self, ninja_args):
        for i in range(len(ninja_args)):
            # print(tem_args[i])
            if '-I' in ninja_args[i] and len(ninja_args[i]) > 2:
                # ninja_args[i] = ninja_args[i].replace('-I', '-I/Volumes/android/android-8.0.0_r34/')
                ninja_args[i] = ninja_args[i].replace('-I', '-I' + project_path)
            if i > 0 and ninja_args[i - 1] == '-I' or ninja_args[i - 1] == '-isystem' or ninja_args[i - 1] == '-o' or \
                    ninja_args[i - 1] == '-MF':
                ninja_args[i] = project_path + ninja_args[i]
            if '-fsanitize-blacklist=' in ninja_args[i]:
                ninja_args[i] = ninja_args[i].replace('-fsanitize-blacklist=', '-fsanitize-blacklist=' + project_path)
            # print(tem_args[i])
        return ninja_args

    def load_cfg_normal(self, index, file, args):

        syspath = ccsyspath.system_include_paths(
            '/hci/chaoran_data/android-12.0.0_r31/prebuilts/clang/host/linux-x86/clang-r416183b1/bin/clang++')
        sysincargs = ['-I' + str(inc, encoding="utf8") for inc in syspath]
        args = args + sysincargs

        tu = index.parse(file, args)
        for d in tu.diagnostics:
            if d.severity == d.Error or d.severity == d.Fatal:
                print(d)
                raise Exception('aaaaaaaaaaaaaaaaaa')
            else:
                print(d)
        # tu.save()
        self.node_start[file] = tu.cursor
        self.file_tu[file] = tu
        self.show_info(tu.cursor)
        return tu

    def load_cfg(self, index, compiler, file, ninja_args):
        print(compiler)

        if 'clang++' in compiler:
            # init_args = init_arg_config
            init_args = init_arg_config
            # init_args = ['-isystem/Volumes/android/android-8.0.0_r34/prebuilts/clang/host/darwin-x86/clang-4053586/lib64/clang/5.0.300080/include']
            ninja_args = init_args + ninja_args
            for i in range(len(ninja_args)):
                if '\\' in ninja_args[i]:
                    print(ninja_args[i])
                    # 两边加双引号 flag中的双引号 才可以被正确识别
                    ninja_args[i] = '"' + ninja_args[i] + '"'
                    print(ninja_args[i])
                if '-DAAUDIO_API=\'__attribute__((visibility("default")))\'' in ninja_args[i]:
                    # print(ninja_args[i])
                    ninja_args[i] = "-DAAUDIO_API=__attribute__((visibility(\"default\")))"
                    # print(ninja_args[i])
                ninja_args[i] = ninja_args[i].replace(r'"-DPACKED=\"\""', '-DPACKED=""')
        ast_path = 'ast/' + file.replace('/', '_') + '.ast'
        tu = None

        ninja_args = ninja_args[:-1]
        # print(ninja_args)
        # exit(2)

        if os.path.exists(ast_path):
            tu = index.read(ast_path)
        else:
            tu = index.parse(file, ninja_args)

        for d in tu.diagnostics:
            if d.severity == d.Error or d.severity == d.Fatal:
                print(d)
                if 'use of undeclared identifier' in str(d) or 'file not found' in str(d):
                    return None
                raise Exception('aaaaaaaaaaaaaaaaaa')
            else:
                print(d)

        if not os.path.exists(ast_path):
            print('save:', ast_path)
            tu.save(ast_path)

        self.node_start[file] = tu.cursor
        self.file_tu[file] = tu
        for child in tu.cursor.get_children():
            # print('2556|', child.location)
            if file in child.location.file.name:
                self.show_info(child)

        return tu

    def get_node_from_child(self, fun_name):
        for k, v in self.CALLGRAPH.items():
            for f in v:
                f = f.referenced
                # 找到了子节点
                if self.fully_qualified_pretty(f) == fun_name or self.fully_qualified(
                        f) == fun_name:
                    return f
        return None

    def extract_jni_fun(self, file_str, pro_path, ninja_args, show_loc=False, print_all_node=True):

        self.show_loc = show_loc
        self.print_all_node = print_all_node
        index = Index.create(1)
        file = self.check_file(file_str)
        self.pro_path = pro_path

        ninja_args = self.parse_ninja_args(ninja_args)
        args = ninja_args
        tu = self.load_cfg(index, 'clang++', file, args)
        # for key in self.CALLGRAPH:
        #     # 应限定在改cpp文件中
        #     print('***** start node *****', key, self.CALLGRAPH[key])+
        not_sys_include_paths = []
        for tem in tu.get_includes():
            include_path = tem.include.name
            if self.pro_path + 'frameworks' in include_path:
                print(include_path)

    def run(self, file_str, pro_path, ninja_args, entry_funs=None, IS_AOSP=True, extend_analyze=True, show_loc=False,
            print_all_node=False, generate_html=False, reverse_search=False, only_preprocess=False):
        print('--- run ---')
        self.show_loc = show_loc
        self.print_all_node = print_all_node
        index = Index.create(1)
        self.index = index
        file = self.check_file(file_str)
        self.pro_path = pro_path

        tu = None
        args = None

        # analyze the cpp file
        if IS_AOSP:
            ninja_args = self.parse_ninja_args(ninja_args)
            args = ninja_args
            tu = self.load_cfg(index, 'clang++', file, args)
        else:
            tu = self.load_cfg_normal(index, file, ninja_args)

        # print('======RUN FOR DEBUG=====')
        # command = '/Volumes/android/android-8.0.0_r34/prebuilts/clang/host/darwin-x86/clang-4053586/bin/clang -v ' + str(args).replace('[', '').replace(']', '').replace('b\'', '').replace('\'', '').replace(',', '').replace('-Wa--noexecstack','-Wa,--noexecstack') + ' ' + file
        # b = os.popen(command)
        # text2 = b.read()
        # print(text2)
        # b.close()

        # else:
        #     print('matching:')
        #     for f, ff in self.FULLNAMES.items():
        #         if f.startswith(entry_fun):
        #             for fff in ff:
        #                 print(fff)
        # print('==========')
        # for f, ff in FULLNAMES.items():
        #     print(f)
        #     print(ff)
        #     print('---')

        # start node
        # for key in self.CALLGRAPH:
        #     # 应限定在改cpp文件中
        #     print('***** start node *****', key, self.CALLGRAPH[key])

        # obtain and traverse the include files
        for tem in tu.get_includes():
            include_path = tem.include.name

            if IS_AOSP:
                if self.pro_path + 'frameworks' in include_path:
                    print('include file', include_path)

        not_sys_include_paths = []
        for tem in tu.get_includes():
            include_path = tem.include.name

            if IS_AOSP:
                if self.pro_path + 'frameworks' in include_path:
                    not_sys_include_paths.append(include_path)
                    # IxxService时加入xxService搜索
                    r = re.findall(r'I.+?Service\.h', include_path)
                    if len(r) > 0:
                        aaa = include_path.replace(r[0], r[0][1:])
                        not_sys_include_paths.append(aaa)

                    r = re.findall(r'I.+?Client\.h', include_path)
                    if len(r) > 0:
                        aaa = include_path.replace(r[0], r[0][1:])
                        not_sys_include_paths.append(aaa)

                    r = re.findall(r'I.+?Client\.h', include_path)
                    if len(r) > 0:
                        aaa = include_path.replace(r[0], r[0][1:-8]) + '.h'
                        not_sys_include_paths.append(aaa)

                    not_sys_include_paths.append(include_path.replace('Manager.h', 'Service.h'))

                    # not_sys_include_paths.append('frameworks/native/libs/gui/ISurfaceComposer.cpp')

                    r = re.findall(r'I.+?\.h', include_path)
                    if len(r) > 0 and 'Service' not in include_path:
                        not_sys_include_paths.append(include_path.replace(r[0], r[0][1:]))
                        # not_sys_include_paths.append('system/core/include/private/android_filesystem_config.h')

                        # 增加include文件扩展分析
                        # not_sys_include_paths.append(include_path.replace(r[0], 'DrmHal.h'))

                        # 增加include文件扩展分析
                        # not_sys_include_paths.append(include_path.replace(r[0], 'SensorService.h'))

                        # 增加include文件扩展分析 android_media_AudioSystem.cpp
                        # del not_sys_include_paths.append(include_path.replace(r[0], 'AudioFlinger.h'))
                        # del not_sys_include_paths.append(include_path.replace(r[0], 'AudioPolicyService.h'))
                        # del not_sys_include_paths.append(include_path.replace(r[0], 'ServiceUtilities.h'))
                        # not_sys_include_paths.append('frameworks/av/services/audiopolicy/service/AudioPolicyInterfaceImpl.cpp')

                        # not_sys_include_paths.append('frameworks/av/services/audioflinger/ServiceUtilities.cpp')
                        # not_sys_include_paths.append('frameworks/av/media/utils/ServiceUtilities.cpp')
                        # not_sys_include_paths.append(
                        #     'frameworks/av/services/audiopolicy/service/AudioPolicyInterfaceImpl.cpp')

                        # not_sys_include_paths.append('frameworks/av/include/media/IMediaPlayerService.h')
                        # not_sys_include_paths.append('frameworks/av/include/media/IMediaDeathNotifier.h')
                        # eee = include_path.replace(r[0], 'MediaPlayerService.h')
                        # not_sys_include_paths.append(eee)
                        # not_sys_include_paths.append('frameworks/av/services/mediadrm/MediaDrmService.cpp')
                        # not_sys_include_paths.append('frameworks/native/services/surfaceflinger/SurfaceFlinger.cpp')

        new_not_sys_include_paths = []
        for not_sys_include_path in not_sys_include_paths:
            if not_sys_include_path not in new_not_sys_include_paths:
                new_not_sys_include_paths.append(not_sys_include_path)
        not_sys_include_paths = new_not_sys_include_paths

        i = 0
        if extend_analyze:
            print('===========ALL INCLUDE FILE=============')
            # not_sys_include_paths.insert(0, project_path + 'frameworks/av/services/audioflinger/AudioFlinger.h')
            # del not_sys_include_paths.insert(0, project_path + 'frameworks/av/services/audiopolicy/service/AudioPolicyService.h')
            # not_sys_include_paths.insert(0, project_path + 'frameworks/av/services/audioflinger/ServiceUtilities.h')
            # not_sys_include_paths.append(include_path.replace(r[0], 'SensorService.h'))
            not_sys_include_paths = set(not_sys_include_paths)
            print(not_sys_include_paths)
            print('===========SEARCH INCLUDE FILE=============')
            for tem in not_sys_include_paths:
                i = i + 1
                print('***************')
                print('Loading CFG ... ', i, '/', len(not_sys_include_paths))

                # print("*.h:", tem)
                if IS_AOSP:
                    # c_cpp_list = find_command(tem)
                    c_cpp_list = find_command(tem, version_prefix='12.0', compdb=True, project_path=project_path)
                    # for i_c_cpp_lists, c_cpp_list in enumerate(c_cpp_lists):
                    #     print('.line 2293 ', i_c_cpp_lists, '/', len(c_cpp_lists))
                    if c_cpp_list is not None and project_path + c_cpp_list['file'] not in self.analyzed_cpp:
                        # next_file = '/Volumes/android/android-7.0.0_r33/' + c_cpp_list['source']
                        next_file = project_path + c_cpp_list['file']
                        self.analyzed_cpp.add(next_file)
                        print('.line 2297', next_file)
                        # '''
                        #         /Volumes/android/android-7.0.0_r33/frameworks/av/media/libstagefright/MediaClock.cpp:93:5: error: use of undeclared identifier 'GE'
                        #         /Volumes/android/android-7.0.0_r33/frameworks/av/media/libstagefright/foundation/AString.cpp:170:5: error: use of undeclared identifier 'LT'
                        #         /Volumes/android/android-7.0.0_r33/frameworks/av/media/libstagefright/MediaSync.cpp:502:9: error: use of undeclared identifier 'EQ'
                        #         /Volumes/android/android-7.0.0_r33/frameworks/av/media/libstagefright/foundation/MediaBuffer.cpp:109:9: error: use of undeclared identifier 'EQ'
                        #         /hci/chaoran_data/android-10.0.0_r45/frameworks/native/libs/ui/Region.cpp:560:24: error: result of comparison 'const int32_t' (aka 'const int') > 2147483647 is always false [-Wtautological-type-limit-compare]
                        #
                        # '''
                        # if 'MediaClock.cpp' in next_file or 'AString.cpp' in next_file or 'MediaSync.cpp' in next_file or 'MediaBuffer.cpp' in next_file or 'Region.cpp' in next_file:
                        #     print('pass: ', next_file)
                        #     continue
                        # ninja_args = c_cpp_list['content']['flags']
                        ninja_args = c_cpp_list['arguments'][1:]
                        ninja_args = self.parse_ninja_args(ninja_args)
                        # print(next_file)
                        # print(ninja_args)
                        # self.load_cfg(index, c_cpp_list['content']['compiler'], next_file, ninja_args)
                        if 'clang++' in c_cpp_list['arguments'][0]:
                            self.load_cfg(index, 'clang++', next_file, ninja_args)
                        else:
                            self.load_cfg(index, 'clang', next_file, ninja_args)
                    else:
                        print(tem, '*.h has implement or *.cpp name is different')

        print('\n====print dependency=====')
        print(file)
        checked_var = []

        print('\n**** var *****')
        print('self.var.keys', '111', self.var.keys())
        for k in self.var.keys():
            if len(self.var[k]) != 0:
                print()
                print('111 \'scope\':', k, '111')
                for tem in self.var[k]:
                    if isinstance(tem, Cursor):
                        print(tem.spelling)
                        checked_var.append({'k': k, 'v': tem})
                    else:
                        print(tem)

        for k in self.structure_var.keys():
                print()
                print('111 \'structure_var\':', k, '111')
                tem = self.structure_var[k]
                    # if isinstance(tem, Cursor):
                print(tem.spelling)
                checked_var.append({'k': k, 'v': tem})
                    # else:
                    #     print(tem)

        checked_assign = []

        def get_right(tem):
            print('get_right |', tem)
            # self.assign[k][j]['right']
            if isinstance(tem, list):
                for temm in tem:
                    print('2998 |')
                    if isinstance(temm, list):
                        for temmm in temm:
                            if temmm is None:
                                print('3026 |', temmm, 'is None')
                            return temmm
                    else:
                        if temm is None:
                            print('3030 |', temm, 'is None')
                        return temm
            else:
                if tem is None:
                    print('3034 |', tem, 'is None')
                return tem


        print('\n**** assign *****')

        print('self.assign.keys', '111', self.assign.keys())
        for k in self.assign.keys():
            if len(self.assign[k]) != 0:
                print()
                print('111 \'scope\':', k, '111')
                for tem in self.assign[k]:
                    # print(tem)
                    if 'left' in tem.keys():
                        # print('\'left\'', end=' ')
                        for j, temm in enumerate(tem['left']):
                            if isinstance(temm, list):
                                for i, temmm in enumerate(temm):
                                    if i != len(temm) - 1:
                                        print(temmm.kind, temmm.spelling, end='. ')
                                        right = get_right(tem['right'])
                                        if right.kind != CursorKind.GNU_NULL_EXPR and right.kind != CursorKind.CXX_NULL_PTR_LITERAL_EXPR:
                                            checked_assign.append({'k': k, 'pos': 'left', 'v': temmm})
                                    else:
                                        print(temmm.kind, temmm.spelling, end=' ')
                                        right = get_right(tem['right'])
                                        if right.kind != CursorKind.GNU_NULL_EXPR and right.kind != CursorKind.CXX_NULL_PTR_LITERAL_EXPR:
                                            checked_assign.append({'k': k, 'pos': 'left', 'v': temmm})
                            else:
                                print(temm.kind, temm.spelling, end=' ')
                                right = get_right(tem['right'])
                                if right.kind != CursorKind.GNU_NULL_EXPR and right.kind != CursorKind.CXX_NULL_PTR_LITERAL_EXPR:
                                    checked_assign.append({'k': k, 'pos': 'left', 'v': temm})
                        # print()
                        print('\'=\'', end=' ')
                        for temm in tem['right']:
                            if isinstance(temm, list):
                                for i, temmm in enumerate(temm):
                                    if i != len(temm) - 1:
                                        print(temmm.kind, temmm.spelling, end='. ')
                                        if temmm.kind != CursorKind.GNU_NULL_EXPR and temmm.kind != CursorKind.STRING_LITERAL and temmm.kind != CursorKind.INTEGER_LITERAL and temmm.kind != CursorKind.CXX_NULL_PTR_LITERAL_EXPR and temmm.kind != CursorKind.CXX_THIS_EXPR:
                                            checked_assign.append({'k': k, 'pos': 'right', 'v': temmm})
                                    else:
                                        print(temmm.kind, temmm.spelling, end=' ')
                                        if temmm.kind != CursorKind.GNU_NULL_EXPR and temmm.kind != CursorKind.STRING_LITERAL and temmm.kind != CursorKind.INTEGER_LITERAL and temmm.kind != CursorKind.CXX_NULL_PTR_LITERAL_EXPR and temmm.kind != CursorKind.CXX_THIS_EXPR:
                                            checked_assign.append({'k': k, 'pos': 'right', 'v': temmm})
                            else:
                                print(temm.kind, temm.spelling, end=' ')
                                if temm.kind != CursorKind.GNU_NULL_EXPR and temm.kind != CursorKind.STRING_LITERAL and temm.kind != CursorKind.INTEGER_LITERAL and temm.kind != CursorKind.CXX_NULL_PTR_LITERAL_EXPR and temm.kind != CursorKind.CXX_THIS_EXPR:
                                    checked_assign.append({'k': k, 'pos': 'right', 'v': temm})
                        print()

                    elif 'fun' in tem.keys():
                        print('\'fun\'', end=' ')
                        pos = tem['pos']
                        for temm in tem['fun']:
                            if isinstance(temm, list):
                                for i, temmm in enumerate(temm):
                                    if i != len(temm) - 1:
                                        print(temmm.kind, temmm.spelling, end='. ')
                                        checked_assign.append({'k': k, 'pos': pos, 'v': temmm})
                                    else:
                                        print(temmm.kind, temmm.spelling, end=' ')
                                        checked_assign.append({'k': k, 'pos': pos, 'v': temmm})
                            else:
                                print(temm.kind, temm.spelling, end=' ')
                                checked_assign.append({'k': k, 'pos': pos, 'v': temm})
                        print()
                        print('\'input\'', end=' ')
                        for temm in tem['input']:
                            if isinstance(temm, list):
                                for i, temmm in enumerate(temm):
                                    if i != len(temm) - 1:
                                        print(temmm.kind, temmm.spelling, end='. ')
                                        checked_assign.append({'k': k, 'pos': pos, 'v': temmm})
                                    else:
                                        print(temmm.kind, temmm.spelling, end=' ')
                                        checked_assign.append({'k': k, 'pos': pos, 'v': temmm})
                            else:
                                print(temm.kind, temm.spelling, end=' ')
                                checked_assign.append({'k': k, 'pos': pos, 'v': temm})
                    else:
                        print('\'else branch\'')
                        print(tem)

        print(checked_var)
        print(checked_assign)
        print('\n====check dependency=====')
        print(file)

        init_var = []
        use_var = []
        clear_var = []
        for assign in checked_assign:
            for var in checked_var:
                # print(assign['v'], assign['v'].kind, assign['v'].spelling)
                # print(var['v'], var['v'].kind, var['v'].spelling)
                # exit(0)
                if assign['v'].spelling == var['v'].spelling:
                    # print(assign['v'], assign['v'].kind, assign['v'].spelling)
                    assign_ref = assign['v'].referenced
                    # print(assign_, assign_.kind, assign_.spelling)
                    # print(var['v'], var['v'].kind, var['v'].spelling)
                    # print(assign_ref == var['v'])
                    # exit(0)
                    if assign_ref == var['v']:
                        if assign['pos'] == 'left':
                            init_var.append(assign)
                            break
                        elif assign['pos'] == 'right':
                            use_var.append(assign)
                            break

        print('\ninit_var:')
        for tem in init_var:
            print(tem['k'], tem['v'].spelling)
        print('\nuse_var:')
        for tem in use_var:
            print(tem['k'], tem['v'].spelling)

        dependency = []
        for init in init_var:
            for use in use_var:
                if init['v'].spelling == use['v'].spelling:
                    dependency.append([init['k'], use['k']])

        print('\n**** print, first => second *****')
        print(file)
        for tem in dependency:
            print('\'', tem[0], '\' => \'', tem[1], '\'')

        jni_methods_full = []
        print()
        print(self.jni_methods)
        for i in range(len(self.jni_methods)):
            if len(self.jni_methods[i].keys())<2:
                continue
            self.jni_methods[i]['class'] = self.jni_methods[i]['class'].replace('/', '.').strip().strip('"')
            clazz = self.jni_methods[i]['class']
            print("\n'clazz'", clazz)
            print("'method_var'", self.jni_methods[i]['method_var'])

            jni_methods = None
            for k in self.var.keys():
                if k == self.jni_methods[i]['method_var']:
                    print(self.var[k])
                    jni_methods = self.var[k]
                    break

            def transformSmaliType(input):
                output = []
                array = 0
                while len(input) > 0:
                    if input.startswith('L'):
                        input = input[1:]
                        input = input.replace('/', '.')
                        if array == 0:
                            output.append(input)
                        elif array == 1:
                            output.append(input+'[]')
                            array = 0
                        elif array == 2:
                            output.append(input+'[][]')
                            array = 0
                        input = ''
                    elif input.startswith('['):
                        array = array + 1
                        input = input[1:]
                    elif input.startswith('V'):
                        if array == 0:
                            output.append('void')
                        elif array == 1:
                            output.append('void[]')
                            array = 0
                        elif array == 2:
                            output.append('void[][]')
                            array = 0
                        input = input[1:]
                    elif input.startswith('Z'):
                        if array == 0:
                            output.append('boolean')
                        elif array == 1:
                            output.append('boolean[]')
                            array = 0
                        elif array == 2:
                            output.append('boolean[][]')
                            array = 0
                        input = input[1:]
                    elif input.startswith('B'):
                        if array == 0:
                            output.append('byte')
                        elif array == 1:
                            output.append('byte[]')
                            array = 0
                        elif array == 2:
                            output.append('byte[][]')
                            array = 0
                        input = input[1:]
                    elif input.startswith('S'):
                        if array == 0:
                            output.append('short')
                        elif array == 1:
                            output.append('short[]')
                            array = 0
                        elif array == 2:
                            output.append('short[][]')
                            array = 0
                        input = input[1:]
                    elif input.startswith('C'):
                        if array == 0:
                            output.append('char')
                        elif array == 1:
                            output.append('char[]')
                            array = 0
                        elif array == 2:
                            output.append('char[][]')
                            array = 0
                        input = input[1:]
                    elif input.startswith('I'):
                        if array == 0:
                            output.append('int')
                        elif array == 1:
                            output.append('int[]')
                            array = 0
                        elif array == 2:
                            output.append('int[][]')
                            array = 0
                        input = input[1:]
                    elif input.startswith('J'):
                        if array == 0:
                            output.append('long')
                        elif array == 1:
                            output.append('long[]')
                            array = 0
                        elif array == 2:
                            output.append('long[][]')
                            array = 0
                        input = input[1:]
                    elif input.startswith('F'):
                        if array == 0:
                            output.append('float')
                        elif array == 1:
                            output.append('float[]')
                            array = 0
                        elif array == 2:
                            output.append('float[][]')
                            array = 0
                        input = input[1:]
                    elif input.startswith('D'):
                        if array == 0:
                            output.append('double')
                        elif array == 1:
                            output.append('double[]')
                            array = 0
                        elif array == 2:
                            output.append('double[][]')
                            array = 0
                        input = input[1:]

                return output

            for i, tem in enumerate(jni_methods):
                print()
                print("'cpp_fun'", tem['cpp_fun'])
                print("'java_fun'", tem['java_fun'])
                print("'java_sig'", tem['java_sig'])
                tem['java_fun'] = tem['java_fun'].strip().strip('"')
                tem['java_sig'] = tem['java_sig'].strip().strip('"')
                l = tem['java_sig'].split(')')
                parList = l[0].strip('(').replace('"', '')
                returnType = l[1].replace('"', '')
                pars = parList.split(';')
                if re.search(r'\s[A-Z]{2,}\s', parList) or re.search(r'\s[A-Z]{2,}\s', returnType):
                    return 'FAIL', 'FAIL'
                parList_output = []
                for par in pars:
                    # print('3243 | ', par)
                    par_tranformed = transformSmaliType(par)
                    parList_output.extend(par_tranformed)
                # print(parList_output)
                return_tranformed = transformSmaliType(returnType)
                # print(return_tranformed)
                jni_methods[i]['java_fun_full'] = clazz + ' ' + return_tranformed[0] + ' ' + tem['java_fun'] + str(parList_output).replace('[','(').replace(']',')').replace('\'','')
                print(jni_methods[i]['java_fun_full'])
            jni_methods_full.extend(jni_methods)

        if len(jni_methods_full) == 0:
            raise Exception('len(jni_methods_full) =0')


        first_lvl_funs = self.fist_lvl_funs
        for i in range(len(first_lvl_funs)):
            first_lvl_funs[i] = first_lvl_funs[i].split('::')[-1]
        print('****** self.fist_lvl_funs ****** \n', self.fist_lvl_funs)

        def in_first_lvl_funs(fun_tem):
            # if 'DngCreator_getNativeContext' in fun_tem or 'DngCreator_setNativeContext' in fun_tem:
            #     return True

            # first_lvl_funs = ['DngCreator_nativeClassInit(', 'DngCreator_init(', ...]
            for first_lvl_funs_t in first_lvl_funs:
                # if 'DngCreator_getNativeContext' in fun_tem and 'DngCreator_getNativeContext' in first_lvl_funs_t:
                    # print('11111111111', fun_tem)
                    # print('22222222222', first_lvl_funs_t)
                if first_lvl_funs_t in fun_tem or fun_tem in first_lvl_funs_t:
                    return True
            return False

        print('****** self.CALLGRAPH.keys() ****** \n', self.CALLGRAPH.keys())
        print('================ dependency ================')
        # print('!!!!!!!!!self.CALLGRAPH.keys() = ', self.CALLGRAPH.keys())
        # print('!!!!!!!!!2for = ', self.fully_qualified_pretty(self.CALLGRAPH[self.CALLGRAPH.keys()[0]][0]))
        # print('!!!!!!!!!first_lvl_funs = ', first_lvl_funs[0])
        for CALLGRAPH_keys in self.CALLGRAPH.keys():
            # print('!!!!!!!!!CALLGRAPH_keys = ', CALLGRAPH_keys + '=>')
            if in_first_lvl_funs(CALLGRAPH_keys):
                for temNode in self.CALLGRAPH[CALLGRAPH_keys]:
                    # print('|', self.fully_qualified_pretty(temNode), end='')
                    # print('!!!!!!!!!self.fully_qualified_pretty(temNode) = ', self.fully_qualified_pretty(temNode))

                    fun_tem = self.fully_qualified_pretty(temNode._referenced)
                    if '(' not in fun_tem:
                        fun_tem = fun_tem + '('
                    # if '::' in fun_tem:
                    #     fun_tem = fun_tem.split('::')[-1]

                    if in_first_lvl_funs(fun_tem):
                        # print('got it')
                        dependency.append([CALLGRAPH_keys, fun_tem])
                        print([CALLGRAPH_keys, fun_tem])
            # print('')
        print('================ END dependency ================')

        with open('dependency/temp/' + file.replace('/', '|') + '.json', 'w') as f:
            json.dump({'file': file, 'jni_methods': jni_methods_full, 'dependency': dependency}, f)

        return None

        if reverse_search == False:
            print('====print CFG=====')
            collect_all_fun = False
            if entry_funs is None or len(entry_funs) == 0:
                collect_all_fun = True
            for tem in self.CALLGRAPH:
                if collect_all_fun:
                    pass
                # print(tem)

            html = ''
            for entry_fun_part in entry_funs:
                entry_funs, entry_fun_vs = self.search_fun(entry_fun_part)
                for i in range(len(entry_funs)):
                    entry_fun = entry_funs[i]
                    entry_fun_v = entry_fun_vs[i]
                    if entry_fun in self.CALLGRAPH:
                        print('----entry_fun----')
                        print(entry_fun)
                        # if 'permission' in entry_fun:
                        #     raise Exception('!!!!!!!!found permission check function!!!!!!!')
                        self.html_log = []
                        permission_strs = []
                        so_far = []
                        so_far.append(entry_fun_v)
                        self.print_calls(entry_fun, so_far, entry_fun_v, permission_strs)
                        print('permission_str', permission_strs)
                        for permission_str in permission_strs:
                            self.found_permission_method.append([entry_fun, permission_str])
                            print('FOUND ', entry_fun, ' ::: ', permission_str)

                        if generate_html:
                            html = html + '<ul><li>' + entry_fun.replace('>', '&gt;').replace('<', '&lt;')
                            last_depth = -1
                            for tem in self.html_log:
                                depth = tem[0]
                                o = tem[1].replace('>', '&gt;').replace('<', '&lt;')
                                if depth > last_depth:
                                    html = html + '\n' + '\t' * depth + '<ul>\n'
                                elif depth == last_depth:
                                    html = html + '</li>\n'
                                elif depth < last_depth:
                                    for temmm in range(last_depth, depth, -1):
                                        html = html + '</li>\n' \
                                               + ('\t' * temmm) + '</ul>\n'
                                    html = html + ('\t' * depth) + '</li>\n'

                                html = html + ('\t' * depth) + '<li>' + o

                                last_depth = depth

                            for temmm in range(last_depth, -1, -1):
                                # if temmm==0:
                                html = html + '</li>\n' + ('\t' * temmm) + '</ul>'
                                # else:
                                #     html = html + '</li>\n' \
                                #            + ('\t' * temmm) + '</ul>\n' \
                                #            + ('\t' * temmm) + '</li>\n'
                            html = html + '</li></ul>'
                            # print(html)
            if generate_html:
                html = '''
                    <!DOCTYPE html>
                    <html>

                      <head>
                        <meta charset="utf-8" />
                        <title>无标题文档</title>
                        <style>ul li ul { display:none; }</style>
                        <script src="http://ajax.aspnetcdn.com/ajax/jQuery/jquery-1.8.0.js"></script>
                        <script type="text/javascript">$(function() {

                            $("li:has(ul)").click(function(event) {
                              if (this == event.target) {
                                if ($(this).children().is(':hidden')) {
                                  $(this).css({
                                    cursor: 'pointer',
                                    'list-style-type': 'none',
                                    'background': 'url(../img/minus.png) no-repeat 0rem 0.1rem',
                                    'background-size': '1rem 1rem',
                                    'text-indent': '2em'
                                  }).children().show();
                                } else {
                                  $(this).css({
                                    cursor: 'pointer',
                                    'list-style-type': 'none',
                                    'background': 'url(../img/plus.png) no-repeat 0rem 0.1rem',
                                    'background-size': '1rem 1rem',
                                    'text-indent': '2em'
                                  }).children().hide();
                                }
                              }
                              return false;
                            }).css('cursor', 'pointer').click();
                            $('li:not(:has(ul))').css({
                              cursor: 'default',
                              'list-style-type': 'none',
                              'text-indent': '2em'
                            });

                            $('li:has(ul)').css({
                              cursor: 'pointer',
                              'list-style-type': 'none',
                              'background': 'url(../img/minus.png) no-repeat 0rem 0.1rem',
                              'background-size': '1rem 1rem',
                              'text-indent': '2em'
                            });
                            $('li:has(ul)').hover(function() {
                              $(this).css("color", "blue");
                            },
                            function() {
                              $(this).css("color", "black");
                            });
                          });</script>
                      </head>

                      <body>
                ''' + html
                html = html + '''
                    </body>
                    </html>
                '''
                path2save = 'tem/html/' + file_str.replace('/', '_') + '/all.html'
                if not os.path.exists('tem/html/' + file_str.replace('/', '_') + '/'):
                    os.makedirs('tem/html/' + file_str.replace('/', '_') + '/')
                with open(path2save, 'w') as file_obj:
                    print('output:', 'file:///' + path2save)
                    file_obj.writelines(html)
                    # import webbrowser
                    # webbrowser.open('file:///Users/chaoranli/PycharmProjects/test/' + path2save)
            tu.save('tem/test_unit')

            print('===========Total permission=============')
            permission_tem = ''
            for [method, permission] in self.found_permission_method:
                if isinstance(permission, list):
                    if permission[0] != None and permission[0] != 'None':
                        i_tem = permission[1].find('*')
                        if i_tem != -1:
                            output_tem = permission[1][i_tem + 1:]
                        else:
                            output_tem = permission[1]
                        print('FOUND ', method, ' ::: ', '[%s]' % permission[0], output_tem)
                elif permission:
                    permission_tem = permission_tem + ' ' + permission
                    if not permission.endswith('&&'):
                        if permission_tem != None and permission_tem != 'None':
                            i_tem = permission_tem.find('*')
                            if i_tem != -1:
                                output_tem = permission_tem[i_tem + 1:]
                            else:
                                output_tem = permission_tem
                            print('FOUND ', method, ' ::: ', '[%s]' % output_tem)
                        permission_tem = ''
                # print('FOUND ', method, ' ::: ', '[%s]' % permission[0], permission[1])





def find_fun_cpp(path, search_str):
    if not os.path.exists(path):
        return None
    try:
        file = open(path, 'r', encoding='UTF-8')  # 转换编码以实现正确输出中文格式
        lines = file.readlines()
    except Exception as e:
        file = open(path, 'r', encoding='latin1')  # 转换编码以实现正确输出中文格式
        lines = file.readlines()
    finally:
        file.close()
    analyze_this_file = False
    line_num = []
    for i, line in enumerate(lines):
        if search_str in line:
            analyze_this_file = True
            line_num.append(i + 1)
    if not analyze_this_file:
        return None
    else:
        return line_num


def test13():
    skip = True
    with open('debug_index.log', 'w') as f:
        f.write('')
    with open('jni12.0/jni.json') as file_obj:
        cpp_jni_list = json.load(file_obj)
        total = len(cpp_jni_list)
        for i, cpp_jni in enumerate(cpp_jni_list):
            print('===============each cpp_jni==================')
            print(i, '/', total)

            with open('debug_index.log', 'a') as f:
                f.write('\n%d / %d' % (i, total))

            # if 'android_util_AssetManager.cpp' not in cpp_jni['cpp']:
            #     continue

            # if 'com_android_server_vibrator_VibratorManagerService.cpp' in cpp_jni['cpp']:
            #     skip = False
            #
            # if skip:
            #     continue

            entry_funs = []
            cpp = cpp_jni['cpp']
            print(cpp)
            # if 'frameworks/base/core/jni/android_hardware_camera2_DngCreator.cpp' not in cpp:
            #     continue
            vars = cpp_jni['pairs']
            for var in vars:
                for pair in var:
                    # if 'nativeScreenshot' in pair:
                    entry_funs.append(pair[-1] + '(')
            first_lvl_funs = entry_funs
            # 暂时只测试一个fun
            entry_funs = entry_funs[:1]
            print(entry_funs)
            # exit(0)
            c_cpp_list = find_command_star_node(cpp.replace(project_path, ''), '12.0', compdb=True)
            c_cpp_list = c_cpp_list[0]

            file = project_path + c_cpp_list['file']

            pro_path = project_path
            ninja_args = c_cpp_list['arguments'][1:]
            main_file_analyser = file_analyser()
            main_file_analyser.run(file, pro_path, ninja_args, entry_funs=entry_funs, extend_analyze=False,
                                   reverse_search=False, print_all_node=False, generate_html=False)
            # break

if __name__ == '__main__':
    # 单个调试
    # test12()
    # 整体流程
    test13()
    # print('sfdsfdsfds','%80s' % 'i love python')

