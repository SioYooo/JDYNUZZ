# coding=utf-8

import os
import datetime
import  re


def ignore_info(tem):
    if 'System.err: ' in tem:
        tem = tem[tem.index('System.err: ') + len('System.err: '):]
        tem = tem.strip()
    return tem


if __name__ == '__main__':
    uniq_list = []
    with open('fuzzEngineLog/log.log', 'r') as f:
        lines = f.readlines()
        for i,line in enumerate(lines):
            line = ignore_info(line)
            if 'Exception: ' in line and 'abstract' not in line:
                # if 'java.lang.NoSuchMethodException:' in line and 'java.lang.Boolean' in line:
                #     continue
                if 'Caused by:' in line or 'but got java.lang.Class' in line:
                    continue
                # if 'java.lang.NullPointerException:' in line:
                #     continue
                if line not in uniq_list:
                    uniq_list.append(line)
                    print(i, '|', line)

