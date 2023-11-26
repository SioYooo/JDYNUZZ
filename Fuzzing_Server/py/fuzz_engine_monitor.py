import os
import subprocess
import multiprocessing
import time

def run_command(cmd, shared_data):
    os.chdir("/home/siyu/tifs/JDYNUZZ/Fuzzing_Server/")
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


def monitor_and_restart(cmd_template, shared_data):
    while True:
        current_index = shared_data.get('api_index')
        cmd = cmd_template.format(api_index=current_index)
        command_process = multiprocessing.Process(target=run_command, args=(cmd, shared_data))
        command_process.start()

        last_index = None
        while command_process.is_alive():
            time.sleep(20)
            current_index = shared_data.get('api_index')
            if last_index is not None and last_index == current_index:
                print("api_index 20秒内没有变化，准备重启进程")
                kill_process()
                command_process.terminate()
                command_process.join()
                break
            last_index = current_index



def kill_process():
    cmd = 'ps -ef | grep "java -jar fuzzEngine.jar -i"'
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
    shared_data = manager.dict({'api_index': 0, 'last_update': time.time()})
    cmd_template = "java -jar fuzzEngine.jar -i {api_index}"
    monitor_process = multiprocessing.Process(target=monitor_and_restart, args=(cmd_template, shared_data))
    monitor_process.start()
    monitor_process.join()
