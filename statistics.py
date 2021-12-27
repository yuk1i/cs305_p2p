import json
import queue
import threading
from typing import List, Dict, Set, Tuple
from wsgiref.simple_server import make_server
from wsgiref.util import application_uri, request_uri

import controller


class PeerInfo:
    def __init__(self, port: int):
        self.peer_port = port
        self.total_chunks = 0

        # to diff
        self.now_inited = False
        self.new_chunk_from = dict()
        self.status = "Not Started"
        self.status_updated = False

        self.peer_status: Dict[int, str] = dict()


def get_speed_str(speed):
    return "{:.2f}".format(speed / 1024)


class Statistics:

    def __init__(self):
        self.peer_list: Dict[int, PeerInfo] = dict()
        self.peer_ctrls: Dict[int, controller.PeerController] = dict()
        self.lock = threading.Lock()
        self.http_thread = threading.Thread(target=self.run_http)
        self.http_thread.daemon = True

        # diff
        self.new_peers: List[int] = list()
        self.first_request = True

    def run_http(self):
        self.httpd.serve_forever()

    def start(self):
        if self.http_thread.is_alive():
            return
        self.httpd = make_server("127.0.0.1", 58080, self.__http_server__)
        self.http_thread.start()
        input("Statistics On, visit http://localhost:58080/ and press any key to continue.")

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
                pc = self.peer_ctrls[p]
                speeds[p] = dict()
                speeds[p]["upload"] = get_speed_str(pc.socket.traffic_monitor.get_uplink_rate())
                speeds[p]["download"] = get_speed_str(pc.socket.traffic_monitor.get_downlink_rate())
                pd = dict()
                for pp in pc.peer_conns:
                    ppc = pc.peer_conns[pp]
                    pp_port = pp[1]
                    pd[pp_port] = dict()
                    pd[pp_port]["upload"] = get_speed_str(ppc.traffic_monitor.get_uplink_rate())
                    pd[pp_port]["download"] = get_speed_str(ppc.traffic_monitor.get_downlink_rate())
                    if pp_port not in pinfo.peer_status:
                        pinfo.peer_status[pp_port] = "N"
                    pd[pp_port]["status"] = pinfo.peer_status[pp_port]
                speeds[p]["peers"] = pd
            ret["speed"] = speeds

            sret = json.dumps(ret, sort_keys=True)

            status = '200 OK'
            headers = [('Content-type', 'application/json')]
            http_stuff(status, headers)
            return [sret.encode(encoding='utf-8')]

    def on_new_client(self, peer_port, peer_ctrl):
        with self.lock:
            self.peer_list[peer_port] = PeerInfo(peer_port)
            self.peer_ctrls[peer_port] = peer_ctrl
            self.new_peers.append(peer_port)

    def on_peer_torrent_downloaded(self, peer_port, total_chunks):
        with self.lock:
            self.peer_list[peer_port].now_inited = True
            self.peer_list[peer_port].total_chunks = total_chunks

    def on_peer_fill_chunk_uploader(self, peer_port, total_chunks):
        src = dict()
        for i in range(1, total_chunks + 1):
            src[i] = 0
        with self.lock:
            self.peer_list[peer_port].new_chunk_from.update(src)

    def on_peer_status_changed(self, peer_port, str_status):
        with self.lock:
            self.peer_list[peer_port].status = str_status
            self.peer_list[peer_port].status_updated = True

    def on_peer_new_chunk(self, peer_port, chunk_seq, src_peer_port):
        with self.lock:
            self.peer_list[peer_port].new_chunk_from[chunk_seq] = src_peer_port

    def set_peer_status(self, peer_port, target_peer_port, str_status):
        with self.lock:
            self.peer_list[peer_port].peer_status[target_peer_port] = str_status


global_statistics = Statistics()


def get_instance():
    return global_statistics
