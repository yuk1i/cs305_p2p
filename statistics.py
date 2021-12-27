import json
import queue
import threading
from typing import List, Dict, Set, Tuple
from wsgiref.simple_server import make_server
from wsgiref.util import application_uri, request_uri


class PeerInfo:
    def __init__(self, port: int):
        self.peer_port = port
        self.total_chunks = 0

        # speeds
        self.upload = ""
        self.download = ""
        self.speeds: Dict[int, Tuple[str, str]] = dict()

        # to diff
        self.now_inited = False
        self.new_chunk_from = dict()
        self.status = "Not Started"
        self.status_updated = False


EV_EXIT = 1
EV_NEW_PEER = 2
EV_PEER_TORRENT_DOWNLOADED = 3
EV_NEW_CHUNK = 4
EV_NEW_CHUNKS = 5
EV_PEER_STATUS_CHANGED = 6


class Statistics:

    def __init__(self):
        self.peer_list: Dict[int, PeerInfo] = dict()
        self.lock = threading.Lock()
        self.queue = queue.SimpleQueue()
        self.thread = threading.Thread(target=self.__run__)
        self.http_thread = threading.Thread(target=self.run_http)
        self.http_thread.daemon = True

        # diff
        self.new_peers: List[int] = list()
        self.first_request = True

        self.thread.daemon = True

    def run_http(self):
        self.httpd.serve_forever()

    def start(self):
        if self.thread.is_alive():
            return
        self.httpd = make_server("127.0.0.1", 58080, self.__http_server__)
        self.http_thread.start()
        self.thread.start()
        input("Statistics On, visit http://localhost:58080/ and press any key to continue.")

    def __run__(self):
        while True:
            ev_type, data = self.queue.get()
            if ev_type == EV_EXIT:
                self.httpd.server_close()
                return
            else:
                with self.lock:
                    if ev_type == EV_NEW_PEER:
                        peer_port = data
                        self.peer_list[peer_port] = PeerInfo(peer_port)
                        self.new_peers.append(peer_port)
                    elif ev_type == EV_PEER_TORRENT_DOWNLOADED:
                        peer_port, total_chunks = data
                        self.peer_list[peer_port].now_inited = True
                        self.peer_list[peer_port].total_chunks = total_chunks
                    elif ev_type == EV_PEER_STATUS_CHANGED:
                        peer_port, status_str = data
                        self.peer_list[peer_port].status = status_str
                        self.peer_list[peer_port].status_updated = True
                    elif ev_type == EV_NEW_CHUNKS:
                        peer_port, chunks = data
                        chunks: Dict[int, int]
                        self.peer_list[peer_port].new_chunk_from.update(chunks)
                    elif ev_type == EV_NEW_CHUNK:
                        peer_port, chunk, src_port = data
                        self.peer_list[peer_port].new_chunk_from[chunk] = src_port

    def __http_server__(self, env, http_stuff):
        if "data" not in request_uri(env, include_query=False):
            print(f"Requesting {request_uri(env, include_query=False)}")
            http_stuff('200 OK', [('Content-type', 'text/html')])
            with open("../statistics_web/index.html", "rb") as f:
                b = f.read()
                return [b]
        with self.lock:
            ret = dict()
            ret["first"] = self.first_request
            if self.first_request:
                self.first_request = False

            ret["new_peer"] = list()
            for p in self.new_peers:
                ret["new_peer"].append(p)
            self.new_peers.clear()

            finish_torrent = dict()
            for p in self.peer_list:
                pinfo = self.peer_list[p]
                if pinfo.now_inited:
                    pinfo.now_inited = False
                    finish_torrent[p] = pinfo.total_chunks
            ret["finish_torrent"] = finish_torrent

            status_changed = dict()
            for p in self.peer_list:
                pinfo = self.peer_list[p]
                if pinfo.status_updated:
                    pinfo.status_updated = False
                    status_changed[p] = pinfo.status
            ret["status"] = status_changed

            chunk_updated = dict()
            for p in self.peer_list:
                pinfo = self.peer_list[p]
                if len(pinfo.new_chunk_from) > 0:
                    chunk_updated[p] = dict()
                    chunk_updated[p].update(pinfo.new_chunk_from)
                    pinfo.new_chunk_from.clear()
            ret["chunk"] = chunk_updated

            speeds = dict()
            for p in self.peer_list:
                pinfo = self.peer_list[p]
                speeds[p] = dict()
                speeds[p]["upload"] = pinfo.upload
                speeds[p]["download"] = pinfo.download
                pd = dict()
                for pp in pinfo.speeds:
                    pd[pp] = dict()
                    pd[pp]["upload"] = pinfo.speeds[pp][0]
                    pd[pp]["download"] = pinfo.speeds[pp][1]
                speeds[p]["peers"] = pd
            ret["speed"] = speeds

            sret = json.dumps(ret, sort_keys=True)

            status = '200 OK'
            headers = [('Content-type', 'application/json')]
            http_stuff(status, headers)
            return [sret.encode(encoding='utf-8')]

    def on_new_client(self, peer_port):
        self.queue.put_nowait((EV_NEW_PEER, peer_port))

    def on_peer_torrent_downloaded(self, peer_port, total_chunks):
        self.queue.put_nowait((EV_PEER_TORRENT_DOWNLOADED, (peer_port, total_chunks)))

    def on_peer_fill_chunk_uploader(self, peer_port, total_chunks):
        src = dict()
        for i in range(1, total_chunks + 1):
            src[i] = 0
        self.queue.put_nowait((EV_NEW_CHUNKS, (peer_port, src)))

    def on_peer_status_changed(self, peer_port, str_status):
        self.queue.put_nowait((EV_PEER_STATUS_CHANGED, (peer_port, str_status)))

    def on_peer_new_chunk(self, peer_port, chunk_seq, src_peer_port):
        self.queue.put_nowait((EV_NEW_CHUNK, (peer_port, chunk_seq, src_peer_port)))

    def update_peer_speed(self, peer_port, speeds: Dict[int, Tuple[str, str]]):
        with self.lock:
            if peer_port not in self.peer_list:
                self.peer_list[peer_port] = PeerInfo(peer_port)
            self.peer_list[peer_port].speeds.update(speeds)

    def update_speed(self, peer_port, up_speed: str, down_speed: str):
        with self.lock:
            if peer_port not in self.peer_list:
                self.peer_list[peer_port] = PeerInfo(peer_port)
            self.peer_list[peer_port].upload = up_speed
            self.peer_list[peer_port].download = down_speed


global_statistics = Statistics()


def get_instance():
    return global_statistics
