# 恩山无线论坛自动签到脚本

## 问题说明

恩山论坛现在的签到流程增加了**滑动拼图验证码**,原有的简单HTTP请求方式已经无法完成签到。本项目提供了两种解决方案来应对这个问题。

## 验证码特征

- **验证码类型**: 滑动拼图验证码
- **触发时机**: 访问签到页面时自动弹出
- **验证要求**: 需要将拼图滑块拖动到正确位置

## 解决方案

### 方案一: Selenium版本 (推荐用于简单部署)

**优点:**
- 配置相对简单
- 兼容性好
- 社区资源丰富

**缺点:**
- 资源占用较大
- 速度相对较慢

**文件:** `enshan_selenium.py`

### 方案二: Playwright版本 (推荐用于生产环境)

**优点:**
- 性能更好,速度更快
- API更现代化
- 更稳定可靠
- 支持异步操作

**缺点:**
- 首次安装需要下载浏览器

**文件:** `enshan_playwright.py`

## 安装步骤

### 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 2. 安装浏览器驱动

#### Selenium方案:

**方式一: 自动安装 (推荐)**
```bash
pip install webdriver-manager
```

然后修改脚本,在初始化driver时使用:
```python
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

service = Service(ChromeDriverManager().install())
self.driver = webdriver.Chrome(service=service, options=chrome_options)
```

**方式二: 手动安装**
- 下载与Chrome版本匹配的ChromeDriver: https://chromedriver.chromium.org/
- 将chromedriver放到系统PATH中

#### Playwright方案:

```bash
playwright install chromium
```

## 配置说明

### 1. 获取Cookie

1. 使用浏览器登录恩山论坛: https://www.right.com.cn/FORUM/
2. 按F12打开开发者工具
3. 切换到"Network"(网络)标签
4. 刷新页面
5. 点击任意请求,在"Headers"中找到"Cookie"
6. 复制完整的Cookie字符串

### 2. 设置环境变量

**Linux/Mac:**
```bash
export ENSHAN_COOKIE="你的Cookie字符串"
export SERVERCHAN_KEY="你的Server酱Key(可选)"
```

**Windows:**
```cmd
set ENSHAN_COOKIE=你的Cookie字符串
set SERVERCHAN_KEY=你的Server酱Key(可选)
```

**或者在代码中直接设置:**
```python
# 在脚本开头添加
os.environ['ENSHAN_COOKIE'] = '你的Cookie字符串'
os.environ['SERVERCHAN_KEY'] = '你的Server酱Key'
```

### 3. Server酱推送配置(可选)

如果需要接收签到结果推送通知:

1. 访问 https://sct.ftqq.com/
2. 使用微信登录
3. 获取SendKey
4. 设置环境变量 `SERVERCHAN_KEY`

## 使用方法

### Selenium版本:

```bash
python enshan_selenium.py
```

### Playwright版本:

```bash
python enshan_playwright.py
```

## 定时任务配置

### Linux/Mac (使用crontab)

```bash
# 编辑crontab
crontab -e

# 添加定时任务 (每天早上8点执行)
0 8 * * * cd /path/to/script && /usr/bin/python3 enshan_playwright.py >> /var/log/enshan_sign.log 2>&1
```

### Windows (使用任务计划程序)

1. 打开"任务计划程序"
2. 创建基本任务
3. 设置触发器(每天)
4. 操作选择"启动程序"
5. 程序选择Python路径,参数填写脚本路径

### GitHub Actions (云端自动签到)

创建 `.github/workflows/enshan_sign.yml`:

```yaml
name: 恩山论坛自动签到

on:
  schedule:
    - cron: '0 0 * * *'  # 每天UTC时间0点(北京时间8点)
  workflow_dispatch:  # 支持手动触发

jobs:
  sign:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium
      
      - name: Run sign script
        env:
          ENSHAN_COOKIE: ${{ secrets.ENSHAN_COOKIE }}
          SERVERCHAN_KEY: ${{ secrets.SERVERCHAN_KEY }}
        run: python enshan_playwright.py
```

然后在GitHub仓库的Settings -> Secrets中添加:
- `ENSHAN_COOKIE`: 你的Cookie
- `SERVERCHAN_KEY`: 你的Server酱Key(可选)

## 注意事项

### 1. Cookie有效期

- Cookie会过期,通常有效期为1-2周
- 如果签到失败,首先检查Cookie是否过期
- 建议定期更新Cookie

### 2. 验证码破解成功率

- 滑动验证码破解不是100%成功
- 脚本会自动重试3次
- 如果多次失败,可能需要手动签到一次

### 3. IP限制

- 频繁访问可能触发IP限制
- 建议每天只运行一次
- 如使用云服务器,注意IP可能被标记

### 4. 浏览器资源占用

- 无头浏览器仍会占用一定内存
- 建议在内存充足的环境运行
- 可以在脚本执行完后自动清理

### 5. 反爬虫检测

- 网站可能更新反爬虫策略
- 如果脚本失效,需要更新破解逻辑
- 建议关注项目更新

## 故障排查

### 问题1: 找不到浏览器驱动

**解决方法:**
- Selenium: 安装webdriver-manager或手动下载ChromeDriver
- Playwright: 运行 `playwright install chromium`

### 问题2: Cookie无效

**解决方法:**
- 重新登录恩山论坛获取新的Cookie
- 确保Cookie格式正确,包含所有必要字段

### 问题3: 验证码无法破解

**解决方法:**
- 调整滑动距离参数(distance变量)
- 增加重试次数
- 检查页面元素选择器是否正确

### 问题4: 签到按钮找不到

**解决方法:**
- 检查页面是否加载完成
- 更新元素选择器
- 查看页面源码确认按钮ID或Class

### 问题5: 内存不足

**解决方法:**
- 使用headless模式(已默认启用)
- 减少浏览器窗口大小
- 确保脚本执行完后正确关闭浏览器

## 技术原理

### 滑动验证码破解流程

1. **检测验证码**: 识别页面中的滑动验证码元素
2. **计算距离**: 估算或计算滑块需要移动的距离
3. **生成轨迹**: 模拟人类滑动行为,生成加速-减速的轨迹
4. **执行滑动**: 按照轨迹移动鼠标并释放
5. **验证结果**: 检查是否通过验证

### 关键技术点

- **轨迹模拟**: 使用物理加速度模型模拟真实滑动
- **随机抖动**: 添加随机偏移避免被识别为机器人
- **延迟控制**: 合理的等待时间确保页面加载完成
- **元素定位**: 多种选择器策略提高兼容性

## 更新日志

### v2.0.0 (2024-11-21)
- ✨ 新增滑动验证码破解功能
- ✨ 提供Selenium和Playwright两种方案
- ✨ 优化滑动轨迹算法,提高成功率
- ✨ 增加自动重试机制
- 📝 完善文档和使用说明

### v1.0.0
- 基础HTTP请求签到(已失效)

## 免责声明

本项目仅供学习交流使用,请勿用于非法用途。使用本脚本产生的任何后果由使用者自行承担。

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request!

## 联系方式

如有问题,请在GitHub提交Issue。
