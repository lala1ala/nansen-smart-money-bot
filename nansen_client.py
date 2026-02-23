"""
Nansen API 客户端
处理与 Nansen Token Screener API 的所有交互
"""
import requests
import time
from datetime import datetime
from typing import List, Dict, Optional
from config import Config


class NansenClient:
    """Nansen API 客户端类"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = Config.NANSEN_BASE_URL
        self.headers = {
            'apikey': api_key,
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, endpoint: str, body: Optional[Dict] = None, method='POST') -> Dict:
        """
        发送 API 请求，带重试机制
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(Config.API_RETRY_TIMES):
            try:
                if method == 'POST':
                    response = requests.post(
                        url,
                        headers=self.headers,
                        json=body or {},
                        timeout=Config.API_TIMEOUT
                    )
                else:
                    response = requests.get(
                        url,
                        headers=self.headers,
                        params=body,
                        timeout=Config.API_TIMEOUT
                    )
                
                response.raise_for_status()
                return response.json()
            
            except requests.exceptions.RequestException as e:
                if attempt == Config.API_RETRY_TIMES - 1:
                    raise Exception(f"API 请求失败: {str(e)}")
                time.sleep(Config.API_RETRY_DELAY)
        
        return {}
    
    def get_token_screener_netflow(
        self,
        timeframe: str,
        chains: Optional[List[str]] = None,
        limit: int = None
    ) -> List[Dict]:
        """
        获取 Token Screener 的 Smart Money 净流入数据
        
        Args:
            timeframe: 时间段，支持 '10m', '1h', '6h'
            chains: 区块链列表，None 表示使用 config 默认值
            limit: 返回结果数量
            
        Returns:
            按净流入降序排列的代币列表
        """
        if chains is None:
            chains = Config.CHAINS
        if limit is None:
            limit = Config.TOP_TOKENS_COUNT
        
        body = {
            'chains': chains,
            'timeframe': timeframe,
            'pagination': {
                'limit': limit,
                'offset': 0
            },
            'filters': {
                'only_smart_money': True
            },
            'sort': [{
                'field': 'net_flow',
                'direction': 'DESC'
            }]
        }
        
        try:
            data = self._make_request('/api/v1/token-screener', body, method='POST')
            tokens = data.get('data', [])
            
            # 只保留净流入为正的代币（真正是聪明钱买入）
            positive_flow = [t for t in tokens if t.get('net_flow', 0) > 0]
            return positive_flow[:limit]
            
        except Exception as e:
            print(f"获取 Token Screener 数据失败 ({timeframe}): {str(e)}")
            return []
    
    def get_screener_for_report(self, timeframes: List[str]) -> Dict[str, List[Dict]]:
        """
        批量获取多个时间段的数据
        
        Args:
            timeframes: 时间段列表，例如 ['10m', '1h', '6h']
            
        Returns:
            { '10m': [...], '1h': [...], '6h': [...] }
        """
        result = {}
        for tf in timeframes:
            print(f"正在获取 {tf} Smart Money 净流入数据...")
            result[tf] = self.get_token_screener_netflow(tf)
            time.sleep(1)  # 避免限流
        return result
