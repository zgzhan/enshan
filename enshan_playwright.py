# 请将以下内容保存为 enshan_playwright.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
恩山无线论坛自动签到脚本 (Playwright最终优化版 - 增强滑块真实性)
"""

import os
import re
import time
import random
import asyncio
import requests
import urllib3
from playwright.async_api import async_playwright

urllib3.disable_warnings()


class EnShanPlaywright:
    """恩山论坛自动签到类 (Playwright最终优化版)"""
    
    name = "恩山无线论坛"
    
    def __init__(self):
        # 从环境变量获取配置
        self.cookie = os.getenv("ENSHAN_COOKIE")
        self.serverchan_key = os.environ.get('SERVERCHAN_KEY')
        self.page = None
        self.browser = None
        self.screenshot_path = "final_screenshot.png" # 截图保存路径
        
    def parse_cookies(self):
        """解析Cookie字符串为列表"""
        cookies = []
        if not self.cookie:
            return cookies
            
        for item in self.cookie.split(';'):
            item = item.strip()
            if '=' in item:
                name, value = item.split('=', 1)
                cookies.append({
                    'name': name.strip(),
                    'value': value.strip(),
                    'domain': '.right.com.cn',
                    'path': '/'
                })
        
        return cookies
        
    def get_track(self, distance):
        """
        生成模拟人类滑动的轨迹 (增强随机性)
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
                a = random.uniform(1.5, 2.5)  # 加速度增加随机性
            else:
                a = random.uniform(-3.5, -2.5)  # 减速度增加随机性
            
            v0 = v
            v = v0 + a * t
            move = v0 * t + 1 / 2 * a * t * t
            current += move
            track.append(round(move))
        
        # 增加回退和随机抖动
        track.append(random.randint(-5, -1)) # 模拟回退
        for _ in range(random.randint(3, 5)):
            track.append(random.randint(-2, 2))
            
        return track
        
    async def solve_slider_captcha(self):
        """解决滑块验证码"""
        try:
            print("检测到验证码,正在尝试破解...")
            
            await asyncio.sleep(3)
            
            slider_selectors = [
                '[class*="slider"]',
                '[class*="slide-verify"]',
                '.slide-verify-slider',
                '[class*="verify-slider"]',
                'div[style*="cursor"]'
            ]
            
            slider = None
            for selector in slider_selectors:
                try:
                    slider = await self.page.query_selector(selector)
                    if slider:
                        print(f"找到滑块元素: {selector}")
                        break
                except:
                    continue
            
            start_x = 430
            start_y = 464
            
            if slider:
                box = await slider.bounding_box()
                if box:
                    start_x = box['x'] + box['width'] / 2
                    start_y = box['y'] + box['height'] / 2
            
            await self.page.mouse.move(start_x, start_y)
            await self.page.mouse.down()
            await asyncio.sleep(random.uniform(0.1, 0.3)) # 增加按下延迟
            
            distance = random.randint(220, 260)
            track = self.get_track(distance)
            
            current_x = start_x
            for move in track:
                current_x += move
                await self.page.mouse.move(
                    current_x,
                    start_y + random.randint(-3, 3) # 增加Y轴抖动
                )
                await asyncio.sleep(random.uniform(0.01, 0.05)) # 增加移动延迟
            
            await asyncio.sleep(random.uniform(0.3, 0.7)) # 增加释放延迟
            await self.page.mouse.up()
            
            await asyncio.sleep(3)
            
            content = await self.page.content()
            if "安全验证" in content or "Security Verification" in content:
                print("验证可能失败,需要重试")
                return False
            
            print("验证码破解成功")
            return True
            
        except Exception as e:
            print(f"滑块验证失败: {e}")
            return False
            
    async def get_credit_info(self):
        """访问个人中心获取积分信息"""
        try:
            print("正在访问个人中心获取积分信息...")
            await self.page.goto("https://www.right.com.cn/FORUM/home.php?mod=spacecp&ac=credit&showcredit=1", timeout=60000, wait_until='networkidle' )
            await asyncio.sleep(3)
            
            page_source = await self.page.content()
            
            coin_match = re.search(r"恩山币[:\s]*</em>([^&<]+)", page_source)
            point_match = re.search(r"积分[:\s]*</em>([^<]+)", page_source)
            
            coin = coin_match.group(1).strip() if coin_match else "未知"
            point = point_match.group(1).strip() if point_match else "未知"
            
            return coin, point
        except Exception as e:
            print(f"获取积分信息失败: {e}")
            return "未知", "未知"
            
    async def sign_in(self):
        """执行签到"""
        try:
            async with async_playwright() as p:
                # 启动浏览器
                self.browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-blink-features=AutomationControlled'
                    ]
                )
                
                # 创建上下文
                context = await self.browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                # 设置Cookie
                cookies = self.parse_cookies()
                if cookies:
                    await context.add_cookies(cookies)
                
                # 创建页面
                self.page = await context.new_page()
                
                # 访问签到页面
                print("正在访问签到页面...")
                await self.page.goto("https://www.right.com.cn/FORUM/erling_qd-sign_in.html", wait_until='networkidle' )
                await asyncio.sleep(3)
                
                # 检查是否需要验证码
                content = await self.page.content()
                if "安全验证" in content or "Security Verification" in content:
                    for i in range(3):
                        print(f"第 {i+1} 次尝试破解验证码...")
                        if await self.solve_slider_captcha():
                            break
                        if i < 2:
                            await asyncio.sleep(2)
                            await self.page.reload()
                            await asyncio.sleep(3)
                
                await asyncio.sleep(3)
                
                # 检查签到前页面上是否有“签到”按钮
                sign_button_selector = 'button:has-text("Check in now")'
                initial_button = await self.page.query_selector(sign_button_selector)
                
                # 检查是否已经签到
                checked_in_today = await self.page.query_selector('div:has-text("Checked in today")')
                
                if checked_in_today:
                    print("页面显示已签到 (Checked in today)，判断为已签到。")
                    sign_status = "success"
                    message = "已签到 (页面显示已签到)"
                elif not initial_button:
                    print("页面上没有签到按钮，判断为已签到。")
                    sign_status = "success"
                    message = "已签到 (页面无签到按钮)"
                else:
                    # 尝试点击签到按钮
                    print("找到签到按钮，尝试点击...")
                    await initial_button.click()
                    print("点击签到按钮成功")
                    
                    # 增加等待时间，等待签到结果弹出或页面跳转
                    await asyncio.sleep(5) 
                    
                    # 再次检查页面是否显示“Checked in today”
                    await self.page.reload()
                    await asyncio.sleep(3)
                    
                    final_checked_in = await self.page.query_selector('div:has-text("Checked in today")')
                    
                    if final_checked_in:
                        print("签到后页面显示 'Checked in today'，判断签到成功。")
                        sign_status = "success"
                        message = "签到成功 (页面显示已签到)"
                    else:
                        print("签到后页面未显示 'Checked in today'，判断签到失败。")
                        sign_status = "failed"
                        message = "签到失败 (页面未显示已签到)"
                
                # 强制截图，无论成功还是失败
                await self.page.screenshot(path=self.screenshot_path)
                print(f"已保存最终页面截图到 {self.screenshot_path}")
                
                # 尝试获取积分信息 (不再依赖它判断成功)
                coin, point = await self.get_credit_info()
                
                return {
                    "status": sign_status,
                    "coin": coin,
                    "point": point,
                    "message": message
                }
                
        except Exception as e:
            if self.page:
                await self.page.screenshot(path=self.screenshot_path)
                print(f"发生异常，已保存截图到 {self.screenshot_path}")
            
            return {
                "status": "failed",
                "message": f"签到失败: {str(e)}"
            }
        finally:
            if self.browser:
                await self.browser.close()
                
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
        if not self.cookie:
            print("未找到恩山论坛的 Cookie,请设置 ENSHAN_COOKIE 环境变量。")
            return
        
        try:
            result = asyncio.run(self.sign_in())
            
            # 格式化消息
            if result["status"] == "success":
                msg = f"{result['message']}\n恩山币: {result.get('coin', '未知')}\n积分: {result.get('point', '未知')}"
            else:
                msg = result.get("message", "签到失败")
            
            # 推送通知
            if self.serverchan_key:
                self.push_notification(msg)
            
            # 打印结果，供GitHub Actions日志使用
            print(f"::set-output name=status::{result['status']}")
            print(f"::set-output name=message::{msg}")
            
            # 强制输出截图路径，无论成功还是失败
            if os.path.exists(self.screenshot_path):
                print(f"::set-output name=screenshot_path::{self.screenshot_path}")
            
            print(msg)
            
        except Exception as e:
            error_msg = f"执行出错: {str(e)}"
            if self.serverchan_key:
                self.push_notification(error_msg)
            print(error_msg)


if __name__ == "__main__":
    EnShanPlaywright().main()
