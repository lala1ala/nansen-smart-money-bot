"""
查询过去24小时以太坊上智能钱包买入最多的代币
使用分页获取尽可能多的数据
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('NANSEN_API_KEY')
if not api_key:
    print("未找到 NANSEN_API_KEY")
    exit(1)

headers = {
    'apikey': api_key,
    'Content-Type': 'application/json'
}

STABLE_COINS = {'USDT', 'USDC', 'DAI', 'BUSD', 'USDE', 'USDS', 'PYUSD', 'GHO',
                'USD1', 'FRAX', 'LUSD', 'CRVUSD', 'TUSD', 'USDP', 'GUSD',
                'SUSDE', 'SDAI', 'PAXG', 'XAUT', 'WBTC', 'WETH', 'STETH', 'WSTETH'}

def post(url, body):
    r = requests.post(url, headers=headers, json=body, timeout=30)
    return r.status_code, r.json() if r.status_code == 200 else r.text

print("=" * 70)
print("  过去24小时 以太坊 智能钱包买入最多的代币")
print("=" * 70)

# ── 分页获取 Token Screener 全部数据 ─────────────────────────────────
print("\n[Token Screener] 分页获取以太坊数据...")
all_screener = {}
for offset in range(0, 100, 10):
    code, data = post('https://api.nansen.ai/api/v1/token-screener', {
        'chains': ['ethereum'],
        'timeframe': '24h',
        'pagination': {'limit': 50, 'offset': offset},
        'sort': [{'field': 'buy_volume', 'direction': 'DESC'}]
    })
    if code == 200:
        items = data.get('data', [])
        if not items:
            break
        for item in items:
            addr = item.get('token_address', '')
            if addr:
                all_screener[addr] = item
        print(f"  offset={offset}: 返回 {len(items)} 条，累计 {len(all_screener)} 条")
        if len(items) < 10:
            break
    else:
        print(f"  offset={offset}: 失败 {code}")
        break

# 按买入量排序，排除稳定币
screener_list = list(all_screener.values())
screener_list.sort(key=lambda x: float(x.get('buy_volume', 0) or 0), reverse=True)

# 全部代币（包括稳定币）
print(f"\n[Token Screener] 全部代币买入量 Top 20（共 {len(screener_list)} 条）")
print(f"{'#':<4} {'代币':<12} {'买入量(USD)':>18} {'卖出量(USD)':>18} {'净流入(USD)':>18} {'价格变化':>10}")
print("-" * 85)
for i, item in enumerate(screener_list[:20], 1):
    sym = item.get('token_symbol', 'N/A')
    buy = float(item.get('buy_volume', 0) or 0)
    sell = float(item.get('sell_volume', 0) or 0)
    net = float(item.get('netflow', 0) or 0)
    chg = float(item.get('price_change', 0) or 0)
    flag = " [稳定币]" if sym.upper() in STABLE_COINS else ""
    print(f"{i:<4} {sym:<12} ${buy:>16,.0f} ${sell:>16,.0f} ${net:>16,.0f} {chg:>+9.2f}%{flag}")

# 排除稳定币
non_stable = [x for x in screener_list if x.get('token_symbol', '').upper() not in STABLE_COINS]
if non_stable:
    print(f"\n[Token Screener] 非稳定币买入量 Top 20（共 {len(non_stable)} 条）")
    print(f"{'#':<4} {'代币':<12} {'买入量(USD)':>18} {'卖出量(USD)':>18} {'净流入(USD)':>18} {'价格变化':>10} {'市值':>14}")
    print("-" * 100)
    for i, item in enumerate(non_stable[:20], 1):
        sym = item.get('token_symbol', 'N/A')
        buy = float(item.get('buy_volume', 0) or 0)
        sell = float(item.get('sell_volume', 0) or 0)
        net = float(item.get('netflow', 0) or 0)
        chg = float(item.get('price_change', 0) or 0)
        mcap = float(item.get('market_cap_usd', 0) or 0)
        print(f"{i:<4} {sym:<12} ${buy:>16,.0f} ${sell:>16,.0f} ${net:>16,.0f} {chg:>+9.2f}% ${mcap:>12,.0f}")

print()

# ── 分页获取 Smart Money Holdings ────────────────────────────────────
print("[Smart Money Holdings] 分页获取以太坊数据...")
all_holdings = {}
for offset in range(0, 200, 10):
    code, data = post('https://api.nansen.ai/api/v1/smart-money/holdings', {
        'chains': ['ethereum'],
        'pagination': {'limit': 100, 'offset': offset},
        'order_by': [{'field': 'balance_24h_percent_change', 'direction': 'DESC'}]
    })
    if code == 200:
        items = data.get('data', [])
        if not items:
            break
        for item in items:
            addr = item.get('token_address', '')
            if addr:
                all_holdings[addr] = item
        print(f"  offset={offset}: 返回 {len(items)} 条，累计 {len(all_holdings)} 条")
        if len(items) < 10:
            break
    else:
        print(f"  offset={offset}: 失败 {code}")
        break

# 计算净增仓并排序
holdings_list = list(all_holdings.values())
for x in holdings_list:
    val = float(x.get('value_usd', 0) or 0)
    chg = float(x.get('balance_24h_percent_change', 0) or 0)
    x['_net_inflow_usd'] = val * chg / 100

# 有增仓的（排除稳定币）
inflows = [
    x for x in holdings_list
    if x['_net_inflow_usd'] > 0
    and x.get('token_symbol', '').upper() not in STABLE_COINS
]
inflows.sort(key=lambda x: x['_net_inflow_usd'], reverse=True)

print(f"\n[Smart Money Holdings] 24h 增仓最多 Top 20（共 {len(holdings_list)} 条，有增仓 {len(inflows)} 条）")
if inflows:
    print(f"{'#':<4} {'代币':<12} {'当前持仓(USD)':>18} {'24h变化%':>10} {'净增仓(USD)':>18} {'持有人数':>8} {'市值':>14}")
    print("-" * 90)
    for i, item in enumerate(inflows[:20], 1):
        sym = item.get('token_symbol', 'N/A')
        val = float(item.get('value_usd', 0) or 0)
        chg = float(item.get('balance_24h_percent_change', 0) or 0)
        net = item['_net_inflow_usd']
        holders = item.get('holders_count', 0)
        mcap = float(item.get('market_cap_usd', 0) or 0)
        sectors = ', '.join(item.get('token_sectors', []) or [])
        print(f"{i:<4} {sym:<12} ${val:>16,.0f} {chg:>+9.2f}% ${net:>16,.0f} {holders:>8} ${mcap:>12,.0f}")
        if sectors:
            print(f"     板块: {sectors}")
else:
    print("  无增仓数据")
    # 显示全部数据供参考
    print(f"\n  全部 Holdings 数据（共 {len(holdings_list)} 条）:")
    for item in holdings_list[:10]:
        sym = item.get('token_symbol', 'N/A')
        val = float(item.get('value_usd', 0) or 0)
        chg = float(item.get('balance_24h_percent_change', 0) or 0)
        holders = item.get('holders_count', 0)
        sectors = ', '.join(item.get('token_sectors', []) or [])
        print(f"  {sym:<12} 持仓=${val:,.0f}  24h={chg:+.2f}%  持有人={holders}  板块={sectors}")

print()
print("=" * 70)
print("查询完成")
print("=" * 70)
