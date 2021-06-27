import os
import pprint

from bs4 import BeautifulSoup
import pandas as pd
from defines import *
import time


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
        self.raw_data_dict = dict()
        self.data_dict = dict()
        self.data_frame = pd.DataFrame(columns=self.get_df_columns())

    def get_df_columns(self):
        return ["Year", "Month", "Volume", "Issue", "OnlineFirst", "ArticleType", "InvitedArticle", "StartingPage",
                "NumPages", "Title", "NumAuthors"] + ["Author"+str(i+1) for i in range(NUM_AUTHORS)] + ["DOIorURL",
                "Editor", "AE"] + ["Keyword"+str(i+1) for i in range(NUM_KEYWORDS)] + ["GoogleCites", "WOSCites"]

    def build_list(self, year, month, vol, issue, online, article_type, invited, starting_page, num_pages,
                   title, num_authors, author_list, doi, editor, ass_editor, keyword_list, google_cite, wos_cite):
        return [year, month, vol, issue, online, article_type, invited, starting_page, num_pages, title, num_authors] +\
               author_list + [doi, editor, ass_editor] + keyword_list + [google_cite, wos_cite]

    def process(self):
        for file_path in self.list_all_files(self.res_dir):
            with open(file_path, "r") as file_object:
                try:
                    soup = BeautifulSoup(file_object, "html.parser")
                    f_volume, f_issue = self.get_volume_issue(soup)
                    f_month, f_year = self.get_issue_time(soup)
                    issue_items_list = soup.find_all(TAG_DIV, class_=CLASS_ISSUE_ITEMS_CONTAINER)
                    for issue_item_group in issue_items_list:
                        f_article_type = self.get_article_type(issue_item_group)
                        if f_article_type == TITLE_ISSUE_INFORMATION:
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
                            f_keyword_list = self.get_keywords(paper_div)
                            item_list = self.build_list(f_year, f_month, f_volume, f_issue, f_epub_date, f_article_type,
                                                        f_invited, f_starting_page, f_num_pages,f_title, f_num_authors,
                                                        f_list_authors, f_doi, "", "", f_keyword_list, "", "")
                            self.data_frame = self.data_frame.append(pd.DataFrame([item_list],
                                                                                  columns=self.get_df_columns()))
                except Exception as e:
                    print(e)
                    print("ERROR: " + "parse process failed for file " + file_path)
        output_path = self.output_dir + "/" + "output-" + str(int(time.time())) + ".xlsx"
        print(output_path)
        self.data_frame.to_excel(output_path)


    def test(self):
        print(self.list_all_files(self.res_dir))

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
        var = soup.find_all(TAG_DIV, class_=CLASS_VOLUME_ISSUE)
        for i in range(len(var[0])):
            if i == 0:
                raw_string = str(var[0].contents[0].contents[0])
                volume = raw_string.strip(" ,").split(" ")[1]
            elif i == 1:
                raw_string = str(var[0].contents[1])
                issue = raw_string.strip().split(" ")[1]
        print(volume, issue)
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
        lst = paper_div.find_all(TAG_UL, {"class": CLASS_TIME_UL})
        for tag in lst:
            raw_date = str(tag.find_all(TAG_LI, class_=CLASS_EPUB_DATE)[0].contents[1].contents[0])
            date_list = raw_date.split(" ")
            date = "{}-{}-{}".format(date_list[0], month_dict[date_list[1]], date_list[2])
        return date

    def get_page_info(self, paper_div):
        start_page, num_pages = "0", "0"
        for tag in paper_div.find_all(TAG_UL, {"class": CLASS_TIME_UL}):
            raw_pages = str(tag.find_all(TAG_LI, class_=CLASS_PAGE_RANGE)[0].contents[1].contents[0])
            page_list = raw_pages.split("-")
            start_page = page_list[0]
            num_pages = str(int(page_list[1]) - int(page_list[0]) + 1)
        return start_page, num_pages

    def get_title(self, paper_div):
        title = "Empty Title"
        for tag in paper_div.find_all(TAG_A, class_=CLASS_PAPER_TITLE):
            title = str(tag.contents[1].contents[0])
        return "\"" + title + "\""

    def get_authors(self, paper_div):
        authors = ["" for _ in range(NUM_AUTHORS)]
        index = 0
        num_authors = 0
        for tag in paper_div.find_all(TAG_DIV, class_=CLASS_AUTHORS):
            num_authors = len(tag.contents[1].contents)
            for author_span in tag.contents[1].contents:
                curr_raw_author = str(author_span.contents[0].contents[0].contents[0]).strip()
                name_list = curr_raw_author.split(" ")
                for i in range(len(name_list)):
                    if i == len(name_list)-1:
                        name_list[i] = name_list[i].strip(". ")
                    else:
                        name_list[i] = name_list[i].strip(". ")[0]
                curr_name = name_list[-1] + " " + "".join(name_list[:-1])
                authors[index] = curr_name
                index += 1
        return authors, num_authors

    def get_issue_time(self, soup):
        month, year = "-1", "-1"

        for tag in soup.find_all(TAG_DIV, class_=CLASS_COVER_IMAGE_DATE):
            time_string = str(tag.contents[0].contents[0])
            month = time_string.split(" ")[0]
            year = time_string.split(" ")[1]
        return month, year

    def get_doi(self, paper_div):
        doi = "empty_doi"
        for tag in paper_div.find_all(TAG_UL, class_=CLASS_ITEM_LINKS):
            li_tag = tag.find_all('a', {"title": "Abstract"})[0]
            href_list = li_tag['href'].split("/")[-2:]
            doi = "/".join(href_list)
        return doi

    def get_keywords(self, paper_div):
        return ["" for _ in range(NUM_KEYWORDS)]