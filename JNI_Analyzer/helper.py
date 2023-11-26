import os.path
import numpy as np
import ccsyspath
from clang.cindex import Config
from clang.cindex import Index
import json


def get_file(base, extension):
    for root, ds, fs in os.walk(base):
        for f in fs:
            if f.endswith(extension):
                fullname = os.path.join(root, f)
                yield fullname


def find_files(path, extension):
    filename = 'tem/' + path.replace('/', '_') + '_' + extension + '_list.npy'
    if not os.path.exists(filename):
        list = []
        for i in get_file(path, extension):
            list.append(i)
        list = np.array(list)
        np.save(filename, list)

    list = np.load(filename)
    return list


def find_c_or_cpp(filename):
    list = []
    filename = '/' + os.path.basename(filename)

    filename = filename.replace('.h', '.c')
    c_list = find_files('/Volumes/android/android-8.0.0_r34', '.c')
    for tem in c_list:
        if filename in tem:
            list.append(tem)

    filename = filename.replace('.c', '.cpp')
    cpp_list = find_files('/Volumes/android/android-8.0.0_r34', '.cpp')
    for tem in cpp_list:
        if filename in tem:
            list.append(tem)
    return list


def get_cpp_files_path(compdb=False, version=''):
    list = []
    if compdb:
        # with open('tem/'+version+'compile_commands_full.json') as file_obj:
        # with open('tem/' + 'complie_commands_full.json') as file_obj:
        with open('/home/siyu/tifs/JDYNUZZ/JNI_Analyzer/tem/10.0compile_commands_full.json') as file_obj:
            js = json.load(file_obj)
            list.extend(js)

        # if os.path.exists('tem/' + version_prefix + 'out_build_ninja.json'):
        #     with open('tem/' + version + 'out_build_ninja.json') as file_obj:
        #         js = json.load(file_obj)
        #         list.extend(js)
        # if os.path.exists('tem/' + version_prefix + 'build-aosp_arm64.json'):
        #     with open('tem/' + version + 'build-aosp_arm64.json') as file_obj:
        #         js = json.load(file_obj)
        #         list.extend(js)

    else:
        if os.path.exists('tem/build-aosp_arm64.json'):
            with open('tem/build-aosp_arm64.json') as file_obj:
                js = json.load(file_obj)
                list.extend(js)
        if os.path.exists('tem/out_build_ninja.json'):
            with open('tem/out_build_ninja.json') as file_obj:
                js = json.load(file_obj)
                list.extend(js)

    return list


def find_command_star_node(filename, version_prefix, compdb=False):
    list = []
    if compdb:
        # with open('tem/' + version_prefix + 'compile_commands_full.json') as file_obj:
        with open('/home/siyu/tifs/JDYNUZZ/JNI_Analyzer/tem/10.0compile_commands_full.json') as file_obj:
            js = json.load(file_obj)

            cpp = filename.replace('.h', '.cpp')
            print('cpp:', cpp)
            c = filename.replace('.h', '.c')
            print('c:', c)
            for tem in js:
                if cpp in tem['file'] or c in tem['file']:
                    print('found cpp', cpp)
                    list.append(tem)
        # if os.path.exists('tem/'+version_prefix+'out_build_ninja.json'):
        #     with open('tem/' + version_prefix + 'out_build_ninja.json') as file_obj:
        #         js = json.load(file_obj)
        #         cpp = filename.replace('.h', '.cpp')
        #         c = filename.replace('.h', '.c')
        #         for tem in js:
        #             if cpp in tem['file'] or c in tem['file']:
        #                 list.append(tem)
        # if os.path.exists('tem/'+version_prefix+'build-aosp_arm64.json'):
        #     with open('tem/' + version_prefix + 'build-aosp_arm64.json') as file_obj:
        #         js = json.load(file_obj)
        #         cpp = filename.replace('.h', '.cpp')
        #         c = filename.replace('.h', '.c')
        #         for tem in js:
        #             if cpp in tem['file'] or c in tem['file']:
        #                 list.append(tem)
    else:
        with open('tem/' + version_prefix + 'build-aosp_arm64.json') as file_obj:
            js = json.load(file_obj)
            cpp = filename.replace('.h', '.cpp')
            c = filename.replace('.h', '.c')
            for tem in js:
                if cpp in tem['source'] or c in tem['source']:
                    list.append(tem)
        with open('tem/' + version_prefix + 'out_build_ninja.json') as file_obj:
            js = json.load(file_obj)
            cpp = filename.replace('.h', '.cpp')
            c = filename.replace('.h', '.c')
            for tem in js:
                if cpp in tem['source'] or c in tem['source']:
                    list.append(tem)

    return list


def cpp_exist_spefic_h(h, cpp, project_path):
    full_cpp = project_path + cpp
    with open(full_cpp) as lines:
        for l in lines:
            l = l.strip()
            if l.startswith('#include ') and os.path.basename(h) in l:
                print('.line 97|', h, cpp, l)
                return True
    return False


def find_command(file, version_prefix, compdb=False, project_path='/Volumes/android/android-8.0.0_r34/'):
    # h_file = file.replace(project_path, '')
    list = []
    if compdb:
        print('searching in ' + 'tem/' + version_prefix + 'compile_commands_full.json ' + ' ...')
        with open('tem/' + version_prefix + 'compile_commands_full.json') as file_obj:
            # Directory Then go to the command to find the directory exists and the file ends with cpp and add it
            # print('.line 98 .h:', h_file)
            # dir = os.path.dirname(h_file)
            # print('.line 99 dir:', dir)
            js = json.load(file_obj)
            filename = '/' + os.path.basename(file)
            cpp = filename.replace('.h', '.cpp')
            print('cpp:', cpp)
            c = filename.replace('.h', '.c')
            print('c:', c)
            for tem in js:
                if cpp in tem['file'] or c in tem['file']:
                    # if '.cpp' in tem['file'] and dir in tem['command']:
                    # if cpp_exist_spefic_h(h_file, tem['file'], project_path):
                    print('found cpp', cpp)
                    list.append(tem)

        # if os.path.exists('tem/' + version_prefix + 'out_build_ninja.json'):
        #     with open('tem/'+version_prefix+'out_build_ninja.json') as file_obj:
        #         # Directory Then go to the command to find the directory exists and the file ends with cpp and add it
        #         # print('.line 98 .h:', h_file)
        #         # dir = os.path.dirname(h_file)
        #         # print('.line 99 dir:', dir)
        #         js = json.load(file_obj)
        #         filename = '/' + os.path.basename(file)
        #         cpp = filename.replace('.h', '.cpp')
        #         print('cpp:', cpp)
        #         c = filename.replace('.h', '.c')
        #         print('c:', c)
        #         for tem in js:
        #             if cpp in tem['file'] or c in tem['file']:
        #                 # if '.cpp' in tem['file'] and dir in tem['command']:
        #                 # if cpp_exist_spefic_h(h_file, tem['file'], project_path):
        #                 print('foundcpp', cpp)
        #                 list.append(tem)
        #
        # if os.path.exists('tem/' + version_prefix + 'build-aosp_arm64.json'):
        #     with open('tem/'+version_prefix+'build-aosp_arm64.json') as file_obj:
        #         # Directory Then go to the command to find the directory exists and the file ends with cpp and add it
        #         # print('.line 98 .h:', h_file)
        #         # dir = os.path.dirname(h_file)
        #         # print('.line 99 dir:', dir)
        #         js = json.load(file_obj)
        #         filename = '/' + os.path.basename(file)
        #         cpp = filename.replace('.h', '.cpp')
        #         print('cpp:', cpp)
        #         c = filename.replace('.h', '.c')
        #         print('c:', c)
        #         for tem in js:
        #             if cpp in tem['file'] or c in tem['file']:
        #                 # if '.cpp' in tem['file'] and dir in tem['command']:
        #                 # if cpp_exist_spefic_h(h_file, tem['file'], project_path):
        #                 print('foundcpp', cpp)
        #                 list.append(tem)
    else:
        with open('tem/' + version_prefix + 'build-aosp_arm64.json') as file_obj:
            js = json.load(file_obj)
            filename = '/' + os.path.basename(file)
            cpp = filename.replace('.h', '.cpp')
            c = filename.replace('.h', '.c')
            for tem in js:
                if cpp in tem['source'] or c in tem['source']:
                    list.append(tem)
        with open('tem/' + version_prefix + 'out_build_ninja.json') as file_obj:
            js = json.load(file_obj)
            filename = '/' + os.path.basename(file)
            cpp = filename.replace('.h', '.cpp')
            c = filename.replace('.h', '.c')
            for tem in js:
                if cpp in tem['source'] or c in tem['source']:
                    list.append(tem)
    best_score = 0
    best_command = None
    for tem in list:
        print('.line 126', tem['file'])
        if compdb:
            a_ls = tem['file'].split('/')
        else:
            a_ls = tem['source'].split('/')
        print('.line 131', a_ls)
        print(project_path)
        print(file)
        b_ls = file.replace(project_path, '').split('/')
        print('.line 133', b_ls)
        min_len = min(len(a_ls), len(b_ls))
        print('.line 136', min_len)
        score = 0
        for i in range(min_len):
            if a_ls[i] == b_ls[i]:
                score = score + 1
        print('score', score)
        if score > best_score:
            best_score = score
            best_command = tem

    if best_command:
        print(best_command['file'])
    print('***** FOUND cpp ******')
    for tem in list:
        print(tem['file'])
    # exit(0)
    return best_command


def find_command_all_cpp(file, version_prefix, compdb=False, project_path='/Volumes/android/android-8.0.0_r34/'):
    h_file = file.replace(project_path, '')
    list = []
    if compdb:
        print('searching in ' + 'tem/' + version_prefix + 'compile_commands_full.json ' + ' ...')
        with open('tem/' + version_prefix + 'compile_commands_full.json') as file_obj:
            # Directory Then go to the command to find the directory exists and the file ends with cpp and add it
            print('.line 98 .h:', h_file)
            dir = os.path.dirname(h_file)
            print('.line 99 dir:', dir)
            js = json.load(file_obj)
            filename = '/' + os.path.basename(file)
            cpp = filename.replace('.h', '.cpp')
            print('cpp:', cpp)
            # c = filename.replace('.h', '.c')
            # print('c:', c)
            for tem in js:
                # if cpp in tem['file'] or c in tem['file']:
                if '.cpp' in tem['file'] and dir in tem['file']:
                    if cpp_exist_spefic_h(h_file, tem['file'], project_path):
                        list.append(tem)
        # if os.path.exists('tem/' + version_prefix + 'out_build_ninja.json'):
        #     with open('tem/' + version_prefix + 'out_build_ninja.json') as file_obj:
        #         # Directory Then go to the command to find the directory exists and the file ends with cpp and add it
        #         print('.line 98 .h:', h_file)
        #         dir = os.path.dirname(h_file)
        #         print('.line 99 dir:', dir)
        #         js = json.load(file_obj)
        #         filename = '/' + os.path.basename(file)
        #         cpp = filename.replace('.h', '.cpp')
        #         print('cpp:', cpp)
        #         # c = filename.replace('.h', '.c')
        #         # print('c:', c)
        #         for tem in js:
        #             # if cpp in tem['file'] or c in tem['file']:
        #             if '.cpp' in tem['file'] and dir in tem['command']:
        #                 if cpp_exist_spefic_h(h_file, tem['file'], project_path):
        #                     list.append(tem)
        # if os.path.exists('tem/' + version_prefix + 'build-aosp_arm64.json'):
        #     with open('tem/' + version_prefix + 'build-aosp_arm64.json') as file_obj:
        #         # Directory Then go to the command to find the directory exists and the file ends with cpp and add it
        #         print('.line 98 .h:', h_file)
        #         dir = os.path.dirname(h_file)
        #         print('.line 99 dir:', dir)
        #         js = json.load(file_obj)
        #         filename = '/' + os.path.basename(file)
        #         cpp = filename.replace('.h', '.cpp')
        #         print('cpp:', cpp)
        #         # c = filename.replace('.h', '.c')
        #         # print('c:', c)
        #         for tem in js:
        #             # if cpp in tem['file'] or c in tem['file']:
        #             if '.cpp' in tem['file'] and dir in tem['command']:
        #                 if cpp_exist_spefic_h(h_file, tem['file'], project_path):
        #                     list.append(tem)
    else:
        with open('tem/' + version_prefix + 'build-aosp_arm64.json') as file_obj:
            js = json.load(file_obj)
            filename = '/' + os.path.basename(file)
            cpp = filename.replace('.h', '.cpp')
            c = filename.replace('.h', '.c')
            for tem in js:
                if cpp in tem['source'] or c in tem['source']:
                    list.append(tem)
        with open('tem/' + version_prefix + 'out_build_ninja.json') as file_obj:
            js = json.load(file_obj)
            filename = '/' + os.path.basename(file)
            cpp = filename.replace('.h', '.cpp')
            c = filename.replace('.h', '.c')
            for tem in js:
                if cpp in tem['source'] or c in tem['source']:
                    list.append(tem)
    # best_score = 0
    # best_command = None
    # for tem in list:
    #     # print('.line 126', tem['file'])
    #     if compdb:
    #         a_ls = tem['file'].split('/')
    #     else:
    #         a_ls = tem['source'].split('/')
    #     print('.line 131', a_ls)
    #     print(project_path)
    #     print(file)
    #     b_ls = file.replace(project_path, '').split('/')
    #     print('.line 133', b_ls)
    #     min_len = min(len(a_ls), len(b_ls))
    #     print('.line 136', min_len)
    #     score = 0
    #     for i in range(min_len):
    #         if a_ls[i] == b_ls[i]:
    #             score = score + 1
    #     if score > best_score:
    #         best_score = score
    #         best_command = tem

    # print(best_command['file'])
    # print('***** FOUND cpp ******')
    # for tem in list:
    #     print(tem['file'])
    # exit(0)
    return list


if __name__ == '__main__':
    # h_list = find_files('/Volumes/android/android-8.0.0_r34', '.h')
    # c_list = find_files('/Volumes/android/android-8.0.0_r34', '.c')

    a = ['aaaaa', r'\"']
    print(a)
    print(a[1])
    aaa = a[1].replace(r'\\', '\\')
    print(a[1])
    a[1] = aaa
    print(a)
    # with open('tem/aaaa.json', 'w') as file_obj:
    #     json.dump(a, file_obj)
