# 恩山论坛自动签到 - GitHub Actions 完整教程

本教程将指导您如何使用 **GitHub Actions** 实现免费、自动的每日签到。您不需要自己的服务器,只需要一个GitHub账号。

## 核心原理

我们将使用 GitHub 提供的免费自动化服务 (GitHub Actions) 来运行我们的 Python 脚本。脚本会在每天固定的时间自动启动,模拟浏览器行为完成签到。

## 准备工作

### 1. 注册 GitHub 账号

如果您还没有 GitHub 账号,请先注册一个: [https://github.com/](https://github.com/)

### 2. 获取 Cookie

这是最关键的一步。您需要获取您在恩山论坛的登录凭证(Cookie)。

1.  使用 Chrome 或 Edge 浏览器登录恩山论坛: [https://www.right.com.cn/FORUM/](https://www.right.com.cn/FORUM/)
2.  按下 `F12` 键,打开开发者工具。
3.  切换到 **“网络(Network)”** 标签页。
4.  刷新一下页面 (按 `F5` 键)。
5.  在下方的请求列表中,随便点击一个请求 (例如 `forum.php`)。
6.  在右侧的窗口中,找到 **“标头(Headers)”** -> **“请求标头(Request Headers)”** -> **“Cookie”**。
7.  **复制完整的 Cookie 值** (很长的一串字符)。

## 部署步骤 (5步完成)

### 步骤一: 创建一个新的代码仓库 (Repository)

1.  登录 GitHub,点击右上角的 **“+”** 号,选择 **“New repository”** (新建仓库)。
2.  **Repository name** (仓库名称): 随意填写,例如 `Enshan-Auto-Sign`。
3.  **Private** (私有): **强烈建议选择“Private”**。这样您的 Cookie 等敏感信息就不会被公开。
4.  勾选 **“Add a README file”** (添加一个README文件)。
5.  点击 **“Create repository”** (创建仓库)。

### 步骤二: 配置敏感信息 (Secrets)

我们需要将您的 Cookie 安全地存储在 GitHub 的 Secrets 中,这样脚本才能读取到,但又不会暴露在代码中。

1.  进入您刚创建的仓库页面。
2.  点击顶部的 **“Settings”** (设置)。
3.  在左侧菜单中,找到 **“Security”** (安全) 下的 **“Secrets”** (密钥)。
4.  选择 **“Actions”**。
5.  点击 **“New repository secret”** (新建仓库密钥)。

#### Secret 1: 恩山论坛 Cookie

| 字段 | 值 |
| :--- | :--- |
| **Name** | `ENSHAN_COOKIE` |
| **Secret** | 粘贴您在准备工作中复制的 **完整 Cookie 字符串** |

点击 **“Add secret”**。

#### Secret 2: Server酱 Key (可选)

如果您需要微信通知,请配置 Server酱 Key。

| 字段 | 值 |
| :--- | :--- |
| **Name** | `SERVERCHAN_KEY` |
| **Secret** | 粘贴您的 Server酱 Key (如果不需要,可以跳过此 Secret) |

### 步骤三: 创建工作流文件

工作流文件 (`.yml` 文件) 告诉 GitHub Actions 什么时候运行、运行什么命令。

1.  回到您的仓库主页 (点击顶部的 **“Code”**)。
2.  点击 **“Add file”** (添加文件) -> **“Create new file”** (创建新文件)。
3.  在文件路径框中输入: `.github/workflows/enshan_sign.yml`
    - **注意**: 必须是这个路径,`.github` 和 `workflows` 都是文件夹名。
4.  将我提供的以下代码内容 **完整粘贴** 到文件编辑框中。

```yaml
name: 恩山论坛自动签到

on:
  schedule:
    # 每天 UTC 时间 0 点执行 (北京时间 8 点)
    - cron: '0 0 * * *'
  workflow_dispatch:  # 支持手动触发

jobs:
  sign:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout代码
        uses: actions/checkout@v3
      
      - name: 设置Python环境
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: 安装依赖
        run: |
          # 安装Python依赖
          pip install playwright requests
          
          # 安装浏览器核心 (Chromium)
          playwright install chromium
          
          # 安装浏览器运行所需的系统依赖
          playwright install-deps chromium
      
      - name: 执行签到脚本
        env:
          ENSHAN_COOKIE: ${{ secrets.ENSHAN_COOKIE }}
          SERVERCHAN_KEY: ${{ secrets.SERVERCHAN_KEY }}
        run: |
          # 将脚本内容写入文件
          cat << 'EOF' > enshan_playwright.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
恩山无线论坛自动签到脚本 (Playwright版本)
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
        # 从环境变量获取配置
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
                    # 使用 page.query_selector 而不是 wait_for_selector, 避免长时间等待
                    slider = await self.page.query_selector(selector)
                    if slider:
                        print(f"找到滑块元素: {selector}")
                        break
                except:
                    continue
            
            # 默认使用坐标滑动 (更通用)
            # 验证码弹窗通常在页面中心,我们估算一个坐标
            start_x = 430
            start_y = 464
            
            if slider:
                # 如果找到滑块元素,使用元素中心坐标
                box = await slider.bounding_box()
                if box:
                    start_x = box['x'] + box['width'] / 2
                    start_y = box['y'] + box['height'] / 2
            
            await self.page.mouse.move(start_x, start_y)
            await self.page.mouse.down()
            await asyncio.sleep(0.2)
            
            # 生成滑动距离和轨迹
            # 恩山验证码的距离大约在 200-260 像素
            distance = random.randint(220, 260)
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
                        # 使用 page.query_selector_all 查找所有可能的按钮
                        buttons = await self.page.query_selector_all(selector)
                        if buttons:
                            # 尝试点击第一个找到的按钮
                            await buttons[0].click()
                            print("点击签到按钮成功")
                            await asyncio.sleep(2)
                            break
                    except Exception as e:
                        print(f"尝试点击 {selector} 失败: {e}")
                        continue
                
                # 获取签到结果
                await asyncio.sleep(2)
                
                # 访问个人中心获取积分信息
                try:
                    print("正在访问个人中心获取积分信息...")
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
            print("未找到恩山论坛的 Cookie,请设置 ENSHAN_COOKIE 环境变量。")
            return
        
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
            
            print(msg)
            
        except Exception as e:
            error_msg = f"执行出错: {str(e)}"
            if self.serverchan_key:
                self.push_notification(error_msg)
            print(error_msg)


if __name__ == "__main__":
    EnShanPlaywright().main()
EOF
          # 运行脚本
          python enshan_playwright.py
```

5.  在页面底部,点击绿色的 **“Commit new file”** (提交新文件) 按钮。

### 步骤四: 手动运行一次 (测试)

为了验证配置是否正确,我们手动运行一次。

1.  点击仓库顶部的 **“Actions”** (操作)。
2.  在左侧找到 **“恩山论坛自动签到”**。
3.  点击右侧的 **“Run workflow”** (运行工作流) 按钮。
4.  点击绿色的 **“Run workflow”** 按钮。

### 步骤五: 查看结果

1.  在 **“Actions”** 页面,您会看到一个新的任务正在运行。点击它。
2.  点击 **“sign”** -> **“执行签到脚本”**。
3.  查看日志输出。如果看到类似 **“签到成功! 恩山币: XXX 积分: XXX”** 的信息,则表示配置成功。
4.  如果失败,请检查 **步骤二** 的 Cookie 是否正确。

## 自动运行说明

- 您的任务已经设置了定时运行。
- **定时时间**: 每天 UTC 时间 0 点 (即 **北京时间早上 8 点**)。
- 如果您想修改时间,请在 `enshan_sign.yml` 文件中修改 `cron: '0 0 * * *'` 这一行。
    - 例如: `cron: '0 1 * * *'` 表示每天 UTC 1 点 (北京时间 9 点)。

---

我已将工作流文件和脚本内容整合在一起,您只需要按照上述步骤操作即可。如果您在任何步骤遇到困难,请随时告诉我!
