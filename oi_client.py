import requests
import json
from typing import List, Dict, Tuple
import time

class CoinalyzeClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.coinalyze.net/v1"
        # 兼容性：同时提供 Header 和 Query Param 认证
        self.headers = {'api_key': self.api_key}

    def _get(self, endpoint: str, params: Dict = None) -> requests.Response:
        """统一的带有 API Key 的 GET 请求封装"""
        if params is None:
            params = {}
        # 为了提高兼容性，在 query param 中也带上 api_key
        params['api_key'] = self.api_key
        url = f"{self.base_url}/{endpoint}"
        return requests.get(url, headers=self.headers, params=params, timeout=15)

    def get_supported_markets(self) -> List[Dict]:
        """获取所有支持的市场"""
        try:
            res = self._get("future-markets")
            if res.status_code == 200:
                return res.json()
            print(f"Coinalyze Markets fail: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"Coinalyze Markets exception: {e}")
        return []

    def get_current_oi(self, symbols: str) -> List[Dict]:
        """获取当前实时 OI"""
        try:
            res = self._get("open-interest", params={"symbols": symbols})
            if res.status_code == 200:
                return res.json()
            print(f"Coinalyze current OI fail: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"Coinalyze current OI exception: {e}")
        return []

    def get_oi_history(self, symbols: str, interval: str = "daily") -> List[Dict]:
        """获取历史 OI 数据 (OHLC)"""
        now = int(time.time())
        five_days_ago = now - (5 * 24 * 3600)
        params = {
            "symbols": symbols,
            "interval": interval,
            "from": five_days_ago,
            "to": now
        }
        try:
            res = self._get("open-interest-history", params=params)
            if res.status_code == 200:
                return res.json()
            print(f"OI History fail for {symbols[:30]}: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"OI History exception: {e}")
        return []

    def get_top_oi_gainers(self, limit: int = 20) -> List[Dict]:
        """精简版抓取策略：先按实时金额筛选，再回溯增长"""
        markets = self.get_supported_markets()
        if not markets:
            return []
        
        # 1. 筛选出 Binance USDT 永续合约
        binance_perps = [m['symbol'] for m in markets if m.get('exchange') == 'A' and 'USDT' in m.get('symbol')]
        if not binance_perps:
            return []

        # 2. 获取这些币种的当前实时 OI 金额，以便找出最“重要”的币种
        # 分批获取实时 OI (每批 20 个)
        current_oi_data = []
        for i in range(0, min(len(binance_perps), 100), 20):
            batch = binance_perps[i:i+20]
            batch_data = self.get_current_oi(",".join(batch))
            if batch_data:
                current_oi_data.extend(batch_data)
            time.sleep(1) # 实时接口通常限制较松，稍微等一下即可
        
        if not current_oi_data:
            return []

        # 按金额降序排列，取前 30 个重点关注，减少后续昂贵的历史 API 调用
        top_active_symbols = sorted(current_oi_data, key=lambda x: x.get('value', 0), reverse=True)[:30]
        active_symbols_str = [x['symbol'] for x in top_active_symbols]

        # 3. 对这 30 个重点币种，分批获取历史数据（每批 20 个，大幅减少请求次数）
        results = []
        for i in range(0, len(active_symbols_str), 20):
            batch = active_symbols_str[i:i+20]
            symbols_query = ",".join(batch)
            
            # 由于历史 API 极其昂贵且频率受限，我们在这里使用更长的延迟和重试
            for attempt in range(3):
                history = self.get_oi_history(symbols_query)
                if history:
                    for item in history:
                        sym = item.get('symbol', '').replace('USDT_PERP.A', '')
                        h_data = item.get('history', [])
                        if len(h_data) >= 2:
                            try:
                                # 尝试 5 元素 OHLC 结构
                                if len(h_data[-1]) >= 5:
                                    prev_c = h_data[-2][4]
                                    curr_c = h_data[-1][4]
                                else: # 尝试 2 元素 [ts, val] 结构
                                    prev_c = h_data[-2][1]
                                    curr_c = h_data[-1][1]
                                
                                if prev_c > 0:
                                    change_pct = (curr_c - prev_c) / prev_c * 100
                                    results.append({'symbol': sym, 'oi_change_pct': change_pct, 'oi_value': curr_c})
                            except Exception:
                                pass
                    break # 成功获取本批次，跳出重试
                else:
                    print(f"Batch {i//20 + 1} history empty, symbol sample: {batch[0]}... retry {attempt+1}")
                    time.sleep(10) # 429 后至少等 10 秒
            
            time.sleep(10) # 批次间强制等待 10 秒以规避频率限制

        # 4. 排序结果
        results.sort(key=lambda x: x['oi_change_pct'], reverse=True)
        return results[:limit]

if __name__ == "__main__":
    client = CoinalyzeClient("84f62b06-6dae-4cf3-aff0-6e3ad52ae825")
    print("Test fetching OI gainers...")
    print(client.get_top_oi_gainers(limit=5))
