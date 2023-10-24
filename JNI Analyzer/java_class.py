# coding=utf-8

import os
import re
import json

def findAllFile(base, extension):
    for root, ds, fs in os.walk(base):
        for f in fs:
            if f.endswith('.' + extension) and 'tests/' not in root and 'test/' not in root:
                    # and 'test/' not in root \
                    # and 'out/' not in root \
                    # and 'tests/' not in root \
                    # and 'development/' not in root \
                    # and 'packages/' not in root\
                    # and 'device/' not in root:
                # if not re.match(r'.*\d.*', f):
                    fullname = os.path.join(root, f)
                    yield fullname

def get_class(path):
    with open(path, 'r', encoding='UTF-8') as file:  # 转换编码以实现正确输出中文格式
        lines = file.readlines()

        analyze_this_file = False
        for i, line in enumerate(lines):
            if 'ServiceManager.getService(' in line:
                analyze_this_file = True
        if not analyze_this_file:
            return None

        # 找左右大括号
        left_pos = []
        pair = []
        package = ''
        package_finded = False
        service_line = -1
        ignore_mode = False
        for i, line in enumerate(lines):
            line = line.strip()
            # print(i, line, end='')
            tem_r = re.findall("/\*.+?\*/", line)
            for r in tem_r:
                line = line.replace(r, '')
            # 去掉字符串
            tem_r = re.findall(r"\".{0,}?[^\\]\"", line)
            for r in tem_r:
                line = line.replace(r, '')
            tem_r = re.findall(r'\'.{0,}?[^\\]\'', line)
            for r in tem_r:
                line = line.replace(r, '')
            tem_r = re.findall(r'//.+', line)

            for r in tem_r:
                line = line.replace(r, '')
            if '/*' in line:
                ignore_mode = True
            if '*/' in line:
                ignore_mode = False
                tem_r = re.findall(".+?\*/", line)
                for r in tem_r:
                    line = line.replace(r, '')

            if ignore_mode:
                # print('')
                continue
            # if line.startswith('*') or line.startswith('//') or line.startswith('/*') or ignore_mode:
            #     print('')
            #     if '/*' in line:
            #         ignore_mode = True
            #     if '*/' in line:
            #         ignore_mode = False
            #     continue


            lines[i] = line

            if 'package ' in line and not package_finded:
                package_finded = True
                package = line.strip().replace('package ', '').replace(';', '')
                # print(package)

            if ' ServiceManager.getService(' in line or line.startswith('ServiceManager.getService('):
                service_line = i

            pos1 = find_all(line, '{')
            pos2 = find_all(line, '}')
            # 先处理本行的{}的位置
            # 如果有} 先检测本行前有无{ 如果没有 pop上一个 如果有则就近成对
            # 剩下的{ 加入pos

            goon = True
            while goon:
                goon = False
                for end_pos in pos2:
                    for start_pos in pos1:
                        if start_pos < end_pos:
                            pos1.remove(start_pos)
                            pos2.remove(end_pos)
                            pair.append([i, i])
                            goon = True


            for tem in pos1:
                # left_pos.append(str(i) + '_' + str(tem))
                left_pos.append(i)
                # print('||||find {', i, end='')

            for tem in pos2:
                # print('||||find }', i, end='')
                # 如果在本行有}只能闭合在其index前的{
                if len(left_pos) == 0:
                    raise Exception('miss {')
                pos = left_pos.pop()
                pair.append([pos, i])

            # print('')

        if len(left_pos) !=0:
            raise Exception('miss }')

        # 找class
        classes = {}
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('*') or line.startswith('//') or line.startswith('/*'):
                continue
            if ' class ' in line and '"' not in line or line.startswith('class '):
                # print('line.', i, line)
                line_index_tem = i
                class_cache = line
                while line_index_tem < len(lines) and len(find_all(lines[line_index_tem], '{'))==0:
                    line_index_tem = line_index_tem + 1
                    class_cache = class_cache + ' ' +lines[line_index_tem]

                class_cache = class_cache.replace('\n', '')
                # a = re.findall(r"class[ ][a-zA-Z0-9_]+(<.+>)*[ {]", class_cache)
                a = re.findall(r"class[ ][a-zA-Z0-9_]+[ <{]", class_cache)
                # if len(a) ==0:
                #     print(class_cache)
                class_name = a[0].strip()
                class_name = class_name.replace('class ', '').replace('{', '').replace('<', '').strip()

                for tem in pair:
                    left = tem[0]
                    right = tem[1]

                    if left == line_index_tem:
                        print(class_name, left, right)
                        classes[class_name] = [left, right]


        def find_outer_class(keys, dic, c_key, visited):
            if len(visited) == len(keys):
                return ''
            start = dic[c_key][0]
            end = dic[c_key][1]
            outer = None
            for k in keys:
                # print(k, classes[k][0], classes[k][1])
                if classes[k][0] < start and classes[k][1] > end:
                    outer = k
                    visited.append(outer)
            if outer != None:
                return find_outer_class(keys, dic, outer, visited) + '$' + outer
            return ''

        full_name_list = []
        keys = classes.keys()
        for k in keys:
            outer_class = find_outer_class(keys, classes, k, [k])
            full_class = outer_class + '$' + k
            if full_class.startswith('$'):
                full_class = full_class[1:]
            # print(package + '.' + full_class, classes[k][0], classes[k][1])
            full_name_list.append([full_class, package + '.', classes[k][0], classes[k][1]])

        min_line_num = 10e10
        best = None
        for tem in full_name_list:
            if service_line > tem[2] and service_line < tem[3] and tem[3] - tem[2] < min_line_num:
                min_line_num = tem[3] - tem[2]
                best = tem

        return best



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

def save():
    # a = '}} {{}} {'
    # pos1 = find_all(a, '{')
    # pos2 = find_all(a, '}')
    # goon = True
    # while goon:
    #     goon = False
    #     for end_pos in pos2:
    #         for start_pos in pos1:
    #             if start_pos < end_pos:
    #                 pos1.remove(start_pos)
    #                 pos2.remove(end_pos)
    #                 goon = True
    #
    # print('{', pos1)
    # print('}', pos2)

    # f = '/Volumes/android/android-8.0.0_r34/frameworks/base/core/java/android/hardware/camera2/CameraManager.java'
    # r = get_class(f)
    # if r != None:
    #     print()
    #     print(f)
    #     print('Static String mainClassStrLast = "' + r[0] + '"')
    #     print('Static String mainClassStr = "' + r[1] + '" + mainClassStrLast')

    list = []

    base = '/Volumes/android/android-8.0.0_r34/frameworks/'
    java_files = findAllFile(base, 'java')
    for f in java_files:
        r = get_class(f)
        if r!= None:
            print()
            print(f)
            print('String filePath = "%s";' % f)
            print('String mainClassStrLast = "' + r[0] + '";')
            print('String mainClassStr = "' + r[1] + '" + mainClassStrLast;')
            print('CppLink.run(mainClassStrLast, mainClassStr);')
            list.append({'last': r[0],
                         'base': r[1],
                         'file_path':f})

    base = '/Volumes/android/android-8.0.0_r34/sdk/'
    java_files = findAllFile(base, 'java')
    for f in java_files:
        r = get_class(f)
        if r != None:
            print()
            print('String filePath = "%s";' % f)
            print('String mainClassStrLast = "' + r[0] + '";')
            print('String mainClassStr = "' + r[1] + '" + mainClassStrLast;')
            print('CppLink.run(mainClassStrLast, mainClassStr);')
            list.append({'last': r[0],
                         'base': r[1],
                         'file_path': f})

    print('FOUND:', len(list))
    json_str = json.dumps({'array': list})
    with open('java_class/java_class.json', 'w', encoding='UTF-8') as file:
        file.write(json_str)
    with open('/Users/chaoranli/IdeaProjects/aosp_java_analyser/javaClass/java_class.json', 'w', encoding='UTF-8') as file:
        file.write(json_str)

def load():
    file = open('java_class/java_class.json', 'r', encoding='UTF-8')
    json_str = file.read()
    json_obj = json.loads(json_str)
    array = json_obj['array']
    total = len(array)
    print('total:', total)
    i = 0
    for obj in array:
        i = i + 1
        print()
        print(i, '/', total)
        last = obj['last'].replace('$', '\$')
        base = obj['base'].replace('$', '\$')
        print(obj['file_path'])
        print(last)
        print(base)
        cmd = 'java -jar /Users/chaoranli/IdeaProjects/aosp_java_analyser/out/artifacts/findCppLink/findCppLink.jar "%s" "%s" > %s' % (last, base, "log/"+base+last+'.txt')
        print(cmd)
        os.system(cmd)
        # exit(2)

if __name__ == '__main__':
    # save()
    load()
    pass