# coding=utf-8

import os
import re
import codecs

def findAllFile(base, extension, exclude):
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

def search_str(path, str):
    # with codecs.open(path, 'r', 'utf-8') as f:
    with open(path, 'r', encoding='UTF-8') as file:  # 转换编码以实现正确输出中文格式
        line_num = 0
        try:
            for line in file:
                line_num = line_num + 1
                if str in line:
                    return [True, line_num, line]
        except Exception as e:
            print(path, line_num)
            raise e
    return [False, None, None]

def main():
    extension = 'java'
    bases = ['/Volumes/android/android-8.0.0_r34/frameworks/', '/Volumes/android/android-8.0.0_r34/sdk/']
    exclude = ['/out/*', '/tools/']
    str = 'ServiceManager.getService('
    for base in bases:
        file_list = findAllFile(base, extension, exclude)
        for file in file_list:
            r = search_str(file, str)
            if r[0]:
                print(file, r[1], r[2])

if __name__ == '__main__':
    main()