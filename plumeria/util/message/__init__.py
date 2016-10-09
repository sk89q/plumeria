import re

from bs4 import BeautifulSoup

MARKDOWN_CODE_BLOCK = re.compile("```(.*?)```", re.S)


def strip_markdown_code(s):
    m = MARKDOWN_CODE_BLOCK.search(s)
    if m:
        return m.group(1)
    return s


def strip_html(s):
    return BeautifulSoup(s, "html.parser").get_text()
