from fastapi import FastAPI
from playwright.sync_api import sync_playwright
from pydantic import BaseModel
from typing import Optional
import subprocess
import os
import uvicorn
from playwright.async_api import async_playwright

# 创建 FastAPI 实例
app = FastAPI(
    title="My API",
    description="This is a sample API",
    version="1.0.0"
)


class CreateDigitalVideoRequest(BaseModel):
    """
    使用heygen生成数字人视频时的请求参数

    Attributes:
        script_content (str): 脚本内容
        script_locale (str): 脚本语言
        digital_human_id (str): 数字人ID
        audio_id (str): 音频ID
        size (str): 大小
    """
    script_content: str
    script_locale: str
    digital_human_id: str
    audio_id: str
    size: str


def open_chrome():
    user_data_dir = os.path.join(os.getcwd(), "chrome_user_data")

    # Chrome启动命令
    cmd = [
        "C:/Program Files/Google/Chrome/Application/chrome.exe",
        f"--user-data-dir={user_data_dir}",
        "--remote-debugging-port=9222",
        "--no-first-run",
        "--no-default-browser-check"
    ]
    # 启动Chrome浏览器
    process = subprocess.Popen(cmd)
    return process


@app.post("/digital-video/")
def create_digital_video(request: CreateDigitalVideoRequest):
    """
    生成数字人视频
    """
    open_chrome()
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        page = browser.new_page()
        page.goto('https://www.heygen.com')
    return "ok"


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0")
    # open_chrome()
    # print(1)
