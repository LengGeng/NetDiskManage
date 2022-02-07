import time

import uvicorn
from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.app import application
from settings import SECRET_KEY

app = FastAPI(
    title="NetDiskManage",
    description="NetDiskManage 网盘管理",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redocs"
)

# mount表示将某个目录下一个完全独立的应用挂载过来，这个不会在API交互文档中显示
app.mount("/static", app=StaticFiles(directory="./static"), name="static")


@app.middleware("http")
async def ware(request: Request, call_next):  # call_next将接收request请求最为参数
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1",
        "http://127.0.0.1:8080"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
# 开启 Session
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# app.include_router(baidu, prefix="/api/baidu", tags=["百度网盘"])
app.include_router(application, tags=["主程序"])

if __name__ == '__main__':
    uvicorn.run("run:app", host="0.0.0.0", port=8000, reload=True, debug=True, workers=1)
