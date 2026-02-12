"""
测试 Nansen API 连接和数据获取
快速诊断脚本
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 测试配置
print("=" * 50)
print("测试 Nansen API 配置")
print("=" * 50)

api_key = os.getenv('NANSEN_API_KEY')
if api_key:
    print(f"✅ NANSEN_API_KEY: {api_key[:10]}..." if len(api_key) > 10 else f"✅ NANSEN_API_KEY: {api_key}")
else:
    print("❌ NANSEN_API_KEY 未设置")
    exit(1)

# 测试 API 连接
print("\n" + "=" * 50)
print("测试 API 连接")
print("=" * 50)

import requests

try:
    # 简单测试 - 尝试调用一个基础端点
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    # 测试端点 - 获取 Ethereum 上的智能资金数据
    test_url = "https://api.nansen.ai/v1/smart-money/token-balances"
    test_params = {
        'chain': 'ethereum',
        'limit': 5
    }
    
    print(f"\n📡 正在测试 API 端点: {test_url}")
    print(f"   参数: chain=ethereum, limit=5")
    
    response = requests.get(
        test_url,
        headers=headers,
        params=test_params,
        timeout=30
    )
    
    print(f"\n📊 响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ API 连接成功！")
        print(f"\n返回的数据结构:")
        print(f"  - 数据类型: {type(data)}")
        if isinstance(data, dict):
            print(f"  - 字段: {list(data.keys())}")
            if 'data' in data:
                print(f"  - 数据条数: {len(data['data'])}")
                if data['data']:
                    print(f"\n示例数据（第一条）:")
                    print(f"  {data['data'][0]}")
                else:
                    print("  ⚠️ 数据列表为空")
        print(f"\n完整响应:")
        import json
        print(json.dumps(data, indent=2, ensure_ascii=False)[:500] + "...")
    elif response.status_code == 401:
        print("❌ API Key 无效或未授权")
        print(f"   响应: {response.text}")
    elif response.status_code == 429:
        print("❌ API 请求超过限制（Too Many Requests）")
        print(f"   响应: {response.text}")
    else:
        print(f"❌ API 请求失败")
        print(f"   响应: {response.text}")
        
except requests.exceptions.Timeout:
    print("❌ 请求超时")
except requests.exceptions.RequestException as e:
    print(f"❌ 请求错误: {str(e)}")
except Exception as e:
    print(f"❌ 未知错误: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("测试完成")
print("=" * 50)
