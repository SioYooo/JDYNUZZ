# coding=utf-8

import datetime
import os
import shutil
from shutil import copyfile, copytree
import re

count_isCallingFunc = 0
bug_in_lib = {}
so_and_log = []
jni_interface_arr = []

cause_log_list = []
# cause_log_set = set()

bugs = {}


def list(path):
    # if not os.path.exists(path):
    #     os.makedirs(path)

    fs = os.listdir(path)
    l = []
    for f in fs:
        if not f.startswith('.') and not f.endswith('.pb'):
            l.append(path + f)
    # print(l)
    return l

def isJavaErr(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                # java报错
                if 'code -' in line:
                    return True
                # 成功执行
                elif 'code 0: success' in line:
                    return False
        # 有文件 无返回 程序崩溃或者超时杀掉
        return True
    else:
        return False

def ignore_info(tem):
    if 'I app_process64:' in tem:
        tem = tem[tem.index('I app_process64:') + len('I app_process64:'):]
        tem = tem.strip()
    return tem

def sanitizer_has_exist(lines):
    san_start = False
    stack_start = False
    error = ''
    stack0 = ''
    stack1 = ''
    stack2 = ''
    specific = ''
    is_specific = False
    # 清理行
    for i, line in enumerate(lines):
        lines[i] = ignore_info(lines[i])
    # 读行
    for i, line in enumerate(lines):
        # print(line)
        if san_start and not stack_start:
            if line.startswith("#"):
                stack_start = True
                stack0 = line
                stack0 = stack0[stack0.index('('):]
                if i+1<len(lines) and lines[i + 1].startswith("#"):
                    stack1 = lines[i + 1]
                    stack1 = stack1[stack1.index('('):]
                if i+2<len(lines) and lines[i + 2].startswith("#"):
                    stack2 = lines[i + 2]
                    stack2 = stack2[stack2.index('('):]

        if is_specific:
            if not line.startswith('==') and not line.startswith('Thread:'):
                specific = line
            is_specific = False
        if san_start and line == '':
            is_specific = True
            san_start = False
        if 'ERROR: HWAddressSanitizer:' in line:
            san_start = True
            error = line
        if line.startswith('SUMMARY:') and specific=='':
            specific = line

    # exit(0)
    '''
                04-04 14:08:28.247 12777 12796 I app_process64: ==12777==ERROR: HWAddressSanitizer: tag-mismatch on address 0x007a50b54cb0 at pc 0x007ac61b89f4
                04-04 14:08:28.247 12777 12796 I app_process64: READ of size 8 at 0x007a50b54cb0 tags: 00/08 (ptr/mem) in thread T34
        stack0            04-04 14:08:28.264 12777 12796 I app_process64:     #0 0x7ac61b89f0  (/apex/com.android.art/lib64/libart.so+0xbb89f0)
        stack1            04-04 14:08:28.264 12777 12796 I app_process64:     #1 0x7ac59c03e4  (/apex/com.android.art/lib64/libart.so+0x3c03e4)
        stack2           04-04 14:08:28.264 12777 12796 I app_process64:     #2 0x7ac59bfa4c  (/apex/com.android.art/lib64/libart.so+0x3bfa4c)
                04-04 14:08:28.264 12777 12796 I app_process64:     #3 0x7ad8b8464c  (/apex/com.android.art/lib64/libsigchain.so+0x264c)
                04-04 14:08:28.264 12777 12796 I app_process64:     #4 0x7af69c88ac  ([vdso]+0x8ac)
                
        specific            04-04 14:08:28.293 12777 12796 I app_process64: 0x007a50b54cb0 is located to the right of a global variable in ([anon:stack_and_tls:12796]+0x103ca0)
    '''
    # 处理标记
    # id = basename.replace('.txt', '')
    # id = re.sub('\|[0-9\- :]+', '', id)
    # print(id)
    # print(error)
    # if 'ERROR: HWAddressSanitizer:' not in error:
    #     unavailable = unavailable + 1
    #     continue
    error = error[error.index('ERROR: HWAddressSanitizer:')+len('ERROR: HWAddressSanitizer:'):]
    error = re.sub('0x[a-z0-9]+', '', error)
    error = error.strip()
    # print(error)
    #
    # print(stack0)
    # print(stack1)
    # print(stack2)

    # print(specific)
    specific = re.sub('0x[a-z0-9]+', '', specific)
    specific = re.sub('[0-9]+', '', specific)
    specific = specific.strip()
    # print(specific)

    # 重复的不加
    val = [error, stack0, stack1, stack2, specific, l]
    str = ' '
    key = str.join(val[:4])
    found = key in bugs.keys()
    # found = False
    # for bug in bugs:
    #     if bug[1] == error and bug[2] == stack0 and bug[3] == stack1 and bug[4] == stack2:
    #         found = True
    #         break

    if not found:
        bugs[key] = val

    return found

def save_tombstones_sanitizer(lines, path, isCalling):
    if not isCalling:
        return None

    goanalyze = True
    start_record = False
    str_sanitizer = ''
    objFileName = None
    separater = '--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---\n'

    found_signal_line = False

    single_log = ''

    for i,line in enumerate(lines):
        if '>>>' in line and '<<<' in line:
            # 获取文本从>>>到<<<
            text = line.split('>>>')[1].split('<<<')[0]
            if text != ' com.example.fuzzer ':
                print('CRASH FROM (NOT "com.example.fuzzer"): ' + text)
                print(path)

        # objFileName: 1651563423839
        if 'objFileName: ' in line:
            objFileName = line.split('objFileName: ')[1].strip()

        # --------------------
        # SANITIZER
        if 'ERROR: HWAddressSanitizer' in line:
            start_record = True
            str_sanitizer = str_sanitizer + separater
        if separater in line:
            start_record = False
        if line.startswith("'"):
            start_record = False
        if start_record:
            str_sanitizer = str_sanitizer + line
            if 'app_process64:     #' in line and goanalyze:
                goanalyze = False
                error_path = line.split('(')[1].split(')')[0]
                error_path = error_path.split('+')[0]
                libname = os.path.basename(error_path)
                # print(error_path)
                # print(libname)
                if 'libclang_rt.hwasan-aarch64-android' in libname:
                    goanalyze = True
                elif 'libc.so' in libname:
                    goanalyze = True
                else:
                    isjavaerr = False
                    if objFileName is not None:
                        isjavaerr = isJavaErr(objFileName + '.obj')
                    if not isjavaerr:
                        if libname == 'libmedia_jni.so':
                            print(lines[i-2:i+5])
                        if not sanitizer_has_exist(lines):
                            if '_runtime.so' in libname or '_jni.so' in libname:
                                print('&&&&&&&&&& for analysis &&&&&&&&&&', libname, path)
                            bug_in_lib[libname] = bug_in_lib.get(libname, 0) + 1
                            so_and_log.append({'libname': libname, 'path': path})
        # --------------------

        # --------------------
        # CAUSE
        if found_signal_line:
            # 是否是#开头     x0  fffffffffffffffa  x1  0000000000000002  x2  020000756331f685  x3  0040000da0008893
            if re.search(r'[x#][0-9]+\s+[0-9a-fx]+', line):
                found_signal_line = False
                if single_log != '':
                    cause_log_list.append(single_log)

        if found_signal_line:
            str_sanitizer = str_sanitizer + line
            single_log = single_log + line


        if re.search(r'signal [0-9]+ \([a-zA-Z_]+\), code [-]*[0-9]+ \([a-zA-Z_]+\), fault addr', line):
            found_signal_line = True



    if objFileName is None:
        print('objFileName is None', path)
        # return None

    if str_sanitizer != '' and separater in str_sanitizer:
        str_sanitizer = str_sanitizer.split(separater)
        # if str_sanitizer[1] == str_sanitizer[2]:
        #     print('objFileName', objFileName)
        #     print(str_sanitizer[1])
        # else:
        #     print('---------------str_sanitizer[1]----------------')
        #     print(str_sanitizer[1])
        #     print('---------------str_sanitizer[2]----------------')
        #     print(str_sanitizer[2])
        #     raise Exception('not equal: str_sanitizer[1] == str_sanitizer[2]')

        # if len(str_sanitizer) == 2:
        #     print(str_sanitizer[1])
        #     raise Exception('len(str_sanitizer) == 2')
        save_file_path = path.replace('tombstones/tombstone_', 'tombstones_sanitizer/tombstone_')
        # print(save_file_path+'.txt')
        with open(save_file_path+'.txt', 'w') as f2:
            if objFileName:
                f2.write('objFileName' + objFileName + '\n')
            f2.write(str_sanitizer[1])

def jni_interface(lines, path):
    className = None
    methodName = None
    res = None
    pars = None

    for line in lines:
        # invoke funtion indecator 1 这种是调用对象的成员函数
        if 'className: ' in line:
            className = line.split('className: ')[1].strip()
        elif 'methodName: ' in line:
            methodName = line.split('methodName: ')[1].strip()
        elif 'pars: ' in line:
            pars = line.split('pars: ')[1].strip()
        elif 'res(return): ' in line:
            res = line.split('res(return): ')[1].strip()


    if className is None or methodName is None:
        print('className or methodName is None', path)
        exit(0)

    full_method = className + ' ' + res + ' ' + methodName + '(' + pars + ')'
    jni_interface_arr.append({'className':className, 'methodName':methodName, 'res':res, 'pars':pars, 'full_method':full_method})


def isCallingFunc(lines, path):
    global count_isCallingFunc

    found = False
    # invoke funtion indecator 1
    indecator1 = False
    for line in lines:
        # invoke funtion indecator 1 这种是调用对象的成员函数
        if indecator1 and 'clazzObj: false' in line:
            # print('===DUBUG===', line)
            found = True # 6个在这种情况里面
            break
        if 'invoke funtion indecator 1' in line:
            indecator1 = True
        if 'invoke funtion indecator 2' in line:
            found = True
            break
        if 'invoke funtion indecator 3' in line:
            print('FOUND invoke funtion indecator 3\n', line)
            found = False
            # exit(0)


    if found:
        count_isCallingFunc = count_isCallingFunc + 1
        print(count_isCallingFunc)
        save_file_path = path.replace('tombstones/tombstone_', 'isCallingFunc/tombstone_')
        # print(save_file_path+'.txt')
        with open(save_file_path+'.txt', 'w') as f2:
            f2.write('TRUE')

    return found

def ignore(lines):
    for line in lines:
        if 'SEGV_ACCERR' in line:
            return True
        if 'methodName: heapUseAfterFree' in line: # 自己埋点的错误
            return True
    return False

def process_tomb(path):
    with open(path, 'r') as f:
        lines = f.readlines()
        if ignore(lines):
            return None

        isCalling = isCallingFunc(lines, path)
        save_tombstones_sanitizer(lines, path, isCalling)
        jni_interface(lines, path)


def RemoveDir(filepath):
    '''
    如果文件夹不存在就创建，如果文件存在就清空！

    '''
    if not os.path.exists(filepath):
        os.mkdir(filepath)
    else:
        shutil.rmtree(filepath)
        os.mkdir(filepath)

def rename_crash_log_with_objfile(path):
    fs = os.listdir(path)
    l = []
    for f in fs:
        if not f.startswith('.'):
            print(path + f + '/crash_log')
            logs = os.listdir(path + f + '/crash_log')
            for log in logs:
                if not log.startswith('.'):
                    # print(path + f + '/crash_log/' + log)
                    l.append(path + f + '/crash_log/' + log)
    # exit(0)

    for t in l:
        lines = None
        with open(t, 'r') as f:
            lines = f.readlines()
        # if ignore(lines):
        #     continue

        objFileName = None
        for line in lines:
            if 'objfileName: ' in line:
                objFileName = line.split('objfileName:')[1].strip()
                break

        if objFileName is not None:
            src_path = t
            dst_path = os.path.dirname(t).replace('crash_log', 'crash_log_W_objfileName') + '/' + objFileName
            print('rename: ' + src_path)
            print('to: ' + dst_path)
            dir = os.path.dirname(dst_path)
            if not os.path.exists(dir):
                os.makedirs(dir)
            shutil.copy(src_path, dst_path)



if __name__ == '__main__':
    rename_crash_log_with_objfile('backup_tombstones/')
    # exit(0)

    l = list('backup_tombstones/')

    # l = list('backup_tombstones_bak/')
    fs = []
    for p in l:
        # 有dependency (无注释) 和 无dependency (有注释)
        # if '2022.07.07' not in p:
        #     continue
        path = p + '/tombstones_sanitizer/'
        RemoveDir(path)

        path = p + '/isCallingFunc/'
        RemoveDir(path)

        l2 = list(p + '/tombstones/')
        # print(l2)
        for t in l2:
            # print(t)
            process_tomb(t)

    # ==========================================================================================
    print('# ====================================== 206 ====================================================')
    # \multirow{25}{*}{\textbf{Android Native System Library}}
    # & \multirow{1}{*}{Xiaomi (7.0)} & 398 \\
    # \multirow{2}{*}{\textbf{Basic Library}}
    comp1_coount = 0
    comp2_coount = 0
    for tem in bug_in_lib:
        if 'libc' in tem or 'libssl' in tem or 'libjavacore' in tem or 'libgui' in tem or 'libutils' in tem or 'libcrypto' in tem or 'libhwui' in tem or 'libpdfium' in tem:
            comp2_coount = comp2_coount + 1
        else:
            comp1_coount = comp1_coount + 1

    print(r'\multirow{'+str(comp1_coount)+r'}{*}{\textbf{Android Native System Library}}')
    for tem in sorted(bug_in_lib):
        if 'libc' in tem or 'libssl' in tem or 'libjavacore' in tem or 'libgui' in tem or 'libutils' in tem or 'libcrypto' in tem or 'libhwui' in tem or 'libpdfium' in tem:
            pass
        else:
            print('& \multirow{1}{*}{' + tem.replace('_', r'\_') + '} & ' + str(bug_in_lib[tem]) + r' \\ ')

    print('\n\midrule\n')

    print(r'\multirow{' + str(comp2_coount) + r'}{*}{\textbf{Basic Library}}')
    for tem in sorted(bug_in_lib):
        if 'libc' in tem or 'libssl' in tem or 'libjavacore' in tem or 'libgui' in tem or 'libutils' in tem or 'libcrypto' in tem or 'libhwui' in tem or 'libpdfium' in tem:
            print('& \multirow{1}{*}{' + tem.replace('_', r'\_') + '} & ' + str(bug_in_lib[tem]) + r' \\ ')

    print(bug_in_lib)
    print(len(bug_in_lib.keys()))

    print('len(so_and_log)', len(so_and_log))
    for tem in so_and_log:
        path = tem['path']
        copyfile(path, '/Users/chaoranli/IdeaProjects/fuzzEngine/backup_tombstones_bak/need_transformed_tombstones/' + path.split('/')[-1] + '.txt')
        print(path)

    # for tem in cause_log_list:
    #     print('-----------------')
    #     print(tem)

    exit(0)

    # ==========================================================================================
    print('===============================按照count排序===============================')
    jni_interface_dict = {}
    for tem in jni_interface_arr:
        full_method = tem['full_method']
        className = tem['className']
        jni_interface_dict[className] = jni_interface_dict.get(className, 0) + 1

    comp1_coount = 0
    comp2_coount = 0
    for tem in jni_interface_dict:
        if not tem.startswith('android.'):
            comp2_coount = comp2_coount + 1
        else:
            comp1_coount = comp1_coount + 1

    jni_interface_arr = sorted(jni_interface_dict.items(), key=lambda item:item[1], reverse=True)
    comp1_coount = 40
    print(r'\multirow{'+str(comp1_coount)+r'}{*}{\textbf{Android Native System Library}}')
    count = 0
    for tem in jni_interface_arr:
        k = tem[0]
        v = tem[1]
        if count > comp1_coount:
            break
        if k.startswith('android.'):
            count =count + 1
            print('& \multirow{1}{*}{' + k.replace('_', r'\_') + '} & ' + str(v) + r' \\ ')

    print('\n\midrule\n')

    print(r'\multirow{' + str(comp2_coount) + r'}{*}{\textbf{Basic Library}}')
    # for tem in sorted(jni_interface_dict):
    #     if not tem.startswith('android.'):
    #         print('& \multirow{1}{*}{' + tem.replace('_', r'\_') + '} & ' + str(jni_interface_dict[tem]) + r' \\ ')
    for tem in jni_interface_arr:
        k = tem[0]
        v = tem[1]
        if not k.startswith('android.'):
            print('& \multirow{1}{*}{' + k.replace('_', r'\_') + '} & ' + str(v) + r' \\ ')
