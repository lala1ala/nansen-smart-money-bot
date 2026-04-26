import os
from datetime import datetime
from dotenv import load_dotenv
import time
import pandas as pd # 用于美化表格输出

from nansen_client import NansenClient
from oi_client import CoinalyzeClient
from database import CryptoDatabase

load_dotenv()

def generate_table(data, title):
    """生成简单的 Markdown 表格视图"""
    if not data:
        return f"\n### {title}\n(暂无数据)\n"
    
    df = pd.DataFrame(data)
    # 重命名列以提高可读�?
    rename_map = {
        'symbol': '币种',
        'netflow': '净流入(USD)',
        'net_position_change': '净头寸变化',
        'oi_change_pct': 'OI变化%',
        'price': '价格',
        'oi_value': '当前OI'
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    
    return f"\n### {title}\n{df.head(10).to_markdown(index=False)}\n"

def main():
    date_str = datetime.now().strftime("%Y-%m-%d")
    print(f"🚀 [{date_str}] 开始自动化加密货币共振分析任务...\n")
    
    # 初始化客户端
    nansen_api_key = os.getenv('NANSEN_API_KEY')
    coinalyze_api_key = os.getenv('COINALYZE_API_KEY', "84f62b06-6dae-4cf3-aff0-6e3ad52ae825")
    
    nansen = NansenClient(nansen_api_key)
    coinalyze = CoinalyzeClient(coinalyze_api_key)
    db = CryptoDatabase()
    
    # 1. 抓取四张图的数据
    print("📥 正在抓取数据...")
    
    # �?: Hyperliquid Perp
    print(" - 获取 Hyperliquid Perp 数据...")
    hl_data = nansen.get_hyperliquid_perp_screener()
    db.save_snapshot('hyperliquid', hl_data)
    
    # �?: Smart Money Spot
    print(" - 获取 Smart Money Spot 数据...")
    sm_data = nansen.get_token_screener('24h', participant_type='smart_money')
    db.save_snapshot('smart_money', sm_data)
    
    # �?: 全网 OI (Coinalyze)
    print(" - 获取 Market OI 数据...")
    oi_raw = coinalyze.get_top_oi_gainers(limit=30)
    oi_data = [{'symbol': t['symbol'], 'oi_change_pct': t['oi_change_pct']} for t in oi_raw]
    db.save_snapshot('oi', oi_data)
    
    # �?: Whale Spot
    print(" - 获取 Whale Spot 数据...")
    whale_data = nansen.get_token_screener('24h', participant_type='whale')
    db.save_snapshot('whale', whale_data)
    
    # 2. 生成报告文本
    report = f"# 📊 加密货币共振分析报告 ({date_str})\n"
    report += "---"
    
    # 输出四张表的表格
    report += generate_table(sm_data, "1. Smart Money Spot 入场 (链上)")
    report += generate_table(whale_data, "2. Whale Spot 入场 (巨鲸)")
    report += generate_table(hl_data, "3. Hyperliquid Perp 持仓变化")
    report += generate_table(oi_data, "4. 全网 OI 暴涨名单 (Coinalyze)")
    
    # 3. 自动化比�?- 横向共振 (当日四张图内重复出现的币)
    report += "\n## 🔥 【今日横向共振�?(多维指标同时看多)\n"
    all_symbols = {}
    for source, data in [('SmartMoney', sm_data), ('Whale', whale_data), ('Hyperliquid', hl_data), ('MarketOI', oi_data)]:
        for item in data:
            sym = item['symbol']
            if sym not in all_symbols:
                all_symbols[sym] = []
            all_symbols[sym].append(source)
    
    resonance_found = False
    for sym, sources in all_symbols.items():
        if len(sources) >= 2:
            report += f"- **`{sym}`**: 出现�?{', '.join(sources)} ({len(sources)}个维�?\n"
            resonance_found = True
    if not resonance_found: report += "暂无显著共振。\n"
    
    # 4. 自动化比�?- 纵向共振 (连续3天出现在同一榜单)
    report += "\n## 📈 �?日纵向共振�?(持续走强趋势)\n"
    longitudinal_found = False
    for source_name, source_key in [('Smart Money', 'smart_money'), ('Whale', 'whale'), ('Hyperliquid', 'hyperliquid'), ('OI', 'oi')]:
        consecutive = db.get_consecutive_tokens(source_key, days=3)
        if consecutive:
            report += f"- **{source_name}**: 连续3天活�?- {', '.join([f'`{s}`' for s in consecutive])}\n"
            longitudinal_found = True
    if not longitudinal_found: report += "暂无持续走强代币。\n"
    
    print("\n�?分析完成！生成报�?..")
    print(report)
    
    # 5. 推送报�?(可�?
    # ... 原有�?TG 推送逻辑可以放在这里 ...
    # 将报告保存到本地文件
    with open(f"report_{date_str}.md", "w", encoding="utf-8") as f:
        f.write(report)

if __name__ == "__main__":
    main()
