"""
测试 Nansen API 的详细错误信息
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('NANSEN_API_KEY')
print(f"使用 API Key: {api_key[:10]}..." if api_key else "未找到 API Key")

# 测试不同的请求格式
tests = [
    {
        'name': '测试1: smart-money/holdings (基础)',
        'url': 'https://api.nansen.ai/api/v1/smart-money/holdings',
        'body': {
            'chains': ['ethereum'],
            'timeframe': '24h',
            'pagination': {
                'limit': 10,
                'offset': 0
            }
        }
    },
    {
        'name': '测试2: smart-money/holdings (无 pagination)',
        'url': 'https://api.nansen.ai/api/v1/smart-money/holdings',
        'body': {
            'chains': ['ethereum'],
            'timeframe': '24h'
        }
    },
    {
        'name': '测试3: token-screener',
        'url': 'https://api.nansen.ai/api/v1/token-screener',
        'body': {
            'chains': ['ethereum'],
            'timeframe': '24h',
            'pagination': {
                'limit': 10,
                'offset': 0
            }
        }
    }
]

headers = {
    'apikey': api_key,
    'Content-Type': 'application/json'
}

print("\n" + "="*60)
for test in tests:
    print(f"\n{test['name']}")
    print(f"URL: {test['url']}")
    print(f"Body: {json.dumps(test['body'], indent=2)}")
    print("-"*60)
    
    try:
        response = requests.post(
            test['url'],
            headers=headers,
            json=test['body'],
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 成功!")
            data = response.json()
            print(f"返回数据类型: {type(data)}")
            if isinstance(data, dict):
                print(f"字段: {list(data.keys())}")
                if 'data' in data:
                    print(f"数据条数: {len(data.get('data', []))}")
        else:
            print(f"❌ 失败")
            print(f"响应内容: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
    
    print("="*60)
