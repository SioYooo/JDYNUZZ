import os

cwd = os.getcwd()

issue_aosp_build_dict = {}


def read_file():
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
            else:
                issue_aosp_build_dict[version] = 1
    print("*" * 50)
    print("Total issue file: " + str(len(issue_aosp_build_dict)))


def save_to_file():
    with open(cwd + os.sep + 'result_aosp_build_count.txt', "w", encoding='utf-8') as f:
        f.write("Total issue file: " + str(len(issue_aosp_build_dict)) + "\n")
        f.write("*" * 50 + "\n")

        for version in issue_aosp_build_dict:
            f.write(version + ": " + str(issue_aosp_build_dict[version]) + "\n")


def sort_file():
    with open(cwd + os.sep + 'result_aosp_build_count.txt', "r", encoding='utf-8') as f:
        lines = f.readlines()
        # 假设文件的第一行和最后一行不需要排序
        lines = lines[1:-1]

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

        with open(cwd + os.sep + 'result_aosp_build_count_sorted.txt', "w", encoding='utf-8') as f2:
            for line in lines:
                f2.write(line)


if __name__ == '__main__':
    read_file()
    save_to_file()
    sort_file()
