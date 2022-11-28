import os

from xybSign import XybSigner

if __name__ == '__main__':
    if not os.getenv("CI"):
        print("Should only run in CI environment")
        exit(1)

    password = os.getenv("XYB_PASSWORD")
    phone = os.getenv("XYB_PHONE")
    adcode = os.getenv("XYB_ADCODE")

    if not password or not phone or not adcode:
        print("Missing environment variables")
        exit(1)

    XybSigner(phone, password, adcode).auto_sign_by_time()