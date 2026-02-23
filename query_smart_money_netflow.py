"""
过去6小时 聪明钱 netflow > $5000 的币种 (ETH/BASE/SOL)
并标出聪明钱买入数量
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('NANSEN_API_KEY')
if not api_key:
    print("未找到 NANSEN_API_KEY")
    exit(1)

headers = {'apikey': api_key, 'Content-Type': 'application/json'}

def post(url, body):
    r = requests.post(url, headers=headers, json=body, timeout=30)
    return r.status_code, r.json() if r.status_code == 200 else r.text

# 尝试的时间段
TIMEFRAMES = ['6h', '6H', '6']
CHAINS = ['ethereum', 'base', 'solana']
NETFLOW_MIN = 5000

print("=" * 85)
print("  过去6小时 聪明钱 netflow > $5,000 的币种 (ETH / BASE / SOL)")
print("  并标出聪明钱买入数量")
print("=" * 85)

all_tokens = {}
for tf in TIMEFRAMES:
    for chain in CHAINS:
        code, data = post('https://api.nansen.ai/api/v1/token-screener', {
            'chains': [chain],
            'timeframe': tf,
            'pagination': {'limit': 100, 'offset': 0},
            'filters': {'only_smart_money': True},
            'sort': [{'field': 'netflow', 'direction': 'DESC'}]
        })
        if code == 200:
            items = data.get('data', [])
            for item in items:
                key = (item.get('chain', chain), item.get('token_address', ''))
                if key[1] and key not in all_tokens:
                    all_tokens[key] = item
            print(f"  {chain} timeframe={tf}: {len(items)} 条")
        else:
            print(f"  {chain} timeframe={tf}: 失败 {code}")

# 若 6h 不支持，回退到 24h
if not all_tokens and '6h' in TIMEFRAMES:
    print("\n  6h 可能不支持，尝试 24h...")
    for chain in CHAINS:
        code, data = post('https://api.nansen.ai/api/v1/token-screener', {
            'chains': [chain],
            'timeframe': '24h',
            'pagination': {'limit': 100, 'offset': 0},
            'filters': {'only_smart_money': True},
            'sort': [{'field': 'netflow', 'direction': 'DESC'}]
        })
        if code == 200:
            items = data.get('data', [])
            for item in items:
                key = (item.get('chain', chain), item.get('token_address', ''))
                if key[1]:
                    all_tokens[key] = item

# 过滤 netflow > 5000，按 netflow 排序
filtered = []
for k, item in all_tokens.items():
    net = float(item.get('netflow', 0) or 0)
    if net > NETFLOW_MIN:
        item['_netflow'] = net
        filtered.append(item)

filtered.sort(key=lambda x: x['_netflow'], reverse=True)

# 解析聪明钱买入数量字段（可能的字段名）
def get_buy_count(item):
    for f in ['nof_traders', 'smart_money_buy_count', 'buy_count', 'inflow_count', 'inflow_wallets', 'buyers_count', 'wallet_buy_count']:
        v = item.get(f)
        if v is not None:
            try:
                return int(v)
            except (ValueError, TypeError):
                pass
    return None

print("\n" + "=" * 85)
print(f"  结果: netflow > ${NETFLOW_MIN:,} 的币种 (共 {len(filtered)} 个)")
print("=" * 85)
if filtered:
    print(f"\n{'#':<4} {'链':<10} {'代币':<12} {'净流入(USD)':>16} {'聪明钱买入数':>14} {'买入量(USD)':>16} {'卖出量':>14} {'价格变化':>10}")
    print("-" * 95)
    for i, item in enumerate(filtered, 1):
        chain = item.get('chain', 'N/A')
        sym = item.get('token_symbol', 'N/A')
        net = item['_netflow']
        buy_count = get_buy_count(item)
        buy_vol = float(item.get('buy_volume', 0) or item.get('smart_money_buy_volume', 0) or 0)
        sell_vol = float(item.get('sell_volume', 0) or 0)
        chg = float(item.get('price_change', 0) or 0)
        buy_str = str(buy_count) if buy_count is not None else "N/A"
        print(f"{i:<4} {chain:<10} {sym:<12} ${net:>14,.0f} {buy_str:>14} ${buy_vol:>14,.0f} ${sell_vol:>12,.0f} {chg:>+9.2f}%")

    print("\n  原始返回字段示例:", list(filtered[0].keys()) if filtered else [])
else:
    print("\n  无符合条件的数据。可能原因:")
    print("  - API 不支持 6h 时间窗口")
    print("  - 当前计划返回数据量有限")
    print("  - 6h 内 netflow>5000 的币种较少")

print("\n" + "=" * 85)
