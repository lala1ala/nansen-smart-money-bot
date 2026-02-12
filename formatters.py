"""
消息格式化模块 - 简洁版
将监控数据格式化为简洁的 Telegram 消息
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
        'BNB': '🟡'
    }
    
    @staticmethod
    def format_value(value: float) -> str:
        """
        格式化美元价值
        """
        if value >= 1_000_000_000:
            return f"${value/1_000_000_000:.2f}B"
        elif value >= 1_000_000:
            return f"${value/1_000_000:.1f}M"
        elif value >= 1_000:
            return f"${value/1_000:.1f}K"
        else:
            return f"${value:.2f}"
    
    @staticmethod
    def format_percent(pct: float) -> str:
        """
        格式化百分比
        """
        if pct > 0:
            return f"+{pct:.2f}%"
        else:
            return f"{pct:.2f}%"
    
    @staticmethod
    def format_holdings_list(tokens: List[Dict]) -> str:
        """
        格式化持仓列表（紧凑格式）
        """
        if not tokens:
            return "  📭 暂无数据\n"
        
        result = []
        for idx, token in enumerate(tokens, 1):
            symbol = token['token']
            value = MessageFormatter.format_value(token['value_usd'])
            change_pct = token.get('change_pct', 0)
            
            line = f"  {idx}. {symbol}: {value}"
            
            # 如果有24h变化，显示变化
            if abs(change_pct) > 0.01:
                change_str = MessageFormatter.format_percent(change_pct)
                line += f" ({change_str})"
            
            result.append(line)
        
        return "\n".join(result) + "\n"
    
    @staticmethod
    def format_changes_list(tokens: List[Dict], change_type: str) -> str:
        """
        格式化变化列表
        change_type: 'increase' 或 'decrease'
        """
        if not tokens:
            return "  📭 暂无\n"
        
        result = []
        for idx, token in enumerate(tokens, 1):
            symbol = token['token']
            change_pct = token.get('change_pct', 0)
            value = MessageFormatter.format_value(token['value_usd'])
            
            change_str = MessageFormatter.format_percent(change_pct)
            result.append(f"  {idx}. {symbol}: {change_str} (持仓: {value})")
        
        return "\n".join(result) + "\n"
    
    @staticmethod
    def format_chain_section(chain_name: str, data: Dict) -> str:
        """
        格式化单个链的数据（新格式）
        """
        emoji = MessageFormatter.CHAIN_EMOJIS.get(chain_name, '⚪')
        
        sections = [
            f"{emoji} **{chain_name}**",
            ""
        ]
        
        # 检查是否有错误
        if 'error' in data:
            sections.append(f"  ⚠️ 数据获取失败\n")
            return "\n".join(sections)
        
        # Top 持仓
        sections.append("💰 持仓最多（按价值）:")
        sections.append(MessageFormatter.format_holdings_list(data.get('top_holdings', [])))
        
        # 增持最多
        increases = data.get('biggest_increases', [])
        if increases:
            sections.append("📈 增持最多(24h):")
            sections.append(MessageFormatter.format_changes_list(increases, 'increase'))
        
        # 减持最多  
        decreases = data.get('biggest_decreases', [])
        if decreases:
            sections.append("📉 减持最多(24h):")
            sections.append(MessageFormatter.format_changes_list(decreases, 'decrease'))
        
        return "\n".join(sections)
    
    @staticmethod
    def format_report(report_data: Dict) -> str:
        """
        格式化完整报告（简洁版）
        """
        # 报告头部
        timestamp = datetime.fromisoformat(report_data['timestamp'])
        time_str = timestamp.strftime('%Y-%m-%d %H:%M')
        
        message = [
            "📊 **智能资金监控报告**",
            f"🕐 {time_str}",
            ""
        ]
        
        # 数据（只显示24小时）
        data = report_data.get('data', {})
        period_data = data.get('24h', {})
        
        if period_data:
            for chain_name in Config.CHAINS.values():
                if chain_name in period_data:
                    message.append(MessageFormatter.format_chain_section(
                        chain_name,
                        period_data[chain_name]
                    ))
        
        # 报告尾部
        message.extend([
            "━━━━━━━━━━━━━━━━━━",
            "💡 数据来源: Nansen Smart Money",
            f"🔄 下次更新: {Config.REPORT_INTERVAL_HOURS}小时后"
        ])
        
        return "\n".join(message)
    
    @staticmethod
    def format_error_message(error: str) -> str:
        """格式化错误消息"""
        return f"⚠️ **错误**\n\n{error}\n\n请检查配置或联系管理员。"
    
    @staticmethod
    def format_status_message() -> str:
        """格式化状态消息"""
        chains = ", ".join(Config.CHAINS.values())
        
        return (
            "✅ **监控状态**\n\n"
            f"📡 监控链: {chains}\n"
            f"⏰ 时间段: 24小时数据\n"
            f"🔄 报告间隔: 每 {Config.REPORT_INTERVAL_HOURS} 小时\n"
            f"📊 显示: Top {Config.TOP_TOKENS_COUNT} 代币\n\n"
            "💡 自动运行中..."
        )
