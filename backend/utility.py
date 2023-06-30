#! /usr/bin/env python3
# -*- coding: UTF-8 -*-
import json
import logging
import re
import time
import threading
import requests

from flask import Response

from config import Config

g_logger = logging.getLogger(__name__)


def init_log():
    ch = logging.StreamHandler()
    ch.setLevel(Config.LOG_LEVEL)
    formatter = logging.Formatter('%(asctime)s [%(thread)d] %(levelname)s %(name)s - %(message)s')
    ch.setFormatter(formatter)
    g_logger.setLevel(Config.LOG_LEVEL)
    g_logger.addHandler(ch)


init_log()


class Const:
    SUCCESS = "success"
    MISSING = "parameter missing"
    BAD_REQ = 'bad request'
    BAD_GRA = "illegal grade"
    BAD_JSON = "illegal json"
    BAD_URL = "illegal url"
    DOWNLOAD_ERR = "download error"
    INTERNAL_ERR = 'internal error'
    ALI_ASR_ERR = 'ali asr error'
    NOT_VIDEO = 'file is not a video'
    FILE_TOO_BIG = 'file too big'


err_code = {
    Const.SUCCESS: (20000, 200),
    Const.MISSING: (3003074000, 400),
    Const.BAD_REQ: (3003074001, 400),
    Const.BAD_URL: (3003074002, 400),
    Const.BAD_GRA: (3003074003, 400),
    Const.BAD_JSON: (3003074005, 400),
    Const.DOWNLOAD_ERR: (3003074010, 400),
    Const.NOT_VIDEO: (3003074020, 400),
    Const.FILE_TOO_BIG: (3003074021, 400),
    Const.INTERNAL_ERR: (3003075000, 500),
    Const.ALI_ASR_ERR: (3003075001, 500),
}


def make_response(msg, req_id):
    return Response(json.dumps({"msg": msg, "data": {"requestId": req_id}, "code": err_code[msg][0],
                                "requestId": req_id}, ensure_ascii=False),
                    status=err_code[msg][1], content_type='application/json')


def type_dict(x):
    if isinstance(x, dict):
        return x
    return json.loads(x)


ip_pattern = re.compile(
    r'^(?:(?:1[0-9][0-9]\.)|(?:2[0-4][0-9]\.)|(?:25[0-5]\.)|(?:[1-9][0-9]\.)|(?:[0-9]\.)){3}'
    r'(?:(?:1[0-9][0-9])|(?:2[0-4][0-9])|(?:25[0-5])|(?:[1-9][0-9])|(?:[0-9]))$')
url_pattern = re.compile(
    r'^(https?)://[\w\-]+(\.[\w\-]+)+([\w\-.,@?^=%&:/~+#]*[\w\-@?^=%&/~+#])?$'
)


def type_url(x):
    if not (ip_pattern.match(x) or url_pattern.match(x)):
        raise ValueError("wrong url")
    return x


class EvaEx(Exception):
    def __init__(self, msg):
        self.msg = msg


class ReadLock:
    def __init__(self, size):
        self.size = size
        self.count = 0
        self.mutex = threading.Lock()
        self.not_full = threading.Condition(self.mutex)
        self.not_empty = threading.Condition(self.mutex)

    def acquire(self):
        with self.not_full:
            while self.count >= self.size:
                self.not_full.wait()
            self.count += 1
            self.not_empty.notify()

    def release(self):
        with self.not_empty:
            while self.count <= 0:
                self.not_empty.wait()
            self.count -= 1
            self.not_full.notify()


def get_internal_url(src_url, req_id):
    # 外网url转内网url
    if not Config.DATA_CHANGE_URL:
        return src_url
    d = {
        "urls": [src_url],
        "requestId": req_id,
        "sendTime": int(round(time.time() * 1000))
    }
    try:
        ret = requests.post(Config.DATA_CHANGE_URL, json=d)
        g_logger.debug("receive internal url:{}".format(ret.text))
        ret_json = ret.json()
        if ret_json['code'] == 2000000:
            dst_url = ret_json['resultBean'][0]['innerUrl']
        else:
            dst_url = src_url
    except Exception as e:
        g_logger.error("{} - error in change url:{}".format(req_id, e))
        dst_url = src_url
    return dst_url


def try_post_json(url, js, idx=None) -> str or None:
    for _ in range(3):
        try:
            ret = requests.post(url, json=js, timeout=10).text
            return ret
        except Exception as e:
            g_logger.error("{} - post json error: {}, {}".format(idx, url, e))
    return None


def http_download(url, file_path, uid=""):
    for _ in range(3):
        try:
            req = requests.get(url, stream=True, timeout=10)
            f = open(file_path, 'wb')
            for chunk in req.iter_content(chunk_size=65535):
                f.write(chunk)
                f.flush()
            f.close()
            return
        except Exception as e:
            g_logger.error("{} - download error: {}".format(uid, e))
    raise EvaEx(Const.DOWNLOAD_ERR)


def make_callback(msg, req_id, data=None):
    return {"msg": msg, "data": data, "code": err_code[msg][0], "requestId": req_id}

