import random
from typing import Optional

from fastapi import APIRouter, Request
from starlette.templating import Jinja2Templates

from api.baidu import get_authorize_url, get_user_info, get_token
from config import CONFIG, refresh_config, Account

application = APIRouter()

templates = Jinja2Templates(directory="./app/templates")


# 2.2 接受授权参数
@application.get("/authorize")
def authorize(request: Request, code: str, state: int):
    if state != request.session.get("state"):
        return {"error": "invalid state."}
    token = get_token(code)
    CONFIG.accounts.append(Account(**token))
    refresh_config()
    return templates.TemplateResponse("authorize.html", {
        "request": request,
        "info": token
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
    users = [get_user_info(account.access_token) for account in CONFIG.accounts]
    return templates.TemplateResponse("admin/index.html", {
        "request": request,
        "authorize_url": authorize_url,
        "users": users
    })


# 放在左后
@application.get("/{filepath:path}")
def index(request: Request, filepath: Optional[str] = None):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": CONFIG.site.title,
        "desc": CONFIG.site.desc,
        "path": filepath
    })
