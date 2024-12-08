import atexit
import signal
import time

from fastapi import FastAPI
from playwright.sync_api import sync_playwright, ElementHandle, Page
from pydantic import BaseModel
from typing import Optional
import subprocess
import os
import uvicorn

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


def get_parent_element(element_handle: ElementHandle):
    """
    获取元素的父元素
    Args:
        element_handle: ElementHandle对象
    Returns:
        ElementHandle: 父元素的ElementHandle对象
    """
    return element_handle.evaluate_handle("element => element.parentElement")


@app.post("/digital-video/")
def create_digital_video(request: CreateDigitalVideoRequest):
    """
    新建一个数字人视频,视频渲染会持续一段时间,所以返回视频id,后续需要通过视频id获取视频
    :param request:
    :return:
    """
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.new_page()
        page.goto('https://app.heygen.com/create-v3/draft?vt=p')
        # 选择头像
        avatar_element = page.wait_for_selector(
            f'div[draggable="false"]>div:nth-child(3)>div>label[title="{request.avatar_name}"]')
        parent1 = get_parent_element(avatar_element)
        parent2 = get_parent_element(parent1)
        avatar_container = get_parent_element(parent2)
        avatar_container.click()

        # 选择外观
        look_element = page.wait_for_selector(
            f'div[data-active="false"][draggable="true"] div.css-1xfwczf[title="{request.look_name}"]')
        parent1 = get_parent_element(look_element)
        parent2 = get_parent_element(parent1)
        look_container = get_parent_element(parent2)
        look_container.click()

        # 选择文本轨道
        text_track = page.wait_for_selector('div[data-draggable-handle-id].css-esngap')
        text_track.click()

        # 输入文案
        text_input = page.wait_for_selector('span[data-slate-string="true"]')
        text_input.fill(request.script_content)

        # 点击播放文案, 这个会导致等待
        # time.sleep(1)
        play_btn = page.wait_for_selector("""button.css-1d5pxp4""")
        play_btn.click()
        # 等待加载状态
        page.wait_for_selector('button.css-1c3nw3f')
        # 等待播放完成
        page.wait_for_selector('button.css-1d5pxp4', timeout=10 * 60 * 1000)

        # 点击提交,弹出确认框
        submit_button = page.wait_for_selector('.css-88rj5c')
        submit_button.click()

        # 输入随机视频名
        video_name_input = page.wait_for_selector('input#input')
        video_id = str(int(time.time()))
        video_name_input.fill(video_id)

        # 去除水印,默认是开启的
        watermark_button = page.wait_for_selector('button.css-19559xf[role="switch"]')
        watermark_button.click()

        # 点击提交
        final_submit = page.wait_for_selector('button.css-17onw6j')
        final_submit.click()

        # 处理可能出现的Submit Anyway按钮
        try:
            submit_anyway = page.wait_for_selector('span:text-is("Submit Anyway")', timeout=5 * 60 * 1000)
            if submit_anyway:
                submit_anyway.click()
        except:
            pass
        page.close()
        return video_id


def get_element_outer_html(element: ElementHandle):
    return element.evaluate('element => element.outerHTML')


@app.post("/clear_drafts")
def clear_drafts():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.new_page()
        page.goto('https://app.heygen.com/home')
        # 等10秒让页面加载完成
        time.sleep(10)
        draft_videos = page.query_selector_all('div:text-is("Draft")')
        for draft_video in draft_videos:
            try:
                draft_video1 = get_parent_element(draft_video)
                draft_video2 = get_parent_element(draft_video1)
                draft_video3 = get_parent_element(draft_video2)
                draft_video4 = get_parent_element(draft_video3)
                draft_video5 = get_parent_element(draft_video4)
                draft_video6 = get_parent_element(draft_video5)
                draft_video7 = get_parent_element(draft_video6)

                # 获取元素的中心位置
                box = draft_video7.bounding_box()
                center_x = box['x'] + box['width'] / 2
                center_y = box['y'] + box['height'] / 2

                # 移动鼠标到元素中心
                page.mouse.move(center_x, center_y)

                # 等待元素变成css-ioxlw8样式
                draft_video7 = page.wait_for_selector('.css-ioxlw8')
                float_menu = draft_video7.query_selector('.css-1qsiyka')
                # 获取浮动菜单的中心位置
                float_menu_box = float_menu.bounding_box()
                float_menu_center_x = float_menu_box['x'] + float_menu_box['width'] / 2
                float_menu_center_y = float_menu_box['y'] + float_menu_box['height'] / 2

                # 移动鼠标到浮动菜单中心
                page.mouse.move(float_menu_center_x, float_menu_center_y)

                # 等待并点击Trash选项
                trash_option = page.wait_for_selector('li.rc-menu-item:has-text("Trash")')
                trash_option.click()
                time.sleep(1)
            except:
                pass
        time.sleep(100)
        page.close()


def get_video_card_by_id(page:Page, video_id):
    js_code = """
    () => {
        const elements = document.querySelectorAll('div.video-card span.css-gt1xo4');
        let clickTarget = null;
        for (const el of elements) {
            if (el.textContent.trim() === '%s') {
                clickTarget = el;
                for (let i = 0; i < 8; i++) {
                    clickTarget = clickTarget.parentElement;
                }
            }
        }
        return clickTarget;
    }
    """ % video_id

    return page.wait_for_function(js_code).as_element()


@app.get("/video_status/{video_id}")
def get_video_status(video_id: str):
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.new_page()
        page.goto('https://app.heygen.com/home')
        # 等待页面加载完成
        time.sleep(10)
        # 查找包含视频ID的span元素
        video_card_element = get_video_card_by_id(page, video_id)
        # 检查是否存在时长信息元素
        try:
            duration_element = video_card_element.query_selector('div.css-nxiqic.content')
            if duration_element:
                # 如果找到时长元素，说明渲染完成
                return {"status": "completed"}
            else:
                return {"status": "processing"}
        except:
            return {"status": "error"}
        finally:
            page.close()


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
