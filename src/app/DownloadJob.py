import logging
from downloader.Downloader import Downloader
from show_site.ShowSite import ShowSite

logger = logging.getLogger(__name__)

class DownloadJob(object):
    def __init__(self, name: str, site: ShowSite, downloader: Downloader, search_string: str, episode: int):
        self.name = name
        self.site = site
        self.downloader = downloader
        self.search_string = search_string
        self.episode = episode
