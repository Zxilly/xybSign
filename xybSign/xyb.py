import hashlib
import logging
from enum import Enum, auto

from xybSign.session import XybSession
from xybSign.utils import get_beijing_time


class XybSigner:
    class __SignType(Enum):
        SIGN_IN = auto()
        SIGN_OUT = auto()

    def __init__(self, phoneNum: str, password: str, adcode: str):
        self.train_type = None
        self.sign_lng = None
        self.sign_lat = None
        self.sign_address = None
        self.is_sign_out = None
        self.is_sign_in = None
        self.post_state = None
        self.train_id = None
        self.ip = None
        self.session_id = None
        self.loginer_id = None

        self.phoneNum = phoneNum
        self.password = password
        self.adcode = adcode

        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
        self.logger = logging.getLogger("xybSign")

        self.session = XybSession()

        self.__init_user_info()
        self.__init_ip_info()
        self.__init_train_info()

    def __init_user_info(self):
        login_data = dict(
            username=self.phoneNum,
            password=hashlib.md5(self.password.encode()).hexdigest(),
            openId="ooru94rWRmf_5CKxp21bzRxXw5ct",
            unionId="oHY-uwUmPNik8tNCSroR4Aiq4WBj",
            model="M2102J2CS",
            brand="Xiaomi",
            platform="android",
            system="Android 12",
            deviceId="",
        )

        resp = self.session.post("https://xcx.xybsyw.com/login/login.action", login_data)
        resp.raise_for_status()
        resp_json = resp.json()
        if resp_json["code"] == "200":
            self.loginer_id = resp_json["data"]["loginerId"]
            self.session_id = resp_json["data"]["sessionId"]

            self.session.set_session(self.session_id)
            logging.info(f"已登录：{self.loginer_id}")
        else:
            raise Exception(f"登录失败：{resp_json['msg']}")

    def __init_ip_info(self):
        resp = self.session.get("https://xcx.xybsyw.com/behavior/Duration!getIp.action")
        resp.raise_for_status()
        data = resp.json()
        if data["code"] == "200":
            self.ip = data["data"]["ip"]

    def __init_train_info(self):
        resp = self.session.get("https://xcx.xybsyw.com/student/clock/GetPlan!getDefault.action")
        resp.raise_for_status()
        resp_json = resp.json()
        if resp_json["code"] == "200":
            if "clockVo" in resp_json["data"]:
                self.train_id = resp_json["data"]["clockVo"]["traineeId"]
                self.logger.info(
                    f"已载入默认实习：{resp_json['data']['clockVo']['planName']}({resp_json['data']['clockVo']['startDate']} - {resp_json['data']['clockVo']['endDate']})")
            else:
                raise Exception("未找到默认实习")
        else:
            raise Exception(f"获取默认实习失败：{resp_json['msg']}")

        post_data = dict(traineeId=self.train_id)
        resp = self.session.post("https://xcx.xybsyw.com/student/clock/GetPlan!detail.action", data=post_data)
        resp.raise_for_status()
        resp_json = resp.json()
        if resp_json["code"] == "200":
            self.train_type = resp_json["data"]["clockRuleType"]
            if not self.train_type:
                raise Exception("集中实习不支持")

            self.post_state = resp_json["data"]["postInfo"]["state"]
            self.is_sign_in = bool(resp_json["data"]["clockInfo"]["inTime"])
            self.is_sign_out = bool(resp_json["data"]["clockInfo"]["outTime"])
            if self.post_state:
                self.sign_lat = resp_json["data"]["postInfo"]["lat"]
                self.sign_lng = resp_json["data"]["postInfo"]["lng"]
                self.sign_address = resp_json["data"]["postInfo"]["address"]
                self.logger.info(f"将使用获取到的实习坐标：{self.sign_lat}, {self.sign_lng}")
            else:
                self.logger.critical("未获取到实习坐标")
                raise Exception("未获取到实习坐标")
            self.logger.info(
                f"考勤状态：Sign in[{'√' if self.is_sign_in else 'x'}] || Sign out[{'√' if self.is_sign_out else 'x'}]"
            )

    def __report_epidemic(self):
        post_data = dict(
            healthCodeStatus=0,
            locationRiskLevel=0,
            healthCodeImg="",
            travelCodeImg=""
        )

        resp = self.session.post('https://xcx.xybsyw.com/student/clock/saveEpidemicSituation.action', data=post_data)
        resp.raise_for_status()

    def auto_sign_by_time(self):
        current = get_beijing_time()
        if current.hour > 12:
            self.sign_out()
        else:
            self.sign_in()

    def sign_in(self):
        self.__report_epidemic()
        self.__sign(self.__SignType.SIGN_IN)

    def sign_out(self):
        self.__report_epidemic()
        self.__sign(self.__SignType.SIGN_OUT)

    def __sign(self, sign_type: __SignType):
        is_update = False

        if sign_type == self.__SignType.SIGN_IN:
            if self.is_sign_out:
                raise Exception("已签退，无法签到")

            if self.is_sign_in:
                self.logger.critical("重复签到")
                is_update = True
            status = 2
        else:
            if not self.is_sign_in:
                raise Exception("未签到，无法签退")

            if self.is_sign_out:
                self.logger.warning("重复签退")
                is_update = True
            status = 1

        post_data = {
            'traineeId': self.train_id,
            'adcode': self.adcode,
            'lat': self.sign_lat,
            'lng': self.sign_lng,
            'address': self.sign_address,
            'deviceName': 'M2102J2CS',
            'punchInStatus': 1,
            'clockStatus': status,
            'imgUrl': "",
            'reason': ""
        }

        if not is_update:
            target_url = "https://xcx.xybsyw.com/student/clock/PostNew.action"
        else:
            target_url = "https://xcx.xybsyw.com/student/clock/Post!updateClock.action"

        resp = self.session.post(target_url, data=post_data)
        resp.raise_for_status()
        resp_json = resp.json()
        if resp_json["code"] == "200":
            self.logger.info(f"签到成功")
        else:
            raise Exception(f"签到失败：{resp_json}")
