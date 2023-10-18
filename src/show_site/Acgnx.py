import logging
import re
import requests
import time
from pyquery import PyQuery
from retry import retry
from show_site.ShowSite import ShowSite

logger = logging.getLogger(__name__)

default_headers: dict[str, str] = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
}

class Acgnx(ShowSite):
    def __init__(self, search_delay_second, cf_clearance_cookie: int):
        super().__init__()
        self.search_url = 'https://share.acgnx.se/search.php'
        self.search_delay_second = search_delay_second
        self.cf_clearance_cookie = cf_clearance_cookie
        self.default_cookie: dict[str, str] = {
            'cf_clearance': self.cf_clearance_cookie
        }
        self.cookie = self.__get_cookie()

    @retry((Exception), tries=5, delay=1)
    def __get_cookie(self) -> dict[str, str]:
        cookie = dict()
        cookie.update(self.default_cookie)
        logger.info(f"Default cookie: {cookie}")
        req = requests.get(self.search_url, headers=default_headers, cookies=cookie, params={'keyword': 'dummy'})
        html = req.text
        logger.info(html)
        cookie, _ = self.__update_cookie(cookie, html)
        return cookie
    
    def __update_cookie(self, cookie: dict[str, str], html: str) -> (dict[str, str], bool):
        split_key_match = re.search(r'\.split\(\'(.+?)\'\)', html)
        if split_key_match is None:
            return cookie, False
        split_key = split_key_match.group(1)
        logger.info(split_key)
        content_match = re.search(f"\'({split_key}.+?)\'\.split", html)
        content = content_match.group(1).split(split_key)
        logger.info(content)
        updated_cookie = dict()
        updated_cookie.update(cookie)
        updated_cookie[content[36]] = content[29]
        logger.info(f"Retrieved cookie: {updated_cookie}")
        return updated_cookie, True
        
    @retry((RuntimeError), tries=3)
    def get_download_link(self, search_string: str, episode_search_string: str, episode: int) -> str:
        logger.info(f"Search string: '{search_string}'")
        payload = {'keyword': search_string}
        logger.info(f"Delay searching for {self.search_delay_second} seconds")
        time.sleep(self.search_delay_second / 2)
        pq, html = self.__send_search_request(default_headers, self.cookie, payload)
        logger.debug(html)
        self.cookie, updated = self.__update_cookie(self.cookie, html)
        time.sleep(self.search_delay_second / 2)
        if updated:
            pq, html = self.__send_search_request(default_headers, self.cookie, payload)
            logger.debug(html)
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
