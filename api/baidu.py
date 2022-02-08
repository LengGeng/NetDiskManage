import urllib.parse
from typing import List

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


def get_user_info(access_token: str) -> dict:
    """
    # 获取用户信息
    :param access_token: access_token
    :return:
    """
    url = "https://pan.baidu.com/rest/2.0/xpan/nas"
    params = {
        "method": "uinfo",
        "access_token": access_token,
    }
    headers = {
        'User-Agent': 'pan.baidu.com'
    }
    response = requests.get(url, params=params, headers=headers)
    return response.json()


def get_netdisk_info(access_token: str, checkfree: int = 0, checkexpire: int = 0) -> dict:
    """
    获取网盘容量信息
    :param access_token: access_token
    :param checkfree: 是否检查免费信息，0为不查，1为查
    :param checkexpire: 是否检查过期信息，0为不查，1为查
    :return:
    """
    url = "https://pan.baidu.com/api/quota"
    params = {
        "access_token": access_token,
        "checkfree": checkfree,
        "checkexpire": checkexpire,
    }
    headers = {
        'User-Agent': 'pan.baidu.com'
    }
    response = requests.get(url, params=params, headers=headers)
    return response.json()


def get_file_list(access_token: str, path: str = "/", start: int = 0, limit: int = 50,
                  order: str = "name", desc: bool = False) -> dict:
    """
    获取文件列表
    :param access_token: access_token
    :param path: 路径
    :param start: 起始位置，从0开始
    :param limit: 每页条目数，默认为50，最大值为10000
    :param order: 先按文件类型排序后的排序字段，time修改时间 name文件名称 size文件大小
    :param desc: 降序排列
    :return:
    """
    url = "https://pan.baidu.com/rest/2.0/xpan/file"
    params = {
        "method": "list",
        "access_token": access_token,
        "dir": path,
        "start": start,
        "limit": limit,
        "order": order,
    }
    if desc:
        params["desc"] = "1"
    headers = {
        'User-Agent': 'pan.baidu.com'
    }
    response = requests.get(url, params=params, headers=headers)
    return response.json()


def get_file_list_walk(access_token: str, path: str = "/", start: int = 0, limit: int = 50,
                       order: str = "name", desc: bool = False) -> dict:
    """
    递归获取文件列表
    :param access_token: access_token
    :param path: 路径
    :param start: 起始位置，从0开始
    :param limit: 每页条目数，默认为50，最大值为10000
    :param order: 先按文件类型排序后的排序字段，time修改时间 name文件名称 size文件大小
    :param desc: 降序排列
    :return:
    """
    url = "https://pan.baidu.com/rest/2.0/xpan/multimedia"
    params = {
        "method": "listall",
        "access_token": access_token,
        "path": path,
        "start": start,
        "limit": limit,
        "order": order,
        "recursion": 1,
    }
    if desc:
        params["desc"] = "1"
    headers = {
        'User-Agent': 'pan.baidu.com'
    }
    response = requests.get(url, params=params, headers=headers)
    return response.json()


def get_filemetas(access_token: str, fsids: List[int], *,
                  dlink: int = 1, thumb: int = 0, extra: int = 0, needmedia: int = 0) -> dict:
    """
    查询文件信息
    :param access_token: access_token
    :param fsids: 文件id数组,上限100个
    :param dlink: 是否需要下载地址，0为否，1为是，默认为1
    :param thumb: 是否需要缩略图地址，0为否，1为是，默认为0
    :param extra: 图片是否需要拍摄时间、原图分辨率等其他信息，0 否、1 是，默认0
    :param needmedia: 视频是否需要展示时长信息，0 否、1 是，默认0
    :return:
    """
    url = "https://pan.baidu.com/rest/2.0/xpan/multimedia"
    params = {
        "method": "filemetas",
        "access_token": access_token,
        "fsids": str(fsids),
        "dlink": dlink,
        "thumb": thumb,
        "extra": extra,
        "needmedia": needmedia
    }
    headers = {
        'User-Agent': 'pan.baidu.com'
    }
    response = requests.get(url, params=params, headers=headers)
    return response.json()
