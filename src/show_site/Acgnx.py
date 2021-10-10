import logging
import re
import requests
import time
from pyquery import PyQuery
from retry import retry
from show_site.ShowSite import ShowSite

logger = logging.getLogger(__name__)

default_headers: dict[str, str] = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36'
}

class Acgnx(ShowSite):
    def __init__(self, search_delay_second: int):
        super().__init__()
        self.search_url = 'https://share.acgnx.se/search.php'
        self.search_delay_second = search_delay_second
        self.cookie = self.__get_cookie()

    @retry((Exception), tries=5, delay=1)
    def __get_cookie(self) -> dict[str, str]:
        req = requests.get(self.search_url, headers=default_headers, params={'keyword': 'dummy'})
        html = req.text
        split_key_match = re.search(r'\.split\(\'(.+)\'\)', html)
        split_key = split_key_match.group(1)
        content_match = re.search(f"\'({split_key}.+?)\'\.split", html)
        content = content_match.group(1).split(split_key)
        cookie = dict()
        cookie[content[36]] = content[29]
        logger.info(f"Retrieved cookie: {cookie}")
        return cookie
        
    @retry((Exception), tries=3)
    def get_download_link(self, search_string: str, episode: int = None) -> str:
        real_search_string = search_string.format(episode=episode) if episode else search_string
        logger.info(f"Real search string: '{real_search_string}'")
        payload = {'keyword': real_search_string}
        logger.info(f"Delay searching for {self.search_delay_second} seconds")
        time.sleep(self.search_delay_second)
        req = requests.get(self.search_url, headers=default_headers, cookies=self.cookie, params=payload)
        html = req.text
        pq = PyQuery(html)
        link = pq('table#listTable a#magnet').eq(0).attr('href')
        if link:
            logger.info(f"Success get download link for '{real_search_string}': {link}")
        else:
            message = f"Unable to get download link with search string: '{real_search_string}'"
            logger.warning(message)
            no_result_text = pq('table#listTable tbody#data_list tr.text_center td').eq(0).text()
            if not no_result_text:
                raise RuntimeError(message)
        return link
