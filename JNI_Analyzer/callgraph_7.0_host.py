#!/usr/bin/env python2

from pprint import pprint
from clang.cindex import CursorKind, Index, CompilationDatabase, TypeKind
from collections import defaultdict
import sys
import json
import os.path
from clang.cindex import Config
import ccsyspath
import numpy as np
from helper import get_file, find_c_or_cpp, find_files, find_command, find_command_star_node, get_cpp_files_path
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
# different clang version
# Config.set_library_file("/usr/local/Cellar/llvm/10.0.0_3/lib/libclang.dylib")
# different clang version
# Config.set_library_file("/usr/local/Cellar/llvm/10.0.0_3/lib/libclang.dylib")

# init_arg_config = '-isystem/Volumes/android/android-8.0.0_r34/prebuilts/clang/host/darwin-x86/clang-4053586/lib64/clang/5.0.300080/include'
# Config.set_library_file("/Volumes/android/android-8.0.0_r34/prebuilts/clang/host/darwin-x86/clang-4053586/lib64/libclang.dylib")

project_path = '/hci/chaoran_data/android-7.0.0_r33/'
clang_prepath = 'prebuilts/clang/host/linux-x86/clang-2690385/'
clang_lib_path = project_path + clang_prepath + 'lib64/libc++.so'
clang_lib_path = '/hci/chaoran_data/android-7.0.0_r33/out/host/linux-x86/lib64/libclang.so'
# clang_lib_path = '/hci/chaoran_data/pythonProject/clang_api24/libclang.so'
print(clang_lib_path)
Config.set_library_file(clang_lib_path)
init_arg_config = '-isystem/hci/chaoran_data/android-7.0.0_r33/prebuilts/clang/host/linux-x86/clang-2690385/lib64/clang/3.8/include'
# Config.set_library_file("/Volumes/android/android-8.0.0_r34/prebuilts/clang/host/darwin-x86/clang-4053586/lib64/libclang.dylib")
h_list = None



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
        elif c.kind == CursorKind.TRANSLATION_UNIT:
            return ''
        else:
            res = self.fully_qualified(c.semantic_parent)
            if res != '':
                return res + '::' + c.spelling
            return c.spelling


    def fully_qualified_pretty(self, c):
        if c is None:
            return ''
        elif c.kind == CursorKind.TRANSLATION_UNIT:
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

    def _get_binop_comparision_operator(self, cursor):
        COMPARISION_OPERATORS = ['==', '<=', '>=', '<', '>', '!=', '&&', '||']
        tokens = []
        for token in cursor.get_tokens():
            tokens.append(token)

        if tokens[-1].spelling in COMPARISION_OPERATORS:
            return tokens[-1].spelling
        else:
            return None

    def _get_binop_operator(self, cursor):
        """
        https://github.com/coala/coala-bears/blob/master/bears/c_languages/codeclone_detection/ClangCountingConditions.py
        Returns the operator token of a binary operator cursor.
        :param cursor: A cursor of kind BINARY_OPERATOR.
        :return:       The token object containing the actual operator or None.
        """
        children = list(cursor.get_children())
        operator_min_begin = (children[0].location.line,
                              children[0].location.column)
        operator_max_end = (children[1].location.line,
                            children[1].location.column)
        left = children[0].displayname
        if children[0].kind == CursorKind.CALL_EXPR:
            left = left + '()'
        right = children[1].displayname
        if children[1].kind == CursorKind.CALL_EXPR:
            right = right + '()'

        for token in cursor.get_tokens():
            if (operator_min_begin < (token.extent.start.line,
                                      token.extent.start.column) and
                    operator_max_end >= (token.extent.end.line,
                                         token.extent.end.column)):
                return left, token.spelling, right

        return None  # pragma: no cover

    def _is_secure_condition(self, cursor):
        children = list(cursor.get_children())
        for child in children:
            print(child.displayname)
            if child.displayname == 'ERROR_PERMISSION_DENIED':
                return True
            else:
                return self._is_secure_condition(child)

    def _get_unaryop_operator(self, cursor):
        """
        https://github.com/coala/coala-bears/blob/master/bears/c_languages/codeclone_detection/ClangCountingConditions.py
        Returns the operator token of a binary operator cursor.
        :param cursor: A cursor of kind BINARY_OPERATOR.
        :return:       The token object containing the actual operator or None.
        """
        children = list(cursor.get_children())
        operator_min_begin = (children[0].location.line,
                              children[0].location.column)

        left = children[0].displayname
        if children[0].kind == CursorKind.CALL_EXPR:
            left = left + '()'

        for token in cursor.get_tokens():
            if operator_min_begin > (token.extent.start.line,
                                      token.extent.start.column):
                return left, token.spelling

        return None  # pragma: no cover

    def show_info(self, node, cur_fun=None, depth=0, print_node=False):
        # and node.kind == CursorKind.STRING_LITERAL
        # if node.location.file and self.print_all_node and self.pro_path in node.location.file.name and self.is_template(node):
        #     t = node.type
        #     print(t.kind, t.spelling, t.get_num_template_arguments())
        #     print(t.get_template_argument_type(0).spelling)
        if 'validateConnectLocked' in node.displayname and node.kind == CursorKind.CXX_METHOD:
            print_node = True
            print('------show_info display nodes------')
        if node.location.file and (self.print_all_node or print_node) and self.pro_path in node.location.file.name:
            print('%2d' % depth + ' ' * depth, node.kind, node.displayname, end='')
            # if('RADIO_PERMISSION' in node.displayname):
            #     print()
            #     node = node.referenced
            #     print(node.kind, node.displayname)
                # for c in node.get_children():
                #     print(c.kind, c.displayname)
                #     for c in node.get_children():
                #         print(c.kind, c.displayname)
                # exit(2)
            type = node.type
            print('|type:', type.kind, end='')
            # if node.kind.is_reference():
            #     ref_node = node.get_definition()
            #     print(ref_node.spelling)
            if node.kind == CursorKind.BINARY_OPERATOR:
                # print(self._is_secure_condition(node))
                ooo = node.get_tokens()
                for tem in ooo:
                    print('/', tem.kind, tem.spelling, end=' ')
                binleft, binop, binright = self._get_binop_operator(node)
                print('\n***', binleft, binop, binright, '***')
                comparisionop = self._get_binop_comparision_operator(node)
                if comparisionop: print('\n*** COMPARISION:', comparisionop, '***')
            elif node.kind == CursorKind.UNARY_OPERATOR:
                # print(self._is_secure_condition(node))
                ooo = node.get_tokens()
                for tem in ooo:
                    print('/', tem.kind, tem.spelling, end=' ')
                left, binop = self._get_unaryop_operator(node)
                print('\n***', binop, left, '***')
                comparisionop = self._get_binop_comparision_operator(node)
                if comparisionop: print('\n*** COMPARISION:', comparisionop, '***')
            elif node.kind == CursorKind.INTEGER_LITERAL:
                value = node.get_tokens()
                for v in value:
                    print('', v.spelling, end='')
                # value = value.__next__().spelling
                # print('',value, end='')
            elif type.kind == TypeKind.RECORD:
                value = type.spelling
                print('', value, end='')
            # and type.kind == TypeKind.DEPENDENT

            elif (node.kind == CursorKind.DECL_REF_EXPR ):
                ooo = node.get_tokens()
                # for tem in ooo:
                #     print('|', tem.kind, tem.spelling, end=' ')

                # iii = type.get_pointee()
                # print(iii)
                o=0
            elif (node.kind == CursorKind.TYPE_REF and type.kind == TypeKind.UNEXPOSED):
                print(type.spelling, end='')
                # print(type.get_align())
                o=0
            # print(node.type.get_typedef_name())
            # if node.kind == CursorKind.TYPE_REF:
            #     num = node.get_num_template_arguments()
            #     print(num)
                # print(self.fully_qualified_pretty(node))
            print()

        if node.kind == CursorKind.FUNCTION_TEMPLATE:
            # if not is_excluded(node, xfiles, xprefs):
                cur_fun = node
                fun_str = self.fully_qualified_pretty(cur_fun)
                self.FULLNAMES[fun_str]=cur_fun
                # if self.print_all_node and self.pro_path in cur_fun.location.file.name:
                #     print('%2d' % depth + ' ' * depth, '|||' + fun_str)

        if node.kind == CursorKind.CXX_METHOD or \
                node.kind == CursorKind.FUNCTION_DECL:
            # if not is_excluded(node, xfiles, xprefs):
                cur_fun = node
                fun_str = self.fully_qualified_pretty(cur_fun)
                self.FULLNAMES[fun_str]=cur_fun
                # if self.print_all_node and self.pro_path in cur_fun.location.file.name:
                #     print('%2d' % depth + ' ' * depth, '|||' + fun_str)

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

        for c in node.get_children():
            # if (node.kind == CursorKind.DECL_REF_EXPR and type.kind == TypeKind.DEPENDENT):
            #     print('fdsafdsafdsafdsafsda')
            self.show_info(c, cur_fun, depth=depth+1, print_node=print_node)


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
        k_list = []
        v_list = []
        for k, v in self.FULLNAMES.items():
            if fun_name in k:
                print('search_fun_list_full Found fun -> ' + k)
                k_list.append(k)
                v_list.append(v)
        return k_list, v_list

    def search_fun_list(self, fun_name):
        list = []
        for k, v in self.FULLNAMES.items():
            if fun_name in k:
                    print('Found fun -> ' + k)
                    list.append(v)
        return list

    def getPermission(self, node):
        # print(node.kind, node.spelling)
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
                    # print('子', node.kind, node.spelling)
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

    def print_childrens(self, node, service_names, depth):
        if node is not None and node.location.file is not None and self.pro_path in node.location.file.name:
            for n in node.get_children():
                print('%2d' % depth + ' ' * depth, n.kind, n.spelling, end=' | ')
                ooo = n.get_tokens()
                tokens_key = []
                tokens_val = []
                for tem in ooo:
                    tokens_key.append(tem.spelling)
                    tokens_val.append(tem)
                for token in tokens_key:
                    print(token, end='')

                if n.kind == CursorKind.DECL_REF_EXPR and 'getServiceName' in tokens_key:
                    key_name = ''
                    for tem in self.FULLNAMES.keys():
                        if 'getServiceName' in tem:
                            key_name = tem
                    tem_node = self.FULLNAMES[key_name]
                    service_name = self.get_para(tem_node)
                    # 这个binder的字符和cpp文件绑定即所需
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
                    print(" " + service_name, end='')
                    service_names.append([service_name, n.location.file.name])
                print()

                if n.kind == CursorKind.STRING_LITERAL:
                    service_name = n.spelling
                    service_names.append([service_name, n.location.file.name])

                if n.kind == CursorKind.DECL_REF_EXPR:
                    n = n.referenced
                    # print(n is not None)
                    if n is not None:
                        print('%2d' % depth + ' ' * depth, n.kind, n.spelling, end=' | ')
                        ooo = n.get_tokens()
                        for tem in ooo:
                            print(tem.spelling, end=' ')

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

    def print_calls(self, fun_name, so_far, last_node, permission_strs, depth=0):
        if fun_name in self.CALLGRAPH:
            for f in self.CALLGRAPH[fun_name]:
                node = f
                f = f.referenced
                # string被忽略了
                if(f.location.file is not None and self.pro_path in f.location.file.name):
                    log = self.pretty_print(f)
                    current_depth = depth


                    if 'check' in log and 'Permission' in log:
                        print('%2d' % current_depth, ' ' * (depth + 1) + log, end='')
                        # print('')
                        # print(node.kind, node.spelling)
                        permission_str = self.getPermission(node)
                        # if permission_str is None:
                        #     print('肝')
                        #     last = so_far[-1]
                        #     print(last.kind, last.spelling)
                        #     for cc in last.get_children():
                        #         print(cc.kind, cc.spelling)
                        print('|||[%s]' % permission_str)
                        # exit(2)
                        log = log + '|||[%s]' % permission_str
                        permission_strs.append(permission_str)
                    elif 'addService' in log:
                        print('%2d' % current_depth, ' ' * (depth + 1) + log)
                        print('***')
                        self.print_childrens(node, permission_strs, current_depth+2)
                        print('***')
                    elif 'getService' in log:
                        print('%2d' % current_depth, ' ' * (depth + 1) + log)
                        print('***')
                        self.print_childrens(node, permission_strs, current_depth+2)
                        print('***')
                    elif 'writeInterfaceToken' in log:
                        print('%2d' % current_depth, ' ' * (depth + 1) + log)
                        print('***')
                        self.print_childrens(node, permission_strs, current_depth+2)
                        print('***')
                    else:
                        if 'instantiate' in log:
                            oo = 0
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
                    r_final = re.findall(r'::I[A-Z].+?::', log)
                    if len(r_final) > 0:
                        print('###### Binder Linking ######')
                        print(log)
                        # next_fun_name = log[:log.index('(') + 1]
                        k_list, v_list = self.search_fun_list_full('::'+f.spelling+'(')
                        next_fun_notshown_list_k = []
                        next_fun_notshown_list_v = []
                        for i in range(len(k_list)):
                            exist = False
                            for so_far_single in so_far:
                                if k_list[i] == self.pretty_print(so_far_single):
                                    exist = True
                            if not exist and '::Bp' not in k_list[i] and '::Bn' not in k_list[i] and '::__' not in k_list[i]:
                                next_fun_notshown_list_k.append(k_list[i])
                                next_fun_notshown_list_v.append(v_list[i])

                        print(next_fun_notshown_list_k)
                        print('###### Binder linked ######')
                        if len(next_fun_notshown_list_k) > 0:
                            so_far.append(next_fun_notshown_list_v[-1])
                            print(next_fun_notshown_list_k[-1])
                            print(next_fun_notshown_list_k[-1] in self.CALLGRAPH)
                            if 'android::DrmHal::signRSA' in next_fun_notshown_list_k[-1]:
                                ppp=0
                            self.print_calls(next_fun_notshown_list_k[-1], so_far, self.pretty_print(f), permission_strs,
                                             depth + 1)
                        else:
                            # self.print_calls(next_fun_notshown_list[0], so_far, self.pretty_print(f), permission_strs,
                            #                  depth + 1)
                            if self.fully_qualified_pretty(f) in self.CALLGRAPH:
                                self.print_calls(self.fully_qualified_pretty(f), so_far, self.pretty_print(f),
                                                 permission_strs, depth + 1)
                            else:
                                self.print_calls(self.fully_qualified(f), so_far, self.pretty_print(f), permission_strs,
                                                 depth + 1)

                        # android::IRadio::tune(unsigned int, unsigned int)
                        # 'android::IServiceManager::getService(const class android::String16 &)'
                        # next_fun_name = log.replace(r1[0], r1[0][1:])
                        # print('%2d' % current_depth, ' ' * (depth + 1) + next_fun_name, '%%% AIDL JUMP')
                        # self.print_calls(next_fun_name, so_far, self.pretty_print(f), permission_strs,
                        #                  depth + 1)
                    # link for AIDL============
                    elif self.fully_qualified_pretty(f) in self.CALLGRAPH:
                        self.print_calls(self.fully_qualified_pretty(f), so_far, self.pretty_print(f), permission_strs, depth + 1)
                    else:
                        self.print_calls(self.fully_qualified(f), so_far, self.pretty_print(f), permission_strs, depth + 1)
                # else:
                #     # print('  ' * (depth + 1) + 'ENDNODE|' + fun_name)
                #     if last_node is not None and last_node not in self.ENDNODE:
                #         self.ENDNODE.append(last_node)
        else:
            # print('  ' * (depth + 1) + 'ENDNODE|'+ fun_name)
            # aaa= self.CALLGRAPH[fun_name]
            if last_node is not None and last_node not in self.ENDNODE:
                self.ENDNODE.append(last_node)



    def read_compile_commands(self, filename):
        if filename.endswith('.json'):
            with open(filename) as compdb:
                return json.load(compdb)
        else:
            return [{'command': '', 'file': filename}]


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
        self.show_info(tu.cursor)

    def parse_ninja_args(self, ninja_args):
        for i in range(len(ninja_args)):
            # print(tem_args[i])
            if '-I' in ninja_args[i] and len(ninja_args[i]) > 2:
                # ninja_args[i] = ninja_args[i].replace('-I', '-I/Volumes/android/android-8.0.0_r34/')
                ninja_args[i] = ninja_args[i].replace('-I', '-I'+project_path)
            if i > 0 and ninja_args[i-1] == '-I' or ninja_args[i-1] == '-isystem' or ninja_args[i-1] == '-o' or ninja_args[i-1] == '-MF':
                ninja_args[i] = project_path + ninja_args[i]
            if '-fsanitize-blacklist=' in ninja_args[i]:
                ninja_args[i] = ninja_args[i].replace('-fsanitize-blacklist=', '-fsanitize-blacklist='+project_path)
            # print(tem_args[i])
        return ninja_args

    def load_cfg_normal(self, index, file, args):

        syspath = ccsyspath.system_include_paths('/hci/chaoran_data/android-7.0.0_r33/prebuilts/clang/host/linux-x86/clang-2690385/bin/clang++')
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
        self.show_info(tu.cursor)
        return tu

    def load_cfg(self, index, compiler, file, ninja_args):
        print(compiler)

        if 'clang++' in compiler:
            # init_args = ['-v', init_arg_config]
            init_args = [init_arg_config]
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
                ninja_args[i] = ninja_args[i].replace(r'"-DPACKED=\"\""','-DPACKED=""')
        ast_path = 'ast7.0/' + file.replace('/','_') + '.ast'
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
                if 'use of undeclared identifier' in d.spelling:
                    return None
                raise Exception('aaaaaaaaaaaaaaaaaa')
            else:
                print(d)

        if not os.path.exists(ast_path):
            print('save:', ast_path)
            tu.save(ast_path)

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
        print('FLAG: start run() function')
        self.show_loc = show_loc
        self.print_all_node = print_all_node
        index = Index.create(1)
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

                    r = re.findall(r'I.+?\.h', include_path)
                    if len(r) > 0 and 'Service' not in include_path:
                        aaa = include_path.replace(r[0], r[0][1:])
                        not_sys_include_paths.append(aaa)

            else:
                if self.pro_path in include_path:
                    not_sys_include_paths.append(include_path)

        i = 0

        if extend_analyze:
            print('===========ALL INCLUDE FILE=============')
            print(not_sys_include_paths)
            print('===========SEARCH INCLUDE FILE=============')
            for tem in not_sys_include_paths:
                i = i+1
                print('***************')
                print('Loading CFG ... ', i, '/', len(not_sys_include_paths))

                # print("*.h:", tem)
                if IS_AOSP:
                    c_cpp_list = find_command(tem, version_prefix='7.0', compdb=True, project_path=project_path)
                    if c_cpp_list is not None:
                        next_file = project_path + c_cpp_list['file']
                        '''
                                /Volumes/android/android-8.0.0_r34/frameworks/av/media/libstagefright/MediaClock.cpp:93:5: error: use of undeclared identifier 'GE'
                                /Volumes/android/android-8.0.0_r34/frameworks/av/media/libstagefright/foundation/AString.cpp:170:5: error: use of undeclared identifier 'LT'
                                /Volumes/android/android-8.0.0_r34/frameworks/av/media/libstagefright/MediaSync.cpp:502:9: error: use of undeclared identifier 'EQ'         
                                /Volumes/android/android-8.0.0_r34/frameworks/av/media/libstagefright/foundation/MediaBuffer.cpp:109:9: error: use of undeclared identifier 'EQ'

                                '''
                        if 'MediaClock.cpp' in next_file or 'AString.cpp' in next_file or 'MediaSync.cpp' in next_file or 'MediaBuffer.cpp' in next_file:
                            print('pass: ', next_file)
                            continue
                        ninja_args = c_cpp_list['command'].split()[1:]
                        ninja_args = self.parse_ninja_args(ninja_args)
                        # print(next_file)
                        # print(ninja_args)
                        # self.load_cfg(index, c_cpp_list['content']['compiler'], next_file, ninja_args)
                        if 'clang++' in c_cpp_list['command'].split()[0]:
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
                        self.print_calls(entry_fun, so_far, None, permission_strs)
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
            for [method, permission] in self.found_permission_method:
                print('FOUND ', method, ' ::: ', '[%s]' % permission)
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

def test000():

    analyser = file_analyser()
    # analyze cpp
    file = '/hci/chaoran_data/pythonProject/test/main.cpp'

    pro_path = '/hci/chaoran_data/pythonProject/test'
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
    c_cpp_list = find_command_star_node('frameworks/base/core/jni/android_hardware_Radio.cpp', compdb=True)
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
    file = project_path + c_cpp_list['file']

    pro_path = project_path
    ninja_args = c_cpp_list['command'].split()[1:]

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
    with open('jni7.0/jni.json') as file_obj:
        cpp_jni_list = json.load(file_obj)
        for cpp_jni in cpp_jni_list:
            # 13个 只有8.0适用
            # if 'android_hardware_Radio.cpp' not in cpp_jni['cpp']:
            #     continue

            # 有问题 1.drmhal.h 对应cpp没加载 2.同名函数多 解决了
            # android.permission.ACCESS_DRM_CERTIFICATES
            # 1个 DrmHal::signRSA(
            # if 'android_media_MediaDrm.cpp' not in cpp_jni['cpp']:
            #     continue

            # 1个
            # status_t MediaPlayerService::Client::setDataSource( 有BUG

            # 1个
            # android.permission.CONTROL_WIFI_DISPLAY
            # listenForRemoteDisplay( android.permission.CONTROL_WIFI_DISPLAY"
            # if 'android_media_RemoteDisplay.cpp' not in cpp_jni['cpp']:
            #     continue

            # 1个 android_media_MediaRecorder_setAudioSource( 同名函数多 未完成
            # if 'android_media_MediaRecorder.cpp' not in cpp_jni['cpp']:
            #     continue

            # if 'android_hardware_SensorManager.cpp' not in cpp_jni['cpp']:
            #     continue

            # ============================== 完整 ======================================
            # 13个
            # permission: android.permission.ACCESS_FM_RADIO
            # pass
            # if 'android_hardware_Radio.cpp' not in cpp_jni['cpp']:
            #     continue

            # 有问题 1.drmhal.h 对应cpp没加载 2.同名函数多
            # permission: android.permission.ACCESS_DRM_CERTIFICATES
            # not pass
            # 1个 DrmHal::signRSA(
            # if 'android_media_MediaDrm.cpp' not in cpp_jni['cpp']:
            #     continue

            # 1个
            # <android.media.MediaPlayer: void nativeSetDataSource(android.os.IBinder,java.lang.String,java.lang.String[],java.lang.String[])>
            # android.permission.INTERNET

            # <android.view.SurfaceControl: android.graphics.Bitmap nativeScreenshot(android.os.IBinder,android.graphics.Rect,int,int,int,int,boolean,boolean,int)>
            # permission: android.permission.READ_FRAME_BUFFER

            # 1个
            # listenForRemoteDisplay( android.permission.CONTROL_WIFI_DISPLAY"
            # permission: android.permission.CONTROL_WIFI_DISPLAY
            # pass
            # if 'android_media_RemoteDisplay.cpp' not in cpp_jni['cpp']:
            #     continue

            # <android.media.MediaRecorder: void setVideoSource(int)>	android.permission.CAMERA
            # <android.media.MediaRecorder: void setAudioSource(int)>	android.permission.RECORD_AUDIO
            # not pass
            # if 'android_media_MediaRecorder.cpp' not in cpp_jni['cpp']:
            #     continue

            # <android.hardware.SystemSensorManager: int nativeSetOperationParameter(long,int,int,float[],int[])>
            # permission: android.permission.LOCATION_HARDWARE
            # not pass
            # if 'android_hardware_SensorManager.cpp' not in cpp_jni['cpp']:
            #     continue

            if 'android_media_AudioRecord.cpp' not in cpp_jni['cpp']:
                continue

            entry_funs = []
            cpp = cpp_jni['cpp']
            print(cpp)
            vars = cpp_jni['pairs']
            for var in vars:
                for pair in var:
                    entry_funs.append(pair[-1]+'(')
            print(entry_funs)
            c_cpp_list = find_command_star_node(cpp.replace(project_path, ''), '7.0', compdb=True)
            c_cpp_list = c_cpp_list[0]

            # main_file_analyser = file_analyser()
            file = project_path + c_cpp_list['file']

            pro_path = project_path
            ninja_args = c_cpp_list['command'].split()[1:]
            main_file_analyser = file_analyser()
            main_file_analyser.run(file, pro_path, ninja_args, entry_funs=entry_funs, extend_analyze=True,
                                   anti_search=False, print_all_node=False)

def test12():
    # c_cpp_list = find_command_star_node('frameworks/av/media/libmediaplayerservice/MediaPlayerService.cpp')
    # entry_funs = ['MediaPlayerService::listenForRemoteDisplay(', 'Client::setDataSource(']
    # cpp = 'frameworks/av/services/camera/libcameraservice/CameraService.cpp'
    # cpp = 'frameworks/av/services/radio/RadioService.cpp'
    # cpp = 'AudioRecord.cpp'
    cpp = 'frameworks/av/services/audioflinger/AudioFlinger.cpp'
    # print(project_path)
    c_cpp_list = find_command_star_node(cpp.replace(project_path, ''), '7.0', compdb=True)
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
    ninja_args = c_cpp_list['command'].split()[1:]

    main_file_analyser.run(file, pro_path, ninja_args, entry_funs=entry_funs, extend_analyze=True, anti_search=False, print_all_node=False)

if __name__ == '__main__':
    # test0()
    # test00()
    # test000()
    # test1()
    # test2()
    # test3()
    # test4()
    # test5()
    # test6()
    # test7()
    # test9()

    # 批量JNI搜索
    # test11()

    # 单个permission或者uid pid提取
    test12()

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
