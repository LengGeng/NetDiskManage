import random
from typing import Optional, List

import requests
from fastapi import APIRouter, Request, Form
from starlette.responses import StreamingResponse, RedirectResponse
from starlette.templating import Jinja2Templates

from sdk.baidu import get_authorize_url, get_user_info, get_token, get_file_list, get_filemetas
from config import (
    CONFIG, addAccount, PathMapping, updatePathMapping, getPathMappingOriginal, getVirtualFolder, refresh_config,
    Authorizer
)

application = APIRouter()

templates = Jinja2Templates(directory="./app/templates")


def getTree(path: str) -> List[dict]:
    account, real_path = getPathMappingOriginal(path)
    if account and real_path:
        return get_file_list(account.token.access_token, real_path).get("list")
    else:
        # 判断真实路径是否存在
        if real_path:
            return list(getVirtualFolder())
        else:
            # 没有授权账户
            if real_path is None:
                return []
            else:  # 错误的路径
                return []


def getJumpFinalUrl(url: str, maxJump: int = 5) -> str:
    """
    获取一个URL最终重定向的URL
    :param url: 原来的URL
    :param maxJump: 最大重定向次数,最大为5
    :return: 最终重定向的URL
    """
    jump = 0
    maxJump = min(maxJump, 5)  # 最大重定向的值为5
    while jump < maxJump:
        response = requests.head(url)
        if response.status_code == 302:
            url = response.headers['Location']
            jump += 1
        else:
            return url
    raise Exception("超出最大重定向次数!")


@application.get("/jump")
def jump(request: Request, title: str = Form("跳转"), msg: str = Form(""), url: str = Form("/"), code: int = Form(0)):
    return templates.TemplateResponse("jump.html", {
        "request": request,
        "title": title,
        "msg": msg,
        "code": code,
        "url": url,
    })


# 2.2 接受授权参数
@application.get("/authorize")
def authorize(request: Request, code: str, state: int):
    # 判断 state，可以防止CSRF攻击
    if state != request.session.get("state"):
        return {"error": "invalid state."}
    # 获取 token
    account_token = get_token(code)
    # 获取账户信息
    account_info = get_user_info(account_token.get("access_token"))
    addAccount(account_token, account_info)
    return templates.TemplateResponse("authorize.html", {
        "request": request,
        "info": account_info,
        "token": account_token,
    })


@application.api_route("/updateMapping", methods=["GET", "POST"])
def updateMapping(request: Request, uuid_: str, original: str = Form(""), mapping: str = Form("")):
    msg = ""
    # 判断请求方式
    if request.method == "POST":
        # 判断参数
        if original and mapping:
            path_mapping = PathMapping(original=original, mapping=mapping)
            result = updatePathMapping(uuid_, path_mapping)
            # 判断结果
            msg = result.get("msg", "未知错误")
        else:
            msg = "路径映射不能为空!!!"
    # 账户数据
    account = CONFIG.accounts[uuid_]
    return templates.TemplateResponse("mapping.html", {
        "request": request,
        "msg": msg,
        "info": account.info.dict(),
        "mapping": account.mapping.dict(),
    })


@application.get("/down")
def down(fid: int, path: str):
    # 根据文件路径判断所属账户
    account, real_path = getPathMappingOriginal(path)
    if not account:
        return "无效的账户文件!"
    access_token = account.token.access_token
    filemetas = get_filemetas(access_token, [fid])
    file_meta = filemetas.get("list")[0]
    link = file_meta.get("dlink")
    filename = file_meta.get("filename")
    filesize = file_meta.get("size")

    def send_chunk():
        url = f"{link}&access_token={access_token}"
        headers = {
            'User-Agent': 'pan.baidu.com'
        }
        # 流式读取
        with requests.get(url, headers=headers, stream=True) as file:
            file.raise_for_status()
            yield from file.iter_content(chunk_size=8192)

    response_headers = {
        "Content-type": "application/octet-stream",
        "Accept-Ranges": "bytes",
        "Content-Disposition": f"attachment; filename={filename}",
        "Content-Length": f"{filesize}",
        "Content-Transfer-Encoding": "binary"
    }
    # 流式读取
    response = StreamingResponse(send_chunk(), headers=response_headers)
    return response


@application.get("/dlink")
def down_link(request: Request, fid: int, path: str):
    # 根据文件路径判断所属账户
    account, real_path = getPathMappingOriginal(path)
    if not account:
        return "无效的账户文件!"
    access_token = account.token.access_token
    filemetas = get_filemetas(access_token, [fid])
    file_meta = filemetas.get("list")[0]
    link = file_meta.get("dlink")
    dlink = f"{link}&access_token={access_token}"
    dlink = getJumpFinalUrl(dlink)
    filename = file_meta.get("filename")
    filesize = file_meta.get("size")
    return templates.TemplateResponse("dlink.html", {
        "request": request,
        "dlink": dlink,
        "filename": filename,
        "filesize": filesize,
    })


@application.get("/about")
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@application.api_route("/login", methods=["GET", "POST"])
def login(request: Request, username: str = Form(""), password: str = Form("")):
    success_redirect_response = RedirectResponse(application.url_path_for("admin"))
    # https://stackoverflow.com/questions/66849929/fastapi-redirect-gives-method-not-allowed-error
    # 解决 POST 跳转到 /admin 返回 Method Not Allowed
    success_redirect_response.status_code = 302
    msg = ""
    # 判断是否登录
    if request.session.get("login"):
        return success_redirect_response
    # 判断请求方式
    if request.method == "POST":
        if username and password:
            if CONFIG.user.lock and CONFIG.user.count >= 3:
                msg = "账户已经锁定!"
            else:
                if username == CONFIG.user.username and password == CONFIG.user.password:
                    print("登陆成功!")
                    request.session.setdefault("login", True)
                    # 清空计数
                    CONFIG.user.count = 0
                    return success_redirect_response
                else:
                    CONFIG.user.count += 1
                    msg = "用户名或密码错误!!!"
        else:
            msg = "用户名或密码不能为空!!!"

    return templates.TemplateResponse("login.html", {
        "request": request,
        "msg": msg
    })


@application.get("/logout")
def logout(request: Request):
    # 清空 session
    request.session.clear()
    # 跳转至首页
    return RedirectResponse("/")


@application.get("/admin")
def admin(request: Request):
    state = random.randint(1, 100)
    request.session["state"] = state
    authorize_url = get_authorize_url(state)
    if not authorize_url:
        return jump(request, "错误", "还未添加授权账户!", application.url_path_for("settings"), code=1)
    users = [
        [account_token.info.dict(), account_token.mapping.dict(), account_token.activated]
        for account_token in CONFIG.accounts.values()
    ]
    return templates.TemplateResponse("admin/index.html", {
        "request": request,
        "authorize_url": authorize_url,
        "users": users
    })


@application.get("/admin/settings")
def settings(request: Request):
    if CONFIG.authorizers:
        authorizer = CONFIG.authorizers[0].dict()
    else:
        authorizer = {}
    settingData = {
        "site": CONFIG.site.dict(),
        "system": CONFIG.system.dict(),
        "administrator": CONFIG.user.dict(),
        "authorize": authorizer,
    }
    return templates.TemplateResponse("admin/settings.html", {
        "request": request,
        "settings": settingData,
        # "msg": msg
    })


@application.post("/admin/settings/site")
def settings_site(request: Request, title: str = Form(""), subtitle: str = Form(""), desc: str = Form("")):
    CONFIG.site.title = title or CONFIG.site.title
    CONFIG.site.subtitle = subtitle or CONFIG.site.subtitle
    CONFIG.site.desc = desc or CONFIG.site.desc
    refresh_config()
    return jump(request, "提示", "更新网站信息成功!", application.url_path_for("settings"))


@application.post("/admin/settings/system")
def settings_system(request: Request, open_download: bool = Form(True), open_dlink: bool = Form(True),
                    open_grant: bool = Form(True)):
    CONFIG.system.open_download = open_download
    CONFIG.system.open_dlink = open_dlink
    CONFIG.system.open_grant = open_grant
    refresh_config()
    return jump(request, "提示", "更新系统设置成功!(但该配置项暂未启用👀)", application.url_path_for("settings"))


@application.post("/admin/settings/administrator")
def settings_administrator(request: Request, username: str = Form(...), password: str = Form(...),
                           lock: bool = Form(True)):
    CONFIG.user.username = username
    CONFIG.user.password = password
    CONFIG.user.lock = lock
    # 重新计数
    CONFIG.user.count = 0
    refresh_config()
    return jump(request, "提示", "更新管理员账户信息成功!", application.url_path_for("settings"))


@application.post("/admin/settings/authorize")
def settings_authorize(request: Request, app_id: str = Form(...), app_key: str = Form(...),
                       secret_key: str = Form(...), sign_key: str = Form(...), ):
    authorizer = Authorizer(AppID=app_id, AppKey=app_key, SecretKey=secret_key, SignKey=sign_key)
    if CONFIG.authorizers:
        CONFIG.authorizers[0] = authorizer
    else:
        CONFIG.authorizers.append(authorizer)
    refresh_config()
    return jump(request, "提示", "更新授权账户信息成功!", application.url_path_for("settings"))


# 放在左后
@application.get("/{filepath:path}")
def index(request: Request, filepath: Optional[str] = None):
    filepath = "/" + filepath
    file_list = getTree(filepath)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": CONFIG.site.title,
        "desc": CONFIG.site.desc,
        "path": filepath,
        "file_list": file_list
    })
