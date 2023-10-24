# coding=utf-8

import os
import datetime
import  re

# crash_log_dir = '/hwasan_crash_log/'
crash_log_dir = '/hwasan_crash_log_transformed/'

def get_objFile(logFile):
    objFile = ''
    with open(logFile, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if re.match('[0-9]+\.obj', line) != None:
                line = line.replace('objfileName:','')
                # line = line.replace('objfileName:','')
                objFile = line.strip()
                # print(objFile)
                new_dir = os.path.dirname(os.path.dirname(logFile))
                return_objFile = new_dir + '/objFiles/DCIM/' + objFile
                return return_objFile

        if objFile== '':
            print('cat "'+logFile+'"')
            return None

def check_objFile(logFiles):
    # print('--------', check_objFile, '--------')
    list = []
    for path in logFiles:
        print(path)
        objFile = ''
        with open(path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if re.match('[0-9]+\.obj', line) != None:
                    line = line.replace('objfileName:','')
                    # line = line.replace('objfileName:','')
                    objFile = line.strip()
                    # print(objFile)
                    new_dir = os.path.dirname(os.path.dirname(path))
                    list.append(new_dir + '/objFiles/DCIM/' + objFile)
                    if not os.path.exists(list[-1]):
                        print('Not found objFile:', list[-1])
                        exit(0)
                    break
            if objFile== '':
                print('error: no objFile')
                # exit(0)
        # extra_path = '/sdcard/Android/data/com.example.fuzzer/files/DCIM/'
        # local_path = os.path.dirname(path)
        # print('local_path:', local_path)
        # cmd = 'adb pull ' + extra_path + objFile + ' ' + local_path
        # print(objFile)

    print('String[] objFiles = ' + str(list).replace('\'','"').replace('[','{').replace(']','}') + ';')



def list():
    # if not os.path.exists(path):
    #     os.makedirs(path)
    path = './backup/'
    dirs = os.listdir(path)
    l = []
    for dir in dirs:
        if not dir.startswith('.'):
            for f in os.listdir(path + dir + crash_log_dir):
                # print(path + dir + '/hwasan_crash_log/' + f)
                l.append(path + dir + crash_log_dir + f)
    # print(l)
    return l

def ignore_info(tem):
    tem = tem.strip()
    return tem


if __name__ == '__main__':
    ls = list()
    bugs = []
    # 遍历文件
    unavailable = 0
    for l in ls:
        # print('\n\n===============')
        print(l)
        basename = os.path.basename(l)
        # print(basename)
        # 读文件
        with open(l, 'r') as f:
            lines = f.readlines()
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
                        tem_stack = ' '
                        stack0 = tem_stack.join(stack0.split(' ')[4:])
                        if i+1<len(lines) and lines[i + 1].startswith("#"):
                            stack1 = lines[i + 1]
                            tem_stack = ' '
                            stack1 = tem_stack.join(stack1.split(' ')[4:])
                        if i+2<len(lines) and lines[i + 2].startswith("#"):
                            stack2 = lines[i + 2]
                            tem_stack = ' '
                            stack2 = tem_stack.join(stack2.split(' ')[4:])

                if is_specific:
                    if not line.startswith('==') and not line.startswith('Thread:'):
                        specific = line
                    is_specific = False
                if san_start and line == '':
                    is_specific = True
                    san_start = False
                if 'ERROR: HWAddressSanitizer:' in line:
                #     if i+1 <= len(lines)-1 and 'tags: 80/00' in lines[i+1]:
                #         continue
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
            id = basename.replace('.txt', '')
            id = re.sub('\|[0-9\- :]+', '', id)
            # print(id)
            # print(error)
            if 'ERROR: HWAddressSanitizer:' not in error:
                unavailable = unavailable + 1
                continue
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

            objFile = get_objFile(l)
            # print(objFile)
            # exit(0)

            # incomplete log
            # if specific == '--------- beginning of crash' or specific == '':
            #     # print('1111111')
            #     continue
            # 重复的不加

            found = False
            for bug_i, bug in enumerate(bugs):
                if bug[1] == error and bug[2] == stack0 and bug[3] == stack1 and bug[4] == stack2:
                    found = True
                    # if exists and the new objFile available, replace old one, make sure the objFile is available unless the first one is unique
                    if objFile is not None and os.path.exists(objFile):
                        bugs[bug_i] = [id, error, stack0, stack1, stack2, specific, l, objFile]
                    break
            
            # the first one, objFile can not exist. Check finally
            if not found:
                bugs.append([id, error, stack0, stack1, stack2, specific, l, objFile])

    # for bug in bugs:
    #     print('--------')
    #     print('path:', 'cat "'+bug[6].replace('../',' /hci/chaoran_data/fuzzEngine/')+'"')
    #     print('id:', bug[0])
    #     print('error:', bug[1])
    #     print('stack0:', bug[2])
    #     print('stack1:', bug[3])
    #     print('stack2:', bug[4])
    #     print('specific:', bug[5])

    objfile_do_not_exist = 0
    for bug in bugs:
        if not os.path.exists(bug[7]):
            print('file do not exist:', bug[7])
            objfile_do_not_exist = objfile_do_not_exist + 1
            # exit(0)

    print('==========')
    lll = []
    full_path = []
    for bug in bugs:
        print('cat "'+bug[6].replace('../',' /Users/chaoranli/IdeaProjects/fuzzEngine/')+'"')

        temm = bug[6].replace('../',' /Users/chaoranli/IdeaProjects/fuzzEngine/')
        full_path.append(temm)
        temm = temm[temm.find('HWAddressSanitizer_'):]
        print(temm)
        lll.append(temm)

    lll.sort()
    only_one = set()
    for ttt in lll:
        print(ttt)
        only_one.add(ttt.split('|')[0]+"|"+ttt.split('|')[1])

    print('去重后的,测试到的总BUG数:', len(bugs), '个!')
    print('保守去重后, 测试到的总BUG数:', len(only_one), '个!')
    print('unavailable log file (cannot find Hwasan error string):', unavailable, '个!')
    print('objfile_do_not_exist):', objfile_do_not_exist, '个!')

    obj_list=[]
    for bug in bugs:
        obj_list.append(bug[7])
    print(obj_list)
    string_obj_list = 'String[] objFiles = ' + str(obj_list).replace('\'','"').replace('[','{').replace(']','}') + ';'
    print(string_obj_list)
    with open('clipboard.txt', 'w') as f:
        f.write(string_obj_list)
    exit(0)
# exit(0)

    # unique = []
    # for a in bugs:
    #     found = False
    #     for b in bugs:
    #         error = b[1]
    #         stack0 = b[2]
    #         stack1 = b[3]
    #         stack2 = b[4]
    #         if a[1] == error and a[2] == stack0 and a[3] == stack1 and a[4] == stack2:
    #             found = True
    #             break
    #     if not found:
    #             unique.append([id, error, stack0, stack1, stack2, specific, l, objFile])
    
    # for a in bugs:
    #     found = False
    #     for b in bugs:
    #         error = b[1]
    #         stack0 = b[2]
    #         stack1 = b[3]
    #         stack2 = b[4]
    #         if a[1] == error and a[2] == stack0 and a[3] == stack1 and a[4] == stack2:
    #             found = True
    #             break

    # check_objFile(full_path)

    # print('去重后的,测试到的总BUG数:', len(bugs), '个!')
    # print('保守去重后, 测试到的总BUG数:', len(only_one), '个!')
    # print('unavailable log file (cannot find Hwasan error string):', unavailable, '个!')

    objfile_do_not_exist = 0
    bugs_full = []
    for bug in bugs:
        path = bug[6].replace('../',' /Users/chaoranli/IdeaProjects/fuzzEngine/')
        # print(path)
        with open(path, 'r') as f:
            lines = f.readlines()
            full_str = ''
            # 清理行
            for i, line in enumerate(lines):
                full_str = full_str + line

            if 'tags: 80/00' in full_str:
                continue
            
            if not os.path.exists(bug[7]):
                print('file do not exist:', bug[7])
                objfile_do_not_exist = objfile_do_not_exist + 1

            bugs_full.append(bug)

    print('-----------------')

    print('log not containing \'tags: 80/00\':', len(bugs_full))
    print('objfile_do_not_exist', objfile_do_not_exist)

    

    # for tem in bugs_full:
    #     print(tem)
    # print(str(bugs_full).replace('\'','"').replace('[','{').replace(']','}'))