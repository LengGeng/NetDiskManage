import time
import uuid
import os.path
from typing import List, Dict, Tuple, Optional

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


class PathMapping(BaseModel):
    original: str = "/"
    mapping: str = "/"


class Account(BaseModel):
    info: AccountInfo
    token: AccountToken
    mapping: PathMapping = PathMapping()
    activated: bool = False


class WebSite(BaseModel):
    title: str
    subtitle: str
    desc: str


class SystemConfig(BaseModel):
    open_download: bool
    open_dlink: bool
    open_grant: bool


class Config(BaseModel):
    user: User
    site: WebSite
    system: SystemConfig
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
  },
  "system": {
    "open_download": true,
    "open_dlink": true,
    "open_grant": true
  }
}
"""


def refresh_config():
    with open(CONFIG_PATH, 'w', encoding="utf-8") as fp:
        fp.write(CONFIG.json(ensure_ascii=False))


def getActiveAccounts():
    return [account for account in CONFIG.accounts.values() if account.activated]


def addAccount(token: dict, info: dict):
    # 生成uuid
    _uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(info.get("uk"))))
    info["uuid"] = _uuid
    # 存储账户信息
    account = Account(info=info, token=token)
    # 判断授权账户是否存在
    if _uuid in CONFIG.accounts:
        # 保留原有路径映射
        account.mapping = CONFIG.accounts.get(_uuid).mapping
    # 添加
    CONFIG.accounts[_uuid] = account
    # 刷新配置文件
    refresh_config()
    return account


def updatePathMapping(uuid_, path_mapping: PathMapping):
    # 获取账户
    account = CONFIG.accounts.get(uuid_)
    # 判断账户是否存在
    if account:
        # 获取所有激活的账户
        active_accounts = getActiveAccounts()
        # 获取映射路径(排除自身)
        paths = [item.mapping.mapping for item in active_accounts if item.info.uuid != uuid_]
        if paths:  # 当为1时，为修改本身，可直接进行修改
            # 当存在多个账户时，不允许映射为根路径。因为可能会出现重复。
            if "/" in paths:
                return {"code": 1, "msg": "存在一个映射为根路径(/)的授权账户，不允许进行多账户映射!"}
            # 映射路由不允许重复
            if path_mapping.mapping in paths:
                return {"code": 2, "msg": "存在一个相同映射的账户!"}
            if path_mapping.mapping == "/":
                return {"code": 3, "msg": "使用多账户时，不允许映射为根路径(/)!"}
        # 添加映射
        account.mapping = path_mapping
        # 激活账户
        account.activated = True
        # 刷新配置文件
        refresh_config()
        return {"code": 0, "msg": "success"}
    else:
        return {"code": -1, "msg": "授权账户不存在!"}


def getPathMappingOriginal(path: str) -> Tuple[Optional[Account], Optional[str]]:
    """
    获取请求路径对应的授权账户以及真实路径
    :param path: 请求路径
    :return: (授权账户, 真实路径)
    """
    accounts = getActiveAccounts()
    if accounts:
        # 可能存在一个账户将目录映射为根目录的
        if accounts[0].mapping.mapping == "/":
            # 真实路径 = 源路径 + 现有路径
            original = accounts[0].mapping.original
            child_path = path.strip("/")
            real_path = os.path.normpath(os.path.join(original, child_path)).replace("\\", "/")
            return accounts[0], real_path
        else:
            # 判断是否是根目录,根目录应返回虚拟目录
            if path == "/":
                return None, "/"
            else:
                # 分割路径
                path_split = path.strip("/").split("/")
                virtual_path = "/" + path_split[0]
                child_path = "/".join(path_split[1:]) if len(path_split) > 1 else ""
                # 获取映射的原路径
                for account in accounts:
                    if virtual_path == account.mapping.mapping:
                        original = account.mapping.original
                        # 拼接最终路径
                        real_path = os.path.normpath(os.path.join(original, child_path)).replace("\\", "/")
                        return account, real_path
                else:
                    # 没有检索到对应的原路径 404
                    return None, ""
    else:
        # 没有授权账户
        return None, None


def getVirtualFolder() -> dict:
    accounts = getActiveAccounts()
    for account in accounts:
        yield {
            "isdir": True,
            "path": account.mapping.mapping,
            "server_filename": account.mapping.mapping.strip("/"),
            "server_mtime": time.time(),
        }


try:
    CONFIG: Config = Config.parse_file(os.path.join(os.path.dirname(__file__), CONFIG_PATH))
except FileNotFoundError:
    print("create default config.")
    CONFIG: Config = Config.parse_raw(default_config)
    refresh_config()
