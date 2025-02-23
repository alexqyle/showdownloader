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
    def __init__(self, config_file: IO[Any], tracker: dict[str, Any]):
        self.download_jobs: list[DownloadJob] = list()
        self.__parse_config(config_file, tracker)

    def __parse_config(self, config_file: IO[Any], tracker: dict[str, Any]) -> None:
        config = yaml.safe_load(config_file)
        self.max_scan_count = config['max_scan_count']
        self.check_interval_second = config['check_interval_second']
        self.check_jitter_second = config['check_jitter_second']
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
            if name in tracker:
                episode = tracker.get(name).get('episode', 1)
                next_check_time = tracker.get(name).get('next_check_time', 0)
            else:
                episode = 1
                next_check_time = 0
            self.download_jobs.append(DownloadJob(name, site, downloader, search_string, episode_search_string, episode, next_check_time))

    def __get_site(self, site_name: str, site_config) -> ShowSite:
        if (site_name.lower() == 'acgnx'):
            search_delay_second = site_config['acgnx']['search_delay_second']
            user_agent = site_config['acgnx']['user_agent']
            cf_iframe_finder = site_config['acgnx']['cf_iframe_finder']
            cf_iframe_selector = site_config['acgnx']['cf_iframe_selector']
            cf_captcha_finder = site_config['acgnx']['cf_captcha_finder']
            cf_captcha_selector = site_config['acgnx']['cf_captcha_selector']
            google_iframe_selector = site_config['acgnx']['google_iframe_selector']
            google_captcha_selector = site_config['acgnx']['google_captcha_selector']
            return Acgnx(search_delay_second, user_agent, cf_iframe_finder, cf_iframe_selector, cf_captcha_finder, cf_captcha_selector, google_iframe_selector, google_captcha_selector)
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
