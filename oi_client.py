import requests
import json
from typing import List, Dict, Tuple
import time

class CoinalyzeClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.coinalyze.net/v1"
        self.headers = {
            'api_key': self.api_key
        }

    def get_supported_markets(self) -> List[Dict]:
        """获取所有支持的市场"""
        url = f"{self.base_url}/future-markets"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        print(f"Coinalyze 市场抓取失败: {response.text}")
        return []

    def get_oi_history(self, symbols: str, interval: str = "1day") -> List[Dict]:
        """
        获取过去 24H 的 OI 数据 (Open Interest)
        symbols: 多个用逗号分隔，如 "BTCUSDT_PERP.A,ETHUSDT_PERP.A"
        """
        url = f"{self.base_url}/open-interest-history"
        params = {
            "symbols": symbols,
            "interval": interval
        }
        res = requests.get(url, headers=self.headers, params=params)
        if res.status_code == 200:
            return res.json()
        return []

    def get_top_oi_gainers(self, limit: int = 20) -> List[Dict]:
        """
        计算 24h OI 增长最多的代币
        这是一个组合逻辑：由于 Coinalyze 没有直接的 "Top OI gainers" 端点，
        我们需要获取市场列表，然后分批检查 OI，或者利用 binance 的数据作为参考，然后 Coinalyze 确认。
        另外，有 /open-interest 接口可以直接获取最新的全市场 OI，但需要自己处理缓存/差值。
        我们先用 /open-interest 结合我们自己实现的按天比对，但最好是获取 24h history。
        为了不过载 API，通常可以直接抓 Binance 市场的，因为绝大部分 OI 在 Binance。
        """
        markets = self.get_supported_markets()
        # 筛选 Binance 且 USDT 合约
        binance_perps = [m for m in markets if m.get('exchange') == 'A' and 'USDT' in m.get('symbol')]
        
        # 为了高效，分批获取
        results = []
        batch_size = 30
        
        # 只取前 150 个主流币，或者全取可能需要 10 几个请求
        # 作为示例，我们限制抓取前 5 批
        for i in range(0, min(len(binance_perps), 150), batch_size):
            batch = binance_perps[i:i+batch_size]
            symbols = ",".join([m['symbol'] for m in batch])
            try:
                # 获取 daily history
                history = self.get_oi_history(symbols, interval="1day")
                for item in history:
                    sym = item.get('symbol', '').replace('USDT_PERP.A', '')
                    h_data = item.get('history', [])
                    if len(h_data) >= 2:
                        # history 是一个数组, 每个元素包含 [timestamp, o, h, l, c]
                        # 比较最后一天和前一天
                        prev_c = h_data[-2][4]
                        curr_c = h_data[-1][4]
                        if prev_c > 0:
                            change_pct = (curr_c - prev_c) / prev_c * 100
                            results.append({
                                'symbol': sym,
                                'oi_change_pct': change_pct,
                                'oi_value': curr_c
                            })
            except Exception as e:
                print(f"Coinalyze batch fail: {e}")
            time.sleep(0.5)

        results.sort(key=lambda x: x['oi_change_pct'], reverse=True)
        return results[:limit]

if __name__ == "__main__":
    client = CoinalyzeClient("84f62b06-6dae-4cf3-aff0-6e3ad52ae825")
    print("Test fetching OI gainers...")
    data = client.get_top_oi_gainers(limit=5)
    for d in data:
        print(d)
