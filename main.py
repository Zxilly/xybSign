import json

from xybSign import XybSigner

if __name__ == '__main__':
    with open('config.json', 'r') as f:
        config = json.load(f)

    XybSigner(config["phone"], config["password"], config["adcode"]).auto_sign_by_time()