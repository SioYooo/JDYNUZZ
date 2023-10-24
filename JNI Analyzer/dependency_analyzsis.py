import json
import os
from os import path
import copy

dependency_involved_apis = set()
dependency_involved_rule = set()



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
# tem = {'java_sig': '(Ljava/lang/Object;Ljava/lang/String;Ljava/lang/String;IIILjava/lang/String;[I[Ljava/lang/Object;Landroid/os/Parcel;Z)I'}
# l = tem['java_sig'].split(')')
# parList = l[0].strip('(').replace('"', '')
# pars = parList.split(';')
# print(pars)
# parList_output = []
# for par in pars:
#     # print('3243 | ', par)
#     par_tranformed = transformSmaliType(par)
#     parList_output.extend(par_tranformed)
# print(parList_output)
# exit(0)

def check_dependency_temp(url="/hci/chaoran_data/jni/dependency/temp/"):
    file  = os.listdir(url)
    for f in file:
        real_url = path.join (url , f)
        if path.isfile(real_url):
            print(path.abspath(real_url))
            # 文本以.json结尾
            if path.abspath(real_url).endswith('.json'):
                print(path.abspath(real_url))
                with open(path.abspath(real_url), 'r') as f:
                    data = json.load(f)
                    jni_methods = data['jni_methods']
                    for jni_method in jni_methods:
                        java_signature = jni_method['java_sig']
                        java_fun_full = jni_method['java_fun_full']

                        l = java_signature.split(')')
                        parList = l[0].strip('(').replace('"', '')
                        returnType = l[1].replace('"', '')
                        pars = parList.split(';')
                        print(pars)
                        parList_output = []
                        for par in pars:
                            # print('3243 | ', par)
                            par_tranformed = transformSmaliType(par)
                            parList_output.extend(par_tranformed)

                        parstr = ''
                        for tem in parList_output:
                            parstr = parstr + tem + ', '
                        parstr = parstr[0:-2]

                        return_tranformed = transformSmaliType(returnType)
                        java_class = java_fun_full.split(' ')[0]
                        java_return = return_tranformed[0].replace(';', '')
                        java_fun = jni_method['java_fun']
                        java_fun_full = java_class + ' ' + java_return + ' ' + java_fun + '(' + parstr + ')'
                        # if parstr!='':
                        #     print(java_fun_full)
                        #     exit(0)
                        jni_method['java_fun_full'] = java_fun_full

                    data['jni_methods'] = jni_methods
                with open(path.abspath(real_url), 'w') as f:
                    json.dump(data, f)

check_dependency_temp()

def get_java_method(data, cfun):
    jni_methods = data['jni_methods']
    for tem in jni_methods:
        if tem['cpp_fun'] in cfun:
            java_fun_full = tem['java_fun_full']
            java_fun_full = java_fun_full.replace(';', '')
            java_fun_full = java_fun_full.replace('()(),', '[][],')
            java_fun_full = java_fun_full.replace('(),', '[],')
            java_fun_full = java_fun_full.replace('())', '[])')
            return java_fun_full
    return None

def scaner_file (url):
    file  = os.listdir(url)
    for f in file:
        real_url = path.join (url , f)
        if path.isfile(real_url):
            print(path.abspath(real_url))
            # 文本以.json结尾
            if path.abspath(real_url).endswith('.json'):
                print(path.abspath(real_url))
                with open(path.abspath(real_url), 'r') as f:
                    data = json.load(f)
                    dependency = data['dependency']
                    for tem in dependency:
                        java_fun0 = get_java_method(data, tem[0])
                        java_fun1 = get_java_method(data, tem[1])

                        if java_fun0 is None:
                            tem[0] = 'cfun!' + tem[0]
                        if java_fun1 is None:
                            tem[1] = 'cfun!' + tem[1]

                        if java_fun0 is not None and java_fun1 is not None:
                            if not tem[0].startswith('cfun!register_') and not tem[1].startswith('cfun!register_') and tem[0] != tem[1]:
                                dependency_involved_apis.add(java_fun0)
                                dependency_involved_apis.add(java_fun1)
                                dependency_involved_rule.add((java_fun0 + '|' + java_fun1))
                        elif java_fun0 is None and java_fun1 is not None:
                            # 一个普通方法到jni
                            if not tem[0].startswith('cfun!register_'):
                                dependency_involved_apis.add(java_fun1)
                                dependency_involved_rule.add(('cfun!'+tem[0] + '|' + java_fun1))
                        elif java_fun0 is not None and java_fun1 is None:
                            # 一个jni到普通方法
                            if not tem[1].startswith('cfun!register_'):
                                dependency_involved_apis.add(java_fun0)
                                dependency_involved_rule.add((java_fun0 + '|' + 'cfun!' + tem[1]))
                        elif java_fun0 is None and java_fun1 is None:
                            # 普通方法到普通方法
                            if not tem[0].startswith('cfun!register_') and not tem[1].startswith('cfun!register_'):
                                dependency_involved_rule.add(('cfun!' + tem[0] + '|' + 'cfun!' + tem[1]))

                    # print(data)
            # 如果是文件，则以绝度路径的方式输出
        elif path.isdir(real_url):
            #如果是目录，则是地柜调研自定义函数 scaner_file (url)进行多次
            scaner_file(real_url)
        else:

            print("其他情况")
            pass
        print(real_url)

scaner_file("/hci/chaoran_data/jni/dependency/temp/")



# print('dependency_involved_apis (set) = ', len(dependency_involved_apis))
# print('dependency_involved_rule (set) = ', len(dependency_involved_rule))

# print(dependency_involved_rule)
dependency_involved_rule_json_tem = []
for tem in dependency_involved_rule:
    array = tem.split('|')
    if array[0] != array[1]:
        dependency_involved_rule_json_tem.append([array[0], array[1]])
# 拼接普通方法
dependency_involved_rule_json = []

# def look_for_not_c_fun(head, tail, visited):
#     # 如果 头是jni1，尾是cpp1。找同样的头是jni2，尾是cpp2。中间可以cpp1-》cpp2或对调，那么就是JNI1->jni2或对调
#     for tem2 in dependency_involved_rule_json_tem:
#         # 新尾和旧头是相同的
#         # 如果头为cpp，那么尾也是cpp, 头和之前的尾相同,则找尾
#         if tem2[0].startswith('cfun!') and tem2[1].startswith('cfun!'):
#             if tem2[0] == tail:
#                 if tem2[1] not in visited:
#                     new_visited = copy.deepcopy(visited)
#                     new_visited.append(tem2[1])
#                     look_for_not_c_fun(head, tem2[1], new_visited)
#         # 如果头为jni，尾为cpp，尾和上一个尾相同，则jni为后置位
#         elif not tem2[0].startswith('cfun!') and tem2[1].startswith('cfun!'):
#             if tem2[1] == tail and head != tem2[0]:
#                 dependency_involved_rule_json.append([head, tem2[0]])

def look_for_not_c_fun(head, tail, visited):
    # 如果 头是jni1，尾是cpp1。找尾是jni
    for tem2 in dependency_involved_rule_json_tem:
        # 旧尾 是 cpp，旧尾和新头相同，新尾是cpp，则继续找
        if tem2[0].startswith('cfun!') and tem2[1].startswith('cfun!'):
            if tem2[0] == tail:
                if tem2[1] not in visited:
                    new_visited = copy.deepcopy(visited)
                    new_visited.append(tem2[1])
                    look_for_not_c_fun(head, tem2[1], new_visited)
        # 如果头为cpp，尾为jni，头和上一个尾相同, 最开始的头和新尾组对
        elif tem2[0].startswith('cfun!') and not tem2[1].startswith('cfun!'):
            if tem2[0] == tail and head != tem2[1]:
                dependency_involved_rule_json.append([head, tem2[1]])

def isCPPfun(tem):
    if tem.startswith('cfun!'):
        return True
    else:
        return False

# for tem in dependency_involved_rule_json_tem:
#     # 如果 头是jni1，尾是cpp1。找同样的头是jni2，尾是cpp2。中间可以cpp1-》cpp2或对调，那么就是JNI1->jni2或对调
#     if not tem[0].startswith('cfun!') and tem[1].startswith('cfun!'):
#         look_for_not_c_fun(tem[0], tem[1], visited=[tem[1]])
#
#     # 头 jni 尾 jni
#     if not tem[1].startswith('cfun!') and not tem[0].startswith('cfun!') and tem[0] != tem[1]:
#         dependency_involved_rule_json.append(tem)

for tem in dependency_involved_rule_json_tem:
    # 如果 头是jni1，尾是cpp1。找尾是jni
    if not tem[0].startswith('cfun!') and tem[1].startswith('cfun!'):
        look_for_not_c_fun(tem[0], tem[1], visited=[tem[1]])

    # 头 jni 尾 jni
    if not tem[1].startswith('cfun!') and not tem[0].startswith('cfun!') and tem[0] != tem[1]:
        dependency_involved_rule_json.append(tem)

involved_apis = set()
dependency_involved_rule_json_new = []
unique = set()
for tem in dependency_involved_rule_json:
    unique.add(tem[0] + '|' + tem[1])
for tem in unique:
    tem = tem.split("|")
    dependency_involved_rule_json_new.append({'A': tem[0], 'B': tem[1]})
    involved_apis.add(tem[0])
    involved_apis.add(tem[1])

# print('dependency_involved_apis (set) = ', len(dependency_involved_apis))
print('involved_apis (set) = ', len(involved_apis))
print('dependency_involved_rule (set) = ', len(dependency_involved_rule_json_new))



# 将边组合在一起
# 找到所有子节点
edge = {}
is_children_check_set = set()
for api in involved_apis:
    for tem in dependency_involved_rule_json_new:
        a = tem['A']
        b = tem['B']
        if api == a:
            if api not in edge.keys():
              edge[api] = []
            edge[api].append(b)
            is_children_check_set.add(b)

# print(edge)
# exit(0)

# 找到顶点 (没有父节点)
parent = []
for node in edge.keys():
    if node not in is_children_check_set:
        parent.append(node)

# print(parent)
# exit(0)

def add_child_graph(node, graph, visited):
    # 如果有子节点，没有就到头了
    if node in edge:
        for child in edge[node]:
            if child not in visited:
              tem_graph = {}
              tem_graph[child] = []
              graph.append(tem_graph)
              visited_new = copy.deepcopy(visited)
              visited_new.append(child)
              add_child_graph(child, tem_graph[child], visited_new)

graphs = []
# 从父节点开始
for node in parent:
    graph = {}
    graph[node] = []
    graphs.append(graph)
    add_child_graph(node, graph[node], visited=[node])

print('总', graphs)


paths = []


def get_child_nodes(node_list, depth, visited):
  depth = depth + 1
  if len(node_list) == 0:
    print('END', visited, len(visited)-1)
    paths.append(visited)
  for node in node_list:
    node_str = list(node.keys())[0]
    visited_new = copy.deepcopy(visited)
    visited_new.append(node_str)
    print(depth, '|' + ' ' * depth + node_str, visited_new)
    nodes = node[node_str]
    get_child_nodes(nodes, depth, visited_new)
    print()

get_child_nodes(graphs, -1, [])

total_path_length = 0
max_path_length = 0

start_node = set()
max_path_length_in_each_group = {}
for path in paths:
  path_length = len(path) - 1
  if path_length > max_path_length:
    max_path_length = path_length
  total_path_length = total_path_length + path_length

  if path[0] not in start_node:
    start_node.add(path[0])
    max_path_length_in_each_group[path[0]] = path_length
  else:
    if path_length > max_path_length_in_each_group[path[0]]:
      max_path_length_in_each_group[path[0]] = path_length


print('len(start_node),应和图的数量相同',len(start_node))
print('path的个数:', len(paths))
print('图的数量:', len(parent))
print('总path长度/图个数:', total_path_length, '/', len(parent), '=', total_path_length/len(parent))
max_path_length_in_each_group_list = list(max_path_length_in_each_group.values())
print('图中的深度均值:', max_path_length_in_each_group_list, '=>', sum(max_path_length_in_each_group_list), '/', len(max_path_length_in_each_group_list), '=', sum(max_path_length_in_each_group_list) / len(max_path_length_in_each_group_list))
print('图中深度(最长走到底路径长度):', max_path_length)

with open('dependency/dependency_api_call_sequence_graphs.json', 'w') as f:
    json.dump(graphs, f)

paths_obj = []
for path in paths:
    paths_obj.append({'path':path})
with open('dependency/dependency_api_call_sequence_paths.json', 'w') as f:
    json.dump(paths_obj, f)
# exit(0)

print('COMPLETE')

with open('dependency/dependency_api_call_sequence.json', 'w') as f:
    json.dump(dependency_involved_rule_json_new, f)