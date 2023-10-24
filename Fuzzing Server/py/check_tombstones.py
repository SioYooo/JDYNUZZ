# coding=utf-8

import datetime
import os
import shutil
from shutil import copyfile, copytree
import re

def list(path):
    # if not os.path.exists(path):
    #     os.makedirs(path)
    path = path + '/hwasan_crash_log/'

    fs = os.listdir(path)
    l = []
    for f in fs:
        if not f.startswith('.'):
            l.append(path + f)
    # print(l)
    return l

def transform(source, target):
    cmd = 'cat "'+source+'" | python2 "/hci/chaoran_data/android-12.0.0_r31/external/compiler-rt/lib/asan/scripts/symbolize.py" > "' + target +'"'
    print(cmd)
    os.system(cmd)

def pull_objFile(path):
    extra_path = '/sdcard/Android/data/com.example.fuzzer/files/DCIM/'
    local_path = path + '/objFiles'
    if not os.path.exists(local_path):
        os.makedirs(local_path)
    print('local_path:', local_path)
    cmd = 'adb pull ' + extra_path + ' ' + local_path
    print(cmd)
    os.system(cmd)

def del_objFile():
    extra_path = '/sdcard/Android/data/com.example.fuzzer/files/DCIM/*'
    cmd = 'adb shell rm ' + extra_path
    print(cmd)
    os.system(cmd)


def pull_objTomb(path):
    extra_path = '/data/tombstones/'
    local_path = path
    if not os.path.exists(local_path):
        os.makedirs(local_path)
    print('local_path:', local_path)
    os.system('adb root')
    cmd = 'adb pull ' + extra_path + ' ' + local_path
    print(cmd)
    os.system(cmd)

def del_objTomb():
    extra_path = '/data/tombstones/*'
    os.system('adb root')
    cmd = 'adb shell rm ' + extra_path
    print(cmd)
    os.system(cmd)

def check():
    path = 'crash_log'
    # if not os.path.exists(path):
    #     os.makedirs(path)
    dirs = os.listdir(path)
    l = []
    for f in dirs:
        # for f in os.listdir(dir):
        print(f)
        if f.startswith('HWAddressSanitizer_'):
            l.append(f)
            print(path + '/' + f +'==> ' + 'hwasan_crash_log/' + f )
            copyfile(path + '/' + f, 'hwasan_crash_log/' + f)
    print(l)

def RemoveDir(filepath):
    '''
    如果文件夹不存在就创建，如果文件存在就清空！

    '''
    if not os.path.exists(filepath):
        os.mkdir(filepath)
    else:
        shutil.rmtree(filepath)
        os.mkdir(filepath)

def empty():
    tem = input("EMPTY the following dirs?\n /crash_log && /hwasan_crash_log\n(Y/n):")
    if tem == 'Y':
        tem = input("EMPTY the following dirs?\n /crash_log && /hwasan_crash_log\n(Y/n):")
        if tem == 'Y':
            print('正在清空')
            RemoveDir('crash_log')
            RemoveDir('hwasan_crash_log')
            print('已清空')
        else:
            print('退出且未删除.')
    else:
        print('退出且未删除.')

def RemoveDir(filepath):
    '''
    如果文件夹不存在就创建，如果文件存在就清空！

    '''
    if not os.path.exists(filepath):
        os.mkdir(filepath)
    else:
        shutil.rmtree(filepath)
        os.mkdir(filepath)

def empty():
    RemoveDir('crash_log')
    RemoveDir('hwasan_crash_log')
    RemoveDir('hwasan_crash_log_tranformed')

if __name__ == '__main__':
    check()
    time_stamp = datetime.datetime.now()
    dir = time_stamp.strftime('%Y.%m.%d-%H:%M:%S')
    print('创建文件夹：', 'backup_tombstones/' + dir)
    os.makedirs('backup_tombstones/' + dir)
    print('复制文件夹：', 'hwasan_crash_log', '=>', 'backup_tombstones/' + dir + '/hwasan_crash_log')
    copytree('hwasan_crash_log', 'backup_tombstones/' + dir + '/hwasan_crash_log')
    print('复制文件夹：', 'crash_log', '=>', 'backup_tombstones/' + dir + '/crash_log')
    copytree('crash_log', 'backup_tombstones/' + dir + '/crash_log')
    print('复制文件夹：', 'fuzzEngineLog', '=>', 'backup_tombstones/' + dir + '/fuzzEngineLog')
    copytree('fuzzEngineLog', 'backup_tombstones/' + dir + '/fuzzEngineLog')
    pull_objFile('backup_tombstones/'+dir)
    pull_objTomb('backup_tombstones/'+dir)
    del_objFile()
    del_objTomb()
    empty()
    # ls = list('backup_tombstones/' + dir)
    # for source in ls:
    #     target = source.replace('hwasan_crash_log', 'hwasan_crash_log_transformed')
    #     if not os.path.exists(os.path.dirname(target)):
    #         os.makedirs(os.path.dirname(target))
    #     transform(source, target)
    # empty()

