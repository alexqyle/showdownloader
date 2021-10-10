from abc import ABC, abstractmethod

class ShowSite(ABC):

    @abstractmethod
    def get_download_link(self, search_string: str, episode: int = None) -> str:
        pass
