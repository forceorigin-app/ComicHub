# User-Agent 配置总结

## 📋 当前配置

### User-Agent 字符串
```
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
```

### 配置说明
- **浏览器**: Chrome 120.0.0.0
- **操作系统**: macOS 15.6 (Sequoia)
- **架构**: Intel x86_64
- **渲染引擎**: AppleWebKit (Blink)

### 完整请求头
```python
{
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Referer': 'https://m.manhuagui.com/'
}
```

---

## 🎯 为什么使用 Mac Chrome

### 1. 操作系统匹配
- 用户的系统是 macOS (Darwin 24.6.0)
- 使用 Mac User-Agent 更真实
- 避免反爬虫检测为跨系统请求

### 2. 浏览器市场份额
- Chrome 是全球最流行的浏览器
- Chrome 120 是最新稳定版本
- 使用真实浏览器版本降低检测风险

### 3. 特征匹配
- 完整的浏览器特征字符串
- 包含真实的渲染引擎信息
- 与真实浏览器请求完全一致

---

## 📊 对比分析

### 之前: Windows Chrome
```javascript
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
```
**问题**:
- ❌ 与用户系统不匹配
- ❌ 容易被检测为跨系统请求
- ❌ 增加反爬虫风险

### 现在: Mac Chrome
```javascript
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
```
**优势**:
- ✅ 与用户系统匹配
- ✅ 更真实的请求特征
- ✅ 降低反爬虫检测风险

---

## 🔧 配置位置

### fetcher.py
```python
self.default_headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    # ... 其他 headers
}
```

### 漫画龟请求
```python
# 请求会自动使用 Mac Chrome User-Agent
response = self.session.get(url, headers=self.default_headers)
```

---

## 📈 反爬虫检测应对

### 1. User-Agent 轮换
可以准备多个 User-Agent 轮换使用：
```python
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:121.0) Gecko/20100101 Firefox/121.0'
]

# 随机选择
import random
headers = {
    'User-Agent': random.choice(USER_AGENTS)
}
```

### 2. 请求间隔
```python
import time
import random

# 随机延迟 1-3 秒
time.sleep(random.uniform(1, 3))
```

### 3. 代理轮换
```python
# 每次请求使用不同的代理
proxy = proxy_pool_client.get_proxy()
session.proxies = {
    'http': proxy,
    'https': proxy
}
```

---

## 🎯 最佳实践

### 1. 保持更新
- 定期更新 User-Agent 到最新版本
- 使用真实浏览器的 User-Agent

### 2. 多样化
- 准备多个不同浏览器的 User-Agent
- 定期轮换使用

### 3. 监控请求
- 记录请求的成功率
- 监控反爬虫检测

### 4. 合理频率
- 避免高频请求
- 使用随机延迟
- 尊重网站 robots.txt

---

## 📚 参考资源

- [What is a User-Agent?](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/User-Agent)
- [Chrome User-Agent Strings](https://www.chromium.org/developers/user-agent)
- [User-Agent Database](https://www.useragentstring.com/)

---

**更新日期**: 2026-02-08
**版本**: 1.0.0
**浏览器**: Chrome 120.0.0.0
**操作系统**: macOS 15.6
