"""
快速测试哪些 timeframe 被 Nansen Token Screener 支持
"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests, os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('NANSEN_API_KEY')
headers = {'apikey': api_key, 'Content-Type': 'application/json'}
BASE = 'https://api.nansen.ai/api/v1/token-screener'

timeframes = ['5m', '10m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '24h']
chains = ['ethereum']

print("测试各时间段支持情况:")
print("="*60)

for tf in timeframes:
    body = {
        'chains': chains,
        'timeframe': tf,
        'pagination': {'limit': 5, 'offset': 0},
        'filters': {'only_smart_money': True},
        'sort': [{'field': 'netflow', 'direction': 'DESC'}]
    }
    r = requests.post(BASE, headers=headers, json=body, timeout=15)
    if r.status_code == 200:
        data = r.json().get('data', [])
        # 检查拿到多少正向 netflow
        pos = [t for t in data if t.get('netflow', 0) > 0]
        print(f"  {tf:6s} → ✅ 200  | {len(data)} 条数据，{len(pos)} 条正向净流入")
        if data and tf in ['10m', '1h', '6h']:
            print(f"          字段示例: netflow={data[0].get('netflow')}, nof_traders={data[0].get('nof_traders')}")
    else:
        print(f"  {tf:6s} → ❌ {r.status_code} | {r.text[:80]}")
