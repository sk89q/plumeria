import re


def escape_markdown(s):
    return MARKDOWN_ESCAPE_PATTERN.sub("\\\\\\1", s)


MARKDOWN_ESCAPE_PATTERN = re.compile("([\\*_`\\{\\}\\[\\]\\-~])")
