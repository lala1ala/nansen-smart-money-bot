import os
from datetime import datetime
from dotenv import load_dotenv
import requests

from oi_client import CoinalyzeClient
from database import DailyStatsDB

load_dotenv()
api_key = os.getenv('NANSEN_API_KEY')
headers = {'apikey': api_key, 'Content-Type': 'application/json'}

def get_nansen_sm_inflows():
    res = requests.post('https://api.nansen.ai/api/v1/smart-money/holdings', headers=headers, json={
        'chains': ['ethereum'],
        'pagination': {'limit': 100, 'offset': 0},
        'order_by': [{'field': 'balance_24h_percent_change', 'direction': 'DESC'}]
    })
    
    if res.status_code == 200:
        items = res.json().get('data', [])
        tokens_map = {} # 使用 symbol 作为 key 去重
        for idx, t in enumerate(items[:50]): # 扩大搜索范围以防主币重复
            sym = t.get('token_symbol', 'UNKNOWN')
            if sym.upper() not in ['USDT', 'USDC', 'DAI']:
                val = float(t.get('value_usd', 0) or 0)
                chg = float(t.get('balance_24h_percent_change', 0) or 0)
                net_inflow = val * (chg/100)
                
                if sym not in tokens_map or net_inflow > tokens_map[sym]['value']:
                    tokens_map[sym] = {'token': sym, 'rank': idx+1, 'value': net_inflow}
        
        # 转换回列表并按数值排序
        sorted_tokens = sorted(tokens_map.values(), key=lambda x: x['value'], reverse=True)
        return sorted_tokens[:30]
    return []

def main():
    date_str = datetime.now().strftime("%Y-%m-%d")
    print(f"[{date_str}] 开始抓取与对比数据...\n")
    
    db = DailyStatsDB()
    coinalyze = CoinalyzeClient("84f62b06-6dae-4cf3-aff0-6e3ad52ae825")
    sm_tokens_db = []
    oi_tokens_db = []
    
    print("1. 正在获取 Nansen Smart Money 24h 增持 (链上聪明钱)...")
    sm_tokens_db = get_nansen_sm_inflows()
    if sm_tokens_db:
        db.save_daily_snapshot(date_str, 'nansen_sm', sm_tokens_db)

    print("2. 正在获取 Coinalyze 全网 OI 升高名单...")
    coinalyze_api_key = os.getenv('COINALYZE_API_KEY')
    if not coinalyze_api_key:
        print("⚠️ COINALYZE_API_KEY not found in environment, using fallback.")
        coinalyze_api_key = "84f62b06-6dae-4cf3-aff0-6e3ad52ae825" # Keep as fallback for now
        
    coinalyze = CoinalyzeClient(coinalyze_api_key)
    try:
        oi_tokens_raw = coinalyze.get_top_oi_gainers(limit=30)
        if not oi_tokens_raw:
            print("⚠️ Coinalyze returned no OI gainers. Check API status/limits.")
        oi_tokens_db = [{'token': t['symbol'], 'rank': idx+1, 'value': t['oi_change_pct']} for idx, t in enumerate(oi_tokens_raw)]
        db.save_daily_snapshot(date_str, 'market_oi', oi_tokens_db)
    except Exception as e:
        print(f"❌ OI Fetch failed with exception: {e}")

    print("3. 交叉查询 Whale / Hyperliquid (暂不适用原生发现接口)...")
    
    # =============== 分析部分 ===============
    report_lines = []
    report_lines.append(f"📊 *Smart Money & OI 每日共振分析报告 ({date_str})*")
    report_lines.append("="*35)

    # 独立榜单 Top N
    report_lines.append("\n🌟 *【今日资金单边流入 Top 10】*")
    if sm_tokens_db:
        sm_top_str = ", ".join([f"`{t['token']}`" for t in sm_tokens_db[:10]])
        report_lines.append(f"  • *链上聪明钱*: {sm_top_str}")
    else:
        report_lines.append(f"  • *链上聪明钱*: (暂无数据)")
        
    if oi_tokens_db:
        oi_top_str = ", ".join([f"`{t['token']}`(+{t['value']:.1f}%)" for t in oi_tokens_db[:10]])
        report_lines.append(f"  • *全网OI暴涨*: {oi_top_str}")
    else:
        report_lines.append(f"  • *全网OI暴涨*: (暂无数据)")

    # 横向对比
    all_sources = ['nansen_sm', 'market_oi']
    overlaps = db.get_overlapping_tokens(date_str, all_sources, min_overlap=2)
    
    report_lines.append("\n🔥 *【今日多维共振】*")
    if not overlaps:
        report_lines.append("  - 无显著重叠代币")
    else:
        for symbol, sources in sorted(overlaps.items(), key=lambda x: len(x[1]), reverse=True):
            display_sources = [s.replace('nansen_sm', '链上聪明钱').replace('market_oi', '全网OI暴涨') for s in sources]
            report_lines.append(f"  • `{symbol:<8}` ({len(sources)}/2) -> {', '.join(display_sources)}")

    # 纵向对比 (3天)
    report_lines.append("\n📈 *【近3天持续活跃榜】*")
    long_trends_3d = db.get_longitudinal_tokens(date_str, days=3, min_appearances=1)
    if not long_trends_3d:
        report_lines.append("  - 无近期持续活跃代币 (3天)")
    else:
        for symbol, data in long_trends_3d.items():
            details = []
            for src, count in data.items():
                if count >= 1:
                    clean_src = src.replace('nansen_sm', '链上').replace('market_oi', 'OI')
                    details.append(f"{clean_src}({count}天)")
            if details:
                report_lines.append(f"  • `{symbol:<8}` (3天内) -> {', '.join(details)}")

    # 纵向对比 (7天)
    report_lines.append("\n👑 *【近7天高频常客榜】* (至少上榜2天)")
    long_trends_7d = db.get_longitudinal_tokens(date_str, days=7, min_appearances=2)
    if not long_trends_7d:
        report_lines.append("  - 无常客代币 (7天)")
    else:
        for symbol, data in long_trends_7d.items():
            details = []
            for src, count in data.items():
                if count >= 2:
                    clean_src = src.replace('nansen_sm', '链上').replace('market_oi', 'OI')
                    details.append(f"{clean_src}({count}次)")
            if details:
                report_lines.append(f"  • `{symbol:<8}` (7天内) -> {', '.join(details)}")

    final_report = "\n".join(report_lines)
    print(final_report)
    
    # === 发送 Telegram 消息 === 
    tg_token = os.getenv('TELEGRAM_BOT_TOKEN')
    tg_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if tg_token and tg_chat_id:
        print("\n正在推送到 Telegram...")
        try:
            tg_url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
            res = requests.post(tg_url, json={
                "chat_id": tg_chat_id,
                "text": final_report,
                "parse_mode": "Markdown"
            })
            if res.status_code == 200:
                print("✅ Telegram 推送成功！")
            else:
                print(f"❌ Telegram 推送失败: {res.text}")
        except Exception as e:
            print(f"❌ Telegram 请求报错: {e}")

if __name__ == "__main__":
    main()
