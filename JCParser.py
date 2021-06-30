import os
import pprint
import warnings

from bs4 import BeautifulSoup
import pandas as pd
from defines import *
import time
import wordninja
import PyPDF2
import inspect

class JCParser(object):
    def __init__(self):
        """
            DATA_REPRESENTATION = {
                "file_path" : list[ list[ fields required] ]
            }
        """
        self.curr_dir = os.path.dirname(os.path.abspath(__file__))
        self.res_dir = self.curr_dir + "/res"
        self.output_dir = self.curr_dir + "/output"
        self.pdf_dir = self.curr_dir + "/pdf"
        self.raw_data_dict = dict()
        self.data_dict = dict()
        self.data_frame = pd.DataFrame(columns=self.get_df_columns())
        self.pdf_loss_info = []

    def print_statistics(self):
        list_paths = self.list_all_files(self.pdf_dir)
        print("The Total Number of pdf files: {}".format(len(list_paths)))
        print("The Total Number of items in DF: {}".format(self.data_frame[self.data_frame.columns[0]].count()))
        print("The dois w/out pdf files: {}".format(self.pdf_loss_info))

    def get_df_columns(self):
        return ["Year", "Month", "Volume", "Issue", "OnlineFirst", "ArticleType", "InvitedArticle", "StartingPage",
                "NumPages", "Title", "NumAuthors"] + ["Author" + str(i + 1) for i in range(NUM_AUTHORS)] + ["DOIorURL",
                                                                                                            "Editor",
                                                                                                            "AE"] + [
                   "Keyword" + str(i + 1) for i in range(NUM_KEYWORDS)] + ["GoogleCites", "WOSCites"]

    def build_list(self, year, month, vol, issue, online, article_type, invited, starting_page, num_pages,
                   title, num_authors, author_list, doi, editor, ass_editor, keyword_list, google_cite, wos_cite):
        return [year, month, vol, issue, online, article_type, invited, starting_page, num_pages, title, num_authors] + \
               author_list + [doi, editor, ass_editor] + keyword_list + [google_cite, wos_cite]

    def process(self):
        html_paths = self.process_path(self.list_all_files(self.res_dir))

        for file_path in html_paths:
            if not file_path.endswith(".html"):
                continue
            with open(file_path, "r") as file_object:
                try:
                    soup = BeautifulSoup(file_object, "html.parser")

                    f_volume, f_issue = self.get_volume_issue(soup)
                    warnings.warn("\nProcessing volume {}, issue {}".format(f_volume, f_issue))

                    f_month, f_year = self.get_issue_time(soup)
                    issue_items_list = soup.find_all(TAG_DIV, class_=CLASS_ISSUE_ITEMS_CONTAINER)
                    for issue_item_group in issue_items_list:
                        f_article_type = self.get_article_type(issue_item_group)
                        if self.is_needless(f_article_type):
                            continue

                        f_invited = "Y" if f_article_type == TITLE_RESEARCH_DIALOGUE \
                                           or f_article_type == TITLE_RESEARCH_DIALOGUES \
                                           or f_article_type == TITLE_RESEARCH_REVIEW \
                                           or f_article_type == TITLE_RESEARCH_REVIEWS else "N"

                        for paper_div in issue_item_group.find_all(TAG_DIV, class_=CLASS_ISSUE_ITEM):
                            f_epub_date: str = self.get_epub_date(paper_div)
                            f_starting_page, f_num_pages = self.get_page_info(paper_div)
                            f_list_authors, f_num_authors = self.get_authors(paper_div)
                            f_title = self.get_title(paper_div)
                            f_doi = self.get_doi(paper_div)
                            f_keyword_list, f_editors = self.get_keywords(f_doi, paper_div)
                            print("Printing Keywords: {}".format(f_keyword_list))
                            print("Printing Editors: {}".format(f_editors), end="\n\n")
                            item_list = self.build_list(f_year, f_month, f_volume, f_issue, f_epub_date, f_article_type,
                                                        f_invited, f_starting_page, f_num_pages, f_title, f_num_authors,
                                                        f_list_authors, f_doi, f_editors, "", f_keyword_list, "", "")
                            self.data_frame = self.data_frame.append(pd.DataFrame([item_list],
                                                                                  columns=self.get_df_columns()))
                except Exception as e:
                    print("ERROR: " + str(e))
                    print("ERROR: " + "parse process failed for file " + file_path)
        output_path = self.output_dir + "/" + "output-" + str(int(time.time())) + ".xlsx"
        print("Result written to: " + output_path)
        self.data_frame.to_excel(output_path)
        self.print_statistics()

    def test(self):
        print("Listing all htmls to be processed...")
        pprint.pprint(self.list_all_files(self.res_dir))

    @staticmethod
    def list_all_files(root_dir):
        _files = []
        lst = os.listdir(root_dir)
        for i in range(0, len(lst)):
            path = os.path.join(root_dir, lst[i])
            if os.path.isdir(path):
                _files.extend(JCParser.list_all_files(path))
            if os.path.isfile(path):
                _files.append(path)
        return _files

    def get_article_type(self, issue_item_group):
        try:
            h3_tag = issue_item_group.find_all(TAG_H3, class_=CLASS_ISSUE_ITEMS_H3)[0]
            t = h3_tag.contents[0]
            return t
        except Exception:
            return "ERROR_TYPE"

    def get_volume_issue(self, soup):
        volume = "-1"
        issue = "-1"
        try:
            var = soup.find_all(TAG_DIV, class_=CLASS_VOLUME_ISSUE)
            for i in range(len(var[0])):
                if i == 0:
                    raw_string = str(var[0].contents[0].contents[0])
                    volume = raw_string.strip(" ,").split(" ")[1]
                elif i == 1:
                    raw_string = str(var[0].contents[1])
                    issue = raw_string.strip().split(" ")[1]
            return volume, issue
        except Exception:
            print("Exception at: {}".format(inspect.stack()[0][3]))
            return volume, issue

    def get_epub_date(self, paper_div):
        month_dict = {
            "January": "01",
            "February": "02",
            "March": "03",
            "April": "04",
            "May": "05",
            "June": "06",
            "July": "07",
            "August": "08",
            "September": "09",
            "October": "10",
            "November": "11",
            "December": "12",
        }
        date = "00-00-0000"
        try:
            lst = paper_div.find_all(TAG_UL, {"class": CLASS_TIME_UL})
            for tag in lst:
                raw_date = str(tag.find_all(TAG_LI, class_=CLASS_EPUB_DATE)[0].contents[1].contents[0])
                date_list = raw_date.split(" ")
                date = "{}-{}-{}".format(date_list[0], month_dict[date_list[1]], date_list[2])
            return date
        except Exception:
            print("Exception at: {}".format(inspect.stack()[0][3]))
            return date

    def get_page_info(self, paper_div):
        start_page, num_pages = "0", "0"
        try:
            for tag in paper_div.find_all(TAG_UL, {"class": CLASS_TIME_UL}):
                raw_pages = str(tag.find_all(TAG_LI, class_=CLASS_PAGE_RANGE)[0].contents[1].contents[0])
                if raw_pages.isnumeric():
                    return raw_pages, 1
                page_list = raw_pages.split("-")
                start_page = page_list[0]
                num_pages = str(int(page_list[1]) - int(page_list[0]) + 1)
            return start_page, num_pages
        except Exception:
            print("Exception at: {}".format(inspect.stack()[0][3]))
            return start_page, num_pages

    def get_title(self, paper_div):
        title = "Empty Title"
        try:
            for tag in paper_div.find_all(TAG_A, class_=CLASS_PAPER_TITLE):
                title = str(tag.contents[1].contents[0])
            return "\"" + title + "\""
        except Exception:
            print("Exception at: {}".format(inspect.stack()[0][3]))
            return title

    def get_authors(self, paper_div):
        authors = ["" for _ in range(NUM_AUTHORS)]
        num_authors = 0
        try:
            index = 0
            for tag in paper_div.find_all(TAG_DIV, class_=CLASS_AUTHORS):
                num_authors = len(tag.contents[1].contents)
                for author_span in tag.contents[1].contents:
                    curr_raw_author = str(author_span.contents[0].contents[0].contents[0]).strip()
                    name_list = curr_raw_author.split(" ")
                    for i in range(len(name_list)):
                        if i == len(name_list) - 1:
                            name_list[i] = name_list[i].strip(". ")
                        else:
                            name_list[i] = name_list[i].strip(". ")[0]
                    curr_name = name_list[-1] + " " + "".join(name_list[:-1])
                    authors[index] = curr_name
                    index += 1
        except Exception:
            print("Exception at: {}".format(inspect.stack()[0][3]))
        return authors, num_authors

    def get_issue_time(self, soup):
        month, year = "-1", "-1"
        try:
            for tag in soup.find_all(TAG_DIV, class_=CLASS_COVER_IMAGE_DATE):
                time_string = str(tag.contents[0].contents[0])
                month = time_string.split(" ")[0]
                year = time_string.split(" ")[1]
        except Exception:
            print("Exception at: {}".format(inspect.stack()[0][3]))
        return month, year

    def get_doi(self, paper_div):
        doi = "empty_doi"
        try:
            for tag in paper_div.find_all(TAG_UL, class_=CLASS_ITEM_LINKS):
                li_tag_1 = tag.find_all('a', {"title": "Abstract"})
                li_tag_2 = tag.find_all('a', {"title": "EPDF"})
                li_tag = li_tag_1 if len(li_tag_1) > 0 else li_tag_2
                if len(li_tag) == 0:
                    return doi
                li_tag_workable = li_tag[0]
                href_list = li_tag_workable['href'].split("/")[-2:]
                doi = "/".join(href_list)
        except Exception:
            print("Exception at: {}".format(inspect.stack()[0][3]))
        return doi

    def get_keywords(self, raw_doi, paper_div):
        doi = raw_doi.split("/")[1]
        file_path = self.pdf_dir + "/" + doi + ".pdf"

        '''return elems'''
        key_words = ["" for _ in range(NUM_KEYWORDS)]
        editors = ""

        if not os.path.isfile(file_path):
            self.pdf_loss_info.append([doi])
            return key_words, editors
        try:
            pdfFileObj = open(file_path, 'rb')
            pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
            pages = pdfReader.numPages
            for i in range(pages):
                if i:
                    continue
                pageObj = pdfReader.getPage(i)
                text = pageObj.extractText().split("  ")
                text = text[0].split("\n")
                for i in range(len(text)):
                    if "Keywords" in text[i]:
                        def process(lst):
                            for j in range(len(lst)):
                                lst[j] = " ".join(wordninja.split(lst[j]))
                            return lst

                        if ";" in text[i]:
                            index = text[i].index(":")
                            loc_keywords = process(text[i][index + 1:].split(";"))
                        else:
                            l1 = text[i + 1]
                            l2 = text[i + 2]
                            final_l = l1 if not l2.startswith("!") and ";" not in l2 else l1 + "!" + l2[:]
                            loc_keywords = process(final_l.split(";"))
                        for k in range(min(len(loc_keywords), len(key_words))):
                            key_words[k] = loc_keywords[k]
                        if len(loc_keywords) > len(key_words):
                            print("WARNING! MAXIMUM NUM KEYWORDS DETECTED IS LARGER THAN THE THRESHOLD SET")

                    if "Acceptedby" in text[i]:
                        editors = text[i].strip()
        except Exception:
            print("Exception at: {}".format(inspect.stack()[0][3]))

        return key_words, editors

    def is_needless(self, f_article_type):
        return f_article_type in [
            TITLE_ISSUE_INFORMATION,
            TITLE_EDITORIAL_BOARD,
            "ERROR_TYPE",
            TITLE_CORRIGENDUM,
            TITLE_ANNOUNCEMENT,
            TITLE_EDITORIAL_NOTE,
            TITLE_CORRIGENDUM_UPPER,
            TITLE_RETRACTION
        ]

    def process_path(self, list_paths):
        result_path: list = list(filter(lambda x : x.endswith(".html"), list_paths))
        result_path.sort(reverse=True)
        return result_path

