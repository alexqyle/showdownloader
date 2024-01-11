import argparse
import logging
import pathlib
import random
import time
import traceback
import yaml
from app.ShowDownloaderConfig import ShowDownloaderConfig

def __parse_args():
    parser = argparse.ArgumentParser(description='Show Downloader')
    parser.add_argument('--log', dest='log_level', type=str, nargs='?', default='INFO', help='Log level')
    parser.add_argument('--config', dest='config_file', type=pathlib.Path, required=True, help='Config file to be used')
    parser.add_argument('--tracker', dest='tracker_file', type=pathlib.Path, required=True, help='File to keep track of episodes')
    return parser.parse_args()

def main():
    args = __parse_args()
    logging.root.setLevel(args.log_level)
    logger = logging.getLogger(__name__)

    with args.tracker_file.open('r', encoding='utf-8') as tracker_file:
        tracker = yaml.safe_load(tracker_file)
    with args.config_file.open('r', encoding='utf-8') as config_file:
        config = ShowDownloaderConfig(config_file, tracker)
    now = int(time.time())
    scan_count = 0
    for download_job in config.download_jobs:
        if scan_count >= config.max_scan_count:
            logger.info(f"Reach max scan count: {scan_count}. Exit now.")
            break
        if download_job.next_check_time > now:
            logger.info(f"Skip show '{download_job.name}' due to next check time '{download_job.next_check_time}' not reached")
        else:
            scan_count = scan_count + 1
            show_info = f"show '{download_job.name}' with search string '{download_job.search_string}' for episode '{download_job.episode}'"
            try:
                try:
                    link = download_job.site.get_download_link(download_job.search_string, download_job.episode_search_string, download_job.episode)
                except Exception as error:
                    logger.error(f"Unable to get download link for show: '{download_job.name}'. Error: {error}")
                    traceback.print_exc()
                    raise error
                if link:
                    download_job.downloader.download(link)
                    logger.info(f"Success create download job for show: '{download_job.name}'")
                    download_job.episode = download_job.episode + 1
                else:
                    logger.warning(f"There is no search result for {show_info}")
                if download_job.name not in tracker:
                    tracker[download_job.name] = {}
                tracker[download_job.name]['episode'] = download_job.episode
                tracker[download_job.name]['next_check_time'] = now + config.check_interval_second + int(random.random() * config.check_jitter_second - (config.check_jitter_second / 2))
            except Exception as error:
                logger.error(f"Unable to download {show_info}. Error: {error}")
                traceback.print_exc()
                continue
    with args.tracker_file.open('w', encoding='utf-8') as tracker_file:
        yaml.safe_dump(tracker, tracker_file, encoding='utf-8', allow_unicode=True, line_break="\n")
    with args.tracker_file.open('r', encoding='utf-8') as tracker_file:
        logger.info(f"Show tracker info:\n{tracker_file.read()}")

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(module)s.%(funcName)s:%(lineno)d] [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )
    main()