from bs4 import BeautifulSoup
import pandas as pd
import os
import pprint

import wordninja

import io

# def main():
#     import PyPDF2
#     pdfName = './pdf/jcpy.1067.pdf'
#     read_pdf = PyPDF2.PdfFileReader(pdfName)
#
#     for i in range(read_pdf.getNumPages()):
#         if not i:
#             page = read_pdf.getPage(i)
#             print()
#             print()
#             print('Page No - ' + str(1 + read_pdf.getPageNumber(page)))
#             page_content = page.extractText()
#             print(page_content)
#
# def main2():
#     import PyPDF4
#     pdfFileObj = open(r'./pdf/jcpy.1067.pdf', 'rb')
#     pdfReader = PyPDF4.PdfFileReader(pdfFileObj)
#     pageObj = pdfReader.getPage(1)
#     pages_text = pageObj.extractText()
#     for line in io.StringIO(pages_text):
#         print(line)
def list_all_files(root_dir):
    _files = []
    lst = os.listdir(root_dir)
    for i in range(0, len(lst)):
        path = os.path.join(root_dir, lst[i])
        if os.path.isdir(path):
            _files.extend(list_all_files(path))
        if os.path.isfile(path):
            _files.append(path)
    return _files

def main3():
    # Importing required modules
    import PyPDF2
    # Creating a pdf file object 1075 1078 'pdf/jcpy.1067.pdf'
    pdfFileObj = open('pdf/j.jcps.2014.05.004.pdf', 'rb')
    # Creating a pdf reader object
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    # Getting number of pages in pdf file
    pages = pdfReader.numPages
    # Loop for reading all the Pages
    for i in range(pages):
        if i: continue
        # Creating a page object
        pageObj = pdfReader.getPage(i)
        # Printing Page Number
        print("Page No: ", i)
        # Extracting text from page
        # And splitting it into chunks of lines
        text = pageObj.extractText().split("  ")
        text = text[0].split("\n")
        # Finally the lines are stored into list
        # For iterating over list a loop is used
        for i in range(len(text)):
            # Printing the line
            # Lines are seprated  using "\n"
            if "Keywords" in text[i]:
                def process(lst):
                    for i in range(len(lst)):
                        lst[i] = " ".join(wordninja.split(lst[i]))
                    return lst
                print(text[i], end="\n")
                print(text[i+1], end="\n")
                print(text[i+2], end="\n")
                l1 = text[i+1]
                l2 = text[i+2]
                final_l = l1 if not l2.startswith("!") and ";" not in l2 else l1 + "fl" + l2[1:]
                print(process(final_l.split(";")))
            if "Acceptedby" in text[i]:
                print(text[i])

            # print(text[i], end="\n\n")
        # pprint.pprint(text)
        # index = text.index("Keywords")
        # if index != -1:
        #     print("No result for page " + str(i))
        #     continue
        # else:
        #
        #     l1 = text[index+1]
        #     l2 = text[index+2]
        #     final_l = l1 if not l2.startswith("!") and ";" not in l2 else l1 + "l" + l2[1:]
        #     print(final_l)



        # For Seprating the Pages
        print()

    # closing the pdf file object
    pdfFileObj.close()

def process_path(list_paths):
    result_path: list = list(filter(lambda x : x.endswith(".html"), list_paths))
    result_path.sort()
    return result_path

def main4():
    list = process_path(list_all_files("res"))
    pprint.pprint(list)

def main5():
    import requests
    from requests_html import HTMLSession
    str_1 = "10.1016"
    str_2 = "j.jcps.2015.06.002"
    surl = "https://scholar.google.com.hk/scholar?hl=zh-CN&as_sdt=0%2C5&q={}%2F{}&btnG=".format(str_1, str_2)
    url = "https://www.searchenginejournal.com/introduction-to-python-seo-spreadsheets/342779/"
    try:
        session = HTMLSession()
        response = session.get(surl)
        html = response.html.html
        print(html)
    except requests.exceptions.RequestException as e:
        print(e)

if __name__ == '__main__':
    # main2()
    # main3()
    main5()
    # main4()