from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import os
import time
from random import randint
import base64

# 如果系统为 windows，则指定 chrome 的驱动
driver = webdriver.Chrome()

issue_id_list = []
id_type_dict = {}
code_start_pattern = "<code>"
code_end_pattern = "</code>"
save_pattern_2 = ".so"

list_file = os.getcwd() + '/issue_id_list.txt'

# # root_url = 'https://issuetracker.google.com/issues?q=jni'
# root_url = "https://issuetracker.google.com/issues?q=jni&p="
# # 初始化页码
# page_no = 1

# root_flag = True
# while root_flag:
#     # 拼接 url
#     url = root_url + str(page_no)
#     print("Original URL: " + url)
#     # 访问 url, 并检查是否返回 200
#     driver.get(url)
#     print("*" * 50)
#     last_page_source = ""
#     flag = True
#     while flag:
#         current_page_source = driver.page_source
#         if current_page_source == last_page_source:
#             flag = False
#         else:
#             last_page_source = current_page_source
#             # 等待页面加载完成
#             time.sleep(randint(2, 4))
#     # 保存源码
#     content_file = os.getcwd() + '/content/page' + str(page_no) + '.html'
#     with open(content_file, "w", encoding='utf-8') as f:  # 注意这里添加了 encoding='utf-8'
#         f.write(last_page_source)
#     # 逐行分析源码，如果有 data-row-id 则保存
#     for line in last_page_source.splitlines():
#         # data-row-id="36968595"
#         if 'data-row-id' in line:
#             issue_id = line.split('data-row-id="')[1].split('"')[0]
#             if issue_id not in issue_id_list:
#                 issue_id_list.append(issue_id)
#             else:
#                 root_flag = False
#             # status-ASSIGNED
#             status = line.split('status-')[1].split(' ')[0]
#             id_type_dict[issue_id] = status
#     print("Current issue_id_list: " + str(issue_id_list))
#     print("*" * 50)
#     page_no += 1

# # write all issue_id_list to file
# 
# # 如果文件存在则清空文件
# if os.path.exists(list_file):
#     with open(list_file, "w", encoding='utf-8') as f:
#         f.write("")
#         f.close()
with open(list_file, "a", encoding='utf-8') as f:
    for issue in issue_id_list:
        status = id_type_dict[issue]
        f.write(issue + "," + status + "\n")

print("Finished processing all root pages.")
print("Total issue_id_list: " + str(issue_id_list))
print("*" * 50)

print("Start processing all issue pages.")

# read all issue_id_list from file
issue_id_list = []
list_file = os.getcwd() + '/issue_id_list.txt'
with open(list_file, "r", encoding='utf-8') as f:
    for line in f.readlines():
        issue_id_list.append(line.split(",")[0])
        id_type_dict[line.split(",")[0]] = line.split(",")[1].strip()

# 逐个访问 issue 页面
issue_url = "https://issuetracker.google.com/issues/"

for issue in issue_id_list:
    url = issue_url + issue
    print("Issue URL: " + url)
    driver.get(url)
    print("*" * 50)
    # 等待页面加载完成
    last_page_source = ""
    flag = True
    while flag:
        current_page_source = driver.page_source
        if current_page_source == last_page_source:
            flag = False
        else:
            last_page_source = current_page_source
            # 等待页面加载完成
            time.sleep(randint(2, 4))
    # 在源码中查找 <code> 和 </code>，如果有则保存
    code_elements = []
    save = False
    # 逐行分析源码，如果有 <code> 则保存

    # pdf 参数
    pdf_options = {
    'landscape': False,
    'format': 'A4',
    'margin': {
        'top': '1cm',
        'bottom': '1cm',
        'left': '1cm',
        'right': '1cm'
        }
    }

    chrome_command = {
    'cmd': '_Chrome.printToPDF',
    'params': pdf_options
    }

    if code_start_pattern in last_page_source:
        pdf_response = driver.execute_cdp_cmd('Page.printToPDF', pdf_options)
        pdf_data = base64.b64decode(pdf_response['data'])
        status = id_type_dict[issue]
        dir = os.getcwd() + os.sep + 'issues' + os.sep + status
        if not os.path.exists(dir):
            os.makedirs(dir)
        content_file = dir + os.sep + issue + '.pdf'
        with open(content_file, "wb") as f:
            f.write(pdf_data)
        print("Finished processing issue " + issue)
        # lines = last_page_source.splitlines()  # 一次性分割所有行
        # line_no = len(lines)
        # i = 0
        # code_elements = []  # 初始化用于保存代码块的列表
        # while i < line_no:
        #     code_content = []  # 初始化用于保存单个代码块内容的列表
        #     line = lines[i]

        #     if code_start_pattern in line:
        #         if code_end_pattern in line:
        #             # <code> 和 </code> 在同一行
        #             code_content.append(line.split(code_start_pattern)[1].split(code_end_pattern)[0])
        #         else:
        #             # <code> 和 </code> 不在同一行
        #             code_content.append(line.split(code_start_pattern)[1])
        #             i += 1
        #             while code_end_pattern not in lines[i]:
        #                 code_content.append(lines[i])
        #                 i += 1
        #             code_content.append(lines[i].split(code_end_pattern)[0])

        #         code_elements.append(code_content)

        #     i += 1

        # print("Current code_elements: ", code_elements)
        # print("*" * 50)
        # for element in code_elements:
        #     if save_pattern_2 in element:
        #         save = True
        #         print("Save issue " + issue + " with code. + .so")
        #         break
        # # 保存源码
        # # check dir exist
        # if save == True:
        #     status = id_type_dict[issue]
        #     dir = os.getcwd() + os.sep + 'issues' + os.sep + status
        #     if not os.path.exists(dir):
        #         os.makedirs(dir)
        #     content_file = dir + os.sep + issue + '.txt'
        #     with open(content_file, "w", encoding='utf-8') as f:
        #         for code_element in code_elements:
        #             for line in code_element:
        #                 f.write(line + "\n")
        #     print("Finished processing issue " + issue)
        #     print("*" * 50)

print("Finished processing all issue pages.")
