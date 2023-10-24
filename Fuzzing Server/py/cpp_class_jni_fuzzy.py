import json
import os
import re
from helper import get_cpp_files_path

# compdb = True
# project_path = '/hci/chaoran_data/android-7.0.0_r33'
# compdb = False
# project_path = '/hci/chaoran_data/android-8.1.0_r67'
# compdb = True
# project_path = '/hci/chaoran_data/android-7.1.2_r33'
# compdb = False
# project_path = '/hci/chaoran_data/android-9.0.0_r47'
# compdb = True
# project_path = '/hci/chaoran_data/android-11.0.0_r39'
# save_path = 'jni11.0/jni.json'
# version = '11.0'
compdb = True
project_path = '/hci/chaoran_data/android-10.0.0_r45'
save_path = 'jni10.0/jni.json'
save_path2 = 'jni10.0/cleaned_java_jni.json'
version = '10.0'
if(compdb):
    file_json_key = 'file'
else:
    file_json_key = 'source'

def find_str_in_file(path, str):
    if not os.path.exists(path):
        return False
    file = None
    try:
        file = open(path, 'r', encoding='UTF-8')
        lines = file.readlines()
    except Exception as e:
        file = open(path, 'r', encoding='latin1')
        lines = file.readlines()
    finally:
        if(file):
            file.close()
    analyze_this_file = False
    for i, line in enumerate(lines):
        if str in line:
            analyze_this_file = True
    if not analyze_this_file:
        return False
    else:
        return True

def extract_jni_list(path, str):
    if not os.path.exists(path):
        return False
    file = None
    try:
        file = open(path, 'r', encoding='UTF-8')
        lines = file.readlines()
    except Exception as e:
        file = open(path, 'r', encoding='latin1')
        lines = file.readlines()
    finally:
        if(file):
            file.close()
    found = False
    cache = ''
    r_list = []
    for i, line in enumerate(lines):
        if str in line:
            found = True
            cache = ''

        if found:
            tem = line.strip()
            #if not tem.startswith("//"):
            if "//" not in tem:
                cache = cache + tem

        if '};' in line:
            found = False
            if cache!='':
                r_list.append(cache)
                cache = ''
    return r_list

def transform(list):
    pairs = []

    for tem in list:

        for a in re.findall('/\*.+?\*/', tem):
            tem = tem.replace(a, '')
        if '/*' in tem or '\*' in tem:
            sss=0
        groups = re.findall('\{(.+?)\}', tem)

        pair = []
        for group in groups:
            if 'NATIVE_METHOD' in group:
                continue
            s_group = group.split(',')
            s_group[0] = re.findall('"(.+?)"', s_group[0])[0]
            s_group[-1] = s_group[-1].strip()

            for a in re.findall('^\(void.+?\)', s_group[-1]):
                s_group[-1] = s_group[-1].replace(a, '')

            s_group[-1] = s_group[-1].strip()
            pair.append(s_group)
        pairs.append(pair)
    return pairs

def getvarName(tem):
    for temm in tem:
        if 'JNINativeMethod' in temm:
            print('114 |', temm)
            start = temm.find('JNINativeMethod')
            end = temm.find('=')
            name = temm[start + len('JNINativeMethod') :end]
            name = name.strip()
            name = name.replace('[]','')
            print('120 |', name)
            return name

def getVarStr(path, str):
    if not os.path.exists(path):
        return False
    file = None
    try:
        file = open(path, 'r', encoding='UTF-8')
        lines = file.readlines()
    except Exception as e:
        file = open(path, 'r', encoding='latin1')
        lines = file.readlines()
    finally:
        if(file):
            file.close()
    found = False
    cache = ''
    r_list = []
    for i, line in enumerate(lines):
        # TO DO
        # if 'clazz = env->FindClass(kClassName);' in line:
        #     exit(0)
        if str + ' =' in line and str + ' ==' not in line:
            print('142 |', line.strip())
            tem = line.strip().split('=')[1].strip().strip(';').strip('"').replace('/', '.')
            if tem=='':
                temm = lines[i+1]
                print('146 |', temm)
                match_obj = re.search(r'"[a-zA-Z0-9_/]+?"', temm)
                temmm = match_obj.group().replace('"', '')
                print('149 |', temmm)
                return temmm
            return tem

    return None

def findClass(path, str):
    if not os.path.exists(path):
        return False
    file = None
    try:
        file = open(path, 'r', encoding='UTF-8')
        lines = file.readlines()
    except Exception as e:
        file = open(path, 'r', encoding='latin1')
        lines = file.readlines()
    finally:
        if(file):
            file.close()
    found = False
    cache = ''
    r_list = []
    for i, line in enumerate(lines):
        if str in line and 'JNINativeMethod' not in line:
            # print(lines[i-1])
            print('line 164 |', line)
            print('line 165 |', lines[i-1])
            cache = []
            goon = True
            i2 = i
            while goon:
                cache.append(lines[i2])
                if '=' in lines[i2] or 'return' in lines[i2] or '{"' in lines[i2]:
                    goon = False
                i2 = i2 - 1
            cache.reverse()
            cacheFull = ''
            for temm in cache:
                cacheFull = cacheFull + temm.replace('\n', '').strip()
            print('156 | cacheFull:', cacheFull)
            
                
            # cacheFull: static const ClassRegistrationInfo gClasses[] = {{"android/opengl/Matrix", gMatrixMethods, NELEM(gMatrixMethods)}
            if '{"' in cacheFull:
                print('184 | cacheFull:', cacheFull)
                match_obj = re.search(r'"[a-zA-Z0-9/]+?"', cacheFull)
                print('196 |', match_obj)
                if match_obj:
                    print('198 |', match_obj.group())
                    classStr = match_obj.group().strip('"')
                    print('200 |', classStr)
                    # exit(0)
                    return classStr
            else:
                # cacheFull: return RegisterMethodsOrDie(env, kClassPathName, gMethods, NELEM(gMethods));
                if 'RegisterNatives' in cacheFull:
                    match_obj = re.search(r'[a-zA-Z0-9_]+?[,]', cacheFull)
                    classStr = match_obj.group().replace(',','').strip()
                    print('198 |', classStr)
                else:
                    l = cacheFull.split(',')
                    classStr = l[1].strip()
                print('202 | classStr', classStr)
                if classStr.startswith('"'):
                    classStr = classStr.strip('"')
                else:
                    print('206 | classStr:', classStr)
                    realCassStr = getVarStr(path, classStr)
                    if realCassStr is not None:
                        print('209 | classStr:', realCassStr)
                        return realCassStr
                    else:
                        print('212 | classStr:', realCassStr)
                        if classStr == "android::classPathName":
                            return "com/google/android/gles_jni/EGLImpl"
                        if re.search('^[A-Z_0-9]+$', classStr) is not None:
                            return 'FAIL'
                        # print(re.search('^[A-Z_0-9]+$', classStr).span() is not None)
                        exit(0)
                        # search in other files
                        pass
                    # exit(0)

                print('line 167 | classStr:', classStr)

                return classStr


def transformSmaliType(input):
    print('239 |', input)
    output = []
    array = 0
    while len(input) > 0:
        if input.startswith('L'):
            input = input[1:]
            input = input.replace('/','.')
            output.append(input)
            input = ''
        elif input.startswith('['):
            array = array + 1
            input = input[1:]
        elif input.startswith('V'):
            output.append('void')
            if array == 1:
                output.append('void[]')
                array = 0
            elif array == 2:
                output.append('void[][]')
                array = 0
            input = input[1:]
        elif input.startswith('Z'):
            output.append('boolean')
            if array == 1:
                output.append('boolean[]')
                array = 0
            elif array == 2:
                output.append('boolean[][]')
                array = 0
            input = input[1:]
        elif input.startswith('B'):
            output.append('byte')
            if array == 1:
                output.append('byte[]')
                array = 0
            elif array == 2:
                output.append('byte[][]')
                array = 0
            input = input[1:]
        elif input.startswith('S'):
            output.append('short')
            if array == 1:
                output.append('short[]')
                array = 0
            elif array == 2:
                output.append('short[][]')
                array = 0
            input = input[1:]
        elif input.startswith('C'):
            output.append('char')
            if array == 1:
                output.append('char[]')
                array = 0
            elif array == 2:
                output.append('char[][]')
                array = 0
            input = input[1:]
        elif input.startswith('I'):
            output.append('int')
            if array == 1:
                output.append('int[]')
                array = 0
            elif array == 2:
                output.append('int[][]')
                array = 0
            input = input[1:]
        elif input.startswith('J'):
            output.append('long')
            if array == 1:
                output.append('long[]')
                array = 0
            elif array == 2:
                output.append('long[][]')
                array = 0
            input = input[1:]
        elif input.startswith('F'):
            output.append('float')
            if array == 1:
                output.append('float[]')
                array = 0
            elif array == 2:
                output.append('float[][]')
                array = 0
            input = input[1:]
        elif input.startswith('D'):
            output.append('double')
            if array == 1:
                output.append('double[]')
                array = 0
            elif array == 2:
                output.append('double[][]')
                array = 0
            input = input[1:]

    return output


def transformTypeSmali2Java(input):
    l = input.split(';')
    output = []
    for tem in l:
        parList = transformSmaliType(tem)

        print('342 |', parList)
        output.extend(parList)
    return output
    pass

def formatParaList(input):
    # ['nativeOpen', ' "(Ljava/lang/String;Ljava/lang/String;III)J"', 'nativeOpen']
    # (parameter list) return type
    print('350 |', input)
    input = input.strip().strip('"')
    print('352 |', input)
    l = input.split(')')
    parList = l[0].strip('(').replace('"', '')
    returnType = l[1].replace('"', '')
    print('346| parList:', parList)
    print('347| returnType:', returnType)
    if re.search( r'\s[A-Z]{2,}\s', parList) or re.search( r'\s[A-Z]{2,}\s', returnType):
        return 'FAIL', 'FAIL'
    parameters = transformTypeSmali2Java(parList)
    returnType = transformTypeSmali2Java(returnType)
    return parameters, returnType

    
def extract_save():
    list = get_cpp_files_path(compdb, version)

    cpp_jni_list = []
    cleaned_jni_list = []

    for tem in list:
        # if 'android_media_RemoteDisplay.cpp' in tem[file_json_key]:
        #     print('*********')
        #     print(tem[file_json_key])
        #     print(tem['command'])
            # exit(2)
        if 'test' in tem[file_json_key].lower() or 'tests' in tem[file_json_key].lower() or 'armv7' in tem[file_json_key].lower():
            continue
        # [{source:'xxxx.cpp', content:{...}}]
        f = project_path + '/' + tem[file_json_key]

        found = False
        for temm in cpp_jni_list:
            if (f == temm['cpp']):
                found = True
        if found:
            continue
        str = 'static JNINativeMethod'
        if 'frameworks/' in f and find_str_in_file(f, str) and 'main.cpp' not in f:
            # print()
            print('391 |', f)
            jni_list = extract_jni_list(f, str)
            print('line 327 |', jni_list)
            # name of var
            name = getvarName(jni_list)
            # find class name registed for the var
            classStr = findClass(f, name)
            if classStr == 'FAIL':
                continue
            classStr = classStr.replace('/', '.')
            print('401 | classStr:', classStr)
            pairs = transform(jni_list)
            print('403 | pairs:', pairs)
            for group in pairs:
                for pair in group:
                    print('406 |', pair)
                    funStr = pair[0]
                    paramList = pair[1]
                    paraList, returnType = formatParaList(paramList)
                    if paraList == 'FAIL':
                        continue
                    print('412 | ================')
                    print('413 |', classStr , '',returnType, funStr, paraList)
                    cleaned_jni_list.append({'class': classStr, 'return': returnType, 'fun': funStr, 'parameters': paraList})
            # exit(0)

            cpp_jni_list.append({'cpp': f, 'pairs': pairs})
        str = 'static const JNINativeMethod'
        if 'frameworks/' in f and find_str_in_file(f, str) and 'main.cpp' not in f:
            # print()
            print('421 |', f)
            jni_list = extract_jni_list(f, str)
            print('423 |', jni_list)
            # name of var
            name = getvarName(jni_list)
            # find class name registed for the var
            classStr = findClass(f, name)
            classStr = classStr.replace('/', '.')
            print('429 | classStr:', classStr)
            pairs = transform(jni_list)
            print('431 | pairs:', pairs)
            for group in pairs:
                for pair in group:
                    print('434 |', pair)
                    funStr = pair[0]
                    paramList = pair[1]
                    paraList, returnType = formatParaList(paramList)
                    print('438 | ================')
                    print('439 |', classStr , '',returnType, funStr, paraList)
                    cleaned_jni_list.append({'class': classStr, 'return': returnType, 'fun': funStr, 'parameters': paraList})

            cpp_jni_list.append({'cpp': f, 'pairs': pairs})

    # with open(save_path, 'w') as file_obj:
    #     json.dump(cpp_jni_list, file_obj)
    with open(save_path2, 'w') as file_obj:
        print('447 | len(cleaned_jni_list):', len(cleaned_jni_list))
        json.dump(cleaned_jni_list, file_obj)

if __name__ == '__main__':
    extract_save()