# coding=utf-8

import os
from shutil import copyfile
# version = '7.0'
# project_path = '/hci/chaoran_data/android-7.0.0_r33/out/target/common/obj/JAVA_LIBRARIES'
# version = '7.1'
# project_path = '/hci/chaoran_data/android-7.1.2_r33/out/target/common/obj/JAVA_LIBRARIES'
# version = '8.0'
# project_path = '/Volumes/android/android-8.0.0_r34/out/target/common/obj/JAVA_LIBRARIES'
# version = '8.1'
# project_path = '/hci/chaoran_data/android-8.1.0_r67/out/target/common/obj/JAVA_LIBRARIES'
# version = '9.0'
# project_path = '/hci/chaoran_data/android-9.0.0_r47/out/target/common/obj/JAVA_LIBRARIES'
# version = '10.0'
# project_path = '/hci/chaoran_data/android-10.0.0_r45/out/target/common/obj/JAVA_LIBRARIES'

version = '10.0'
# project_path = '/hci/chaoran_data/android-12.0.0_r31/out/target/common/obj/JAVA_LIBRARIES'
project_path = '/data_ssd_1/siyu/10.0.0_r2/aosp/out/target/common/obj/JAVA_LIBRARIES'


def findAllFile(base):
    # path = 'jar' + '/jar' + version
    path = "/home/siyu/tifs/JDYNUZZ/Fuzzing_Server/jar/jar10.0"
    print(base)
    if not os.path.exists(path):
        os.makedirs(path)
    dirs = os.listdir(base)
    for dir in dirs:
        # print(base+'/'+dir)
        for f in os.listdir(base+'/'+dir):
            if(f=='classes.jar'):
                print(base+'/'+dir+'/'+f +'==>' + 'jar' + version + '/'+dir+'.jar')
                copyfile(base+'/'+dir+'/'+f, path + '/'+dir+'.jar')
                print('jar_list.add(BASE + "%s");'% (''+dir+'.jar'))
    # for root, ds, fs in os.walk(base):
    #     for f in fs:
    #         if f.endswith('.' + extension) and 'tests/' not in root and 'test/' not in root:
    #                 # and 'test/' not in root \
    #                 # and 'out/' not in root \
    #                 # and 'tests/' not in root \
    #                 # and 'development/' not in root \
    #                 # and 'packages/' not in root\
    #                 # and 'device/' not in root:
    #             # if not re.match(r'.*\d.*', f):
    #                 fullname = os.path.join(root, f)
    #                 yield fullname

def find():
    findAllFile(project_path)

def collect(path):
    for f in os.listdir(path):
        if f.endswith('.jar'):
            print('jar_list.add(BASE + "%s");'% f)

if __name__ == '__main__':
    find()
    # collect('jar/jar10.0')
    collect("/home/siyu/tifs/JDYNUZZ/Fuzzing_Server/jar/jar10.0")
    pass