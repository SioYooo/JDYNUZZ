import sys

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import os
from time import sleep
from random import randint
import base64
import argparse

# 如果系统为 windows，则指定 chrome 的驱动
driver = webdriver.Chrome()

issue_id_list = []
id_type_dict = {}
aosp_build_list = []
aosp_count_dict = {}
code_start_pattern = "<code>"
code_end_pattern = "</code>"
save_pattern_2 = ".so"


def args_parse(input_args):
    # 创建解析器
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--start", help="Start index", type=int, default=0)
    # 解析参数
    input_args = parser.parse_args()

    # 获取 start_index
    index = input_args.start
    return index


def root_page_process():
    global issue_id_list
    list_file = os.getcwd() + '/issue_id_list.txt'

    # root_url = 'https://issuetracker.google.com/issues?q=jni'
    root_url = "https://issuetracker.google.com/issues?q=jni&p="
    # 初始化页码
    page_no = 1

    root_flag = True
    while root_flag:
        # 拼接 url
        url = root_url + str(page_no)
        print("Original URL: " + url)
        # 访问 url, 并检查是否返回 200
        driver.get(url)
        print("*" * 50)
        last_page_source = ""
        flag = True
        while flag:
            current_page_source = driver.page_source
            if current_page_source == last_page_source:
                flag = False
            else:
                last_page_source = current_page_source
                # 等待页面加载完成
                sleep(randint(2, 4))
        # 保存源码
        content_file = os.getcwd() + '/content/page' + str(page_no) + '.html'
        with open(content_file, "w", encoding='utf-8') as f:  # 注意这里添加了 encoding='utf-8'
            f.write(last_page_source)
        # 逐行分析源码，如果有 data-row-id 则保存
        for line in last_page_source.splitlines():
            # data-row-id="36968595"
            if 'data-row-id' in line:
                issue_id = line.split('data-row-id="')[1].split('"')[0]
                if issue_id not in issue_id_list:
                    issue_id_list.append(issue_id)
                else:
                    root_flag = False
                # status-ASSIGNED
                status = line.split('status-')[1].split(' ')[0]
                id_type_dict[issue_id] = status
        print("Current issue_id_list: " + str(issue_id_list))
        print("*" * 50)
        page_no += 1

    # write all issue_id_list to file

    # 如果文件存在则清空文件
    if os.path.exists(list_file):
        with open(list_file, "w", encoding='utf-8') as f:
            f.write("")
            f.close()
    with open(list_file, "a", encoding='utf-8') as f:
        for issue in issue_id_list:
            status = id_type_dict[issue]
            f.write(issue + "," + status + "\n")

    print("Finished processing all root pages.")
    print("Total issue_id_list: " + str(issue_id_list))
    print("*" * 50)


def individual_issue_process(index: int):
    print("Start processing all issue pages.")
    aosp_build_list = []
    issue_id_list = []
    id_type_dict = {}
    # 从文件中读取所有的问题 ID
    list_file = os.getcwd() + '/issue_id_list.txt'
    with open(list_file, "r", encoding='utf-8') as f:
        for line in f.readlines():
            issue_id_list.append(line.split(",")[0])
            id_type_dict[line.split(",")[0]] = line.split(",")[1].strip()
    print("Total issue_id_list: " + str(issue_id_list))
    build_file = os.getcwd() + '/aosp_build_list.txt'
    with open(build_file, "r", encoding='utf-8') as f:
        for line in f.readlines():
            aosp_build_list.append(line.strip())

    issue_url = "https://issuetracker.google.com/issues/"

    if index != 0:
        # 如果 index 不为 0，则从 index 开始
        issue_id_list = issue_id_list[index:]

    for issue in issue_id_list:
        try:
            # 设置 PDF 选项
            pdf_options = {
                "landscape": False,
                "displayHeaderFooter": False,
                "printBackground": True,
                "preferCSSPageSize": True,
            }
            url = issue_url + issue
            print("Issue URL: " + url)
            driver.get(url)
            print("*" * 50)
            # 等待页面加载完成
            last_page_source = ""
            save_flag = False
            flag = True
            while flag:
                current_page_source = driver.page_source
                if current_page_source == last_page_source:
                    flag = False
                else:
                    last_page_source = current_page_source
                    # 等待页面加载完成
                    sleep(randint(2, 4))
            # 找到所有 div
            # div_elements = driver.find_elements(By.TAG_NAME, 'div')
            # # 在 div_elements 中找到包含 "AOSP ID" 的 div
            # aosp_id_div = None
            # for div in div_elements:
            #     if div.text == "AOSP ID":
            #         aosp_id_div = div
            #         break
            # # 如果没有找到 "AOSP ID"，则跳过
            # if aosp_id_div is None:
            #     continue
            # if aosp_id_div is not None:
            #     aosp_id_div_index = div_elements.index(aosp_id_div)
            #     # 找到紧随其后的一个 div
            #     aosp_id_value_div = div_elements[aosp_id_div_index + 1]
            #     # 找到紧随其后的一个 div 中的相关属性
            #     aosp_id_value_div_attribute = aosp_id_value_div.get_attribute('class')
            #     aosp_id_value_div_text = aosp_id_value_div.text
            #     print("AOSP ID div text: " + aosp_id_value_div_text)
            #     if aosp_id_value_div_text != "--":
            #         save_flag = True
            #         print("AOSP ID: " + aosp_id_value_div_text)
            #         # 将 aosp_id_value_div_text 写入文件
            #         if aosp_id_value_div_text in aosp_count_dict.keys():
            #             aosp_count_dict[aosp_id_value_div_text] += 1
            #         else:
            #             aosp_count_dict[aosp_id_value_div_text] = 1
            #         # 如果找到了非 -- 的 AOSP ID，在添加完 AOSP ID 之后，结束当前页面的处理
            #         continue
            #     # 如果 aosp_id_value_div_attribute == "--"，则查看整个页面的源码，其中是否涉及了 AOSP build ID
            #     if aosp_id_value_div_text == "--":
            print("System does not provide AOSP ID, check source page for AOSP build ID.")
            for aosp_build in aosp_build_list:
                if aosp_build in last_page_source:
                    save_flag = True
                    print("Found AOSP build ID: " + aosp_build)
                    aosp_id_value_div_text = aosp_build
                    if aosp_id_value_div_text in aosp_count_dict.keys():
                        aosp_count_dict[aosp_id_value_div_text] += 1
                    else:
                        aosp_count_dict[aosp_id_value_div_text] = 1
                    break
            # 如果 save_flag == True，则将当前 issue_id 保存到文件中
            if save_flag:
                # 将页面保存为 PDF
                # 生成 PDF
                pdf = driver.execute_cdp_cmd("Page.printToPDF", pdf_options)
                pdf_content = base64.b64decode(pdf['data'])
                # 保存 PDF
                issue_type = id_type_dict[issue]
                pdf_file_name = os.getcwd() + os.sep + "pdf" + os.sep + issue_type + os.sep + issue + "_" + aosp_id_value_div_text + ".pdf"
                # 检查path是否存在
                if not os.path.exists(os.getcwd() + os.sep + "pdf" + os.sep + issue_type):
                    os.makedirs(os.getcwd() + os.sep + "pdf" + os.sep + issue_type)
                with open(pdf_file_name, "wb") as f:
                    f.write(pdf_content)
            # 将 aosp_count_dict 写入文件
            with open(os.getcwd() + os.sep + "aosp_count.txt", "w", encoding='utf-8') as f:
                for k, v in aosp_count_dict.items():
                    f.write(k + "," + str(v) + "\n")
        except Exception as e:
            print("Error occurred when processing issue " + issue + ": " + str(e))

        # 查看这个页面内的所有 div 元素
        # div_elements = driver.find_elements(By.TAG_NAME, 'div')
        # if len(div_elements) == 0:
        #     print("No div elements found!")
        #     continue
        # else:
        #     for div in div_elements:
        #         div_attribute = div.get_attribute('class')
        #         div_text = div.text
        #         if div_attribute is not None and div_text is not None or div_text != "":
        #             print("Div attribute " + div.get_attribute('class'))
        #             print("Div text " + div.text)
        #             # 查看 div 元素中的内容
        #             sleep(0.5)

    # 在源码中查找 <code> 和 </code>，如果有则保存
    # code_elements = []
    # save = False
    # # 逐行分析源码，如果有 <code> 则保存

    # # pdf 参数
    # pdf_options = {
    # 'landscape': False,
    # 'format': 'A4',
    # 'margin': {
    #     'top': '1cm',
    #     'bottom': '1cm',
    #     'left': '1cm',
    #     'right': '1cm'
    #     }
    # }
    #
    # chrome_command = {
    # 'cmd': '_Chrome.printToPDF',
    # 'params': pdf_options
    # }

    # if code_start_pattern in last_page_source:
    #     pdf_response = driver.execute_cdp_cmd('Page.printToPDF', pdf_options)
    #     pdf_data = base64.b64decode(pdf_response['data'])
    #     status = id_type_dict[issue]
    #     dir = os.getcwd() + os.sep + 'issues' + os.sep + status
    #     if not os.path.exists(dir):
    #         os.makedirs(dir)
    #     content_file = dir + os.sep + issue + '.pdf'
    #     with open(content_file, "wb") as f:
    #         f.write(pdf_data)
    #     print("Finished processing issue " + issue)
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


# def test():
#     # url
#     url = "https://issuetracker.google.com/issues/284266334"
#     # 等待页面加载
#     driver.get(url)
#     # 等待页面加载完成
#     webdriver_wait = WebDriverWait(driver, 10)
#
#     # 加载完成后，获取页面的所有 p, pre, code 元素
#     p_elements = driver.find_elements(By.TAG_NAME, 'p')
#     pre_elements = driver.find_elements(By.TAG_NAME, 'pre')
#     code_elements = driver.find_elements(By.TAG_NAME, 'code')
#
#     # 遍历所有 p 元素
#     for p in p_elements:
#         p_attribute = p.get_attribute('class')
#         p_text = p.text
#         if p_attribute is not None and p_text is not None or p_text != "":
#             # print("p attribute " + p.get_attribute('class'))
#             print(p.text)
#             # 查看 p 元素中的内容
#             sleep(0.5)


def get_aosp_version():
    url = "https://source.android.com/docs/setup/about/build-numbers"
    # 页面加载
    driver.get(url)
    # 等待页面加载完成
    webdriver_wait = WebDriverWait(driver, 10)
    # 获取所有 tables
    tables = driver.find_elements(By.TAG_NAME, 'table')
    # 获取第一个 table
    # table = tables[0]
    # # 获取所有 tr
    # trs = table.find_elements(By.TAG_NAME, 'tr')
    # for tr in trs:
    #     print(tr.text)
    # 获取第二个 table
    table = tables[1]
    # 获取所有 tr
    trs = table.find_elements(By.TAG_NAME, 'tr')
    for tr in trs:
        # 获取所有 tr 的第一列
        tds = tr.find_elements(By.TAG_NAME, 'td')
        if len(tds) == 0:
            continue
        # 获取第一列的内容
        td = tds[0]
        aosp_build_list.append(td.text)
    # 将 aosp_build_list 写入文件
    with open("aosp_build_list.txt", "w", encoding='utf-8') as f:
        for item in aosp_build_list:
            f.write(item + "\n")
    print("Finished processing aosp_build_list.")


if __name__ == "__main__":
    args = sys.argv
    if "aosp_build_list.txt" not in os.listdir():
        get_aosp_version()
    else:
        with open("aosp_build_list.txt", "r", encoding='utf-8') as f:
            if len(f.readlines()) == 0:
                get_aosp_version()
    if "issue_id_list.txt" not in os.listdir():
        root_page_process()
    else:
        with open("issue_id_list.txt", "r", encoding='utf-8') as f:
            if len(f.readlines()) == 0:
                root_page_process()
    # index 699 处理有问题，跳过
    start_index = args_parse(args)
    individual_issue_process(start_index)
    driver.quit()
    print("Finished processing all issues.")
