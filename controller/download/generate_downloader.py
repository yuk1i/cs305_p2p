from . import RandomDownloadController
from .titfortat_downloader import TitfortatDownloadController

DOWN_ALG_RANDOM = 1
DOWN_ALG_TITFORTAT = 2


def generate_download_controller(itype) -> callable:
    if itype == DOWN_ALG_RANDOM:
        return RandomDownloadController
    elif type == DOWN_ALG_TITFORTAT:
        return TitfortatDownloadController
