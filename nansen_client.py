"""
Nansen API 客户端
处理与 Nansen API 的所有交互
"""
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from config import Config


class NansenClient:
    """Nansen API 客户端类"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = Config.NANSEN_BASE_URL
        self.headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        发送 API 请求，带重试机制
        
        Args:
            endpoint: API 端点
            params: 查询参数
            
        Returns:
            API 响应数据
        """
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(Config.API_RETRY_TIMES):
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=Config.API_TIMEOUT
                )
                response.raise_for_status()
                return response.json()
            
            except requests.exceptions.RequestException as e:
                if attempt == Config.API_RETRY_TIMES - 1:
                    raise Exception(f"API 请求失败: {str(e)}")
                time.sleep(Config.API_RETRY_DELAY)
        
        return {}
    
    def get_smart_money_token_balances(
        self, 
        chain: str, 
        hours: int,
        limit: int = 100
    ) -> List[Dict]:
        """
        获取智能资金的代币持仓变化
        
        Args:
            chain: 区块链名称 (ethereum, base, solana, bsc)
            hours: 时间段（小时）
            limit: 返回结果数量
            
        Returns:
            代币列表，包含买入/卖出数据
        """
        # 计算时间范围
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # 构建请求参数
        params = {
            'chain': chain,
            'from': start_time.strftime('%Y-%m-%d'),
            'to': end_time.strftime('%Y-%m-%d'),
            'limit': limit
        }
        
        try:
            # 调用 Nansen API
            data = self._make_request('smart-money/token-balances', params)
            return data.get('data', [])
        except Exception as e:
            print(f"获取 {chain} 智能资金数据失败: {str(e)}")
            return []
    
    def get_token_flows(
        self,
        chain: str,
        hours: int,
        segment: str = 'smart_money'
    ) -> List[Dict]:
        """
        获取代币资金流向数据
        
        Args:
            chain: 区块链名称
            hours: 时间段（小时）
            segment: 用户群体 (smart_money, funds, whales)
            
        Returns:
            代币流向数据
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        params = {
            'chain': chain,
            'from': start_time.strftime('%Y-%m-%d'),
            'to': end_time.strftime('%Y-%m-%d'),
            'segment': segment
        }
        
        try:
            data = self._make_request('token/flows', params)
            return data.get('data', [])
        except Exception as e:
            print(f"获取 {chain} 资金流向失败: {str(e)}")
            return []
    
    def aggregate_trading_data(
        self,
        chain: str,
        hours: int
    ) -> Dict[str, List[Dict]]:
        """
        聚合交易数据，分别统计买入和卖出最多的代币
        
        Args:
            chain: 区块链名称
            hours: 时间段（小时）
            
        Returns:
            包含 'buys' 和 'sells' 的字典
        """
        # 获取智能资金持仓变化
        balances = self.get_smart_money_token_balances(chain, hours)
        
        # 分离买入和卖出
        buys = []
        sells = []
        
        for item in balances:
            # 根据余额变化判断买入/卖出
            balance_change = item.get('balance_change', 0)
            
            if balance_change > 0:
                buys.append({
                    'token': item.get('token_symbol', 'Unknown'),
                    'token_name': item.get('token_name', ''),
                    'amount': abs(balance_change),
                    'value_usd': item.get('value_usd', 0),
                    'count': item.get('trader_count', 0)
                })
            elif balance_change < 0:
                sells.append({
                    'token': item.get('token_symbol', 'Unknown'),
                    'token_name': item.get('token_name', ''),
                    'amount': abs(balance_change),
                    'value_usd': item.get('value_usd', 0),
                    'count': item.get('trader_count', 0)
                })
        
        # 按交易价值排序
        buys.sort(key=lambda x: x['value_usd'], reverse=True)
        sells.sort(key=lambda x: x['value_usd'], reverse=True)
        
        return {
            'buys': buys[:Config.TOP_TOKENS_COUNT],
            'sells': sells[:Config.TOP_TOKENS_COUNT]
        }
    
    def get_monitoring_report(self) -> Dict:
        """
        生成完整的监控报告
        
        Returns:
            包含所有链和时间段的数据
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'data': {}
        }
        
        for hours in Config.TIME_PERIODS:
            report['data'][f'{hours}h'] = {}
            
            for chain_id, chain_name in Config.CHAINS.items():
                print(f"正在获取 {chain_name} {hours}小时数据...")
                
                try:
                    chain_data = self.aggregate_trading_data(chain_id, hours)
                    report['data'][f'{hours}h'][chain_name] = chain_data
                except Exception as e:
                    print(f"获取 {chain_name} 数据失败: {str(e)}")
                    report['data'][f'{hours}h'][chain_name] = {
                        'buys': [],
                        'sells': [],
                        'error': str(e)
                    }
                
                # 避免 API 限流
                time.sleep(0.5)
        
        return report
