#!/usr/bin/env python2

from pprint import pprint
from clang.cindex import CursorKind, Index, CompilationDatabase, TypeKind, TokenKind
from collections import defaultdict
import sys
import json
import os.path
from clang.cindex import Config
import ccsyspath
import numpy as np
# from helper_local import get_file, find_c_or_cpp, find_files, find_command, find_command_star_node, get_cpp_files_path
from helper import get_file, find_c_or_cpp, find_files, find_command, find_command_star_node, get_cpp_files_path, find_command_all_cpp
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
"""
project_path = '/hci/chaoran_data/android-10.0.0_r45/'
clang_prepath = 'prebuilts/clang/host/linux-x86/clang-r353983c1/'
clang_lib_path = project_path + clang_prepath + 'lib64/libc++.so'
clang_lib_path = '/hci/chaoran_data/android-10.0.0_r45/out/host/linux-x86/lib64/libclang_android.so'
clang_lib_path = '/hci/chaoran_data/android-10.0.0_r45/prebuilts/clang/host/linux-x86/clang-r353983c1/lib64/libclang.so.9svn'
# clang_lib_path = '/hci/chaoran_data/pythonProject/clang_api24/libclang.so'
print(clang_lib_path)
Config.set_library_file(clang_lib_path)
init_arg_config = ['-isystem/hci/chaoran_data/android-10.0.0_r45/prebuilts/clang/host/linux-x86/clang-r353983c1/lib64/clang/9.0.3/include']
# init_arg_config = ['-x', 'c++', '-isystem/hci/chaoran_data/android-10.0.0_r45/prebuilts/clang/host/linux-x86/clang-r353983c1/lib64/clang/9.0.3/include']
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
        elif c.kind == CursorKind.TRANSLATION_UNIT or c.kind ==CursorKind.IF_CONDITION:
            return ''
        else:
            res = self.fully_qualified(c.semantic_parent)
            if res != '':
                return res + '::' + c.spelling
            return c.spelling


    def fully_qualified_pretty(self, c):
        if c is None:
            return ''
        elif c.kind == CursorKind.TRANSLATION_UNIT or c.kind ==CursorKind.IF_CONDITION:
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
            self.get_all_children(child, list, level+1)

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
                self.get_all_children_ref(child, list, level+1, so_far)

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
                if found and children[i][1].kind == CursorKind.TYPE_REF and children[i][1].displayname!='':
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
                    para_index = para_index+1
                    if para_index == index:
                        return tem[1].displayname, 'local', i
                if tem[1].kind == CursorKind.MEMBER_REF_EXPR:
                    para_index = para_index+1
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
                    if children[i+2][1].kind == CursorKind.DECL_REF_EXPR:
                        para = children[i+2][1].displayname
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
                            for tem_i in range(i+1, len(children)):
                                print(children[tem_i][0], 'interface_cast|', ' ' * children[tem_i][0], children[tem_i][1].kind, children[tem_i][1].displayname, children[tem_i][1].location)
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
                        assert len(entry_fun_vs)==1, '没找到函数或函数过多 ' + tem[1].referenced.displayname
                        print('.line 170')
                        return_class = self.get_return(entry_fun_vs[0], node)
                        print(return_class)
                        # exit(2)

                        # assign_mode = False
                        if return_class!=None:
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

                if tem[1].kind == CursorKind.CALL_EXPR and 'operator->' not in tem[1].displayname and 'operator!=' not in tem[1].displayname and 'operator==' not in tem[1].displayname and 'operator=' not in tem[1].displayname and 'sp' not in tem[1].displayname and 'asBinder' not in tem[1].displayname:
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
                if tem[0] > call_mode_last_level and not children_ignore and (tem[1].kind == CursorKind.MEMBER_REF_EXPR or tem[1].kind == CursorKind.DECL_REF_EXPR):
                    # print(tem[0], 'line 322|', ' ' * tem[0], tem[1].kind, tem[1].displayname)
                    if tem[1].displayname != call_node.displayname and 'operator->' not in tem[1].displayname and \
                            children[i-1][1].kind != CursorKind.CALL_EXPR and 'operator->' not in children[i-1][1].displayname \
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
                            print(call_node_referenced.kind, call_node_referenced.displayname, call_node_referenced.location)
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
        if str =='sensorservice':
            return 'android::SensorService'
        elif str =='permission':
            return 'android::PermissionService'
        elif str =='SurfaceFlinger':
            # SurfaceFlinger.h
            self.extend_h_analysis('frameworks/SurfaceFlinger_hwc1.cpp', '10.0', True, project_path, fuzzy=True)
            return 'android::SurfaceFlinger'
        else:
            return str

    def getService(self, index, children):
        print('*** getService ***')
        var = None
        start2find_var = False
        print(children[index][1].location)
        for i in range(index, index+30):
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
            if not ignore and children[i][1].kind == CursorKind.DECL_REF_EXPR and children[i][1].displayname != 'getService':
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
                for tem_i in range(i+1, len(children)):
                    print('getService|', ' ' * children[tem_i][0], children[tem_i][1].kind, children[tem_i][1].displayname)
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
                    for tem_i in range(i-1, 0, -1):
                        if children[tem_i][1].kind == CursorKind.CALL_EXPR and children[tem_i][1].displayname == 'operator=':
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
                if tem[1].kind == CursorKind.CALL_EXPR and declare_mode and tem[1].displayname!='' and tem[1].displayname!='sp':
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
                    if(tem[1].displayname != 'GetLongField'):
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
                    print(children[i+1][1].kind)
                    if children[i+1][1].kind == CursorKind.TYPE_REF:
                        assert children[i+1][1].displayname.startswith('class ')
                        return_class = children[i+1][1].displayname[6:]
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
                    return_class =self.find_var(tem[1].displayname, tem[1].location.file.name)
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
                    return_class = self.get_return(tem[1].referenced, parent_node, level=tem[0]+1)
                    print('\n*** END END END analyze_fun ***')
                    if return_class!=None:
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
            if tem[1].kind == CursorKind.CALL_EXPR and tem[1].referenced is not None and tem[1].referenced.displayname == current.displayname:
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
                if tem[1].displayname !='interface_cast':
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
        if scope =='global':
            print('.line 432')
            return_class = self.find_var(r, file)
        elif scope =='local':
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
            return None,None,None
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
            c_cpp_list = find_command(tem_head, version_prefix='10.0', compdb=True, project_path=project_path)
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
                if not('MediaClock.cpp' in next_file or 'AString.cpp' in next_file or 'MediaSync.cpp' in next_file or 'MediaBuffer.cpp' in next_file):
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
                if ('checkCallingPermission' in node.displayname or 'checkPermission' in node.displayname) and node.kind == CursorKind.CALL_EXPR:
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

    def show_info(self, node, cur_fun=None, depth=0, print_node=False, if_stmt=None, last_node=None, case_identifier=[], case_mode=[False], case_level=[10e10]):
        # and node.kind == CursorKind.STRING_LITERAL
        # if node.location.file and self.print_all_node and self.pro_path in node.location.file.name and self.is_template(node):
        #     t = node.type
        #     print(t.kind, t.spelling, t.get_num_template_arguments())
        #     print(t.get_template_argument_type(0).spelling)

        # if 'signRSA' in node.displayname:
        #     print_node = True
        #     print('------show_info display nodes------')
        # if 'JDrm' in node.displayname:
        #     print_node = True
        #     print('------show_info display nodes------')
        fun_str = self.fully_qualified_pretty(node)
        # if 'DrmHal::openSession(' in fun_str:
        #     print(node.kind)
        #     print(fun_str)
        #     o=0
        # if 'MediaRecorder::setCamera(' in fun_str:
        #     print(node.kind)
        #     print(fun_str)
        #     o=0
        # if 'captureScreen(' in fun_str:
        #     print('----1----')
        #     print(node.kind, fun_str, node.location)
        #     print('----1----')

        # if 'SensorManager::sensorManagerDied()' in fun_str:
        #     print_node = True
        #     print('\n------show_info display nodes------')

        # if 'RadioService::Module::addClient(' in fun_str:
        #     print_node = True
        #     print('\n------show_info display nodes------')
            # print(node.kind)
            # print(fun_str)
            # print(self.fully_qualified_pretty(node))
            # print(self.fully_qualified(node))
            # print(self.fully_qualified(node.semantic_parent))
            # exit(7)
        # if '::NativeRemoteDisplay(' in fun_str:
        #     print(node.kind)
        #     print(fun_str)
        #     print(self.fully_qualified_pretty(node))
        #     print(self.fully_qualified(node))
        #     print(self.fully_qualified(node.semantic_parent))

        # if 'NativeRemoteDisplay' in fun_str:
        #     print_node = True
        #     print('\n------show_info display nodes------')

        # if 'Radio::attach(' in fun_str:
        #     print_node = True
        #     print('\n------show_info display nodes------')

        # if 'SensorManager::configureDirectChannel(' in fun_str:
        #     print_node = True
        #     print('\n------show_info display nodes------')

        # if '::find' in fun_str:
        #     print('\n------show_info display nodes------')
        #     print(fun_str)

        # if 'SensorService::createSensorDirectConnection(' in fun_str:
        #     print(node.kind)
        #     print(fun_str)
        #     print(self.fully_qualified_pretty(node))
        #     print(self.fully_qualified(node))
        #     print(self.fully_qualified(node.semantic_parent))

        # if 'SensorService::setOperationParameter(' in fun_str:
        #     print_node = True
        #     print('\n------show_info display nodes------')

        # if 'CameraService::validateClientPermissionsLocked(' in fun_str:
        #     print_node = True
        #     print('\n\n------show_info display nodes------')
        #     print(node.location)
        
        if 'CheckTransactCodeCredentials' in fun_str:
            print_node = True
            print('\n\n------show_info display nodes------')
            print('\n\n------CheckTransactCodeCredentials(------')
            print('\n\n------show_info display nodes------')
            print(node.location)

        # debug 显示制定node
        if node.location.file and (self.print_all_node or print_node) and self.pro_path in node.location.file.name:
            print('\n1358|%2d' % depth + ' ' * depth, node.kind, node.spelling, '|current case_identifier:', case_identifier, end='')

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

        if node.kind == CursorKind.IF_STMT:
            if_stmt = node

        # path start
        if node.kind == CursorKind.FUNCTION_TEMPLATE or node.kind == CursorKind.CONSTRUCTOR:
            # if not is_excluded(node, xfiles, xprefs):
                cur_fun = node
                fun_str = self.fully_qualified_pretty(cur_fun)
                # 没有或者location在cpp中
                if fun_str not in self.FULLNAMES.keys() or cur_fun.location.file.name.endswith('.cpp'):
                    # ::RadioService::attach
                    # ::MediaRecorderClient::MediaRecorderClient(
                    # if '::RadioService::attach(' in fun_str:
                    #     print('添加', fun_str, cur_fun.location.file.name)
                    self.FULLNAMES[fun_str] = cur_fun
                # if self.print_all_node and self.pro_path in cur_fun.location.file.name:
                #     print('%2d' % depth + ' ' * depth, '|||' + fun_str)

        if node.kind == CursorKind.CXX_METHOD or \
                node.kind == CursorKind.FUNCTION_DECL:
            # if not is_excluded(node, xfiles, xprefs):
                cur_fun = node
                fun_str = self.fully_qualified_pretty(cur_fun)
                if fun_str not in self.FULLNAMES.keys() or cur_fun.location.file.name.endswith('.cpp'):
                    # if '::RadioService::attach(' in fun_str:
                    #     print('添加', fun_str, cur_fun.location.file.name)
                    #     print('fun_str not in self.FULLNAMES.keys()', fun_str not in self.FULLNAMES.keys())
                    #     print('cur_fun.location.file.name.endswith(\'.cpp\')', cur_fun.location.file.name.endswith('.cpp'))
                    self.FULLNAMES[fun_str] = cur_fun
                # if self.print_all_node and self.pro_path in cur_fun.location.file.name:
                #     print('%2d' % depth + ' ' * depth, '|||' + fun_str)
        # path end

        # 在某函数中发现了调用，那么把这个函数->调用函数的mapping，加入call graph
        if node.kind == CursorKind.CALL_EXPR:
            # if node.referenced and not is_excluded(node.referenced, xfiles, xprefs):
            # if
            # print(node.referenced==None)

            if node.referenced:
                fun_str = self.fully_qualified_pretty(cur_fun)
                if cur_fun is not None and self.pro_path in cur_fun.location.file.name:
                    # self.CALLGRAPH[fun_str].append(node.referenced)
                    # 在一个函数(fun_str)中找到了函数调用(node)，加入call graph
                    self.CALLGRAPH[fun_str].append(node)
                    # 打印的是起点/父节点
                    # if self.print_all_node:
                    #     print('%2d' % depth + ' ' * depth, '|||' + self.fully_qualified_pretty(cur_fun))

        # if node.location.file and self.pro_path in node.location.file.name:
            # ============== IF START TEST================
            # if node.kind == CursorKind.IF_STMT:
            #     ooo = node.get_tokens()
            #     for tem in ooo:
            #         print('/', tem.kind, tem.spelling, end=' ')
            #     binop = self._get_binop_operator(node)
            #     print('\n***', binop, '***')

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
                condition = binop + ' ' +left
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
            # if (node.kind == CursorKind.DECL_REF_EXPR and type.kind == TypeKind.DEPENDENT):
            #     print('fdsafdsafdsafdsafsda')
            self.show_info(c, cur_fun, depth=depth+1, print_node=print_node, if_stmt=if_stmt, last_node=node, case_identifier=case_identifier,case_mode=case_mode,case_level=case_level)


    def pretty_print(self, n):
        v = ''
        # if n.is_virtual_method():
        #     v = ' virtual'
        # if n.is_pure_virtual_method():
        #     v = ' = 0'
        if self.show_loc:
            return self.fully_qualified_pretty(n) + v + "|" + str(n.location)
        else:
            return self.fully_qualified_pretty(n) + v

    # def search_fun(self, fun_name):
    #     for k, v in self.FULLNAMES.items():
    #         if fun_name in k:
    #                 print('Found fun -> ' + k)
    #                 yield k
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
        full_fun_name = re.sub('\(.+?\)',r'', fun_name)
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
        full_fun_name = re.sub('\(.+?\)',r'', fun_name)
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

        #get_tokens
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
                    self.print_childrens(n, service_names, depth=depth+1)

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
            tem = tem.replace(temCOMPARISION_OPERATORS, temCOMPARISION_OPERATORS+'@@')
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
                    ori_tem_only_fun[k] = re.sub(r'[a-zA-Z0-9_]+ \(.+\)', '('+v+')', ori_tem_only_fun[k])
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
                    if '/'+f.replace('.cpp', '.h') in include_path:
                        h_no_I = include_path
        print(h_no_I)
        # exit(0)
        return h_no_I
    
    def extract_onTransact(self, node, identifier, conditions, depth=0, case_mode=False, case_level = 10e10):
        if node is not None and node.location.file is not None and self.pro_path in node.location.file.name:
            for n in node.get_children():
                print('1818| %2d' % depth + ' ' * depth, n.kind, n.spelling, end=' | ')
                print()
                print('case_mode and depth > case_level and n.kind == CursorKind.DECL_REF_EXPR and n.spelling == identifier', case_mode and depth > case_level and n.kind == CursorKind.DECL_REF_EXPR and n.spelling == identifier)
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
                    self.extract_onTransact(n, identifier, conditions, case_mode=case_mode, case_level=case_level, depth=depth + 1)
        
    def onTransact(self, identifier, onTransact_class):
        print(identifier)
        print(onTransact_class)
        k_list, v_list = self.search_fun_list_full(onTransact_class+'::onTransact(')
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
                if(f.location.file is not None and self.pro_path in f.location.file.name):
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
                                speci_conds_tem = speci_conds_tem.replace(' PermissionCache :: ','')
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
                        self.print_childrens(node, permission_strs, current_depth+2)
                        if DEBUG:
                            print('***')
                    elif 'getService' in log:
                        if DEBUG:
                            print('%2d' % current_depth, ' ' * (depth + 1) + log)
                        if DEBUG:
                            print('***')
                        self.print_childrens(node, permission_strs, current_depth+2)
                        if DEBUG:
                            print('***')
                    elif 'writeInterfaceToken' in log:
                        if DEBUG:
                            print('%2d' % current_depth, ' ' * (depth + 1) + log)
                            print('***')
                        self.print_childrens(node, permission_strs, current_depth+2)
                        if DEBUG:
                            print('***')
                    else:
                        if DEBUG:
                            print('%2d' % current_depth, ' ' * (depth + 1) + log)

                    self.html_log.append([depth, log])

                    if f in so_far:
                        continue
                    so_far.append(f)

                    # link for AIDL============
                    # r1 = re.findall(r'I.+?Service::', log)
                    # r2 = re.findall(r'IRadio::', log)
                    # if len(r1) > 0:
                    #     next_fun_name = log.replace(r1[0], r1[0][1:])
                    #     print('%2d' % current_depth, ' ' * (depth + 1) + next_fun_name, '%%% AIDL JUMP')
                    #     self.print_calls(next_fun_name, so_far, self.pretty_print(f), permission_strs,
                    #                      depth + 1)
                    # elif len(r2) > 0:
                    #     # RadioService.cpp  attach 最后一个参数赋值时返回类型
                    #     next_fun_name = log.replace(r2[0], 'RadioService::ModuleClient::')
                    #     print('%2d' % current_depth, ' ' * (depth + 1) + next_fun_name, '%%% AIDL JUMP')
                    #     self.print_calls(next_fun_name, so_far, self.pretty_print(f), permission_strs,
                    #                      depth + 1)

                    # ::IDrm:: YES  ::IPCThreadState:: NO
                    r_final = re.findall(r'::I[A-Z][a-z].+?::', log)
                    print(log)

                    if len(r_final) > 0 and self.has_no_ignore_fun(self.fully_qualified_pretty(last_node)) and self.has_no_ignore_fun(self.fully_qualified_pretty(f)):
                        print('\n\n###### binder start ######')
                        # if 'frameworks/native/lib' in last_node.location.file.name:
                        #     print('*** END OF CALL because go to native lib')
                        #     continue
                        print('original FROM:', self.fully_qualified_pretty(last_node), last_node.location)
                        print(last_node.location.file.name)
                        print('last_node.location.file.name.endswith(\'.h\')', last_node.location.file.name.endswith('.h'))
                        # 如果函数是从.h来的，需要检查有无同名cpp文件，同名cpp文件中是否有这个函数，有的话以cpp中分析为准
                        if last_node.location.file.name.endswith('.h'):
                            print('方法为 .h中的方法，将其替换为cpp中的方法')
                            k_list, v_list = self.search_fun_list_full(self.fully_qualified_pretty(last_node))
                            for tem_v_list in v_list:
                                print(tem_v_list.location.file.name)
                                if tem_v_list.location.file.name.endswith('.cpp'):
                                    print('last_node 替换为 cpp中的方法：', tem_v_list.kind, self.fully_qualified_pretty(tem_v_list), tem_v_list.location.file.name)
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
                            self.extend_h_analysis(h_no_I, '10.0', True, project_path)
                            print('.line 1903')
                            # exit(0)
                            
                        if self.has_ignore_fun_Ixx(method_full) and len(tema)>0:
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
                            assert len(v_list)==1, '没有找到或找到多个方法，请检查'
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
                            if 'ISurfaceComposer::captureScreen' in self.fully_qualified_pretty(f) and return_class !='no_caller':
                                print('解析', f.location.file.name)
                                self.extend_h_analysis(f.location.file.name, '10.0', True, project_path, fuzzy=True)
                                # exit(8)
                                # 找到Ixxx::xx中的transact 第一个参数的变量名
                                # method_full = method_full.replace('android::ISurfaceComposer::', '')
                                # print(method_full)
                                Ixx_method_cpp_k = None
                                Ixx_method_cpp_v = None
                                function_transact = self.fully_qualified_pretty(f)
                                print('line2136', function_transact)
                                # function_transact = function_transact.split('(')[0].split('::')[-1]
                                function_transact = function_transact.split('(')[0].split('::')[-1] + '(' + function_transact.split('(')[1]
                                print('现在开始搜索', function_transact)
                                k_list, v_list = self.search_fun_list_full(function_transact + '(')
                                for i, tem_v_list in enumerate(v_list):
                                    print(tem_v_list.location.file.name)
                                    if tem_v_list.location.file.name.endswith('.cpp') and 'BpSurfaceComposer::captureScreen(' in k_list[i]:
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

    def extend_h_analysis(self, file, version_prefix, compdb=False, project_path='/Volumes/android/android-8.0.0_r34/', fuzzy=False):

        if fuzzy:
            c_cpp_lists = [find_command(file, version_prefix=version_prefix, compdb=compdb, project_path=project_path)]
        else:
            c_cpp_lists = find_command_all_cpp(file, version_prefix=version_prefix, compdb=compdb, project_path=project_path)
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
            print(str(tem, encoding = "utf-8"), path)
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
            '/hci/chaoran_data/android-10.0.0_r45/prebuilts/clang/host/linux-x86/clang-2690385/bin/clang++')
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
        ast_path = 'ast10.0/' + file.replace('/', '_') + '.ast'
        tu = None

        ninja_args = ninja_args[:-1]
        # print(ninja_args)
        # exit(2)

        if os.path.exists(ast_path):
            tu = index.read(ast_path)
        else:
            tu = index.parse(file, ninja_args)

        # args = ninja_args

        # command = '/Volumes/android/android-8.0.0_r34/prebuilts/clang/host/darwin-x86/clang-4053586/bin/clang++ -v '
        # for i in range(len(ninja_args)):
        #     command = command+ ninja_args[i] + ' '
        # command = command.replace(',', '').replace('-Wa--noexecstack','-Wa,--noexecstack').replace(r'-DLOG_TAG=\\"libagl\\"', r'"-DLOG_TAG=\"libagl\""') + ' ' + file
        # print(command+'++++++++++')

        # b = os.popen(command)
        # text2 = b.read()
        # print(text2)
        # b.close()

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
        self.show_info(tu.cursor)

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
    def extract_jni_fun(self, file_str, pro_path,  ninja_args, show_loc=False, print_all_node=True):

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

    def run(self, file_str, pro_path,  ninja_args, entry_funs=None, IS_AOSP=True, extend_analyze=True, show_loc=False, print_all_node=False, generate_html=False, anti_search=False, only_preprocess = False):
        print('--- run ---')
        self.show_loc = show_loc
        self.print_all_node = print_all_node
        index = Index.create(1)
        self.index = index
        file = self.check_file(file_str)
        self.pro_path = pro_path

        tu = None
        args = None

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

        for tem in tu.get_includes(0):
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
                        not_sys_include_paths.append('frameworks/av/media/utils/ServiceUtilities.cpp')
                        not_sys_include_paths.append('frameworks/av/services/audiopolicy/service/AudioPolicyInterfaceImpl.cpp')

                        # not_sys_include_paths.append('frameworks/av/include/media/IMediaPlayerService.h')
                        # not_sys_include_paths.append('frameworks/av/include/media/IMediaDeathNotifier.h')
                        # eee = include_path.replace(r[0], 'MediaPlayerService.h')
                        # not_sys_include_paths.append(eee)
                        # not_sys_include_paths.append('frameworks/av/services/mediadrm/MediaDrmService.cpp')
                        not_sys_include_paths.append('frameworks/native/services/surfaceflinger/SurfaceFlinger.cpp')
            else:
                if self.pro_path in include_path:
                    not_sys_include_paths.append(include_path)

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
                i = i+1
                print('***************')
                print('Loading CFG ... ', i, '/', len(not_sys_include_paths))

                # print("*.h:", tem)
                if IS_AOSP:
                    # c_cpp_list = find_command(tem)
                    c_cpp_list = find_command(tem, version_prefix='10.0', compdb=True, project_path=project_path)
                    # for i_c_cpp_lists, c_cpp_list in enumerate(c_cpp_lists):
                    #     print('.line 2293 ', i_c_cpp_lists, '/', len(c_cpp_lists))
                    if c_cpp_list is not None and project_path + c_cpp_list['file'] not in self.analyzed_cpp:
                        # next_file = '/Volumes/android/android-7.0.0_r33/' + c_cpp_list['source']
                        next_file = project_path + c_cpp_list['file']
                        self.analyzed_cpp.add(next_file)
                        print('.line 2297', next_file)
                        '''
                                /Volumes/android/android-7.0.0_r33/frameworks/av/media/libstagefright/MediaClock.cpp:93:5: error: use of undeclared identifier 'GE'
                                /Volumes/android/android-7.0.0_r33/frameworks/av/media/libstagefright/foundation/AString.cpp:170:5: error: use of undeclared identifier 'LT'
                                /Volumes/android/android-7.0.0_r33/frameworks/av/media/libstagefright/MediaSync.cpp:502:9: error: use of undeclared identifier 'EQ'         
                                /Volumes/android/android-7.0.0_r33/frameworks/av/media/libstagefright/foundation/MediaBuffer.cpp:109:9: error: use of undeclared identifier 'EQ'
                                /hci/chaoran_data/android-10.0.0_r45/frameworks/native/libs/ui/Region.cpp:560:24: error: result of comparison 'const int32_t' (aka 'const int') > 2147483647 is always false [-Wtautological-type-limit-compare]

                        '''
                        if 'MediaClock.cpp' in next_file or 'AString.cpp' in next_file or 'MediaSync.cpp' in next_file or 'MediaBuffer.cpp' in next_file or 'Region.cpp' in next_file:
                            print('pass: ', next_file)
                            continue
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
                else:
                    cpp = tem.replace('.h', '.cpp')
                    c = tem.replace('.h', '.c')

                    if (os.path.exists(cpp)):
                        print("*.cpp:", cpp)
                        if cpp != file_str:
                            self.load_cfg_normal(index, cpp, ninja_args)
                        else:
                            print('skip to analyze itself')
                    elif (os.path.exists(c)):
                        print("*.c:", c)
                        if c != file_str:
                            self.load_cfg_normal(index, c, ninja_args)
                        else:
                            print('skip to analyze itself')
                    else:
                        print(tem, '*.h has implement or *.cpp name is different')
                # if len(c_cpp_list) == 0:
                #     print(tem, '*.h has implement or *.cpp name is different')
                # elif len(c_cpp_list) == 1:

                # else:
                #     raise Exception('multiple c/cpp files for', tem, c_cpp_list)

        # if('GetDrm' in node.displayname and str(node.kind)=='CursorKind.CALL_EXPR'):
        #     if node.referenced is not None:
        #         node = node.referenced
        #         return_class = self.get_return(node)
        #         print(return_class[0], return_class[1])
        #         if return_class[0] == CursorKind.MEMBER_REF_EXPR:
        #             self.find_var(return_class[1])

        if anti_search == False:
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
                            html = html + '<ul><li>' + entry_fun.replace('>','&gt;').replace('<','&lt;')
                            last_depth = -1
                            for tem in self.html_log:
                                depth = tem[0]
                                o = tem[1].replace('>','&gt;').replace('<','&lt;')
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
                path2save = 'tem/html/' + file_str.replace('/','_') + '/all.html'
                if not os.path.exists('tem/html/' + file_str.replace('/','_')+'/'):
                    os.makedirs('tem/html/' + file_str.replace('/','_')+'/')
                with open(path2save, 'w') as file_obj:
                    print('output:', 'file:///Users/chaoranli/PycharmProjects/test/' + path2save)
                    file_obj.writelines(html)
                    import webbrowser
                    webbrowser.open('file:///Users/chaoranli/PycharmProjects/test/' + path2save)
            tu.save('tem/test_unit')

            print('===========Total permission=============')
            permission_tem = ''
            for [method, permission] in self.found_permission_method:
                if isinstance(permission, list):
                    if permission[0] != None and permission[0] != 'None':
                        i_tem = permission[1].find('*')
                        if i_tem!=-1:
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


        # 逆向搜索
        else:
            print('====逆向搜索 结果====')
            anti_list = []
            for entry_fun_part in entry_funs:
                entry_fun_list = self.search_fun(entry_fun_part)
                for entry_fun in entry_fun_list:
                    if self.get_node_from_child(entry_fun) is not None:
                        print(entry_fun)

                        self.html_log = []
                        permission_strs = []
                        graphs = []
                        self.get_print_ndoe(entry_fun, list(), graphs)

                        for i in range(len(graphs)):
                            graphs[i].append(entry_fun)

                        print(graphs)
                        anti_list.append(graphs)
            return anti_list

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
            line_num.append(i+1)
    if not analyze_this_file:
        return None
    else:
        return line_num



def test0():

    analyser = file_analyser()
    # analyze cpp
    file = '/Users/chaoranli/CLionProjects/untitled/main.cpp'

    pro_path = '/Users/chaoranli/CLionProjects/untitled/'
    args = '-x c++'.split()
    entry_funs = ['main()']

    analyser.run(file, pro_path, args, entry_funs, IS_AOSP=False, extend_analyze=True, print_all_node=True, show_loc=False, generate_html=False)
    # analyser.save()

def test00():

    analyser = file_analyser()
    # analyze cpp
    file = '/Users/chaoranli/CLionProjects/untitled/main2.cpp'

    pro_path = '/Users/chaoranli/CLionProjects/untitled/'
    args = '-x c++'.split()
    entry_funs = ['main()']

    analyser.run(file, pro_path, args, entry_funs, IS_AOSP=False, extend_analyze=True, print_all_node=True, show_loc=True, generate_html=False)
    if False:
        analyser.print_calls('', list(), None)


def test1():
    # out/build-aosp_arm64.ninja
    main_file_analyser = file_analyser()
    # analyze cpp
    file = '/Volumes/android/android-8.0.0_r34/frameworks/av/services/camera/libcameraservice/api2/CameraDeviceClient.cpp'

    pro_path = '/Volumes/android/android-8.0.0_r34/'
    args = ['-isystem/Volumes/android/android-8.0.0_r34/prebuilts/clang/host/darwin-x86/clang-4053586/lib64/clang/5.0.300080/include']
    ninja_args = '-I system/media/private/camera/include -I frameworks/native/include/media/openmax -I frameworks/av/services/camera/libcameraservice -I out/target/product/generic_arm64/obj/SHARED_LIBRARIES/libcameraservice_intermediates -I out/target/product/generic_arm64/gen/SHARED_LIBRARIES/libcameraservice_intermediates -I libnativehelper/include/nativehelper -Iframeworks/native/libs/ui/include -Iframeworks/native/libs/nativebase/include -Ihardware/libhardware/include -Isystem/media/audio/include -Isystem/core/libcutils/include -Isystem/core/libsystem/include -Iframeworks/native/libs/arect/include -Iframeworks/native/libs/math/include -Isystem/core/liblog/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iframeworks/native/libs/binder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libcutils/include -Iframeworks/av/media/libmedia/aidl -Iframeworks/av/media/libmedia/include -Iframeworks/av/media/libmedia/include -Isystem/libhidl/transport/token/1.0/utils/include -Iframeworks/native/libs/binder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/hardware/interfaces/graphics/common/1.0/android.hardware.graphics.common@1.0_genc++_headers/gen -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/hardware/interfaces/graphics/common/1.0/android.hardware.graphics.common@1.0_genc++_headers/gen -Iout/soong/.intermediates/hardware/interfaces/media/1.0/android.hardware.media@1.0_genc++_headers/gen -Iout/soong/.intermediates/hardware/interfaces/graphics/bufferqueue/1.0/android.hardware.graphics.bufferqueue@1.0_genc++_headers/gen -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/hardware/interfaces/graphics/common/1.0/android.hardware.graphics.common@1.0_genc++_headers/gen -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/hardware/interfaces/graphics/common/1.0/android.hardware.graphics.common@1.0_genc++_headers/gen -Iout/soong/.intermediates/hardware/interfaces/media/1.0/android.hardware.media@1.0_genc++_headers/gen -Iout/soong/.intermediates/hardware/interfaces/media/omx/1.0/android.hardware.media.omx@1.0_genc++_headers/gen -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/hardware/interfaces/graphics/common/1.0/android.hardware.graphics.common@1.0_genc++_headers/gen -Iout/soong/.intermediates/hardware/interfaces/media/1.0/android.hardware.media@1.0_genc++_headers/gen -Iframeworks/native/libs/ui/include -Iframeworks/native/libs/nativebase/include -Ihardware/libhardware/include -Isystem/media/audio/include -Isystem/core/libcutils/include -Isystem/core/libsystem/include -Iframeworks/native/libs/arect/include -Iframeworks/native/libs/math/include -Iframeworks/native/libs/binder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iexternal/sonivox/arm-wt-22k/include -Iexternal/icu/icu4c/source/common -Iexternal/icu/icu4c/source/i18n -Iframeworks/av/media/libstagefright/foundation/include -Iframeworks/native/libs/binder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iframeworks/native/libs/ui/include -Iframeworks/native/libs/nativebase/include -Ihardware/libhardware/include -Isystem/media/audio/include -Isystem/core/libcutils/include -Isystem/core/libsystem/include -Iframeworks/native/libs/arect/include -Iframeworks/native/libs/math/include -Iout/soong/.intermediates/frameworks/av/drm/libmediadrm/libmediadrm/android_arm64_armv8-a_shared_core/gen/aidl -Isystem/libhidl/libhidlmemory/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/memory/1.0/android.hidl.memory@1.0_genc++_headers/gen -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/memory/1.0/android.hidl.memory@1.0_genc++_headers/gen -Iout/soong/.intermediates/frameworks/av/media/libmedia/libmedia/android_arm64_armv8-a_shared_core/gen/aidl -Iframeworks/av/media/utils/include -Iframeworks/av/camera/include -Iframeworks/av/camera/include/camera -Isystem/media/camera/include -Iout/soong/.intermediates/frameworks/av/camera/libcamera_client/android_arm64_armv8-a_shared_core/gen/aidl -Isystem/media/camera/include -Isystem/libfmq/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iframeworks/native/libs/gui/include -Iframeworks/native/libs/gui/include -Iframeworks/native/libs/binder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iframeworks/native/opengl/libs/EGL/include -Iframeworks/native/opengl/include -Iframeworks/native/libs/ui/include -Iframeworks/native/libs/nativebase/include -Ihardware/libhardware/include -Isystem/media/audio/include -Isystem/core/libcutils/include -Isystem/core/libsystem/include -Iframeworks/native/libs/arect/include -Iframeworks/native/libs/math/include -Iframeworks/native/libs/nativewindow/include -Iframeworks/native/libs/nativebase/include -Iframeworks/native/libs/arect/include -Isystem/libhidl/transport/token/1.0/utils/include -Iframeworks/native/libs/binder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/hardware/interfaces/graphics/common/1.0/android.hardware.graphics.common@1.0_genc++_headers/gen -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/hardware/interfaces/graphics/common/1.0/android.hardware.graphics.common@1.0_genc++_headers/gen -Iout/soong/.intermediates/hardware/interfaces/media/1.0/android.hardware.media@1.0_genc++_headers/gen -Iout/soong/.intermediates/hardware/interfaces/graphics/bufferqueue/1.0/android.hardware.graphics.bufferqueue@1.0_genc++_headers/gen -Ihardware/libhardware/include -Isystem/media/audio/include -Isystem/core/libcutils/include -Isystem/core/libsystem/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Iexternal/libjpeg-turbo -Isystem/core/libmemunreachable/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/hardware/interfaces/camera/common/1.0/android.hardware.camera.common@1.0_genc++_headers/gen -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/hardware/interfaces/camera/common/1.0/android.hardware.camera.common@1.0_genc++_headers/gen -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/hardware/interfaces/camera/common/1.0/android.hardware.camera.common@1.0_genc++_headers/gen -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/hardware/interfaces/graphics/common/1.0/android.hardware.graphics.common@1.0_genc++_headers/gen -Iout/soong/.intermediates/hardware/interfaces/camera/device/1.0/android.hardware.camera.device@1.0_genc++_headers/gen -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/hardware/interfaces/camera/common/1.0/android.hardware.camera.common@1.0_genc++_headers/gen -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/hardware/interfaces/graphics/common/1.0/android.hardware.graphics.common@1.0_genc++_headers/gen -Iout/soong/.intermediates/hardware/interfaces/camera/device/3.2/android.hardware.camera.device@3.2_genc++_headers/gen -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/hardware/interfaces/graphics/common/1.0/android.hardware.graphics.common@1.0_genc++_headers/gen -Iout/soong/.intermediates/hardware/interfaces/camera/provider/2.4/android.hardware.camera.provider@2.4_genc++_headers/gen -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/hardware/interfaces/camera/common/1.0/android.hardware.camera.common@1.0_genc++_headers/gen -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/hardware/interfaces/graphics/common/1.0/android.hardware.graphics.common@1.0_genc++_headers/gen -Iout/soong/.intermediates/hardware/interfaces/camera/device/1.0/android.hardware.camera.device@1.0_genc++_headers/gen -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/hardware/interfaces/camera/common/1.0/android.hardware.camera.common@1.0_genc++_headers/gen -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/transport/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/libhidl/base/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Isystem/core/base/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Isystem/core/libcutils/include -Iout/soong/.intermediates/hardware/interfaces/graphics/common/1.0/android.hardware.graphics.common@1.0_genc++_headers/gen -Iout/soong/.intermediates/hardware/interfaces/camera/device/3.2/android.hardware.camera.device@3.2_genc++_headers/gen -Iexternal/libcxx/include -Iexternal/libcxxabi/include -I system/core/include -I system/media/audio/include -I hardware/libhardware/include -I hardware/libhardware_legacy/include -I hardware/ril/include -I libnativehelper/include -I frameworks/native/include -I frameworks/native/opengl/include -I frameworks/av/include -isystem out/target/product/generic_arm64/obj/include -isystem bionic/libc/arch-arm64/include -isystem bionic/libc/include -isystem bionic/libc/kernel/uapi -isystem bionic/libc/kernel/uapi/asm-arm64 -isystem bionic/libc/kernel/android/scsi -isystem bionic/libc/kernel/android/uapi -c -fno-exceptions -Wno-multichar -fno-strict-aliasing -fstack-protector-strong -ffunction-sections -fdata-sections -funwind-tables -Wa,--noexecstack -Werror=format-security -D_FORTIFY_SOURCE=2 -fno-short-enums -no-canonical-prefixes -Werror=pointer-to-int-cast -Werror=int-to-pointer-cast -Werror=implicit-function-declaration -DNDEBUG -O2 -g -Wstrict-aliasing=2 -DANDROID -fmessage-length=0 -W -Wall -Wno-unused -Winit-self -Wpointer-arith -DNDEBUG -UDEBUG -D__compiler_offsetof=__builtin_offsetof -Werror=int-conversion -Wno-reserved-id-macro -Wno-format-pedantic -Wno-unused-command-line-argument -fcolor-diagnostics -Wno-expansion-to-defined -Werror=return-type -Werror=non-virtual-dtor -Werror=address -Werror=sequence-point -Werror=date-time -nostdlibinc -target aarch64-linux-android -Bprebuilts/gcc/darwin-x86/aarch64/aarch64-linux-android-4.9/aarch64-linux-android/bin -Wsign-promo -Wno-inconsistent-missing-override -Wno-null-dereference -D_LIBCPP_ENABLE_THREAD_SAFETY_ANNOTATIONS -Wno-thread-safety-negative -fvisibility-inlines-hidden -std=gnu++14 -fno-rtti -Wall -Wextra -Werror -fPIC -D_USING_LIBCXX -Wno-error=unused-lambda-capture -DANDROID_STRICT -Werror=int-to-pointer-cast -Werror=pointer-to-int-cast -Werror=address-of-temporary -Werror=return-type -MD -MF out/target/product/generic_arm64/obj/SHARED_LIBRARIES/libcameraservice_intermediates/api2/CameraDeviceClient222.d -o out/target/product/generic_arm64/obj/SHARED_LIBRARIES/libcameraservice_intermediates/api2/CameraDeviceClient222.o'.split()

    entry_funs = ['android::CameraDeviceClient::submitRequest(const hardware::camera2::CaptureRequest &, bool, hardware::camera2::utils::SubmitInfo *)']

    main_file_analyser.run(file, pro_path, ninja_args, entry_funs, extend_analyze=False, print_all_node=False, generate_html=False)

def test2():
    # out/soong/build.ninja
    main_file_analyser = file_analyser()
    # analyze cpp
    file = '/Volumes/android/android-8.0.0_r34/frameworks/base/core/jni/android_hardware_Camera.cpp'

    pro_path = '/Volumes/android/android-8.0.0_r34/'
    init_args = ['-isystem/Volumes/android/android-8.0.0_r34/prebuilts/clang/host/darwin-x86/clang-4053586/lib64/clang/5.0.300080/include']
    ninja_args = '-c -Iframeworks/base/core/jni -Iframeworks/base/core/jni/include -Iframeworks/base/core/jni/android/graphics -Ibionic/libc/private -Iexternal/skia/include/private -Iexternal/skia/src/codec -Iexternal/skia/src/core -Iexternal/skia/src/effects -Iexternal/skia/src/image -Iexternal/skia/src/images -Iframeworks/base/media/jni -Ilibcore/include -Isystem/media/camera/include -Isystem/media/private/camera/include -Iframeworks/base/core/jni  -fno-exceptions -Wno-multichar -fno-strict-aliasing -fstack-protector-strong -ffunction-sections -fdata-sections -funwind-tables -Wa,--noexecstack -Werror=format-security -D_FORTIFY_SOURCE=2 -fno-short-enums -no-canonical-prefixes -Werror=pointer-to-int-cast -Werror=int-to-pointer-cast -Werror=implicit-function-declaration -DNDEBUG -O2 -g -Wstrict-aliasing=2 -DANDROID -fmessage-length=0 -W -Wall -Wno-unused -Winit-self -Wpointer-arith -DNDEBUG -UDEBUG -D__compiler_offsetof=__builtin_offsetof -Werror=int-conversion -Wno-reserved-id-macro -Wno-format-pedantic -Wno-unused-command-line-argument -fcolor-diagnostics -Wno-expansion-to-defined -fdebug-prefix-map=$$PWD/= -Werror=return-type -Werror=non-virtual-dtor -Werror=address -Werror=sequence-point -Werror=date-time -nostdlibinc  -Iexternal/giflib -Ibionic/libc/seccomp/include -Iexternal/selinux/libselinux/include -Iexternal/pcre/include -Isystem/core/libpackagelistparser/include -Iexternal/boringssl/src/include -Isystem/core/libgrallocusage/include -Isystem/core/libmemtrack/include -Iframeworks/base/libs/androidfw/include -Isystem/core/libappfuse/include -Isystem/core/base/include -Ilibnativehelper/include -Ilibnativehelper/platform_include -Isystem/core/liblog/include -Isystem/core/libcutils/include -Isystem/core/debuggerd/include -Isystem/core/debuggerd/common/include -Isystem/core/libutils/include -Isystem/core/libbacktrace/include -Isystem/core/libsystem/include -Iframeworks/native/libs/binder/include -Iframeworks/native/libs/ui/include -Iframeworks/native/libs/nativebase/include -Ihardware/libhardware/include -Isystem/media/audio/include -Iframeworks/native/libs/arect/include -Iframeworks/native/libs/math/include -Iframeworks/native/libs/graphicsenv/include -Iframeworks/native/libs/gui/include -Iframeworks/native/opengl/libs/EGL/include -Iframeworks/native/opengl/include -Iframeworks/native/libs/nativewindow/include -Isystem/libhidl/transport/token/1.0/utils/include -Isystem/libhidl/base/include -Isystem/libhidl/transport/include -Iout/soong/.intermediates/system/libhidl/transport/manager/1.0/android.hidl.manager@1.0_genc++_headers/gen -Iout/soong/.intermediates/system/libhidl/transport/base/1.0/android.hidl.base@1.0_genc++_headers/gen -Isystem/libhwbinder/include -Iout/soong/.intermediates/hardware/interfaces/graphics/common/1.0/android.hardware.graphics.common@1.0_genc++_headers/gen -Iout/soong/.intermediates/hardware/interfaces/media/1.0/android.hardware.media@1.0_genc++_headers/gen -Iout/soong/.intermediates/hardware/interfaces/graphics/bufferqueue/1.0/android.hardware.graphics.bufferqueue@1.0_genc++_headers/gen -Iframeworks/native/libs/sensor/include -Iframeworks/av/camera/include -Iframeworks/av/camera/include/camera -Isystem/media/camera/include -Iout/soong/.intermediates/frameworks/av/camera/libcamera_client/android_arm64_armv8-a_shared_core/gen/aidl -Iexternal/skia/include/android -Iexternal/skia/include/c -Iexternal/skia/include/codec -Iexternal/skia/include/config -Iexternal/skia/include/core -Iexternal/skia/include/effects -Iexternal/skia/include/encode -Iexternal/skia/include/gpu -Iexternal/skia/include/gpu/gl -Iexternal/skia/include/pathops -Iexternal/skia/include/ports -Iexternal/skia/include/svg -Iexternal/skia/include/utils -Iexternal/skia/include/utils/mac -Iexternal/sqlite/dist -Iexternal/sqlite/android -Iframeworks/native/vulkan/include -Ihardware/libhardware_legacy/include -Iexternal/icu/icu4c/source/common -Iframeworks/av/media/libmedia/aidl -Iframeworks/av/media/libmedia/include -Iout/soong/.intermediates/hardware/interfaces/media/omx/1.0/android.hardware.media.omx@1.0_genc++_headers/gen -Iexternal/sonivox/arm-wt-22k/include -Iexternal/icu/icu4c/source/i18n -Iframeworks/av/media/libstagefright/foundation/include -Iout/soong/.intermediates/frameworks/av/drm/libmediadrm/libmediadrm/android_arm64_armv8-a_shared_core/gen/aidl -Isystem/libhidl/libhidlmemory/include -Iout/soong/.intermediates/system/libhidl/transport/memory/1.0/android.hidl.memory@1.0_genc++_headers/gen -Iout/soong/.intermediates/frameworks/av/media/libmedia/libmedia/android_arm64_armv8-a_shared_core/gen/aidl -Iframeworks/av/media/libaudioclient/include -Iexternal/libjpeg-turbo -Isystem/core/libusbhost/include -Iexternal/harfbuzz_ng/src -Iexternal/zlib -Iexternal/pdfium/public -Iframeworks/av/media/img_utils/include -Isystem/netd/include -Iframeworks/minikin/include -Iexternal/freetype/include -Isystem/core/libprocessgroup/include -Isystem/media/radio/include -Isystem/core/libnativeloader/include -Isystem/core/libmemunreachable/include -Isystem/libvintf/include -Iframeworks/base/libs/hwui -Iout/soong/.intermediates/frameworks/base/libs/hwui/libhwui/android_arm64_armv8-a_static_core/gen/proto/frameworks/base/libs/hwui -Iout/soong/.intermediates/frameworks/base/libs/hwui/libhwui/android_arm64_armv8-a_static_core/gen/proto -Iexternal/protobuf/src -Iframeworks/rs/cpp -Iframeworks/rs -Iout/soong/.intermediates/frameworks/base/libs/hwui/libhwui/android_arm64_armv8-a_shared_core/gen/proto/frameworks/base/libs/hwui -Iout/soong/.intermediates/frameworks/base/libs/hwui/libhwui/android_arm64_armv8-a_shared_core/gen/proto -Iexternal/libcxx/include -Iexternal/libcxxabi/include -Isystem/core/include -Isystem/media/audio/include -Ihardware/libhardware/include -Ihardware/libhardware_legacy/include -Ihardware/ril/include -Ilibnativehelper/include -Iframeworks/native/include -Iframeworks/native/opengl/include -Iframeworks/av/include -isystem bionic/libc/arch-arm64/include -isystem bionic/libc/include -isystem bionic/libc/kernel/uapi -isystem bionic/libc/kernel/uapi/asm-arm64 -isystem bionic/libc/kernel/android/scsi -isystem bionic/libc/kernel/android/uapi -Ilibnativehelper/include/nativehelper -Wno-unused-parameter -Wno-non-virtual-dtor -Wno-parentheses -DGL_GLEXT_PROTOTYPES -DEGL_EGLEXT_PROTOTYPES -DU_USING_ICU_NAMESPACE=0 -Wall -Werror -Wno-error=deprecated-declarations -Wunused -Wunreachable-code -Wno-unknown-pragmas -D__ANDROID_DEBUGGABLE__ -target aarch64-linux-android -Bprebuilts/gcc/darwin-x86/aarch64/aarch64-linux-android-4.9/aarch64-linux-android/bin -DANDROID_STRICT -fPIC -D_USING_LIBCXX -std=gnu++14 -Wsign-promo -Wno-inconsistent-missing-override -Wno-null-dereference -D_LIBCPP_ENABLE_THREAD_SAFETY_ANNOTATIONS -Wno-thread-safety-negative -Wno-conversion-null -fno-rtti -fvisibility-inlines-hidden -Werror=int-to-pointer-cast -Werror=pointer-to-int-cast -Werror=address-of-temporary -Werror=return-type -MD -MF out/soong/.intermediates/frameworks/base/core/jni/libandroid_runtime/android_arm64_armv8-a_shared_core/obj/frameworks/base/core/jni/android_hardware_Camera222.o.d -o out/soong/.intermediates/frameworks/base/core/jni/libandroid_runtime/android_arm64_armv8-a_shared_core/obj/frameworks/base/core/jni/android_hardware_Camera222.o'.split()

    # entry_funs = ['android_hardware_Camera_getNumberOfCameras(JNIEnv *, jobject)']
    entry_funs = ['android_hardware_Camera_native_setup(JNIEnv *, jobject, jobject, jint, jint, jstring)']

    main_file_analyser.run(file, pro_path, ninja_args, entry_funs)

def test3():
    # c_cpp_list = find_command_star_node('frameworks/av/services/camera/libcameraservice/CameraService.cpp')
    # c_cpp_list = c_cpp_list[0]
    # entry_funs = ['getNumberOfCameras(', 'getCameraInfo(', 'connect(', 'connectDevice(', 'connectLegacy(',
    #               'getCameraCharacteristics(', 'getCameraVendorTagDescriptor(', 'getCameraVendorTagCache(',
    #               'getLegacyParameters(', 'supportsCameraApi(', 'setTorchMode(', 'notifySystemEvent(']
    # entry_funs = ['::' + 'CameraService' + '::' + tem for tem in entry_funs]

    c_cpp_list = find_command_star_node('frameworks/av/services/camera/libcameraservice/CameraService.cpp')
    c_cpp_list = c_cpp_list[0]
    entry_funs = ['getNumberOfCameras(', 'getCameraInfo(', 'connect(', 'connectDevice(', 'connectLegacy(',
                  'getCameraCharacteristics(', 'getCameraVendorTagDescriptor(', 'getCameraVendorTagCache(',
                  'getLegacyParameters(', 'supportsCameraApi(', 'setTorchMode(', 'notifySystemEvent(']
    entry_funs = ['::' + 'CameraService' + '::' + tem for tem in entry_funs]

    # out/soong/build.ninja
    main_file_analyser = file_analyser()
    # analyze cpp
    file = '/Volumes/android/android-8.0.0_r34/' + c_cpp_list['source']

    pro_path = '/Volumes/android/android-8.0.0_r34/'
    ninja_args = c_cpp_list['content']['flags']

    # entry_funs = ['android::CameraService::connectDevice(const sp<> &, const android::String16 &, const android::String16 &, int, sp<> *)']
    # entry_funs = ['android::CameraService::connectHelper(const sp<CALLBACK> &, const android::String8 &, int, const android::String16 &, int, int, android::CameraService::apiLevel, bool, bool, sp<CLIENT> &)']
    # entry_funs = None
    main_file_analyser.run(file, pro_path, ninja_args, entry_funs, extend_analyze=False)
    with open('tem/cpp_permission_fun/CameraService.txt', 'w', encoding='UTF-8') as file:
        for [method, permission] in main_file_analyser.found_permission_method:
            file.write(method + ' ::: ' + '[%s]' % permission + '\n')


def test4():
    # c_cpp_list = find_command_star_node('frameworks/av/camera/cameraserver/main_cameraserver.cpp')
    # c_cpp_list = find_command_star_node('frameworks/av/drm/drmserver/main_drmserver.cpp')
    # c_cpp_list = find_command_star_node('frameworks/av/media/audioserver/main_audioserver.cpp')
    # c_cpp_list = find_command_star_node('frameworks/av/media/mediaserver/main_mediaserver.cpp')
    # c_cpp_list = find_command_star_node('frameworks/av/services/mediacodec/main_codecservice.cpp')
    # c_cpp_list = find_command_star_node('frameworks/av/services/mediaextractor/main_extractorservice.cpp')
    c_cpp_list = find_command_star_node('frameworks/av/services/mediaanalytics/main_mediametrics.cpp')
    c_cpp_list = c_cpp_list[0]

    # out/soong/build.ninja
    main_file_analyser = file_analyser()
    # analyze cpp
    file = '/Volumes/android/android-8.0.0_r34/' + c_cpp_list['source']

    pro_path = '/Volumes/android/android-8.0.0_r34/'
    ninja_args = c_cpp_list['content']['flags']

    entry_funs = ['main(']
    # entry_funs = ['android::CameraService::connectHelper(const sp<CALLBACK> &, const android::String8 &, int, const android::String16 &, int, int, android::CameraService::apiLevel, bool, bool, sp<CLIENT> &)']
    # entry_funs = None
    main_file_analyser.run(file, pro_path, ninja_args, entry_funs, extend_analyze=True, print_all_node=False, generate_html=False)
    # for [method, permission] in main_file_analyser.found_permission_method:
    #     print('FOUND ', method, ' ::: ', permission)
    if len(main_file_analyser.found_permission_method) > 0:
        with open('tem/cpp_service_name.txt', 'a', encoding='UTF-8') as file:
            file.write(c_cpp_list['source'] + " ::: [" + main_file_analyser.found_permission_method[0][1][0] + ']' + main_file_analyser.found_permission_method[0][1][1] + '\n')

def test5():
    # analyser = file_analyser()
    index = Index.create()
    index.read('/Users/chaoranli/PycharmProjects/test/main2.ast')

def test6():
    main_file_analyser = file_analyser()
    index = Index.create(1)
    # c_cpp_list = find_command('/Volumes/android/android-8.0.0_r34/frameworks/av/services/audioflinger/StateQueue.h')
    c_cpp_list = find_command('/Volumes/android/android-8.0.0_r34/frameworks/av/media/libaaudio/src/utility/HandleTracker.h')
    if c_cpp_list is not None:
        next_file = '/Volumes/android/android-8.0.0_r34/' + c_cpp_list['source']
        ninja_args = c_cpp_list['content']['flags']
        ninja_args = main_file_analyser.parse_ninja_args(ninja_args)
        print(ninja_args)
        main_file_analyser.load_cfg(index, c_cpp_list['content']['compiler'], next_file, ninja_args)

def reverse_search(list, fun_name, full_name, past):
    found_list = {}
    for tem in list:
        if tem['source'] in past:
            continue
        if 'test' in tem['source'].lower() or 'tests' in tem['source'].lower() or 'armv7' in tem['source'].lower():
            continue
        # if 'ICameraDeviceUser' in tem['source']:
        #     print(tem['source'])
        # 返回行数 [{source:'xxxx.cpp', content:{...}}]
        r = find_fun_cpp('/Volumes/android/android-8.0.0_r34/' + tem['source'], fun_name)
        if r is not None:
            found_list[tem['source']] = [tem, r]
            past.append(tem['source'])

    for k, tem in found_list.items():
        print(tem[0]['source'], tem[1])

        cpp = tem[0]
        main_file_analyser = file_analyser()
        # analyze cpp
        file = '/Volumes/android/android-8.0.0_r34/' + cpp['source']

        pro_path = '/Volumes/android/android-8.0.0_r34/'
        ninja_args = cpp['content']['flags']

        entry_funs = [full_name]

        graphs_file = main_file_analyser.run(file, pro_path, ninja_args, entry_funs, extend_analyze=False, anti_search=True)
        for graphs in graphs_file:
            for graph in graphs:
                if len(graph) < 2:
                    continue
                parent_node_name = graph[0]

                node_list = main_file_analyser.search_fun_list(parent_node_name)
                if len(node_list)==0:
                    continue
                node = node_list[0]
                child_node_name = node.spelling
                print('最父节点搜索，简单函数：', child_node_name + '(', '完整函数：', parent_node_name)
                reverse_search(list, child_node_name + '(', parent_node_name, past)

def test7():
    list = get_cpp_files_path()
    past = []
    fun_name = 'enforceRequestPermissions('
    fill_name = 'android::CameraDeviceClient::enforceRequestPermissions(class android::CameraMetadata &)'
    reverse_search(list, fun_name, fill_name, past)

def test8():
    list = get_cpp_files_path()
    past = []
    fun_name = 'listModules('
    fill_name = 'RadioService::listModules('
    reverse_search(list, fun_name, fill_name, past)

def test9():
    c_cpp_list = find_command_star_node('frameworks/base/core/jni/android_hardware_Radio.cpp')
    # entry_funs = ['android_hardware_Radio_listModules(']
    entry_funs = ['android_hardware_Radio_listModules(',
                  'android_hardware_Radio_setup(',
                  'android_hardware_Radio_finalize(',
                  'android_hardware_Radio_close(',
                  'android_hardware_Radio_setConfiguration(',
                  'android_hardware_Radio_getConfiguration(',
                  'android_hardware_Radio_setMute(',
                  'android_hardware_Radio_getMute(',
                  'android_hardware_Radio_step(',
                  'android_hardware_Radio_scan(',
                  'android_hardware_Radio_tune(',
                  'android_hardware_Radio_cancel(',
                  'android_hardware_Radio_getProgramInformation(',
                  'android_hardware_Radio_isAntennaConnected(',
                  'android_hardware_Radio_hasControl(']

    # c_cpp_list = find_command_star_node('frameworks/av/services/radio/RadioService.cpp')
    # entry_funs = ['listModules(']

    # c_cpp_list = find_command_star_node('frameworks/av/radio/Radio.cpp')
    # entry_funs = ['setConfiguration(']

    c_cpp_list = c_cpp_list[0]
    # entry_funs = ['::' + 'CameraService' + '::' + tem for tem in entry_funs]

    # out/soong/build.ninja
    main_file_analyser = file_analyser()
    # analyze cpp
    file = '/Volumes/android/android-8.0.0_r34/' + c_cpp_list['source']

    pro_path = '/Volumes/android/android-8.0.0_r34/'
    ninja_args = c_cpp_list['content']['flags']

    # entry_funs = ['android::CameraService::connectDevice(const sp<> &, const android::String16 &, const android::String16 &, int, sp<> *)']
    # entry_funs = ['android::CameraService::connectHelper(const sp<CALLBACK> &, const android::String8 &, int, const android::String16 &, int, int, android::CameraService::apiLevel, bool, bool, sp<CLIENT> &)']
    # entry_funs = None
    main_file_analyser.run(file, pro_path, ninja_args, entry_funs=entry_funs, extend_analyze=True, anti_search=False, print_all_node=False)

def test10():
    # c_cpp_list = find_command_star_node('frameworks/base/core/jni/android_hardware_Radio.cpp')
    c_cpp_list = find_command_star_node('frameworks/base/media/jni/android_media_MediaDrm.cpp')

    c_cpp_list = c_cpp_list[0]

    main_file_analyser = file_analyser()
    # analyze cpp
    file = '/Volumes/android/android-8.0.0_r34/' + c_cpp_list['source']

    pro_path = '/Volumes/android/android-8.0.0_r34/'
    ninja_args = c_cpp_list['content']['flags']

    # entry_funs = ['android::CameraService::connectDevice(const sp<> &, const android::String16 &, const android::String16 &, int, sp<> *)']
    # entry_funs = ['android::CameraService::connectHelper(const sp<CALLBACK> &, const android::String8 &, int, const android::String16 &, int, int, android::CameraService::apiLevel, bool, bool, sp<CLIENT> &)']
    # entry_funs = None
    main_file_analyser.extract_jni_fun(file, pro_path, ninja_args)

def test11():
    start = False
    with open('jni10.0/jni.json') as file_obj:
        cpp_jni_list = json.load(file_obj)
        for cpp_jni in cpp_jni_list:
            # 13个
            # if 'android_hardware_Radio.cpp' not in cpp_jni['cpp']:
            #     continue

            # 有问题 1.drmhal.h 对应cpp没加载 2.同名函数多
            # 1个 DrmHal::signRSA(
            if 'android_media_MediaDrm.cpp' not in cpp_jni['cpp']:
                continue

            # 1个
            # status_t MediaPlayerService::Client::setDataSource( 有BUG

            # 1个
            # listenForRemoteDisplay( android.permission.CONTROL_WIFI_DISPLAY"
            # if 'android_media_RemoteDisplay.cpp' not in cpp_jni['cpp']:
            #     continue

            # 1个 android_media_MediaRecorder_setAudioSource( 同名函数多
            # if 'android_media_MediaRecorder.cpp' not in cpp_jni['cpp']:
            #     continue

            # if 'android_hardware_SensorManager.cpp' not in cpp_jni['cpp']:
            #     continue

            entry_funs = []
            cpp = cpp_jni['cpp']
            print(cpp)
            vars = cpp_jni['pairs']
            for var in vars:
                for pair in var:
                    entry_funs.append(pair[-1]+'(')
            print(entry_funs)
            c_cpp_list = find_command_star_node(cpp.replace(project_path, ''), '10.0', compdb=True)
            c_cpp_list = c_cpp_list[0]

            # main_file_analyser = file_analyser()
            # file = '/Volumes/android/android-8.0.0_r34/' + c_cpp_list['source']
            file = project_path + c_cpp_list['file']

            # pro_path = '/Volumes/android/android-8.0.0_r34/'
            pro_path = project_path
            # ninja_args = c_cpp_list['content']['flags']
            ninja_args = c_cpp_list['arguments'][1:]
            main_file_analyser = file_analyser()
            main_file_analyser.run(file, pro_path, ninja_args, entry_funs=entry_funs, extend_analyze=True,
                                   anti_search=False, print_all_node=False)

def test12():
    # c_cpp_list = find_command_star_node('frameworks/av/media/libmediaplayerservice/MediaPlayerService.cpp')
    # entry_funs = ['MediaPlayerService::listenForRemoteDisplay(', 'Client::setDataSource(']
    # c_cpp_list = find_command_star_node('frameworks/av/services/radio/RadioService.cpp')
    # entry_funs = ['RadioService::ModuleClient::setMute(']
    # c_cpp_list = find_command_star_node('frameworks/av/media/libmedia/mediarecorder.cpp')
    # entry_funs = ['android::MediaRecorder::MediaRecorder(']

    # c_cpp_list = find_command_star_node('frameworks/native/libs/sensor/SensorManager.cpp')
    # entry_funs = ['SensorManager::setOperationParameter(']
    # c_cpp_list = find_command_star_node('frameworks/av/media/libaudioclient/AudioSystem.cpp')
    # entry_funs = ['AudioSystem::get_audio_flinger(']

    # c_cpp_list = find_command_star_node('frameworks/base/core/jni/android_media_AudioSystem.cpp')
    # entry_funs = ['android_media_AudioSystem_setAudioPortConfig(']
    # c_cpp_list = find_command_star_node('frameworks/av/media/libaudioclient/AudioSystem.cpp')
    # entry_funs = ['AudioSystem::setAudioPortConfig(']
    # c_cpp_list = find_command_star_node('frameworks/av/services/audiopolicy/service/AudioPolicyService.cpp')
    # entry_funs = ['android::AudioPolicyService::registerClient(']

    # c_cpp_list = find_command_star_node('frameworks/av/services/camera/libcameraservice/CameraService.cpp')
    # entry_funs = ['CameraService::validateClientPermissionsLocked(']

    # c_cpp_list = find_command_star_node('frameworks/av/media/libaudioclient/AudioRecord.cpp')
    # entry_funs = ['AudioRecord::start(']

    # c_cpp_list = find_command_star_node('frameworks/av/services/audioflinger/AudioFlinger.cpp')
    # entry_funs = ['AudioFlinger::openRecord(']

    # c_cpp_list = find_command_star_node('frameworks/av/services/audioflinger/ServiceUtilities.cpp')
    # entry_funs = ['android::recordingAllowed(']

    # c_cpp_list = find_command_star_node('frameworks/av/media/libmedia/mediaplayer.cpp')
    # entry_funs = ['MediaPlayer::attachNewPlayer(']

    c_cpp_list = find_command_star_node('frameworks/native/services/surfaceflinger/SurfaceFlinger.cpp', '10.0', compdb=True)
    entry_funs = ['SurfaceFlinger::CheckTransactCodeCredentials(']

    c_cpp_list = c_cpp_list[0]
    main_file_analyser = file_analyser()
    pro_path = '/hci/chaoran_data/android-10.0.0_r45/'
    file = pro_path + c_cpp_list['file']
    ninja_args = c_cpp_list['arguments'][1:]
    main_file_analyser = file_analyser()
    main_file_analyser.run(file, pro_path, ninja_args, entry_funs=entry_funs, extend_analyze=False,
                           anti_search=False, print_all_node=False)

# AST variable tracker
def test13():
    start = False
    with open('jni10.0/jni.json') as file_obj:
        cpp_jni_list = json.load(file_obj)
        for cpp_jni in cpp_jni_list:
            # 加载额外涉及不到的h cpp文件 需要自动引入 无其他问题 8.0有这个问题
            # 1个 DrmHal::signRSA(
            # 11/26 通过 ✅
            # android 10.0 能编译 android::MediaDrmService::makeDrm() 找不到 仅支持32bit | 没有这个permission了
            # permission: android.permission.ACCESS_DRM_CERTIFICATES
            # if 'android_media_MediaDrm.cpp' not in cpp_jni['cpp']:
            #     continue

            # <android.media.MediaRecorder: void setVideoSource(int)>	android.permission.CAMERA
            # <android.media.MediaRecorder: void setAudioSource(int)>	android.permission.RECORD_AUDIO
            # 11/26 通过 ✅
            # android 10.0 能编译 有结果 android.permission.RECORD_AUDIO android.permission.CAMERA ✅
            '''
            FOUND  android_media_MediaRecorder_setAudioSource(JNIEnv *, jobject, jint)  :::  [!(nextObject <> mObjects [ nextObject ]) && *! ("android.permission.RECORD_AUDIO")]
            FOUND  android_media_MediaRecorder_setVideoSource(JNIEnv *, jobject, jint)  :::  [!(nextObject <> mObjects [ nextObject ]) && *vs != VIDEO_SOURCE_SURFACE && ! ("android.permission.CAMERA")]
            '''
            # if 'android_media_MediaRecorder.cpp' not in cpp_jni['cpp']:
            #     continue

            # frameworks/av/media/utils/ServiceUtilities.cpp X
            # android.permission.RECORD_AUDIO [处理调用函数没到最低端，暂时写死替代]【1】一起解决✅已经解决 是个BUG
            # android 10.0 能编译 android::AudioPolicyService::registerClient(sp<> &)
            '''
            FOUND  android_media_AudioRecord_start(JNIEnv *, jobject, jint, jint)  :::  [! ("android.permission.MODIFY_AUDIO_ROUTING")]
            FOUND  android_media_AudioRecord_start(JNIEnv *, jobject, jint, jint)  :::  [! ("android.permission.RECORD_AUDIO")]
            FOUND  android_media_AudioRecord_start(JNIEnv *, jobject, jint, jint)  :::  [( attr -> source == AUDIO_SOURCE_VOICE_UPLINK || attr -> source == AUDIO_SOURCE_VOICE_DOWNLINK || attr -> source == AUDIO_SOURCE_VOICE_CALL || attr -> source == AUDIO_SOURCE_ECHO_REFERENCE ) && ! canCaptureOutput]
            '''
            # if 'android_media_AudioRecord.cpp' not in cpp_jni['cpp']:
            #     continue

            # IxxService -> xxService❓ 问题不大命名规则，实际去找getservice函数，找string对应类名
            # checkpermission -> getcallingPid + permissions❓【1】一起解决
            # android.permission.DUMP❓ 暂时不考虑

            # NO_ERROR ✅ # 7.0搜索去源码查一下有没有这个权限 没收到
            # 有传参赋值行为
            # 13个
            # permission: android.permission.ACCESS_FM_RADIO
            # 11/26 实际12个 少了一个 android_hardware_Radio_tune(
            # if 'android_hardware_Radio.cpp' not in cpp_jni['cpp']:
            #     continue

            # android 10.0 ✅
            # 1个 ✅[ !(( strncmp ( url , "http://" , 7 ) == 0 ) || ( strncmp ( url , "https://" , 8 ) == 0 ) || ( strncmp ( url , "rtsp://" , 7 ) ==] 去除无用的换成url == ""
            # <android.media.MediaPlayer: void nativeSetDataSource(android.os.IBinder,java.lang.String,java.lang.String[],java.lang.String[])>
            # android.permission.INTERNET
            '''
            FOUND  android_media_MediaPlayer_setDataSourceAndHeaders(JNIEnv *, jobject, jobject, jstring, jobjectArray, jobjectArray)  :::  [!(nextObject <> mObjects [ nextObject ]) && *!(( strncmp ( url , "http://" , 7 ) == 0 ) || ( strncmp ( url , "https://" , 8 ) == 0 ) || ( strncmp ( url , "rtsp://" , 7 ) ==]
            FOUND  android_media_MediaPlayer_setDataSourceAndHeaders(JNIEnv *, jobject, jobject, jstring, jobjectArray, jobjectArray)  :::  [! ("android.permission.INTERNET")]
            '''
            # if 'android_media_MediaPlayer.cpp' not in cpp_jni['cpp']:
            #     continue

            # android 10.0 能编译 ✅
            # ontransct  ✅
            # <android.view.SurfaceControl: android.graphics.Bitmap nativeScreenshot(android.os.IBinder,android.graphics.Rect,int,int,int,int,boolean,boolean,int)>
            # permission: android.permission.READ_FRAME_BUFFER
            '''
            switch (static_cast<ISurfaceComposerTag>(code)) {
                case REMOVE_REGION_SAMPLING_LISTENER: {
            '''
            '''
            FOUND  android::nativeScreenshot(JNIEnv *, jclass, jobject, jobject, jint, jint, bool, int, bool)  :::  [( uid != AID_GRAPHICS ) && ! ("android.permission.READ_FRAME_BUFFER")]
            FOUND  android::nativeApplyTransaction(JNIEnv *, jclass, jlong, jboolean)  :::  [!(nextObject <> mObjects [ nextObject ]) && *( uid != AID_GRAPHICS && uid != AID_SYSTEM ) && ! PermissionCache :: ("android.permission.ACCESS_SURFACE_FLINGER")]
            '''
            # if 'android_view_SurfaceControl.cpp' not in cpp_jni['cpp']:
            #     continue

            # android 10.0 能编译 貌似没有这个permission
            # 有传参赋值行为
            # 1个
            # 11/26 通过 ✅
            # # listenForRemoteDisplay( android.permission.CONTROL_WIFI_DISPLAY"
            # if 'android_media_RemoteDisplay.cpp' not in cpp_jni['cpp']:
            #     continue

            # android 10.0 能编译  line 2143 换类名 ✅
            # 在SensorManager中mSensorServer指向的类
            # 是通过waitForSensorService()获得的
            # permission: android.permission.LOCATION_HARDWARE
            # Bind 测试通过 11/26 ✅
            '''
            FOUND  nativeSetOperationParameter(JNIEnv *, jclass, jlong, jint, jint, jfloatArray, jintArray)  :::  [!(nextObject <> mObjects [ nextObject ]) && *! ("android.permission.LOCATION_HARDWARE")]
            '''
            # if 'android_hardware_SensorManager.cpp' not in cpp_jni['cpp']:
            #     continue

            # android 10.0 能编译 AudioPolicyService.cpp 不是clang编译找不到 ✅
            # frameworks/av/media/utils/ServiceUtilities.cpp
            # android.permission.CAPTURE_AUDIO_OUTPUT❓ 有个switch case函数获取 过于复杂。。
            # android.permission.MODIFY_AUDIO_SETTINGS ✅
            # android.permission.MODIFY_AUDIO_ROUTING ✅需要引用（找所有含有.h的cpp，现在是根据名字只找同名的cpp）
            # android.permission.DUMP❓ 暂时都不考虑

            # android 10.0 找不到的permission：
            '''
            FOUND  android_media_AudioSystem_registerPolicyMixes(JNIEnv *, jobject, jobject, jboolean)  :::  [needCaptureMediaOutput && ! ("android.permission.CAPTURE_MEDIA_OUTPUT")]
            FOUND  android_media_AudioSystem_setForceUse(JNIEnv *, jobject, jint, jint)  :::  [! ("android.permission.MODIFY_AUDIO_ROUTING")]
            FOUND  android_media_AudioSystem_setParameters(JNIEnv *, jobject, jstring)  :::  [! ("android.permission.MODIFY_AUDIO_SETTINGS")]
            '''
            if 'android_media_AudioSystem.cpp' not in cpp_jni['cpp']:
                continue

            # android 10.0 可以用 但是要开关
            # frameworks/av/media/utils/ServiceUtilities.cpp
            # line 2566 not_sys_include_paths.append('frameworks/av/media/utils/ServiceUtilities.cpp')
            # android.permission.CAPTURE_AUDIO_HOTWORD ✅
            '''
            FOUND  android_hardware_SoundTrigger_listModules(JNIEnv *, jobject, jstring, jobject)  :::  [! ("android.permission.CAPTURE_AUDIO_HOTWORD")]
            '''
            # if 'android_hardware_SoundTrigger.cpp' not in cpp_jni['cpp']:
            #     continue

            # 相机 AIDL的 写在这里随便做个测试
            # if 'android_hardware_Camera.cpp' not in cpp_jni['cpp']:
            #     continue

            entry_funs = []
            cpp = cpp_jni['cpp']
            print(cpp)
            vars = cpp_jni['pairs']
            for var in vars:
                for pair in var:
                    # if 'nativeScreenshot' in pair:
                    # if 'nativeSetOperationParameter' in pair:
                    # if 'android_media_AudioRecord_setup' in pair:
                        entry_funs.append(pair[-1] + '(')
            print(entry_funs)
            # c_cpp_list = find_command_star_node(cpp.replace('/Volumes/android/android-8.0.0_r34/', ''))
            c_cpp_list = find_command_star_node(cpp.replace(project_path, ''), '10.0', compdb=True)
            c_cpp_list = c_cpp_list[0]

            # main_file_analyser = file_analyser()
            # file = '/Volumes/android/android-8.0.0_r34/' + c_cpp_list['source']
            file = project_path + c_cpp_list['file']

            # pro_path = '/Volumes/android/android-8.0.0_r34/'
            # ninja_args = c_cpp_list['content']['flags']
            pro_path = project_path
            ninja_args = c_cpp_list['arguments'][1:]
            main_file_analyser = file_analyser()
            main_file_analyser.run(file, pro_path, ninja_args, entry_funs=entry_funs, extend_analyze=True,
                                   anti_search=False, print_all_node=False)

def test14(tem):
    def find_all(str, par):
        start = 0
        poses = []
        while True:
            index = str.find(par, start)
            start = index + 1

            if index != -1:
                poses.append(index)
            else:
                break

        return poses


    ori_tem = tem
    tem = tem.replace(' ', '')

    update = True
    while '!(' in tem:
        for i in range(len(tem)):
            ###############################
            if update:
                update = False
                pair = []
                pos1 = find_all(tem, '(')
                pos2 = find_all(tem, ')')
                # (和)中间不能有任何其余(或)
                print(pos1, pos2)
                while len(pos1) > 0 and len(pos2) > 0:
                    left_pos = 0
                    found_left = 0
                    for i in range(len(tem)):
                        if tem[i] == '(':
                            found_left = found_left + 1
                        elif tem[i] == ')':
                            found_left = found_left - 1

                        if i in pos1:
                            left_pos = i
                        elif i in pos2:
                            # 括号左index 括号右index 层级
                            pair.append([left_pos, i, found_left])
                            pos1.remove(left_pos)
                            pos2.remove(i)
                            break

                print(pair)

                for i in range(len(tem)):
                    print('%3s' % tem[i], end='')
                print()
                for i in range(len(tem)):
                    print('%3s' % i, end='')
                print()

                opers = []
                level = 0
                for i in range(len(tem)):
                    if tem[i] == '(':
                        level = level + 1
                    elif tem[i] == ')':
                        level = level - 1
                    if (tem[i] == '&' and tem[i + 1] == '&') \
                            or (tem[i] == '|' and tem[i + 1] == '|') \
                            or (tem[i] == '!' and tem[i + 1] == '=') \
                            or (tem[i] == '=' and tem[i + 1] == '='):
                        print(i, level - 1, tem[i] + tem[i])
                        opers.append([i, level - 1, tem[i] + tem[i]])
                    elif tem[i] == '!' and tem[i+1]!='(':
                        opers.append([i, level - 1, tem[i]])
            ###############################

            if i >= len(tem):
                break

            if tem[i] == '!' and (tem[i+1] == '(' or (tem[i+1] == ' ' and tem[i+2] == '(')):
                update = True
                print('发现非括号', i)
                start = 0
                end = 0
                l = 0
                for temmm in pair:
                    if i+1 == temmm[0] or i+2 == temmm[0]:
                        start = temmm[0]
                        end = temmm[1]
                        l = temmm[2]
                print('start', start, 'end', end, 'level', l)

                found = None
                for oper in opers:
                    print(oper)
                    print(oper[2] == '||' , oper[0]>start , oper[0]<end)
                    if oper[2] == '&&' and oper[0]>start and oper[0]<end:
                        found = oper
                        print('FOUND', oper)
                        tem = tem[:oper[0]] + '||' + tem[oper[0]+2:]
                        print(tem)
                    elif oper[2] == '||' and oper[0]>start and oper[0]<end:
                        found = oper
                        print('FOUND', oper)
                        tem = tem[:oper[0]] + '&&' + tem[oper[0]+2:]
                        print(tem)
                    elif oper[2] == '!' and oper[0]>start and oper[0]<end:
                        found = oper
                        print('FOUND', oper)
                        tem = tem[:oper[0]] + tem[oper[0]+1:]
                        print(tem)

                if found:
                    print('FOUND true')
                    for oper in opers:
                        print(oper)
                        if (oper[1] >= level+1 or oper[1] <= level+1) and ((start < oper[0] and oper[0] < found[0]) or (found[0] < oper[0] and oper[0] < end)):
                            if oper[2] == '!!':
                                tem = tem[:oper[0]] + '==' + tem[oper[0] + 2:]
                            elif oper[2] == '==':
                                tem = tem[:oper[0]] + '!=' + tem[oper[0] + 2:]

                tem = tem[:i] + tem[i+2:]
                print(':', end-3)
                print(tem[:end-2], tem[end-1:])
                tem = tem[:end-2] + tem[end-1:]
                print(tem)
    print(ori_tem)
    print('=>')
    print(tem)

def test122():
    # c_cpp_list = find_command_star_node('frameworks/av/media/libmediaplayerservice/MediaPlayerService.cpp')
    # entry_funs = ['MediaPlayerService::listenForRemoteDisplay(', 'Client::setDataSource(']
    # cpp = 'frameworks/av/services/camera/libcameraservice/CameraService.cpp'
    # cpp = 'frameworks/av/services/radio/RadioService.cpp'
    cpp = 'frameworks/av/services/audioflinger/AudioFlinger.cpp'
    # cpp = 'AudioRecord.cpp'
    # print(project_path)
    c_cpp_list = find_command_star_node(cpp.replace(project_path, ''), '10.0', compdb=True)
    # 7.0 和 8.0函数名不同
    # entry_funs = ['validateConnectLocked(']
    # entry_funs = ['RadioService::ModuleClient::setMute(']
    # entry_funs = ['AudioRecord::start(']
    entry_funs = ['AudioFlinger::openRecord(']
    print('c_cpp_list:', c_cpp_list)
    c_cpp_list = c_cpp_list[0]
    # print(c_cpp_list)
    main_file_analyser = file_analyser()

    file = project_path + c_cpp_list['file']
    pro_path = project_path
    # ninja_args = c_cpp_list['command'].split()[1:]
    ninja_args = c_cpp_list['arguments'][1:]

    main_file_analyser.run(file, pro_path, ninja_args, entry_funs=entry_funs, extend_analyze=False, anti_search=False, print_all_node=False)

if __name__ == '__main__':
    # test0()
    # test00()
    # test1()
    # test2()
    # test3()
    # test4()
    # test5()
    # test6()
    # test7()
    # test11()


    # 单个调试
    # test12()
    # 整体流程
    test13()
    # test122()
    # tem = '!(callingPid != getpid() && ( mAllowedUsers . find ( clientUserId ) == mAllowedUsers . end ( ) ))'
    # tem = '!(!(clientUid == USE_CALLING_UID) && ! (uid == AID_MEDIA || uid == AID_CAMERASERVER || uid == AID_RADIO))'
    tem = '!(callingPid != getpid() && ! "android.permission.CAMERA")'
    tem ='!((uid != AID_GRAPHICS && uid != AID_SYSTEM) && !PermissionCache::checkPermission(sAccessSurfaceFlinger, pid, uid))'
    # test14(tem)


    # kTemplateArgTest = """\
    #         template <int kInt, typename T, bool kBool>
    #         void foo();
    #
    #         void foo<-7, float, true>();
    #     """
    #
    # aaa = '''
    # class CameraService :
    #     public BinderService<CameraService>{
    # public:
    #     static int const getServiceName() { return 123; }
    # };
    #
    # template<typename SERVICE>
    # class BinderService {
    # public:
    #     static void publish() {
    #         return addService(SERVICE::getServiceName());
    #     }
    #
    #     static void instantiate() { publish(); }
    # };
    #
    # int main(){
    #     CameraService::instantiate();
    #     return 0;
    # }
    # '''
    # tu = get_tu(aaa, lang='cpp')
    # c = tu.cursor
    # tem = c.walk_preorder()
    # for t in tem:
    #     print(t.kind, t.spelling)
    # print('===============')
    # print(analyser.CALLGRAPH)
    # analyser.print_calls('CameraService::instantiate()', list(), None)
    #
    # # foos = get_cursors(tu, 'foo')
    # # for foo in foos:
    # #     print(foo.kind, foo.spelling)
    # # print('===============')
    # # n = foos[-2]
    # # print(n.spelling)
    # # # n = n.referenced
    # # # print(n.kind, n.spelling)
    # # for n in n.get_children():
    # #     print(n.spelling)
    # #     for n in n.get_children():
    # #         print(n.spelling)
    # #         for n in n.get_children():
    # #             print(n.spelling)
    #     # print(foo.get_num_template_arguments())
    # # print(foos[-2].spelling)
    # # print(foos[-2].get_num_template_arguments())
    # # print(foos[1].get_template_argument_value(0))
    # # print(foos[1].get_template_argument_value(2))


    # index = Index.create()
    # tu = index.parse("/Users/chaoranli/CLionProjects/untitled/main2.cpp")
    # for d in tu.diagnostics:
    #     if d.severity == d.Error or d.severity == d.Fatal:
    #         print(d)
    #         raise Exception('aaaaaaaaaaaaaaaaaa')
    #     else:
    #         print(d)
    # c = tu.cursor
    #
    # c.clang_visitChildren()
