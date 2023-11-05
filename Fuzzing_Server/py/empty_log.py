import os
import shutil

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
    tem = input("EMPTY the following dirs?\n /crash_log && /hwasan_crash_log && /hwasan_crash_log_tranformed\n(Y/n):")
    if tem == 'Y':
        tem = input("EMPTY the following dirs?\n /crash_log && /hwasan_crash_log && /hwasan_crash_log_tranformed\n(Y/n):")
        if tem == 'Y':
            RemoveDir('crash_log')
            RemoveDir('hwasan_crash_log')
            RemoveDir('hwasan_crash_log_tranformed')
    else:
        print('not delete and exit.')

if __name__ == '__main__':
    empty()