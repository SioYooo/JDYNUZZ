import os
import subprocess
import multiprocessing
import time


def run_command(cmd):
    os.chdir("/home/siyu/tifs/JDYNUZZ/Fuzzing_Server/")  # 切换目录
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())
            if 'From here, new call!!!' in output:
                shared_data['api_index'] = int(output.split('From here, new call!!!(')[1].split('/')[0])
                shared_data['last_update'] = time.time()


def monitor_and_restart(cmd, shared_data):
    while True:
        # 启动 run_command 进程
        command_process = multiprocessing.Process(target=run_command, args=(cmd,))
        command_process.start()

        last_index = None
        while command_process.is_alive():
            time.sleep(20)
            current_index = shared_data.get('api_index')
            if last_index is not None and last_index == current_index:
                print("api_index 20秒内没有变化，准备重启进程")
                kill_process()
                command_process.terminate()  # 杀死当前进程
                command_process.join()  # 等待进程结束
                break  # 跳出内层循环，重新启动命令
            last_index = current_index


def kill_process():
    # 查找进程
    cmd = 'ps -ef | grep java -jar fuzzEngine.jar'
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    output = process.stdout.readline()
    if output == '' and process.poll() is not None:
        return
    if output:
        print(output.strip())
        pid = int(output.split()[1])
        os.kill(pid, 9)


if __name__ == "__main__":
    cmd = 'adb shell settings put global crash_dialog_blacklist_pkglist "com.example.fuzzer"'
    os.system(cmd)
    time.sleep(1)
    manager = multiprocessing.Manager()
    shared_data = manager.dict({'api_index': None, 'last_update': time.time()})

    # cmd = 'java -jar fuzzEngine.jar'
    cmd = 'java -jar fuzzEngine.jar'
    monitor_process = multiprocessing.Process(target=monitor_and_restart, args=(cmd, shared_data))
    monitor_process.start()
    monitor_process.join()
