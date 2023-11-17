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
from helper import get_file, find_c_or_cpp, find_files, find_command, find_command_star_node
import re
import pickle
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
Config.set_library_file("/Volumes/android/android-8.0.0_r34/prebuilts/clang/host/darwin-x86/clang-4053586/lib64/libclang.dylib")
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

    def show_info(self, node, cur_fun=None, depth=0, print_node=False):
        # and node.kind == CursorKind.STRING_LITERAL
        # if node.location.file and self.print_all_node and self.pro_path in node.location.file.name and self.is_template(node):
        #     t = node.type
        #     print(t.kind, t.spelling, t.get_num_template_arguments())
        #     print(t.get_template_argument_type(0).spelling)
        if 'addService' in node.spelling:
            print_node = True
        if node.location.file and (self.print_all_node or print_node) and self.pro_path in node.location.file.name:
            print('%2d' % depth + ' ' * depth, node.kind, node.displayname, end='')
            type = node.type
            print('|type:', type.kind, end='')
            # if node.kind.is_reference():
            #     ref_node = node.get_definition()
            #     print(ref_node.spelling)
            if node.kind == CursorKind.CALL_EXPR:
                o=0
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
                for tem in ooo:
                    print('|', tem.kind, tem.spelling, end=' ')
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
        if n.is_virtual_method():
            v = ' virtual'
        if n.is_pure_virtual_method():
            v = ' = 0'
        if self.show_loc:
            return self.fully_qualified_pretty(n) + v + "|" + str(n.location)
        else:
            return self.fully_qualified_pretty(n) + v

    # def search_fun(self, fun_name):
    #     for k, v in self.FULLNAMES.items():
    #         if fun_name in k:
    #             for fff in v:
    #                 print('Found fun -> ' + fff)

    def get_para(self, node):
        if node is None:
            return None

        if self.pro_path in node.location.file.name:
            if node.kind == CursorKind.DECL_REF_EXPR:
                node = node.referenced

            if node is None:
                return None

            if node.kind == CursorKind.STRING_LITERAL:
                return node.spelling

            if node.kind == CursorKind.INTEGER_LITERAL:
                value = node.get_tokens()
                for v in value:
                    return v.spelling

            for n in node.get_children():
                return_str = self.get_para(n)
                if return_str is not None:
                    return return_str
        return None

    def print_childrens(self, node, depth):
        if node is not None and self.pro_path in node.location.file.name:
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
                print()

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
                    self.print_childrens(n, depth=depth+1)


    def print_calls(self, fun_name, so_far, last_node, depth=0):
        if fun_name in self.CALLGRAPH:
            for f in self.CALLGRAPH[fun_name]:
                node = f
                f = f.referenced
                # string被忽略了
                if(self.pro_path in f.location.file.name):
                    log = self.pretty_print(f)
                    current_depth = depth
                    if 'check' in log and 'Permission' in log:
                        print('%2d' % current_depth, ' ' * (depth + 1) + log, end='')
                        permission_str = self.get_para(node)
                        print('|||[%s]' % permission_str)
                        log = log + '|||[%s]' % permission_str
                    elif 'addService' in log:
                        print('%2d' % current_depth, ' ' * (depth + 1) + log)
                        # print('***')
                        # self.print_childrens(node, current_depth+2)
                        # print('***')

                    else:
                        if 'instantiate' in log:
                            oo = 0
                        print('%2d' % current_depth, ' ' * (depth + 1) + log)

                    self.html_log.append([depth, log])

                    if f in so_far:
                        continue
                    so_far.append(f)
                    if self.fully_qualified_pretty(f) in self.CALLGRAPH:
                        self.print_calls(self.fully_qualified_pretty(f), so_far, self.pretty_print(f), depth + 1)
                    else:
                        self.print_calls(self.fully_qualified(f), so_far, self.pretty_print(f),  depth + 1)
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
                ninja_args[i] = ninja_args[i].replace('-I', '-I/Volumes/android/android-8.0.0_r34/')
            if i > 0 and ninja_args[i-1] == '-I' or ninja_args[i-1] == '-isystem' or ninja_args[i-1] == '-o' or ninja_args[i-1] == '-MF':
                ninja_args[i] = '/Volumes/android/android-8.0.0_r34/' + ninja_args[i]
            if '-fsanitize-blacklist=' in ninja_args[i]:
                ninja_args[i] = ninja_args[i].replace('-fsanitize-blacklist=', '-fsanitize-blacklist=/Volumes/android/android-8.0.0_r34/')
            # print(tem_args[i])
        return ninja_args

    def load_cfg_normal(self, index, file, args):

        syspath = ccsyspath.system_include_paths('clang++')
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

    def load_cfg(self,index, compiler, file, ninja_args):
        print(compiler)
        if 'clang++' in compiler:
            init_args = ['-isystem/Volumes/android/android-8.0.0_r34/prebuilts/clang/host/darwin-x86/clang-4053586/lib64/clang/5.0.300080/include']
            ninja_args = init_args + ninja_args
            for i in range(len(ninja_args)):
                if '\\' in ninja_args[i]:
                    print(ninja_args[i])
                    # 两边加双引号 flag中的双引号 才可以被正确识别
                    ninja_args[i] = '"' + ninja_args[i] + '"'
                    print(ninja_args[i])

        tu = index.parse(file, ninja_args)
        # args = ninja_args
        # command = '/Volumes/android/android-8.0.0_r34/prebuilts/clang/host/darwin-x86/clang-4053586/bin/clang++ -v ' + str(args).replace('[', '').replace(']', '').replace('\'', '').replace(',', '').replace('-Wa--noexecstack','-Wa,--noexecstack').replace(r'-DLOG_TAG=\\"libagl\\"', r'"-DLOG_TAG=\"libagl\""') + ' ' + file
        # print(command+'++++++++++')
        # b = os.popen(command)
        # text2 = b.read()
        # print(text2)
        # b.close()

        for d in tu.diagnostics:
            if d.severity == d.Error or d.severity == d.Fatal:
                print(d)
                raise Exception('aaaaaaaaaaaaaaaaaa')
            else:
                print(d)

        self.show_info(tu.cursor)
        return tu

    def run(self, file_str, pro_path,  ninja_args, entry_funs=None, IS_AOSP=True, extend_analyze=True, show_loc=False, print_all_node=False, generate_html=False):
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

        print('===========SEARCH INLCUDE FILE=============')

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
        # for tem in self.CALLGRAPH:
        #     # 应限定在改cpp文件中
        #     print('***** start node *****', tem)



        not_sys_include_paths = []
        for tem in tu.get_includes():
            include_path = tem.include.name

            if IS_AOSP:
                if self.pro_path + 'frameworks' in include_path:
                    not_sys_include_paths.append(include_path)
            else:
                if self.pro_path in include_path:
                    not_sys_include_paths.append(include_path)

        i = 0

        if extend_analyze:
            for tem in not_sys_include_paths:
                i = i+1
                print('***************')
                print('Loading CFG ... ', i, '/', len(not_sys_include_paths))

                # print("*.h:", tem)
                if IS_AOSP:
                    c_cpp_list = find_command(tem)
                    if c_cpp_list is not None:
                        next_file = '/Volumes/android/android-8.0.0_r34/' + c_cpp_list['source']
                        ninja_args = c_cpp_list['content']['flags']
                        ninja_args = self.parse_ninja_args(ninja_args)
                        # print(next_file)
                        # print(ninja_args)
                        self.load_cfg(index, c_cpp_list['content']['compiler'], next_file, ninja_args)
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

        print('====print CFG=====')

        collect_all_fun = False
        if entry_funs is None or len(entry_funs) == 0:
            collect_all_fun = True
        for tem in self.CALLGRAPH:
            if collect_all_fun:
                pass
            # print(tem)

        html = ''
        for entry_fun in entry_funs:
            if entry_fun in self.CALLGRAPH:
                print(entry_fun)
                # if 'permission' in entry_fun:
                #     raise Exception('!!!!!!!!found permission check function!!!!!!!')
                self.html_log = []
                self.print_calls(entry_fun, list(), None)

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


def aosp():
    main_file_analyser = file_analyser()
    # analyze cpp
    file = '/Volumes/android/android-8.0.0_r34/frameworks/av/services/camera/libcameraservice/api2/CameraDeviceClient.cpp'
    main_file_analyser.run(file)

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

    main_file_analyser.run(file, pro_path, ninja_args, entry_funs, extend_analyze=True, print_all_node=True, generate_html=False)

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
    c_cpp_list = find_command_star_node('frameworks/av/services/camera/libcameraservice/CameraService.cpp')
    c_cpp_list = c_cpp_list[0]

    # out/soong/build.ninja
    main_file_analyser = file_analyser()
    # analyze cpp
    file = '/Volumes/android/android-8.0.0_r34/' + c_cpp_list['source']

    pro_path = '/Volumes/android/android-8.0.0_r34/'
    ninja_args = c_cpp_list['content']['flags']

    entry_funs = ['android::CameraService::connectDevice(const sp<> &, const android::String16 &, const android::String16 &, int, sp<> *)']
    # entry_funs = ['android::CameraService::connectHelper(const sp<CALLBACK> &, const android::String8 &, int, const android::String16 &, int, int, android::CameraService::apiLevel, bool, bool, sp<CLIENT> &)']
    # entry_funs = None
    main_file_analyser.run(file, pro_path, ninja_args, entry_funs, extend_analyze=False)

def test4():
    c_cpp_list = find_command_star_node('frameworks/av/camera/cameraserver/main_cameraserver.cpp')
    c_cpp_list = c_cpp_list[0]

    # out/soong/build.ninja
    main_file_analyser = file_analyser()
    # analyze cpp
    file = '/Volumes/android/android-8.0.0_r34/' + c_cpp_list['source']

    pro_path = '/Volumes/android/android-8.0.0_r34/'
    ninja_args = c_cpp_list['content']['flags']

    entry_funs = ['main(int, char **)']
    # entry_funs = ['android::CameraService::connectHelper(const sp<CALLBACK> &, const android::String8 &, int, const android::String16 &, int, int, android::CameraService::apiLevel, bool, bool, sp<CLIENT> &)']
    # entry_funs = None
    main_file_analyser.run(file, pro_path, ninja_args, entry_funs, extend_analyze=False, print_all_node=False, generate_html=False)

def test5():
    # analyser = file_analyser()
    index = Index.create()
    index.read('/Users/chaoranli/PycharmProjects/test/main2.ast')

if __name__ == '__main__':
    # test0()
    # test00()
    # test1()
    # test2()
    # test3()
    # test4()
    # test5()
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




    def find_template_class(name):
        for c in tu.cursor.walk_preorder():
            if (c.kind == CursorKind.CLASS_TEMPLATE) and (c.spelling == name):
                return c


    def inherits_from_template_class(node, base):
        for c in node.get_children():
            if c.kind != CursorKind.CXX_BASE_SPECIFIER:
                continue
            children = list(c.get_children())
            if len(children) != 2:
                continue
            if children[0].kind != CursorKind.TEMPLATE_REF:
                continue
            ctd = children[0].get_definition()
            if ctd == base:
                return True
        return False

    kTemplateArgTest = """
    template<class T>
    class Base { };
    class X1 : public Base<X1> {};
    class Y1 {};
    class X2 : public Y1 {};
        """

    '''
    TRANSLATION_UNIT tmp.cpp
      +--CLASS_TEMPLATE Base
      |  +--TEMPLATE_TYPE_PARAMETER T
      +--CLASS_DECL X1
      |  +--CXX_BASE_SPECIFIER Base<class X1>
      |     +--TEMPLATE_REF Base
      |     +--TYPE_REF class X1
      +--CLASS_DECL Y1
      +--CLASS_DECL X2
         +--CXX_BASE_SPECIFIER class Y1
            +--TYPE_REF class Y1
    
    1. For each class
    2. Find all it's children that have CXX_BASE_SPECIFIER kind
    3. For the base nodes, find all of those have two children (and one of those is has the kind TEMPLATE_REF)
    4. For the TEMPLATE_REF nodes, check if they have a common definition with the class template of interest.
    '''

    tu = get_tu(kTemplateArgTest, lang='cpp')

    base = find_template_class('Base')
    for c in tu.cursor.walk_preorder():
        if CursorKind.CLASS_DECL != c.kind:
            continue
        if inherits_from_template_class(c, base):
            print(c.spelling)