from typing import List, Dict

from pydantic import BaseModel

from settings import CONFIG_PATH


class User(BaseModel):
    username: str
    password: str


class Authorizer(BaseModel):
    AppID: int
    AppKey: str
    SecretKey: str
    SignKey: str


class AccountInfo(BaseModel):
    uuid: str  # 本应用中的用户ID
    uk: int  # 用户ID
    baidu_name: str  # 百度账号
    netdisk_name: str  # 网盘账号
    avatar_url: str  # 头像地址
    vip_type: int  # 会员类型，0普通用户、1普通会员、2超级会员


class AccountToken(BaseModel):
    scope: str
    expires_in: int
    access_token: str
    refresh_token: str


class Account(BaseModel):
    info: AccountInfo
    token: AccountToken


class WebSite(BaseModel):
    title: str
    subtitle: str
    desc: str


class Config(BaseModel):
    user: User
    site: WebSite
    authorizers: List[Authorizer] = []
    accounts: Dict[str, Account] = {}


default_config = """
{
  "user": {
    "username": "admin",
    "password": "123456"
  },
  "site": {
    "title": "NetDiskManage",
    "subtitle": "网盘管理",
    "desc": "NetDiskManage是一个网盘管理程序,旨在方便用户整合管理多个网盘中的资源进行管理。"
  }
}
"""


def refresh_config():
    with open(CONFIG_PATH, 'w', encoding="utf-8") as fp:
        fp.write(CONFIG.json(ensure_ascii=False))


try:
    CONFIG: Config = Config.parse_file(CONFIG_PATH)
except FileNotFoundError:
    print("create default config.")
    CONFIG: Config = Config.parse_raw(default_config)
    refresh_config()
