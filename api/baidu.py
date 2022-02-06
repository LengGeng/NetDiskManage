import urllib.parse

import requests

from config import CONFIG
from settings import redirect_uri


def get_authorize_url(state: int) -> str:
    """
    2.1 拼接授权链接
    :param state: 授权重定向后会带上state参数。可以利用state参数来防止CSRF攻击
    :return:
    """
    url = "https://openapi.baidu.com/oauth/2.0/authorize?"
    params = {
        'response_type': 'code',
        'client_id': CONFIG.authorizers[0].AppKey,
        'redirect_uri': redirect_uri,
        'scope': 'basic,netdisk',
        'display': 'popup',
        'state': state
    }
    query_string = urllib.parse.urlencode(params)
    return url + query_string


def get_token(code: str) -> dict:
    """
    2.3 用CODE换取Access_token
    :param code: 获取用户授权后得到的code
    :return:
    """
    url = "https://openapi.baidu.com/oauth/2.0/token"
    params = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": CONFIG.authorizers[0].AppKey,
        "client_secret": CONFIG.authorizers[0].SecretKey,
        "redirect_uri": redirect_uri
    }
    response = requests.get(url, params=params)
    return {**response.json(), "redirect_uri": redirect_uri}


def refresh_token(token: str) -> dict:
    """
    # 2.4 刷新Access_token
    :param token: 用于刷新的refresh_token
    :return:
    """
    url = "https://openapi.baidu.com/oauth/2.0/token"
    params = {
        "grant_type": "refresh_token",
        "refresh_token": token,
        "client_id": CONFIG.authorizers[0].AppKey,
        "client_secret": CONFIG.authorizers[0].SecretKey,
    }
    response = requests.get(url, params=params)
    return response.json()


# 获取用户信息
def get_user_info(access_token: str):
    url = "https://pan.baidu.com/rest/2.0/xpan/nas"
    params = {
        "method": "uinfo",
        "access_token": access_token,
    }
    payload = {}
    headers = {
        'User-Agent': 'pan.baidu.com'
    }

    response = requests.request("GET", url, params=params, headers=headers, data=payload)
    # response = requests.get(url, params=params, headers=headers)

    return response.json()
