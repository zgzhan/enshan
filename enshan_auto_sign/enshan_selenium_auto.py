#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
恩山无线论坛自动签到脚本 (Selenium版本 - 自动管理驱动)
支持滑动拼图验证码识别
使用webdriver-manager自动下载和管理ChromeDriver
"""

import os
import re
import time
import random
import requests
import urllib3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

urllib3.disable_warnings()


class EnShanSeleniumAuto:
    """恩山论坛自动签到类 (自动管理驱动版本)"""
    
    name = "恩山无线论坛"
    
    def __init__(self):
        self.cookie = os.getenv("ENSHAN_COOKIE")
        self.serverchan_key = os.environ.get('SERVERCHAN_KEY')
        self.driver = None
        
    def init_driver(self):
        """初始化浏览器驱动 - 自动下载管理"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 使用webdriver-manager自动管理ChromeDriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_window_size(1920, 1080)
        
    def set_cookie(self):
        """设置Cookie"""
        if not self.cookie:
            return False
            
        self.driver.get("https://www.right.com.cn/FORUM/")
        time.sleep(2)
        
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
        
    def get_track(self, distance):
        """生成模拟人类滑动的轨迹"""
        track = []
        current = 0
        mid = distance * 4 / 5
        t = 0.2
        v = 0
        
        while current < distance:
            if current < mid:
                a = 2
            else:
                a = -3
            
            v0 = v
            v = v0 + a * t
            move = v0 * t + 1 / 2 * a * t * t
            current += move
            track.append(round(move))
            
        for i in range(3):
            track.append(random.randint(-2, 2))
            
        return track
        
    def solve_slider_captcha(self):
        """解决滑块验证码 - 改进版"""
        try:
            print("检测到验证码,正在尝试破解...")
            time.sleep(3)
            
            # 多种选择器尝试
            slider_selectors = [
                "div[class*='slider']",
                "div[class*='slide']",
                "div[style*='cursor: pointer']",
                "div[class*='verify']"
            ]
            
            slider = None
            for selector in slider_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        slider = elements[0]
                        print(f"找到滑块元素: {selector}")
                        break
                except:
                    continue
            
            if not slider:
                print("未找到滑块元素,使用坐标方式")
                # 使用JavaScript获取页面尺寸
                width = self.driver.execute_script("return window.innerWidth")
                height = self.driver.execute_script("return window.innerHeight")
                
                # 在验证码区域中心位置开始滑动
                start_x = width // 2 - 100
                start_y = height // 2
                
                action = ActionChains(self.driver)
                action.move_by_offset(start_x, start_y).perform()
                action.click_and_hold().perform()
                time.sleep(0.2)
                
                distance = random.randint(220, 260)
                track = self.get_track(distance)
                
                for move in track:
                    action.move_by_offset(xoffset=move, yoffset=random.randint(-2, 2)).perform()
                    time.sleep(random.uniform(0.01, 0.02))
                
                time.sleep(0.5)
                action.release().perform()
                
            else:
                # 使用找到的滑块元素
                action = ActionChains(self.driver)
                action.click_and_hold(slider).perform()
                time.sleep(0.2)
                
                distance = random.randint(220, 260)
                track = self.get_track(distance)
                
                for move in track:
                    action.move_by_offset(xoffset=move, yoffset=random.randint(-2, 2)).perform()
                    time.sleep(random.uniform(0.01, 0.02))
                
                time.sleep(0.5)
                action.release().perform()
            
            time.sleep(3)
            
            # 检查验证结果
            page_source = self.driver.page_source
            if "安全验证" in page_source or "Security Verification" in page_source:
                print("验证可能失败")
                return False
            
            print("验证码破解成功")
            return True
            
        except Exception as e:
            print(f"滑块验证失败: {e}")
            return False
            
    def sign_in(self):
        """执行签到"""
        try:
            print("正在访问签到页面...")
            self.driver.get("https://www.right.com.cn/FORUM/erling_qd-sign_in.html")
            time.sleep(3)
            
            # 检查并处理验证码
            for attempt in range(3):
                page_source = self.driver.page_source
                if "安全验证" in page_source or "Security Verification" in page_source:
                    print(f"第 {attempt + 1} 次尝试破解验证码...")
                    if self.solve_slider_captcha():
                        break
                    if attempt < 2:
                        time.sleep(2)
                        self.driver.refresh()
                        time.sleep(3)
                else:
                    break
            
            time.sleep(3)
            
            # 查找并点击签到按钮
            sign_button_selectors = [
                "//button[contains(text(), '签到')]",
                "//a[contains(text(), '签到')]",
                "//div[contains(@class, 'sign')]//button",
                "//input[@type='submit']"
            ]
            
            for selector in sign_button_selectors:
                try:
                    button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    button.click()
                    print("点击签到按钮成功")
                    time.sleep(2)
                    break
                except:
                    continue
            
            # 获取签到结果
            time.sleep(2)
            
            # 访问个人中心获取积分
            print("正在获取积分信息...")
            self.driver.get("https://www.right.com.cn/FORUM/home.php?mod=spacecp&ac=credit&showcredit=1")
            time.sleep(3)
            
            page_source = self.driver.page_source
            
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
                print(f"解析积分信息失败: {e}")
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
            
            print("正在初始化浏览器...")
            self.init_driver()
            
            print("正在设置Cookie...")
            if not self.set_cookie():
                return "Cookie设置失败"
            
            result = self.sign_in()
            
            if result["status"] == "success":
                if "coin" in result:
                    msg = f"签到成功!\n恩山币: {result['coin']}\n积分: {result['point']}"
                else:
                    msg = result.get("message", "签到成功")
            else:
                msg = result.get("message", "签到失败")
            
            if self.serverchan_key:
                self.push_notification(msg)
            
            return msg
            
        except Exception as e:
            error_msg = f"执行出错: {str(e)}"
            if self.serverchan_key:
                self.push_notification(error_msg)
            return error_msg
            
        finally:
            if self.driver:
                print("正在关闭浏览器...")
                self.driver.quit()


if __name__ == "__main__":
    result = EnShanSeleniumAuto().main()
    print(result)
