"""
SSL 诊断脚本 - 分析为什么浏览器能访问但 Python 不能
"""

import socket
import ssl
import logging
from urllib.parse import urlparse
import struct
import subprocess

logging.basicConfig(level=logging.INFO)

print("="*80)
print("SSL 诊断工具")
print("="*80)
print()

hostname = "m.manhuagui.com"
port = 443

# 1. DNS 解析
print("1. DNS 解析:")
try:
    import socket
    ip_address = socket.gethostbyname(hostname)
    print(f"   IP 地址: {ip_address}")
except Exception as e:
    print(f"   ❌ DNS 解析失败: {e}")
print()

# 2. TCP 连接测试
print("2. TCP 连接测试:")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((hostname, port))
    print(f"   ✅ TCP 连接成功")
    sock.close()
except Exception as e:
    print(f"   ❌ TCP 连接失败: {e}")
print()

# 3. SSL 握手测试 (各种配置）
print("3. SSL 握手测试:")

test_configs = [
    ("默认配置", ssl.create_default_context(), False, False),
    ("TLS 1.0", ssl.SSLContext(ssl.PROTOCOL_TLSv1_2), False, False),
    ("TLS 1.1", ssl.SSLContext(ssl.PROTOCOL_TLSv1_2), False, False),
    ("TLS 1.2", ssl.SSLContext(ssl.PROTOCOL_TLSv1_2), False, False),
    ("TLS 1.3", ssl.SSLContext(ssl.PROTOCOL_TLSv1_3), False, False),
    ("宽松 TLS 1.0", ssl.SSLContext(ssl.PROTOCOL_TLSv1), False, True),
    ("宽松 TLS 1.2", ssl.SSLContext(ssl.PROTOCOL_TLSv1_2), False, True),
]

for config_name, ctx, verify, loose in test_configs:
    try:
        print(f"   测试配置: {config_name}")
        
        # 配置 SSL
        if loose:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            ctx.set_ciphers('DEFAULT:@SECLEVEL=0')
        else:
            ctx.check_hostname = not verify
            ctx.verify_mode = ssl.CERT_NONE if not verify else ssl.CERT_REQUIRED
        
        # 创建 socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        
        # 包装为 SSL socket
        ssl_sock = ctx.wrap_socket(sock, server_hostname=hostname)
        
        # 连接
        ssl_sock.connect((hostname, port))
        
        print(f"     ✅ SSL 握手成功")
        print(f"     SSL 版本: {ssl_sock.version()}")
        print(f"     加密套件: {ssl_sock.cipher()}")
        print(f"     压缩: {ssl_sock.compression()}")
        
        # 发送 HTTP 请求
        http_request = f"GET / HTTP/1.1\r\nHost: {hostname}\r\nConnection: close\r\n\r\n"
        ssl_sock.send(http_request.encode())
        
        # 接收响应
        response = ssl_sock.recv(4096).decode('utf-8', errors='ignore')
        print(f"     HTTP 响应: {response[:100]}...")
        
        # 关闭连接
        ssl_sock.close()
        sock.close()
        
    except Exception as e:
        print(f"     ❌ 测试失败: {e}")
    
    print()

# 4. 使用 curl 测试
print("4. 使用 curl 测试:")
print("   测试各种协议:")

curl_commands = [
    ("HTTP", f"curl -s -o /dev/null -w '%{{http_code}}' --max-time 10 'http://{hostname}/'"),
    ("HTTPS", f"curl -s -o /dev/null -w '%{{http_code}}' --max-time 10 'https://{hostname}/'"),
    ("HTTPS (v1)", f"curl -s -o /dev/null -w '%{{http_code}}' --max-time 10 --http1.1 'https://{hostname}/'"),
    ("HTTPS (v1.0)", f"curl -s -o /dev/null -w '%{{http_code}}' --max-time 10 --tlsv1.0 'https://{hostname}/'"),
    ("HTTPS (v1.1)", f"curl -s -o /dev/null -w '%{{http_code}}' --max-time 10 --tlsv1.1 'https://{hostname}/'"),
    ("HTTPS (v1.2)", f"curl -s -o /dev/null -w '%{{http_code}}' --max-time 10 --tlsv1.2 'https://{hostname}/'"),
    ("HTTPS (v1.3)", f"curl -s -o /dev/null -w '%{{http_code}}' --max-time 10 --tlsv1.3 'https://{hostname}/'"),
]

for name, cmd in curl_commands:
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        http_code = result.stdout.strip()
        if http_code == "000":
            status = "❌ 失败"
        else:
            status = f"✅ {http_code}"
        print(f"   {name}: {status}")
    except subprocess.TimeoutExpired:
        print(f"   {name}: ❌ 超时")
    except Exception as e:
        print(f"   {name}: ❌ 错误: {e}")

print()

# 5. 使用 OpenSSL s_client 测试
print("5. 使用 OpenSSL s_client 测试:")

openssl_commands = [
    ("OpenSSL 默认", f"openssl s_client -connect {hostname}:443 -servername {hostname} </dev/null 2>&1 | grep -E '(New|Verify|Secure|ALERT)' | head -5"),
    ("OpenSSL TLS 1.0", f"openssl s_client -connect {hostname}:443 -servername {hostname} -tls1 </dev/null 2>&1 | grep -E '(New|Verify|Secure|ALERT)' | head -5"),
    ("OpenSSL TLS 1.1", f"openssl s_client -connect {hostname}:443 -servername {hostname} -tls1_1 </dev/null 2>&1 | grep -E '(New|Verify|Secure|ALERT)' | head -5"),
    ("OpenSSL TLS 1.2", f"openssl s_client -connect {hostname}:443 -servername {hostname} -tls1_2 </dev/null 2>&1 | grep -E '(New|Verify|Secure|ALERT)' | head -5"),
]

for name, cmd in openssl_commands:
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        if result.stdout:
            print(f"   {name}:")
            for line in result.stdout.strip().split('\n')[:5]:
                print(f"     {line}")
    except subprocess.TimeoutExpired:
        print(f"   {name}: ❌ 超时")
    except Exception as e:
        print(f"   {name}: ❌ 错误: {e}")

print()

# 6. 对比浏览器信息
print("6. 浏览器信息分析:")
print("   请检查浏览器的开发者工具:")
print("   - Network 标签")
print("   - 查看 TLS 版本")
print("   - 查看加密套件")
print("   - 查看证书信息")
print()
print("   建议:")
print("   - 在浏览器中访问 https://m.manhuagui.com/")
print("   - 打开开发者工具 (F12)")
print("   - 切换到 Network 标签")
print("   - 刷新页面")
print("   - 点击第一个请求")
print("   - 查看 Security 标签")
print("   - 记录 TLS 版本、加密套件、证书信息")
print()

# 7. 总结
print("="*80)
print("诊断总结")
print("="*80)
print()
print("可能的解决方案:")
print("1. 如果 TLS 1.2/1.3 可用但 TLS 1.0/1.1 不可用:")
print("   -> 需要强制使用 TLS 1.2/1.3")
print()
print("2. 如果所有协议都失败:")
print("   -> 可能是 IP 黑名单问题")
print("   -> 可能需要使用代理")
print("   -> 可能需要更换漫画网站")
print()
print("3. 如果特定加密套件失败:")
print("   -> 可以限制使用的加密套件")
print()
print("4. 建议:")
print("   - 浏览器可能使用了不同的 TLS 库（OpenSSL vs LibreSSL）")
print("   - 浏览器可能支持更灵活的 SSL/TLS 配置")
print("   - 可能需要使用更接近浏览器的库（如 Selenium）")
print()

print()
print("诊断完成！")
