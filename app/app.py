import random
from typing import Optional, List

import requests
from fastapi import APIRouter, Request, Form
from starlette.responses import StreamingResponse, RedirectResponse
from starlette.templating import Jinja2Templates

from sdk.baidu import get_authorize_url, get_user_info, get_token, get_file_list, get_filemetas
from config import CONFIG, addAccount, PathMapping, updatePathMapping, getPathMappingOriginal, getVirtualFolder

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
            if username == CONFIG.user.username and password == CONFIG.user.password:
                print("登陆成功!")
                request.session.setdefault("login", True)
                return success_redirect_response
            else:
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
    return templates.TemplateResponse("admin/settings.html", {
        "request": request,
        # "msg": msg
    })


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
