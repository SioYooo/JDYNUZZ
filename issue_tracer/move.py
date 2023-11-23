import os
import shutil

# 遍历 issues 目录，获取所有 issue 文件的路径
issue_file_dict = {}

# 遍历 issues 目录，获取所有 issue 文件的路径
def read_file():
    for root, dirs, files in os.walk(os.getcwd() + os.sep + 'issues'):
        for file in files:
            if file.endswith('.txt'):
                path = os.path.join(root, file)
                issue_file_dict[path] = root.split(os.sep)[-1]
                print("Issue file: " + path)
                print("Issue category: " + root.split(os.sep)[-1])

def copy_file():
    for issue in issue_file_dict:
        category = issue_file_dict[issue]
        dir = os.getcwd() + os.sep + 'issues_new' + os.sep + category
        # 如果目录不存在则创建目录
        if not os.path.exists(dir):
            os.makedirs(dir)
        # 复制文件
        shutil.copy(issue, dir)
        # rename file to html
        shutil.move(dir + os.sep + issue.split(os.sep)[-1], dir + os.sep + issue.split(os.sep)[-1].split('.')[0] + '.html')

if __name__ == "__main__":
    read_file()
    copy_file()