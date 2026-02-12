"""
消息格式化模块
将监控数据格式化为美观的 Telegram 消息
"""
from datetime import datetime
from typing import Dict, List
from config import Config


class MessageFormatter:
    """Telegram 消息格式化器"""
    
    # Emoji 配置
    CHAIN_EMOJIS = {
        'ETH': '🔵',
        'BASE': '🔷',
        'SOL': '🟣',
        'BSC': '🟡'
    }
    
    TIME_EMOJIS = {
        2: '⏰',
        4: '🕐',
        12: '🕛',
        24: '📅'
    }
    
    @staticmethod
    def format_value(value: float) -> str:
        """
        格式化美元价值
        
        Args:
            value: 美元价值
            
        Returns:
            格式化后的字符串
        """
        if value >= 1_000_000:
            return f"${value/1_000_000:.2f}M"
        elif value >= 1_000:
            return f"${value/1_000:.1f}K"
        else:
            return f"${value:.2f}"
    
    @staticmethod
    def format_token_list(tokens: List[Dict], list_type: str = 'buy') -> str:
        """
        格式化代币列表
        
        Args:
            tokens: 代币列表
            list_type: 'buy' 或 'sell'
            
        Returns:
            格式化后的文本
        """
        if not tokens:
            return "  暂无数据\n"
        
        emoji = "💰" if list_type == 'buy' else "📉"
        result = []
        
        for idx, token in enumerate(tokens, 1):
            token_symbol = token['token']
            value = MessageFormatter.format_value(token['value_usd'])
            count = token.get('count', 0)
            
            result.append(f"  {idx}. {token_symbol} - {value}")
            if count > 0:
                result[-1] += f" ({count}个地址)"
        
        return "\n".join(result) + "\n"
    
    @staticmethod
    def format_chain_section(chain_name: str, data: Dict) -> str:
        """
        格式化单个链的数据
        
        Args:
            chain_name: 链名称
            data: 包含 buys 和 sells 的数据
            
        Returns:
            格式化后的文本
        """
        emoji = MessageFormatter.CHAIN_EMOJIS.get(chain_name, '⚪')
        
        sections = [
            f"{emoji} {chain_name}",
            ""
        ]
        
        # 检查是否有错误
        if 'error' in data:
            sections.append(f"  ⚠️ 获取数据失败: {data['error']}\n")
            return "\n".join(sections)
        
        # 买入数据
        sections.append("💰 买入最多：")
        sections.append(MessageFormatter.format_token_list(data.get('buys', []), 'buy'))
        
        # 卖出数据
        sections.append("📉 卖出最多：")
        sections.append(MessageFormatter.format_token_list(data.get('sells', []), 'sell'))
        
        return "\n".join(sections)
    
    @staticmethod
    def format_time_period_section(hours: int, chains_data: Dict) -> str:
        """
        格式化时间段部分
        
        Args:
            hours: 小时数
            chains_data: 所有链的数据
            
        Returns:
            格式化后的文本
        """
        emoji = MessageFormatter.TIME_EMOJIS.get(hours, '⏰')
        
        sections = [
            "━━━━━━━━━━━━━━━━━━",
            f"{emoji} 过去 {hours} 小时",
            ""
        ]
        
        for chain_name in Config.CHAINS.values():
            if chain_name in chains_data:
                sections.append(MessageFormatter.format_chain_section(
                    chain_name,
                    chains_data[chain_name]
                ))
        
        return "\n".join(sections)
    
    @staticmethod
    def format_report(report_data: Dict) -> str:
        """
        格式化完整报告
        
        Args:
            report_data: 完整的监控报告数据
            
        Returns:
            格式化后的 Telegram 消息（Markdown 格式）
        """
        # 报告头部
        timestamp = datetime.fromisoformat(report_data['timestamp'])
        time_str = timestamp.strftime('%Y-%m-%d %H:%M')
        
        message = [
            "📊 *智能资金监控报告*",
            f"🕐 时间：{time_str}",
            ""
        ]
        
        # 各时间段数据
        data = report_data.get('data', {})
        
        for hours in Config.TIME_PERIODS:
            period_key = f'{hours}h'
            if period_key in data:
                message.append(MessageFormatter.format_time_period_section(
                    hours,
                    data[period_key]
                ))
        
        # 报告尾部
        message.extend([
            "━━━━━━━━━━━━━━━━━━",
            "💡 数据来源：Nansen",
            f"🔄 下次更新：{Config.REPORT_INTERVAL_HOURS}小时后"
        ])
        
        return "\n".join(message)
    
    @staticmethod
    def format_error_message(error: str) -> str:
        """
        格式化错误消息
        
        Args:
            error: 错误信息
            
        Returns:
            格式化后的错误消息
        """
        return f"⚠️ *错误*\n\n{error}\n\n请检查配置或联系管理员。"
    
    @staticmethod
    def format_status_message() -> str:
        """
        格式化状态消息
        
        Returns:
            当前配置状态
        """
        chains = ", ".join(Config.CHAINS.values())
        periods = ", ".join([f"{h}h" for h in Config.TIME_PERIODS])
        
        return (
            "✅ *监控状态*\n\n"
            f"📡 监控链：{chains}\n"
            f"⏰ 时间段：{periods}\n"
            f"🔄 报告间隔：每 {Config.REPORT_INTERVAL_HOURS} 小时\n"
            f"📊 每组显示：前 {Config.TOP_TOKENS_COUNT} 个代币\n\n"
            "💡 使用 /report 立即生成报告"
        )
