import logging
import re
import requests
import time
from pyquery import PyQuery
from retry import retry
from show_site.ShowSite import ShowSite
from DrissionPage import WebPage
from DrissionPage import ChromiumOptions

logger = logging.getLogger(__name__)

class Acgnx(ShowSite):
    def __init__(self, search_delay_second: int, user_agent: str, captcha_selector: str):
        super().__init__()
        self.search_url = 'https://share.acgnx.se/search.php'
        self.search_delay_second = search_delay_second
        self.default_headers: dict[str, str] = {
            'user-agent': user_agent
        }
        self.user_agent = user_agent
        self.captcha_selector = captcha_selector

    @retry((Exception), tries=2, delay=1)
    def __get_cf_cookie(self) -> dict[str, str]:
        co = ChromiumOptions()
        # co.set_argument('--headless')
        co.set_argument('--no-sandbox')
        co.set_argument('--user-agent', self.user_agent)
        page = WebPage(chromium_options=co)
        page.get(self.search_url)

        if not self.__is_cf_bypassed(page, 5): 
            wrapper = page.ele(".cf-turnstile-wrapper")
            shadow_root = wrapper.shadow_root
            iframe = shadow_root.ele("tag=iframe", timeout=15)
            iframe_body = iframe.ele('tag:body', timeout=15).shadow_root
            ele = iframe_body.ele(self.captcha_selector, timeout=15)
            ele.click(timeout=10, by_js=None)
            logger.info('clicked cloudflare verify button')
        
        if not self.__is_cf_bypassed(page, 10):
            raise RuntimeError('unable to bypass cloudflare')

        for cookie in page.cookies():
            if cookie['name'] == 'cf_clearance':
                cf_clearance_cookie = cookie['value']
                break

        page.quit()
        return {
            'cf_clearance': cf_clearance_cookie
        }
    
    def __is_cf_bypassed(self, page: WebPage, retries: int) -> bool:
        bypassed = False
        for _ in range(retries):
            logger.debug(page.html)
            if 'Project AcgnX' in page.title:
                bypassed = True
                break
            time.sleep(1)
        return bypassed
    
    @retry((Exception), tries=2, delay=1)
    def __get_cookie(self) -> dict[str, str]:
        cookie = dict()
        cookie.update(self.__get_cf_cookie())
        logger.debug(f"Default cookie: {cookie}")
        req = requests.get(self.search_url, headers=self.default_headers, cookies=cookie, params={'keyword': 'dummy'})
        html = req.text
        logger.debug(html)
        cookie, _ = self.__update_cookie(cookie, html)
        return cookie
    
    def __update_cookie(self, cookie: dict[str, str], html: str) -> (dict[str, str], bool):
        split_key_match = re.search(r'\.split\(\'(.+?)\'\)', html)
        if split_key_match is None:
            return cookie, False
        split_key = split_key_match.group(1)
        logger.debug(split_key)
        content_match = re.search(f"\'({split_key}.+?)\'\.split", html)
        content = content_match.group(1).split(split_key)
        logger.debug(content)
        updated_cookie = dict()
        updated_cookie.update(cookie)
        updated_cookie[content[36]] = content[29]
        logger.debug(f"Retrieved cookie: {updated_cookie}")
        return updated_cookie, True
        
    @retry((RuntimeError), tries=2)
    def get_download_link(self, search_string: str, episode_search_string: str, episode: int) -> str:
        cookie = self.__get_cookie()
        logger.info(f"Cookies: {cookie}")
        logger.info(f"Search string: '{search_string}'")
        payload = {'keyword': search_string}
        logger.info(f"Delay searching for {self.search_delay_second} seconds")
        time.sleep(self.search_delay_second)
        pq, html = self.__send_search_request(self.default_headers, cookie, payload)
        logger.debug(html)
        html_title = pq('title').eq(0).text()
        if search_string not in html_title:
            message = f"unable to search for '{search_string}'"
            logger.error(message)
            raise RuntimeError(message)
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

    def __send_search_request(self, headers, cookies, payload) -> (PyQuery, str):
        try:
            req = requests.get(self.search_url, headers=headers, cookies=cookies, params=payload)
            html = req.text
            return PyQuery(html), html
        except Exception as error:
            raise RuntimeError(error)
