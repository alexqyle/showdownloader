import logging
import yaml
from typing import IO, Any
from app.DownloadJob import DownloadJob
from downloader.Downloader import Downloader
from downloader.QBittorrent import QBittorrent
from show_site.Acgnx import Acgnx
from show_site.ShowSite import ShowSite

logger = logging.getLogger(__name__)

class ShowDownloaderConfig(object):
    def __init__(self, config_file: IO[Any], tracker: dict[str, int]):
        self.download_jobs: list[DownloadJob] = list()
        self.__parse_config(config_file, tracker)

    def __parse_config(self, config_file: IO[Any], tracker: dict[str, int]) -> None:
        config = yaml.safe_load(config_file)
        site_dict: dict[str, ShowSite] = dict()
        site_config = config['show_site_config']
        downloader_dict: dict[str, Downloader] = dict()
        downloader_config = config['downloader_config']
        for job_yaml in config['download_jobs']:
            name = job_yaml['name']
            site_name = job_yaml['site']
            downloader_name = job_yaml['downloader']
            search_string = job_yaml['search_string']
            episode_search_string = job_yaml['episode_search_string']
            if site_name in site_dict:
                site = site_dict[site_name]
            else:
                site = self.__get_site(site_name, site_config)
                site_dict[site_name] = site
            if downloader_name in downloader_dict:
                downloader = downloader_dict[downloader_name]
            else:
                downloader = self.__get_downloader(downloader_name, downloader_config)
                downloader_dict[downloader_name] = downloader
            episode = tracker.get(name, 1)
            self.download_jobs.append(DownloadJob(name, site, downloader, search_string, episode_search_string, episode))

    def __get_site(self, site_name: str, site_config) -> ShowSite:
        if (site_name.lower() == 'acgnx'):
            search_delay_second = site_config['acgnx']['search_delay_second']
            return Acgnx(search_delay_second)
        else:
            message = f"Unknown site: {site_name}"
            raise RuntimeError(message)

    def __get_downloader(self, downloader_name: str, downloader_config) -> Downloader:
        if (downloader_name.lower() == 'qbittorrent'):
            base_url = downloader_config['qbittorrent']['base_url']
            return QBittorrent(base_url)
        else:
            message = f"Unknown downloader: {downloader_name}"
            raise RuntimeError(message)
