from typing import Optional

from fastapi import APIRouter, Request
from starlette.templating import Jinja2Templates

from api.baidu import get_authorize_url, get_user_info
from config import CONFIG

application = APIRouter()

templates = Jinja2Templates(directory="./app/templates")


@application.get("/about")
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@application.get("/admin")
def admin(request: Request):
    authorize_url = get_authorize_url()
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
