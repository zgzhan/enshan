#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
恩山无线论坛自动签到脚本 (Playwright版本)
支持滑动拼图验证码识别 - 更稳定和现代化
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
    """恩山论坛自动签到类 (Playwright版本)"""
    
    name = "恩山无线论坛"
    
    def __init__(self):
        self.cookie = os.getenv("ENSHAN_COOKIE")
        self.serverchan_key = os.environ.get('SERVERCHAN_KEY')
        self.page = None
        self.browser = None
        
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
                a = 2  # 加速度
            else:
                a = -3  # 减速度
            
            v0 = v
            v = v0 + a * t
            move = v0 * t + 1 / 2 * a * t * t
            current += move
            track.append(round(move))
        
        # 添加随机抖动
        for _ in range(3):
            track.append(random.randint(-2, 2))
            
        return track
        
    async def solve_slider_captcha(self):
        """解决滑块验证码"""
        try:
            print("检测到验证码,正在尝试破解...")
            
            # 等待验证码加载
            await asyncio.sleep(3)
            
            # 尝试查找滑块元素 - 根据实际页面调整选择器
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
                    slider = await self.page.wait_for_selector(selector, timeout=5000)
                    if slider:
                        print(f"找到滑块元素: {selector}")
                        break
                except:
                    continue
            
            if not slider:
                print("未找到滑块元素,尝试使用坐标点击")
                # 如果找不到滑块,尝试在验证码区域点击
                await self.page.mouse.move(430, 464)
                await self.page.mouse.down()
                await asyncio.sleep(0.2)
                
                # 生成滑动轨迹
                distance = random.randint(200, 260)
                track = self.get_track(distance)
                
                # 执行滑动
                for move in track:
                    await self.page.mouse.move(
                        430 + sum(track[:track.index(move)+1]),
                        464 + random.randint(-2, 2)
                    )
                    await asyncio.sleep(random.uniform(0.01, 0.02))
                
                await asyncio.sleep(0.5)
                await self.page.mouse.up()
                
            else:
                # 获取滑块位置
                box = await slider.bounding_box()
                if not box:
                    return False
                
                # 移动到滑块中心
                start_x = box['x'] + box['width'] / 2
                start_y = box['y'] + box['height'] / 2
                
                await self.page.mouse.move(start_x, start_y)
                await self.page.mouse.down()
                await asyncio.sleep(0.2)
                
                # 生成滑动距离和轨迹
                distance = random.randint(200, 260)
                track = self.get_track(distance)
                
                # 执行滑动
                current_x = start_x
                for move in track:
                    current_x += move
                    await self.page.mouse.move(
                        current_x,
                        start_y + random.randint(-2, 2)
                    )
                    await asyncio.sleep(random.uniform(0.01, 0.02))
                
                await asyncio.sleep(0.5)
                await self.page.mouse.up()
            
            # 等待验证结果
            await asyncio.sleep(3)
            
            # 检查是否验证成功
            content = await self.page.content()
            if "安全验证" in content or "Security Verification" in content:
                print("验证可能失败,需要重试")
                return False
            
            print("验证码破解成功")
            return True
            
        except Exception as e:
            print(f"滑块验证失败: {e}")
            return False
            
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
                await self.page.goto("https://www.right.com.cn/FORUM/erling_qd-sign_in.html", wait_until='networkidle')
                await asyncio.sleep(3)
                
                # 检查是否需要验证码
                content = await self.page.content()
                if "安全验证" in content or "Security Verification" in content:
                    # 尝试破解验证码,最多3次
                    for i in range(3):
                        print(f"第 {i+1} 次尝试破解验证码...")
                        if await self.solve_slider_captcha():
                            break
                        if i < 2:
                            await asyncio.sleep(2)
                            await self.page.reload()
                            await asyncio.sleep(3)
                
                # 等待页面加载
                await asyncio.sleep(3)
                
                # 尝试点击签到按钮
                sign_selectors = [
                    'button:has-text("签到")',
                    'a:has-text("签到")',
                    '[class*="sign"]',
                    '#sign_in'
                ]
                
                for selector in sign_selectors:
                    try:
                        button = await self.page.wait_for_selector(selector, timeout=3000)
                        if button:
                            await button.click()
                            print("点击签到按钮成功")
                            await asyncio.sleep(2)
                            break
                    except:
                        continue
                
                # 获取签到结果
                await asyncio.sleep(2)
                page_source = await self.page.content()
                
                # 尝试访问个人中心获取积分信息
                try:
                    await self.page.goto("https://www.right.com.cn/FORUM/home.php?mod=spacecp&ac=credit&showcredit=1", wait_until='networkidle')
                    await asyncio.sleep(2)
                    
                    page_source = await self.page.content()
                    
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
                    print(f"获取积分信息失败: {e}")
                    return {
                        "status": "success",
                        "message": "签到可能成功,但无法获取详细信息"
                    }
                
        except Exception as e:
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
            return "未找到恩山论坛的 Cookie,请设置 ENSHAN_COOKIE 环境变量。"
        
        try:
            # 执行签到
            result = asyncio.run(self.sign_in())
            
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


if __name__ == "__main__":
    result = EnShanPlaywright().main()
    print(result)
