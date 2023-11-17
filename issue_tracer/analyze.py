# This python script is used to analyze collected issues.
import os
import sys

cwd = os.getcwd()
issue_file_dict = {}
issue_categories_dict = {}
sep = os.sep

def read_file():
    # read all issue file from cwd/issues
    for root, dirs, files in os.walk(cwd + os.sep + 'issues'):
        for file in files:
            # if file.endswith('.pdf'):
                path = os.path.join(root, file)
                category = get_issue_category(root)
                print("Issue category: " + category)
                issue_file_dict[path] = category
    print("*" * 50)
    print("Total issue file: " + str(len(issue_file_dict)))

def get_categories():
    for root, dirs, files in os.walk(cwd + os.sep + 'issues'):
        for dir in dirs:
            issue_categories_dict[dir] = 0

def calculate_issue_category():
    for issue in issue_file_dict:
        print("Issue file: " + issue)
        print("Issue category: " + issue_file_dict[issue])
        if issue_file_dict[issue] in issue_categories_dict:
            issue_categories_dict[issue_file_dict[issue]] += 1
    print("*" * 50)
    print("Total issue categories: " + str(len(issue_categories_dict)))
    print("*" * 50)
    print("Issue categories: ")
    for category in issue_categories_dict:
        print(category + ": " + str(issue_categories_dict[category]))

def save_to_file():
    with open(cwd + os.sep + 'result.txt', "w", encoding='utf-8') as f:
        for category in issue_categories_dict:
            f.write(category + ": " + str(issue_categories_dict[category]) + "\n")

        current_category = ""

        for issue in issue_file_dict:
            temp = issue_file_dict[issue]
            if temp != current_category:
                current_category = temp
                f.write("*" * 50 + "\n")
                f.write(temp + "\n")
                f.write("*" * 50 + "\n")
            f.write(issue + ": " + issue_file_dict[issue] + "\n")


def get_issue_category(root):
    return root.split(sep)[-1]

if __name__ == '__main__':
    get_categories()
    read_file()
    calculate_issue_category()
    save_to_file()
