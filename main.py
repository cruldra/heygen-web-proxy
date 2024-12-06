import atexit
import signal
import time

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


class ChromeManager:
    _instance = None
    _chrome_process = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ChromeManager()
        return cls._instance

    def start_chrome(self):
        if self._chrome_process is None:
            user_data_dir = os.path.join(os.getcwd(), "chrome_user_data")
            cmd = [
                "C:/Program Files/Google/Chrome/Application/chrome.exe",
                f"--user-data-dir={user_data_dir}",
                "--remote-debugging-port=9222",
                "--no-first-run",
                "--no-default-browser-check"
            ]
            self._chrome_process = subprocess.Popen(cmd)
        return self._chrome_process

    def close_chrome(self):
        if self._chrome_process is not None:
            self._chrome_process.terminate()
            self._chrome_process.wait()
            self._chrome_process = None

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


# 在应用启动时启动Chrome
chrome_manager = ChromeManager.get_instance()
chrome_manager.start_chrome()



@app.post("/digital-video/")
async def create_digital_video(request: CreateDigitalVideoRequest):
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page =await context.new_page()
        await page.goto('https://app.heygen.com/create-v3/draft?vt=p')
        time.sleep(3)
        await page.close()
    return "ok"
def cleanup():
    chrome_manager = ChromeManager.get_instance()
    chrome_manager.close_chrome()

def signal_handler(signum, frame):
    cleanup()
    exit(0)

if __name__ == '__main__':
    # 注册清理函数
    atexit.register(cleanup)
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    uvicorn.run(app, host="0.0.0.0")
