import hashlib
import random
import re
import time
from urllib.parse import quote

import requests


class XybSession:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Referer": "https://servicewechat.com/wx9f1c2e0bbc10673c/269/page-frame.html",
        })

    def post(self, url, data):
        if data is None:
            data = {}
        return self.session.post(url, data=data, headers=self.get_sign_header(data))

    def get(self, url):
        return self.session.get(url, headers=self.get_sign_header({}))

    def set_session(self, value):
        self.session.cookies.set("JSESSIONID", value)

    @staticmethod
    def get_sign_header(data: dict):
        re_punctuation = re.compile("[`~!@#$%^&*()+=|{}':;,\\[\\].<>/?！￥…（）—【】‘；：”“’。，、？]")
        cookbook = ["5", "b", "f", "A", "J", "Q", "g", "a", "l", "p", "s", "q", "H", "4", "L", "Q", "g", "1", "6",
                    "Q",
                    "Z", "v", "w", "b", "c", "e", "2", "2", "m", "l", "E", "g", "G", "H", "I", "r", "o", "s", "d",
                    "5",
                    "7", "x", "t", "J", "S", "T", "F", "v", "w", "4", "8", "9", "0", "K", "E", "3", "4", "0", "m",
                    "r",
                    "i", "n"]
        except_key = ["content", "deviceName", "keyWord", "blogBody", "blogTitle", "getType", "responsibilities",
                      "street", "text", "reason", "searchvalue", "key", "answers", "leaveReason", "personRemark",
                      "selfAppraisal", "imgUrl", "wxname", "deviceId", "avatarTempPath", "file", "file", "model",
                      "brand", "system", "deviceId", "platform", "code", "openId", "unionid"]

        noce = [random.randint(0, len(cookbook) - 1) for _ in range(20)]
        now_time = int(time.time())
        sorted_data = dict(sorted(data.items(), key=lambda x: x[0]))

        sign_str = ""
        for k, v in sorted_data.items():
            v = str(v)
            if k not in except_key and not re.search(re_punctuation, v):
                sign_str += str(v)
        sign_str += str(now_time)
        sign_str += "".join([cookbook[i] for i in noce])
        sign_str = re.sub(r'\s+', "", sign_str)
        sign_str = re.sub(r'\n+', "", sign_str)
        sign_str = re.sub(r'\r+', "", sign_str)
        sign_str = sign_str.replace("<", "")
        sign_str = sign_str.replace(">", "")
        sign_str = sign_str.replace("&", "")
        sign_str = sign_str.replace("-", "")
        sign_str = re.sub(f'\uD83C[\uDF00-\uDFFF]|\uD83D[\uDC00-\uDE4F]', "", sign_str)
        sign_str = quote(sign_str)
        sign = hashlib.md5(sign_str.encode('ascii'))

        return {
            "n": ",".join(except_key),
            "t": str(now_time),
            "s": "_".join([str(i) for i in noce]),
            "m": sign.hexdigest(),
            "v": "1.7.53"
        }