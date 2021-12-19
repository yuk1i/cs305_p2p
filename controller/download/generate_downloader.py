from . import RandomDownloadController

DOWN_ALG_RANDOM = 1


def generate_download_controller(itype) -> callable:
    if itype == DOWN_ALG_RANDOM:
        return RandomDownloadController
