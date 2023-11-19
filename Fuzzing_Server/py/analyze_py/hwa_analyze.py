# this script is used to analyze the hwasan result

# ---------------------- import -----------------------
import os
import re

# ---------------------- global variable -----------------------
project_dir = '/home/siyu/tifs/JDYNUZZ/Fuzzing_Server/'
key_string = 'hwasan_crash_log'
hwasan_dir = []
# hwasan_crash_list 为crash report 的存放路径
hwasan_crash_list = []

# api_list 为去重后的 crash report
api_list = []
repeated_api_list = []
# 用于存储 crash 相关的 traceback 信息，如果已经出现过的 traceback 信息，就证明为重复的 crash
crash_check_list = []
crash_cause_dict = {}


def find_hwasan_crash_dir():
    for files, dirs, root in os.walk(project_dir):
        for directory in dirs:
            if key_string in directory:
                hwasan_dir.append(os.path.join(files, directory))


# 找到需要忽略的行
# def ignore_info(tem):
#     if 'I app_process64:' in tem:
#         tem = tem[tem.index('I app_process64:') + len('I app_process64:'):]
#         tem = tem.strip()
#     return tem


def analyze_files_in_dir():
    for path in hwasan_dir:
        for files, dirs, root in os.walk(path):
            # 查看文件夹下所有的文件
            for file in root:
                if file.endswith('.log'):
                    hwasan_crash_list.append(os.path.join(files, file))
                    file_name = os.path.basename(file)
                    api_name = file_name.split('_')[2] + '_' + file_name.split('_')[3]
                    if api_name not in api_list:
                        api_list.append(api_name)
                    else:
                        print('api name repeat: ', api_name)
                        repeated_api_list.append(api_name)


def print_and_save():
    print("Found hwasan crash dir: ", len(hwasan_dir))
    print("Found hwasan crash files: ", len(hwasan_crash_list))
    print("Found api: ", len(api_list))
    print("Found repeated api: ", len(repeated_api_list))
    with open("/home/siyu/tifs/JDYNUZZ/Fuzzing_Server/hwasan_result.txt", "w") as file:
        file.write("Found hwasan crash files: " + str(len(hwasan_crash_list)) + "\n")
        for crash in hwasan_crash_list:
            file.write(crash + "\n")
        file.write("*" * 50 + "\n")
        file.write("Found unsafe api: " + str(len(api_list)) + "\n")
        for api in api_list:
            file.write(api + "\n")
        file.write("*" * 50 + "\n")
        file.write("Found repeated unsafe api: " + str(len(repeated_api_list)) + "\n")
        for api in repeated_api_list:
            file.write(api + "\n")
        file.write("*" * 50 + "\n")


def analyze_file():
    bug_list = []
    # 遍历所有 crash log 文件
    for f in hwasan_crash_list:
        filename = os.path.basename(f)
        with open(f, 'r') as file:
            lines = file.readlines()
            for line in lines:
                # 跳过空行
                if line == '' or line == '/n':
                    continue
                # # when found "I app_process64:", delete this string
                # if "I app_process64:" in line:
                #     line = line[line.index("I app_process64:") + len("I app_process64:"):]
                #     line = line.strip()
                # 检查所有行中是否含有 ERROR: HWAddressSanitizer:
                if 'ERROR: HWAddressSanitizer:' in line:
                    # 获取当前line 的行数
                    line_num = lines.index(line)
                    # get next 3 lines and merge into one string
                    stack_string = lines[line_num + 1] + lines[line_num + 2] + lines[line_num + 3]
                    if stack_string in crash_check_list:
                        repeated_api_list.append(f)
                        continue
                    else:
                        crash_check_list.append(stack_string)
                    # 首先为i crash reason 赋一个基础的原因，如果 crash reason 为 summary，则会被替换
                    crash_reason = line.split('ERROR: HWAddressSanitizer:')[1]
                    crash_cause_dict[f] = crash_reason
                # 当找到 summary 时，说明当前行会输出 crash 的原因，替换之前的 crash reason
                if ' SUMMARY: ' in line:
                    crash_reason = line.split(' SUMMARY: ')[1]
                    crash_cause_dict[f] = crash_reason

            result = [f, stack_string, crash_reason]
            if result is None:
                continue
            else:
                api_list.append(result)


# def analyze_file():
#     bug_list = []
#     unavailable_crashes = 0
#     for f in hwasan_crash_list:
#         with open(f, 'r') as file:
#             lines = file.readlines()
#             basename = os.path.basename(f)
#             san_start = False
#             stack_start = False
#             error = ''
#             stack0 = ''
#             stack1 = ''
#             stack2 = ''
#             specific = ''
#             is_specific = False
#             # 清理行
#             for i, line in enumerate(lines):
#                 lines[i] = ignore_info(lines[i])
#             # 读行
#             for i, line in enumerate(lines):
#                 # print(line)
#                 if san_start and not stack_start:
#                     if line.startswith("#"):
#                         stack_start = True
#                         stack0 = line
#                         stack0 = stack0[stack0.index('('):]
#                         if i+1<len(lines) and lines[i + 1].startswith("#"):
#                             stack1 = lines[i + 1]
#                             stack1 = stack1[stack1.index('('):]
#                         if i+2<len(lines) and lines[i + 2].startswith("#"):
#                             stack2 = lines[i + 2]
#                             stack2 = stack2[stack2.index('('):]
#
#                 if line.startswith('SUMMARY:') and specific == '':
#                     specific = line
#                     is_specific = True
#                 if is_specific:
#                     if not line.startswith('==') and not line.startswith('Thread:'):
#                         specific = line
#                         specific_api_dict[basename.split('_')[2] + '_' + basename.split('_')[3]] = specific
#                     is_specific = False
#
#                 if san_start and line == '':
#                     is_specific = True
#                     san_start = False
#                 if 'ERROR: HWAddressSanitizer:' in line:
#                     san_start = True
#                     error = line
#
#
#             # 处理标记
#             id = basename.split('_')[2] + '_' + basename.split('_')[3]
#
#             if 'ERROR: HWAddressSanitizer:' not in error:
#                 unavailable_crashes += 1
#                 continue
#
#             error = error[error.index('ERROR: HWAddressSanitizer:') + len('ERROR: HWAddressSanitizer:'):]
#             error = re.sub('0x[a-z0-9]+', '', error)
#             error = error.strip()
#
#             specific = re.sub('0x[a-z0-9]+', '', specific)
#             specific = re.sub('[0-9]+', '', specific)
#             specific = specific.strip()
#
#             found = False
#             for bug in bug_list:
#                 if bug[1] == error and bug[2] == stack0 and bug[3] == stack1 and bug[4] == stack2:
#                     found = True
#                     break
#
#             if not found:
#                 bug_list.append([id, error, stack0, stack1, stack2, specific, f])
#
#     print("Found bugs: ", len(bug_list))
#     print("Unavailable crashes: ", unavailable_crashes)


if __name__ == '__main__':
    find_hwasan_crash_dir()
    analyze_files_in_dir()
    analyze_file()
    print_and_save()
