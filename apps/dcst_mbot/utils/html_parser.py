# dcst_mbot/utils/html_parser.py
from html.parser import HTMLParser
from configs.logging_setup import log


class SimpleHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parsed = []

    def handle_data(self, data):
        self._parsed.append(data)

    def get_text(self) -> str:
        return "".join(self._parsed)


def parse_html_content(html_content: str) -> str:
    parser = SimpleHTMLParser()
    try:
        parser.feed(html_content)
        return parser.get_text()
    except Exception:
        log.exception("[HTML] Failed parsing")
        return html_content
