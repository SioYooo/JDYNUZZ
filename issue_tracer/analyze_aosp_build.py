import os
import shutil

cwd = os.getcwd()

total_issue_file = 0
reproducible_issue_file = 0
# 用来存储所有版本号 和 个数
issue_aosp_build_dict = {}
# 用来存储所有 category 和 个数
category_dict = {}
# 用来存储所有 reproducible 的文件路径 和 个数
reproducible_dict = {}
# 用来存储所有 reproducible 的文件路径
reproducible_list = []
# 用来存储所有 aosp ID 和 tag 的对应关系
id_tag_dict = {}
# 用来存储所有的 backtrace 的文件路径 和 是否有 backtrace
backtrace_dict = {}
# 用来存储有 backtrace 的文件路径
available_backtrace_list = []
# 用来存储无 backtrace 的文件路径
no_backtrace_list = []
# 用来存储有问题的 backtrace 的文件路径
questionable_backtrace_list = []
# 用来储存拥有 backtrace 的 issue report 的 个数
backtrace_tag_dict = {}
# 用来存储拥有 backtrace 的 版本大于 10 的 issue report 的 个数
backtrace_tag_10_more_count = 0
# 用来存储拥有 backtrace 的 版本小于 10 的 issue report 的 个数
backtrace_tag_10_less_count = 0
# 用来存储 backtrace 的 设备信息
backtrace_device_dict = {}


def read_id_tag():
    global id_tag_dict
    with open(cwd + os.sep + 'id_tag_dict.txt', "r", encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            parts = line.split(' ')
            if len(parts) >= 2:
                id_tag_dict[parts[0].strip()] = parts[1].strip()
        print(id_tag_dict)


def read_file():
    global total_issue_file, reproducible_issue_file
    # read all issue file from cwd/pdf
    for root, dirs, files in os.walk(cwd + os.sep + 'pdf'):
        for file in files:
            # if file.endswith('.pdf'):
            path = os.path.join(root, file)
            # 获得文件的文件夹名
            category = os.path.basename(root)
            print("Issue category: " + category)
            # 获取文件的版本号
            print("Issue file: " + path)
            version = os.path.basename(path).split('_')[1].split('.pdf')[0]
            print("Issue version: " + version)
            if version in issue_aosp_build_dict:
                issue_aosp_build_dict[version] += 1
                print("Issue version: " + version + " count: " + str(issue_aosp_build_dict[version]))
            else:
                issue_aosp_build_dict[version] = 1
            if category in category_dict:

                category_dict[category] += 1
            else:
                category_dict[category] = 1
        total_issue_file += len(files)
    print("*" * 50)
    print("Total issue file: " + str(total_issue_file))

    for root, dirs, files in os.walk(cwd + os.sep + 'pdf'):
        for file in files:
            # if file.endswith('.pdf'):
            path = os.path.join(root, file)
            # 获得文件的文件夹名
            category = os.path.basename(root)
            if category == 'NOT_REPRODUCIBLE' or category == 'INTENDED_BEHAVIOR' or category == 'INFEASIBLE':
                continue
            else:
                reproducible_issue_file += 1
                reproducible_list.append(path)
            print("Issue category: " + category)
            # 获取文件的版本号
            print("Issue file: " + path)
            version = os.path.basename(path).split('_')[1].split('.pdf')[0]
            print("Issue version: " + version)
            if category in reproducible_dict:
                reproducible_dict[category] += 1
            else:
                reproducible_dict[category] = 1
    print("*" * 50)
    print("Total reproducible issue file: " + str(reproducible_issue_file))


def save_to_file():
    global total_issue_file, reproducible_issue_file, available_backtrace_list, no_backtrace_list, \
        questionable_backtrace_list, backtrace_tag_dict, backtrace_device_dict, backtrace_tag_10_more_count, \
        backtrace_tag_10_less_count
    with open(cwd + os.sep + 'result_aosp_build_count.txt', "w", encoding='utf-8') as f:
        f.write("Total issue file: " + str(total_issue_file) + "\n")
        f.write("Version Count Start" + "\n")
        for version in issue_aosp_build_dict:
            f.write(version + ": " + str(issue_aosp_build_dict[version]) + "\n")
        f.write("Version Count End" + "\n")
        f.write("*" * 50 + "\n")

        f.write("Category Count Start" + "\n")
        for category in category_dict:
            f.write(category + ": " + str(category_dict[category]) + "\n")
        f.write("Category Count End" + "\n")
        f.write("*" * 50 + "\n")

        f.write("Total reproducible issue file: " + str(reproducible_issue_file) + "\n")
        f.write("Reproducible Category Count Start" + "\n")
        for category in reproducible_dict:
            f.write(category + ": " + str(reproducible_dict[category]) + "\n")
        f.write("Reproducible Category Count End" + "\n")
        f.write("*" * 50 + "\n")

        f.write("Reproducible Category List Start" + "\n")
        for path in reproducible_list:
            f.write(path + "\n")
        f.write("Reproducible Category List End" + "\n")
        f.write("*" * 50 + "\n")

        f.write("Available Backtrace Count: " + str(len(available_backtrace_list)) + "\n")
        f.write("Available Backtrace List Start" + "\n")
        for path in available_backtrace_list:
            f.write(path + "\n")
        f.write("Available Backtrace List End" + "\n")
        f.write("No Backtrace Count: " + str(len(no_backtrace_list)) + "\n")
        f.write("Questionable Backtrace Count: " + str(len(questionable_backtrace_list)) + "\n")
        f.write("*" * 50 + "\n")

        f.write("Backtrace Tag Count Start" + "\n")
        for tag in backtrace_tag_dict:
            f.write(tag + ": " + str(backtrace_tag_dict[tag]) + "\n")
        f.write("Backtrace Tag Count End" + "\n")
        f.write("*" * 50 + "\n")

        f.write("Backtrace Tag 10 More Count: " + str(backtrace_tag_10_more_count) + "\n")
        f.write("Backtrace Tag 10 Less Count: " + str(backtrace_tag_10_less_count) + "\n")
        f.write("*" * 50 + "\n")

        f.write("Backtrace Device Count Start" + "\n")
        for device in backtrace_device_dict:
            f.write(device + ": " + str(backtrace_device_dict[device]) + "\n")
        f.write("Backtrace Device Count End" + "\n")
        f.write("*" * 50 + "\n")


def sort_file(begin_line: str, end_line: str):
    with open(cwd + os.sep + 'result_aosp_build_count.txt', "r", encoding='utf-8') as f:
        lines = f.readlines()
        begin_line_index = 0
        end_line_index = 0
        for i in range(len(lines)):
            if lines[i].strip() == begin_line:
                begin_line_index = i + 1
            if lines[i].strip() == end_line:
                end_line_index = i - 1
        print("begin_line_index: " + str(begin_line_index))
        print("end_line_index: " + str(end_line_index))
        lines = lines[begin_line_index:end_line_index + 1]

        # 准备一个函数来安全地处理行
        def sort_key(line):
            parts = line.split(':')
            if len(parts) >= 2:
                try:
                    return int(parts[1].strip())
                except ValueError:
                    return 0
            return 0

        # 使用安全处理的函数作为排序的键
        lines.sort(key=sort_key, reverse=True)

        # 然后写入排序后的文件
        with open(cwd + os.sep + 'result_aosp_build_count_sorted.txt', "a", encoding='utf-8') as f2:
            for line in lines:
                f2.write(line)
            f2.write("*" * 50 + "\n")


def copy_reproducible_file():
    for path in reproducible_list:
        file_name = os.path.basename(path)
        category = os.path.basename(os.path.dirname(path))
        print("Path: " + path)
        print("*" * 50)
        dest_path = cwd + os.sep + 'repro' + os.sep + category
        print("dest_path: " + dest_path)
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)
        shutil.copy(path, dest_path)


def copy_traceback_file():
    for path in available_backtrace_list:
        file_name = os.path.basename(path)
        category = os.path.basename(os.path.dirname(path))
        print("Path: " + path)
        print("*" * 50)
        dest_path = cwd + os.sep + 'backtrace' + os.sep + category
        print("dest_path: " + dest_path)
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)
        shutil.copy(path, dest_path)


def analyze_tag():
    global reproducible_list, id_tag_dict
    for path in reproducible_list:
        category = os.path.basename(os.path.dirname(path))
        build_id = os.path.basename(path).split('_')[1].split('.pdf')[0]
        for aosp_id in id_tag_dict:
            if aosp_id == build_id:
                print("Path: " + path)
                print("category: " + category + " build_id: " + build_id + " tag: " + id_tag_dict[aosp_id])
                print("*" * 50)


def analyze_backtrace_list():
    global backtrace_dict, available_backtrace_list, id_tag_dict, backtrace_tag_dict, \
        backtrace_tag_10_more_count, backtrace_tag_10_less_count
    with open(cwd + os.sep + 'backtrace_list.txt', "r", encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            parts = line.split(':')
            if len(parts) >= 2:
                file_path = parts[0].strip()
                status = parts[1].strip()
                index = lines.index(line)
                backtrace_dict[file_path] = status
                if status == 'Yes':
                    available_backtrace_list.append(file_path)
                if status == 'No':
                    no_backtrace_list.append(file_path)
                if status == '?':
                    questionable_backtrace_list.append(file_path)
        print("available_backtrace_list: " + str(len(available_backtrace_list)))
        print("no_backtrace_list: " + str(len(no_backtrace_list)))
        print("questionable_backtrace_list: " + str(len(questionable_backtrace_list)))

    for file in available_backtrace_list:
        file_name = os.path.basename(file)
        aosp_id = file_name.split('_')[1].split('.pdf')[0]
        # check the version of the tag
        tag = id_tag_dict[aosp_id]
        print("file: " + file + " tag: " + tag)
        if tag in backtrace_tag_dict:
            backtrace_tag_dict[tag] += 1
        else:
            backtrace_tag_dict[tag] = 1

    for tag in backtrace_tag_dict:
        if 'security' in tag:
            version = tag.split('.')[0].split('-')[2]
        else:
            version = tag.split('.')[0].split('-')[1]
        if int(version) >= 10:
            backtrace_tag_10_more_count += backtrace_tag_dict[tag]
        else:
            backtrace_tag_10_less_count += backtrace_tag_dict[tag]

def get_device():
    global backtrace_device_dict
    with open(os.getcwd() + os.sep + "backtrace_device.txt") as f:
        lines = f.readlines()
        for line in lines:
            parts = line.split(':')
            if len(parts) >= 2:
                file_path = parts[0].strip()
                device = parts[1].strip()
                if "emulator" in device:
                    device = "emulator"
                if "," in device:
                    devices = device.split(',')
                    for d in devices:
                        if d in backtrace_device_dict:
                            backtrace_device_dict[d] += 1
                        else:
                            backtrace_device_dict[d] = 1
                    continue
                if device in backtrace_device_dict:
                    backtrace_device_dict[device] += 1
                else:
                    backtrace_device_dict[device] = 1
        print(backtrace_device_dict)


if __name__ == '__main__':
    read_file()
    read_id_tag()
    analyze_backtrace_list()
    get_device()
    save_to_file()
    # 首先清空文件
    with open(cwd + os.sep + 'result_aosp_build_count_sorted.txt', "w", encoding='utf-8') as zero:
        zero.write("")
    # 首先排序所有的版本code name 的个数
    sort_file("Version Count Start", "Version Count End")
    # 然后排序所有的category的个数
    sort_file("Category Count Start", "Category Count End")
    # 然后排序所有的producible category的个数
    sort_file("Reproducible Category Count Start", "Reproducible Category Count End")
    # 然后排序所有的backtrace tag的个数
    sort_file("Backtrace Tag Count Start", "Backtrace Tag Count End")
    # 然后复制所有的reproducible文件
    copy_reproducible_file()
    # 然后复制所有的backtrace文件
    copy_traceback_file()
    # read_tag
    # read_id_tag()
    # analyze_tag()
