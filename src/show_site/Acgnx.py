import logging
import re
import requests
from pyquery import PyQuery
from retry import retry
from show_site.ShowSite import ShowSite

logger = logging.getLogger(__name__)

class Acgnx(ShowSite):
    def __init__(self):
        super().__init__()
        self.search_url = 'https://share.acgnx.se/search.php'
        self.cookie = self.__get_cookie()

    @retry((Exception), tries=5, delay=1)
    def __get_cookie(self) -> dict[str, str]:
        req = requests.get(self.search_url, params={'keyword': 'dummy'})
        html = req.text
        split_key_match = re.search(r'\.split\(\'(.+)\'\)', html)
        split_key = split_key_match.group(1)
        content_match = re.search(f"\'({split_key}.+?)\'\.split", html)
        content = content_match.group(1).split(split_key)
        cookie = dict()
        cookie[content[36]] = content[29]
        logger.info(f"Retrieved cookie: {cookie}")
        return cookie
        
    @retry((Exception), tries=5, delay=1)
    def get_download_link(self, search_string: str, episode: int = None) -> str:
        real_search_string = search_string.format(episode=episode) if episode else search_string
        payload = {'keyword': real_search_string}
        req = requests.get(self.search_url, cookies=self.cookie, params=payload)
        pq = PyQuery(req.text)
        link = pq('table#listTable a#magnet').eq(0).attr('href')
        logger.info(f"Success get download link for '{search_string}': {link}")
        return link
