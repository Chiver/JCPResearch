from bs4 import BeautifulSoup
import pandas as pd
import os
import pprint


PAPER_TITLE_CLASS = "issue-item__title visitable"


def main():
    pass


if __name__ == '__main__':
    string = '<h3 id="heading-level-1-1" class="toc__heading section__header to-section" title="Issue Information" tabindex="0">Issue Information</h3>'
    soup = BeautifulSoup(string, "html.parser")
    for child in soup.children:
        print(child.contents[0])
    print("JCP Finished")


