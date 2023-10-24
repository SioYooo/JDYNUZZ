import os
import subprocess
import re
import json

def get_file(base, extension):
    list = []
    for root, ds, fs in os.walk(base):
        for f in fs:
            if f.endswith(extension):
                fullname = os.path.join(root, f)
                list.append(fullname)
    return list


def call(args, timeout):
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        out, err = p.communicate(timeout=timeout)
        # print(out)
        return out
    except subprocess.TimeoutExpired:
        print('*** time out ***', timeout, 's')
        p.kill()
        out, err = p.communicate()
        print(out)
        return out


def run(files, version):
    if(len(files)>10000):
        files = files[:10000]
    # print(files)
    total = len(files)
    for i, apk in enumerate(files):
        # if i < 2698:
        #     continue
        # if not os.path.exists('log/%i_%i' % (i, total)):
        #     os.mkdir('log/%i_%i' % (i, total))
        print(i, '/', total)
        # sdkVersion
        # sdkVersion: '26'
        # targetSdkVersion: '30'
        # apk = '../apkreflect/app-debug.apk'
        sdkVersion_cmd = 'aapt dump badging %s' % apk
        # print('sdkVersion_cmd', '\n', sdkVersion_cmd)
        # out = os.system(sdkVersion_cmd)
        sdkVersion_cmd = sdkVersion_cmd.split(' ')
        out = call(sdkVersion_cmd, 60).decode('utf-8')
        out_lines = out.split('\n')
        sdkVersion = -1
        targetSdkVersion = -1
        for tem in out_lines:
            if tem.startswith('sdkVersion:\''):
                sdkVersion = tem.replace('sdkVersion:\'', '').replace('\'', '').strip()
                # print(sdkVersion)
            elif tem.startswith('targetSdkVersion:\''):
                targetSdkVersion = tem.replace('targetSdkVersion:\'', '').replace('\'', '').strip()
                # print(targetSdkVersion)

        # package: com.example.myapplication
        # uses-permission: name='android.permission.WRITE_SYNC_SETTINGS'
        # permission: com.android.chrome.permission.CHILD_SERVICE
        permission_cmd = 'aapt dump permissions %s' % apk
        permission_cmd = permission_cmd.split(' ')
        out = call(permission_cmd, 60).decode('utf-8')
        permissions = re.findall("[a-zA-Z_\.]+permission\.[a-zA-Z_\.]+", out)
        # print(permissions)
        save_json = {'sdkVersion': sdkVersion, 'targetSdkVersion': targetSdkVersion, 'permissions': permissions}
        with open('apk_info/' + apk.replace("/", "_") + '.txt', 'w') as file_obj:
            json.dump({"array": save_json}, file_obj)
        # exit(1)
        cmd = 'java -jar sysAppAna.jar -android-jars android-platforms-master -process-dir %s -process-multiple-dex %s' % (apk, version)
        print(cmd)
        cmd_args = cmd.split(' ')
        print(cmd_args)
        exit(1)
        # os.system(cmd)
        # call(['ping', 'www.baidu.com'], 10)
        # 5 mins
        timeout = 60 * 5
        call(cmd_args, timeout)
        # exit(1)

if __name__ == '__main__':
    # base = '/mal/APK/malware16171819'
    # base = '/mal/APK/google_benign'
    # files = get_file(base, '.apk')

    base = '/hci/chaoran_data/sysapp/7.0/'
    files = get_file(base, '.apk')
    print(files)
    exit(1)
    run(files, '7.0')