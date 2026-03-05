"""
测试 Nansen Token Screener 各时间范围的数据返回情况
当前北京时间: 2026-03-05 10:24 CST
"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests, os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('NANSEN_API_KEY')
if not api_key:
    print("❌ 未找到 NANSEN_API_KEY")
    sys.exit(1)

print(f"✅ API Key: {api_key[:8]}...")

headers = {'apikey': api_key, 'Content-Type': 'application/json'}
BASE = 'https://api.nansen.ai/api/v1/token-screener'

# 测试所有可能的时间段
timeframes = ['5m', '10m', '15m', '30m', '1h', '2h', '3h', '4h', '6h', '12h', '24h']
chains = ['ethereum', 'solana', 'base']

print(f"\n测试链: {chains}")
print("="*70)

for tf in timeframes:
    body = {
        'chains': chains,
        'timeframe': tf,
        'pagination': {'limit': 10, 'offset': 0},
        'filters': {'only_smart_money': True},
        'sort': [{'field': 'netflow', 'direction': 'DESC'}]
    }
    try:
        r = requests.post(BASE, headers=headers, json=body, timeout=15)
        if r.status_code == 200:
            resp = r.json()
            data = resp.get('data', [])
            pos = [t for t in data if t.get('netflow', 0) > 0]
            neg = [t for t in data if t.get('netflow', 0) < 0]
            zero = [t for t in data if t.get('netflow', 0) == 0]
            
            status = "✅"
            print(f"  {tf:6s} → {status} 200 | 总计{len(data)}条 | 正向净流入:{len(pos)} | 负向:{len(neg)} | 零:{len(zero)}")
            
            # 显示第一条数据的详细信息
            if data:
                first = data[0]
                netflow = first.get('netflow', 'N/A')
                symbol = first.get('symbol', first.get('token_symbol', 'N/A'))
                traders = first.get('nof_traders', first.get('smartMoneyTraders', 'N/A'))
                print(f"         第1条: symbol={symbol}, netflow={netflow}, traders={traders}")
            
            if not data:
                print(f"         ⚠️  data 为空数组，完整响应键: {list(resp.keys())}")
        elif r.status_code == 422:
            print(f"  {tf:6s} → ❌ 422 (不支持此时间段) | {r.text[:120]}")
        else:
            print(f"  {tf:6s} → ❌ {r.status_code} | {r.text[:120]}")
    except Exception as e:
        print(f"  {tf:6s} → ❌ 异常: {str(e)}")

print("\n" + "="*70)
print("测试完成")
print("\n--- 无过滤测试 10m (不加 only_smart_money 过滤) ---")
body_nofilter = {
    'chains': chains,
    'timeframe': '10m',
    'pagination': {'limit': 5, 'offset': 0},
    'sort': [{'field': 'netflow', 'direction': 'DESC'}]
}
r2 = requests.post(BASE, headers=headers, json=body_nofilter, timeout=15)
print(f"状态码: {r2.status_code}")
if r2.status_code == 200:
    data2 = r2.json().get('data', [])
    print(f"返回 {len(data2)} 条 (无过滤)")
    for t in data2[:3]:
        print(f"  symbol={t.get('symbol','?')}, netflow={t.get('netflow','?')}, chain={t.get('chain','?')}")
else:
    print(r2.text[:200])
