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
        self.base_url = 'https://api.nansen.ai'
        self.headers = {
            'apikey': api_key,  # 注意：Nansen 使用 'apikey' 而不是 'X-API-KEY'
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, endpoint: str, body: Optional[Dict] = None, method='POST') -> Dict:
        """
        发送 API 请求，带重试机制
        
        Args:
            endpoint: API 端点
            body: POST 请求体
            method: HTTP 方法 (POST/GET)
            
        Returns:
            API 响应数据
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
    
    def get_smart_money_holdings(
        self, 
        chains: List[str],
        limit: int = 100,
        include_24h_changes_only: bool = True
    ) -> List[Dict]:
        """
        获取智能资金的代币持仓数据
        
        Args:
            chains: 区块链列表 (["ethereum"], ["solana"], etc.)
            limit: 返回结果数量
            include_24h_changes_only: 仅包含24小时有变化的代币
            
        Returns:
            代币列表，包含持仓变化数据
        """
        # 构建请求体 - 移除了不支持的 timeframe 参数
        body = {
            'chains': chains,
            'pagination': {
                'limit': limit,
                'offset': 0
            },
            'order_by': [
                {
                    'field': 'value_usd',
                    'direction': 'DESC'
                }
            ]
        }
        
        # 不再过滤 - 显示所有智能资金持仓数据
        # Smart money holdings 的变化通常很少，过滤会丢失大量有价值的数据
        
        try:
            # 调用 Nansen API
            data = self._make_request('/api/v1/smart-money/holdings', body, method='POST')
            return data.get('data', [])
        except Exception as e:
            print(f"获取 {chains} 智能资金数据失败: {str(e)}")
            return []
    
    def get_token_screener(
        self,
        chains: List[str],
        timeframe: str = '24h',
        only_smart_money: bool = True,
        limit: int = 50
    ) -> List[Dict]:
        """
        使用 token screener 获取代币数据
        
        Args:
            chains: 区块链列表
            timeframe: 时间范围
            only_smart_money: 仅智能资金活跃的代币
            limit: 返回结果数量
            
        Returns:
            代币列表
        """
        body = {
            'chains': chains,
            'timeframe': timeframe,
            'pagination': {
                'limit': limit,
                'offset': 0
            },
            'filters': {
                'only_smart_money': only_smart_money
            },
            'sort': [{
                'field': 'smart_money_buy_volume',
                'direction': 'DESC'
            }]
        }
        
        try:
            data = self._make_request('/api/v1/token-screener', body, method='POST')
            return data.get('data', [])
        except Exception as e:
            print(f"获取 token screener 数据失败: {str(e)}")
            return []
    
    def aggregate_trading_data(
        self,
        chain: str,
        hours: int
    ) -> Dict[str, List[Dict]]:
        """
        聚合智能资金持仓数据，按价值和24小时变化排序
        
        Args:
            chain: 区块链名称
            hours: 时间段（小时）- 注意：API 返回24小时数据
            
        Returns:
            包含 'top_holdings', 'biggest_increases', 'biggest_decreases' 的字典
        """
        # 获取智能资金持仓数据
        holdings = self.get_smart_money_holdings([chain])
        
        all_tokens = []
        increases = []
        decreases = []
        
        for item in holdings:
            # 获取数据
            balance_change_pct = item.get('balance_24h_percent_change', 0)
            value_usd = item.get('value_usd', 0)
            
            # 获取代币符号
            symbol = item.get('token_symbol', 'Unknown')
            
            # 获取扇区信息
            sectors = item.get('token_sectors', [])
            sector = sectors[0] if sectors else 'Other'
            
            token_info = {
                'token': symbol,
                'value_usd': value_usd,
                'change_pct': balance_change_pct,
                'holders': item.get('holders_count', 0),
                'sector': sector
            }
            
            all_tokens.append(token_info)
            
            # 分类增持和减持（只有变化 > 0.01% 才算）
            if balance_change_pct > 0.01:
                increases.append(token_info)
            elif balance_change_pct < -0.01:
                decreases.append(token_info)
        
        # 排序
        all_tokens.sort(key=lambda x: x['value_usd'], reverse=True)
        increases.sort(key=lambda x: x['change_pct'], reverse=True)
        decreases.sort(key=lambda x: x['change_pct'])  # 降序（负数小的在前）
        
        return {
            'top_holdings': all_tokens[:Config.TOP_TOKENS_COUNT],
            'biggest_increases': increases[:5],
            'biggest_decreases': decreases[:5]
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
                time.sleep(1)
        
        return report
