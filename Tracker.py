from proxy import Proxy

import controller


class Tracker:
    def __init__(self, upload_rate=10000, download_rate=10000, port=None):
        self.proxy = Proxy(upload_rate, download_rate, port)
        self.trackerController = controller.TrackerController(self.proxy)

    def start(self):
        pass


if __name__ == '__main__':
    tracker = Tracker(port=10086)
    tracker.start()
