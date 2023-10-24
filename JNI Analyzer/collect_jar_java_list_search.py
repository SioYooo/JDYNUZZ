# coding=utf-8

import os
import re
import json
from shutil import copyfile

def findAllFile(base):
    dirs = os.listdir(base)
    for dir in dirs:
        # print(base+'/'+dir)
        if dir=='.DS_Store':
            continue
        for f in os.listdir(base+'/'+dir):
            if(f.endswith('java-source-list')):
                with open(base+'/'+dir+'/'+f) as file:
                    for line in file.readlines():
                        if 'WifiDisplayAdapter.java' in line:
                            print('FOUND:', base+'/'+dir+'/'+f, line)
                # print(base+'/'+dir+'/'+f +'==>'+ 'jar/'+dir+'.jar')
                # copyfile(base+'/'+dir+'/'+f, 'jar/'+dir+'.jar')
                # print('jar_list.add(BASE + "%s");'% ('jar/'+dir+'.jar'))
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
    # project_path = '/Volumes/android/android-8.0.0_r34/out/target/common/obj/JAVA_LIBRARIES'
    project_path = '/hci/chaoran_data/android-7.0.0_r33/out/target/common/obj/JAVA_LIBRARIES'
    findAllFile(project_path)

if __name__ == '__main__':
    find()
    pass