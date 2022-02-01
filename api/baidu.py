import urllib.parse

import requests
from fastapi import APIRouter

from settings import AppKey, SecretKey, redirect_uri, AUTHORIZE_STATE

baidu = APIRouter()


# 2.1 拼接授权链接
def get_authorize_url():
    url = "https://openapi.baidu.com/oauth/2.0/authorize?"
    params = {
        'response_type': 'code',
        'client_id': AppKey,
        'redirect_uri': redirect_uri,
        'scope': 'basic,netdisk',
        'display': 'popup',
        'state': AUTHORIZE_STATE
    }
    query_string = urllib.parse.urlencode(params)
    return url + query_string


# 2.2 接受授权参数
@baidu.get("/authorize")
def authorize(code: str, state: int):
    if state != AUTHORIZE_STATE:
        return {"error": "invalid state."}
    return get_token(code)


# 2.3 用CODE换取Access_token
def get_token(code):
    url = "https://openapi.baidu.com/oauth/2.0/token"
    params = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": AppKey,
        "client_secret": SecretKey,
        "redirect_uri": redirect_uri
    }
    response = requests.get(url, params=params)
    print(response.json())
    return {**response.json(), "redirect_uri": redirect_uri}


# 2.4 刷新Access_token
def refresh_token(token: str):
    url = "https://openapi.baidu.com/oauth/2.0/token"
    params = {
        "grant_type": "refresh_token",
        "refresh_token": token,
        "client_id": AppKey,
        "client_secret": SecretKey,
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
