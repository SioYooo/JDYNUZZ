import os
import json
import signal
import sys


class Watcher():
    # 解决使用 ctrl+c 不能杀死程序的问题

    def __init__(self):
        self.child = os.fork()
        if self.child == 0:
            return
        else:
            self.watch()

    def watch(self):
        try:
            os.wait()
        except KeyboardInterrupt:
            self.kill()
        os._exit(0)

    def kill(self):
        try:
            os.kill(self.child, signal.SIGKILL)
        except OSError:
            pass


# 解析JSON文件
def parse_json(json_file):
    with open(json_file, 'r') as f:
        j_data = json.load(f)
    return j_data

if __name__ == "__main__":
    Watcher()
    j_data = parse_json('jni12.0/jni.json')

    clazz_l = set()
    for j in j_data:
        clazz = j['class_']
        fun = j['fun']
        # print(clazz, fun)
        clazz_l.add(clazz)

    print(len(clazz_l))
    clazz_l = list(clazz_l)
    for i, clazz in enumerate(clazz_l):
        cmd = 'java -jar JavaLink.jar ' + clazz
        print(i, '/', len(clazz_l))
        print(cmd)
        os.system(cmd)