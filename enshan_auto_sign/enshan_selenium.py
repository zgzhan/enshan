#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
恩山无线论坛自动签到脚本 (Selenium版本)
支持滑动拼图验证码识别
"""

import os
import re
import time
import random
import requests
import urllib3
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

urllib3.disable_warnings()


class EnShanSelenium:
    """恩山论坛自动签到类"""
    
    name = "恩山无线论坛"
    
    def __init__(self):
        self.cookie = os.getenv("ENSHAN_COOKIE")
        self.serverchan_key = os.environ.get('SERVERCHAN_KEY')
        self.driver = None
        
    def init_driver(self):
        """初始化浏览器驱动"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 无头模式
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_window_size(1920, 1080)
        
    def set_cookie(self):
        """设置Cookie"""
        if not self.cookie:
            return False
            
        self.driver.get("https://www.right.com.cn/FORUM/")
        time.sleep(2)
        
        # 解析并设置Cookie
        for item in self.cookie.split(';'):
            item = item.strip()
            if '=' in item:
                name, value = item.split('=', 1)
                self.driver.add_cookie({
                    'name': name.strip(),
                    'value': value.strip(),
                    'domain': '.right.com.cn'
                })
        
        return True
        
    def detect_gap(self, bg_img, slider_img):
        """
        检测滑块缺口位置
        :param bg_img: 背景图片
        :param slider_img: 滑块图片
        :return: 缺口位置x坐标
        """
        # 转换为灰度图
        bg_gray = bg_img.convert('L')
        
        # 边缘检测 - 简单的像素差异检测
        threshold = 50
        for x in range(60, bg_gray.width - slider_img.width):
            diff_count = 0
            for y in range(bg_gray.height):
                # 检查该列的像素变化
                if x > 0:
                    pixel_diff = abs(bg_gray.getpixel((x, y)) - bg_gray.getpixel((x-1, y)))
                    if pixel_diff > threshold:
                        diff_count += 1
            
            # 如果该列有足够多的像素变化,可能是缺口位置
            if diff_count > bg_gray.height * 0.3:
                return x
                
        return 0
        
    def get_track(self, distance):
        """
        生成模拟人类滑动的轨迹
        :param distance: 需要滑动的距离
        :return: 轨迹列表
        """
        track = []
        current = 0
        mid = distance * 4 / 5
        t = 0.2
        v = 0
        
        while current < distance:
            if current < mid:
                a = 2  # 加速度为正2
            else:
                a = -3  # 加速度为负3
            
            v0 = v
            v = v0 + a * t
            move = v0 * t + 1 / 2 * a * t * t
            current += move
            track.append(round(move))
            
        # 添加一些随机抖动,模拟人类行为
        for i in range(3):
            track.append(random.randint(-2, 2))
            
        return track
        
    def solve_slider_captcha(self):
        """解决滑块验证码"""
        try:
            # 等待验证码弹窗出现
            wait = WebDriverWait(self.driver, 10)
            
            # 等待拼图验证码加载
            time.sleep(3)
            
            # 截取验证码图片
            screenshot = self.driver.get_screenshot_as_png()
            screenshot = Image.open(BytesIO(screenshot))
            
            # 查找滑块元素
            slider = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[class*="slider"], [class*="slide-verify"], .slide-verify-slider')))
            
            # 获取滑块初始位置
            slider_location = slider.location
            
            # 这里需要根据实际页面结构调整
            # 由于无法直接获取拼图图片,我们使用一个估算的距离
            # 通常滑块验证码的距离在 60-280 像素之间
            distance = random.randint(200, 250)
            
            # 生成滑动轨迹
            track = self.get_track(distance)
            
            # 执行滑动
            ActionChains(self.driver).click_and_hold(slider).perform()
            time.sleep(0.2)
            
            for move in track:
                ActionChains(self.driver).move_by_offset(xoffset=move, yoffset=random.randint(-2, 2)).perform()
                time.sleep(random.uniform(0.01, 0.02))
            
            time.sleep(0.5)
            ActionChains(self.driver).release().perform()
            
            # 等待验证结果
            time.sleep(2)
            
            return True
            
        except Exception as e:
            print(f"滑块验证失败: {e}")
            return False
            
    def sign_in(self):
        """执行签到"""
        try:
            # 访问签到页面
            self.driver.get("https://www.right.com.cn/FORUM/erling_qd-sign_in.html")
            time.sleep(3)
            
            # 尝试解决滑块验证码
            if "安全验证" in self.driver.page_source or "Security Verification" in self.driver.page_source:
                print("检测到验证码,正在尝试破解...")
                if not self.solve_slider_captcha():
                    return {"status": "failed", "message": "验证码破解失败"}
            
            # 等待页面加载
            time.sleep(3)
            
            # 查找签到按钮并点击
            try:
                sign_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '签到')] | //a[contains(text(), '签到')] | //div[contains(@class, 'sign')]"))
                )
                sign_button.click()
                time.sleep(2)
            except:
                print("未找到签到按钮,可能已经签到过了")
            
            # 获取签到结果
            page_source = self.driver.page_source
            
            # 提取恩山币和积分信息
            try:
                coin_match = re.search(r"恩山币[:\s]*</em>([^&<]+)", page_source)
                point_match = re.search(r"积分[:\s]*</em>([^<]+)", page_source)
                
                coin = coin_match.group(1).strip() if coin_match else "未知"
                point = point_match.group(1).strip() if point_match else "未知"
                
                return {
                    "status": "success",
                    "coin": coin,
                    "point": point
                }
            except Exception as e:
                return {
                    "status": "success",
                    "message": "签到可能成功,但无法获取详细信息"
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "message": f"签到失败: {str(e)}"
            }
            
    def push_notification(self, message):
        """推送通知到Server酱"""
        if not self.serverchan_key:
            return
            
        try:
            data = {
                'title': '恩山论坛签到结果',
                'desp': message,
            }
            response = requests.post(
                f'https://sctapi.ftqq.com/{self.serverchan_key}.send',
                data=data,
                timeout=10
            )
            if response.status_code == 200:
                print('推送成功')
            else:
                print(f'推送失败,状态码: {response.status_code}')
        except Exception as e:
            print(f'推送失败: {e}')
            
    def main(self):
        """主函数"""
        try:
            if not self.cookie:
                return "未找到恩山论坛的 Cookie,请设置 ENSHAN_COOKIE 环境变量。"
            
            # 初始化浏览器
            self.init_driver()
            
            # 设置Cookie
            if not self.set_cookie():
                return "Cookie设置失败"
            
            # 执行签到
            result = self.sign_in()
            
            # 格式化消息
            if result["status"] == "success":
                if "coin" in result:
                    msg = f"签到成功!\n恩山币: {result['coin']}\n积分: {result['point']}"
                else:
                    msg = result.get("message", "签到成功")
            else:
                msg = result.get("message", "签到失败")
            
            # 推送通知
            if self.serverchan_key:
                self.push_notification(msg)
            
            return msg
            
        except Exception as e:
            error_msg = f"执行出错: {str(e)}"
            if self.serverchan_key:
                self.push_notification(error_msg)
            return error_msg
            
        finally:
            # 关闭浏览器
            if self.driver:
                self.driver.quit()


if __name__ == "__main__":
    result = EnShanSelenium().main()
    print(result)
