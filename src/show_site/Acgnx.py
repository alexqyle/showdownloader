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
        logger.info(html)
        split_key_match = re.search(r'\.split\(\'(.+?)\'\)', html)
        split_key = split_key_match.group(1)
        logger.info(split_key)
        content_match = re.search(f"\'({split_key}.+?)\'\.split", html)
        content = content_match.group(1).split(split_key)
        cookie = dict()
        cookie[content[36]] = content[29]
        logger.info(f"Retrieved cookie: {cookie}")
        return cookie
        
    @retry((RuntimeError), tries=3)
    def get_download_link(self, search_string: str, episode_search_string: str, episode: int) -> str:
        logger.info(f"Search string: '{search_string}'")
        payload = {'keyword': search_string}
        logger.info(f"Delay searching for {self.search_delay_second} seconds")
        time.sleep(self.search_delay_second)
        pq, html = self.__send_search_request(default_headers, self.cookie, payload)
        is_require_cookie = pq('body').eq(0).attr('onload')
        if is_require_cookie:
            logger.warning(f"Getting new cookie")
            self.cookie = self.__get_cookie()
            time.sleep(self.search_delay_second)
            pq, html = self.__send_search_request(default_headers, self.cookie, payload)
        if pq('div#recaptcha-widget').length:
            message = f"ReCaptcha needed for '{search_string}'"
            logger.error(message)
            raise RuntimeWarning(message)
        return self.__get_download_link(pq, episode_search_string.format(episode=episode))

    def __get_download_link(self, pq: PyQuery, episode_search_string: str) -> str:
        logger.info(f"Episode search string: '{episode_search_string}'")
        no_result_text = pq('table#listTable tbody#data_list tr.text_center td').eq(0).text()
        if no_result_text:
            return None
        for item in pq('table#listTable tr').items():
            item_title = item.find('td').eq(2).find('a').eq(0).text()
            logger.info(f"Check: {item_title}")
            if re.search(episode_search_string, item_title):
                link = item.find('a#magnet').eq(0).attr('href')
                logger.info(f"Success get download link for '{episode_search_string}': {link}")
                return link
        return None

    def __send_search_request(self, headers, cookies, payload) -> tuple[PyQuery, str]:
        try:
            req = requests.get(self.search_url, headers=headers, cookies=cookies, params=payload)
            html = req.text
            return PyQuery(html), html
        except Exception as error:
            raise RuntimeError(error)
