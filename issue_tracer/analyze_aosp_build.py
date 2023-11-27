import os
import shutil

cwd = os.getcwd()

total_issue_file = 0
reproducible_issue_file = 0
issue_aosp_build_dict = {}
category_dict = {}
reproducible_dict = {}
reproducible_list = []
id_tag_dict = {}
backtrace_dict = {}
available_backtrace_list = []


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
    global total_issue_file, reproducible_issue_file
    with open(cwd + os.sep + 'result_aosp_build_count.txt', "w", encoding='utf-8') as f:
        f.write("Total issue file: " + str(total_issue_file) + "\n")
        f.write("Version Count Start" + "\n")

        for version in issue_aosp_build_dict:
            f.write(version + ": " + str(issue_aosp_build_dict[version]) + "\n")
        f.write("Version Count End" + "\n")

        f.write("Category Count Start" + "\n")
        for category in category_dict:
            f.write(category + ": " + str(category_dict[category]) + "\n")
        f.write("Category Count End" + "\n")

        f.write("Total reproducible issue file: " + str(reproducible_issue_file) + "\n")

        f.write("Reproducible Category Count Start" + "\n")
        for category in reproducible_dict:
            f.write(category + ": " + str(reproducible_dict[category]) + "\n")
        f.write("Reproducible Category Count End" + "\n")

        f.write("Reproducible Category List Start" + "\n")
        for path in reproducible_list:
            f.write(path + "\n")
        f.write("Reproducible Category List End" + "\n")

        f.write("Available Backtrace List Start" + "\n")
        for path in available_backtrace_list:
            f.write(path + "\n")
        f.write("Available Backtrace List End" + "\n")


def sort_file(begin_line: str, end_line: str):
    with open(cwd + os.sep + 'result_aosp_build_count.txt', "r", encoding='utf-8') as f:
        lines = f.readlines()
        # 假设文件的第一行和最后一行不需要排序
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
    global backtrace_dict, available_backtrace_list
    with open(cwd + os.sep + 'backtrace_list.txt', "r", encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            parts = line.split(':')
            if len(parts) >= 2:
                file_path = parts[0].strip()
                status = parts[1].strip()
                backtrace_dict[file_path] = status
                if status == 'Yes':
                    available_backtrace_list.append(file_path)
        print("backtrace_dict: " + str(backtrace_dict))
        print("available_backtrace_list: " + str(available_backtrace_list))
        print("available_backtrace_list: " + str(len(available_backtrace_list)))



if __name__ == '__main__':
    read_file()
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
    # 然后复制所有的reproducible文件
    copy_reproducible_file()
    # 然后排序所有的available backtrace的个数
    analyze_backtrace_list()
    # read_tag
    # read_id_tag()
    # analyze_tag()

