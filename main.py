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
from playwright.async_api import async_playwright, ElementHandle

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
        avatar_name (str): 数字人头像名称
        look_name (str): 数字人外观名称
        audio_id (str): 音频ID
        size (str): 大小
    """
    script_content: str
    script_locale: str
    avatar_name: str
    look_name: str
    audio_id: str
    size: str


# 在应用启动时启动Chrome
chrome_manager = ChromeManager.get_instance()
chrome_manager.start_chrome()


async def get_parent_element(element_handle: ElementHandle):
    """
    获取元素的父元素
    Args:
        element_handle: ElementHandle对象
    Returns:
        ElementHandle: 父元素的ElementHandle对象
    """
    return await element_handle.evaluate_handle("element => element.parentElement")


@app.post("/digital-video/")
async def create_digital_video(request: CreateDigitalVideoRequest):
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = await context.new_page()
        await page.goto('https://app.heygen.com/create-v3/draft?vt=p')
        # 选择头像
        avatar_element = await page.wait_for_selector(
            f'div[draggable="false"]>div:nth-child(3)>div>label[title="{request.avatar_name}"]')
        parent1 = await get_parent_element(avatar_element)
        parent2 = await get_parent_element(parent1)
        avatar_container = await get_parent_element(parent2)
        await avatar_container.click()

        # 选择外观
        look_element = await page.wait_for_selector(
            f'div[data-active="false"][draggable="true"] div.css-1xfwczf[title="{request.look_name}"]')
        parent1 = await get_parent_element(look_element)
        parent2 = await get_parent_element(parent1)
        look_container = await get_parent_element(parent2)
        await look_container.click()

        # 选择文本轨道
        text_track = await page.wait_for_selector('div[data-draggable-handle-id].css-esngap')
        await text_track.click()

        # 输入文案
        text_input = await page.wait_for_selector('span[data-slate-string="true"]')
        await text_input.fill(request.script_content)

        # 生成一个随机视频id
        time.sleep(1)
        video_id = str(int(time.time()))
        # 点击播放文案, 这个会导致等待
        play_btn = await  page.wait_for_selector("""button.unloaded""")
        await play_btn.click()
        # 点击提交,弹出确认框
        submit_button = await page.wait_for_selector('.css-88rj5c')
        await submit_button.click()

        # 输入随机视频名
        video_name_input = await page.wait_for_selector('input#input')
        await video_name_input.fill(video_id)

        # 去除水印,默认是开启的
        watermark_button = await page.wait_for_selector('button.css-19559xf[role="switch"]')
        await watermark_button.click()

        # 点击提交
        final_submit = await page.wait_for_selector('button.css-17onw6j')
        await final_submit.click()

        time.sleep(300000)
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
