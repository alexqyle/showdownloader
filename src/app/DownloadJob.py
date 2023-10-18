import logging
from downloader.Downloader import Downloader
from show_site.ShowSite import ShowSite

logger = logging.getLogger(__name__)

class DownloadJob(object):
    def __init__(self, 
                 name: str, 
                 site: ShowSite, 
                 downloader: Downloader, 
                 search_string: str, 
                 episode_search_string: str, 
                 episode: int,
                 next_check_time: int):
        self.name = name
        self.site = site
        self.downloader = downloader
        self.search_string = search_string
        self.episode_search_string = episode_search_string
        self.episode = episode
        self.next_check_time = next_check_time
