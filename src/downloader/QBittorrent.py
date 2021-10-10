import logging
import requests
from retry import retry
from downloader.Downloader import Downloader

logger = logging.getLogger(__name__)

class QBittorrent(Downloader):
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.cookie = self.__get_cookie()

    @retry((Exception), tries=5, delay=1)
    def __get_cookie(self) -> dict[str, str]:
        req = requests.get(self.base_url)
        cookie = {c.name: c.value for c in req.cookies}
        logger.info(f"Retrieved cookie: {cookie}")
        return cookie

    @retry((Exception), tries=5, delay=1)
    def download(self, link: str) -> None:
        payload = {'urls': link}
        req = requests.post(f'{self.base_url}/api/v2/torrents/add', cookies=self.cookie, data=payload)
        if (req.text == 'Ok.'):
            logger.info(f"Success add download job for link: {link}")
        else:
            message = f"Failed to add download job for link: {link}"
            logger.warning(message)
            raise RuntimeError(message)
