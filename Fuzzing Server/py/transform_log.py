# coding=utf-8

import os
import datetime
import  re

def list():
    # if not os.path.exists(path):
    #     os.makedirs(path)
    path = './backup/'
    dirs = os.listdir(path)
    l = []
    for dir in dirs:
        if not dir.startswith('.'):
            tranformed_path = path + dir + '/hwasan_crash_log_transformed/'
            if not os.path.exists(tranformed_path):
                os.makedirs(tranformed_path)
            for f in os.listdir(path + dir + '/hwasan_crash_log/'):
                # print(path + dir + '/hwasan_crash_log/' + f)
                l.append([path + dir + '/hwasan_crash_log/' + f, tranformed_path])
    # print(l)
    return l


if __name__ == '__main__':
    ls = list()
    # exit(0)
    # 遍历文件
    total = len(ls)
    i=0
    for l in ls:
        i=i+1
        print('\n\n===============', i,'/',total)
        print(l)
        basename = os.path.basename(l[0])
        cmd = 'cat "'+l[0]+'" | python2 "/hci/chaoran_data/android-12.0.0_r31/external/compiler-rt/lib/asan/scripts/symbolize.py" > "' + l[1] + basename +'"'
        print(cmd)
        os.system(cmd)
        # exit(0)