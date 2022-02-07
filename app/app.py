import random
import uuid
from typing import Optional

from fastapi import APIRouter, Request
from starlette.templating import Jinja2Templates

from api.baidu import get_authorize_url, get_user_info, get_token, get_file_list
from config import CONFIG, refresh_config, Account

application = APIRouter()

templates = Jinja2Templates(directory="./app/templates")


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
    # 存储账户信息
    account = Account(info=account_info, token=account_token)
    account_id = uuid.uuid5(uuid.NAMESPACE_DNS, str(account.info.uk))
    CONFIG.accounts[str(account_id)] = account
    refresh_config()
    return templates.TemplateResponse("authorize.html", {
        "request": request,
        "info": account_info,
        "token": account_token,
    }
                                      )


@application.get("/about")
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@application.get("/admin")
def admin(request: Request):
    state = random.randint(1, 100)
    request.session["state"] = state
    authorize_url = get_authorize_url(state)
    users = [account_token.info.dict() for account_token in CONFIG.accounts.values()]
    return templates.TemplateResponse("admin/index.html", {
        "request": request,
        "authorize_url": authorize_url,
        "users": users
    })


# 放在左后
@application.get("/{filepath:path}")
def index(request: Request, filepath: Optional[str] = None):
    filepath = "/" + filepath
    access_token = [account.token.access_token for account in CONFIG.accounts.values()][0]
    file_list = get_file_list(access_token, path=filepath)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": CONFIG.site.title,
        "desc": CONFIG.site.desc,
        "path": filepath,
        "file_list": file_list
    })
