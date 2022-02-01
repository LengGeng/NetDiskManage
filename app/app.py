from typing import Optional

from fastapi import APIRouter, Request
from starlette.templating import Jinja2Templates

from api.baidu import get_authorize_url, get_user_info

application = APIRouter()

templates = Jinja2Templates(directory="./app/templates")


@application.get("/about")
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@application.get("/admin")
def admin(request: Request):
    authorize_url = get_authorize_url()
    access_token = "121.3b5b5714002e498009d24ad64e38d5ab.YgoiplwVRVchAH29jO2A6_I7ggFBxQP7lddx4w-.U42RMA"
    user = get_user_info(access_token)
    users = [user]
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
        "title": "NetDiskManage",
        "desc": "网盘管理程序",
        "path": filepath
    })
