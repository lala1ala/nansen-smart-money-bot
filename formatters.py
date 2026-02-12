"""
消息格式化模块 - 精简版
聪明钱净流入/流出报告
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
            return f"${value/1_000_000_000:.1f}B"
        elif value >= 1_000_000:
            return f"${value/1_000_000:.1f}M"
        elif value >= 1_000:
            return f"${value/1_000:.1f}K"
        else:
            return f"${value:.0f}"
    
    @staticmethod
    def format_flow_list(tokens: List[Dict], flow_type: str) -> str:
        """
        格式化流入/流出列表
        
        Args:
            tokens: 代币列表
            flow_type: 'inflow' 或 'outflow'
        
        Returns:
            格式化后的文本
        """
        if not tokens:
            return "  📭 暂无明显流动\n"
        
        result = []
        prefix = "+" if flow_type == 'inflow' else "-"
        
        for idx, token in enumerate(tokens, 1):
            symbol = token['token']
            net_flow = MessageFormatter.format_value(token['net_flow_usd'])
            
            result.append(f"  {idx}. {symbol} {prefix}{net_flow}")
        
        return "\n".join(result) + "\n"
    
    @staticmethod
    def format_chain_section(chain_name: str, data: Dict) -> str:
        """
        格式化单个链的数据（净流入/流出版）
        
        Args:
            chain_name: 链名称
            data: 包含 net_inflows 和 net_outflows 的数据
        
        Returns:
            格式化后的文本
        """
        emoji = MessageFormatter.CHAIN_EMOJIS.get(chain_name, '⚪')
        
        sections = [
            f"◆ **{emoji} {chain_name} 聪明钱净流动 TOP 5 (24h)**",
            ""
        ]
        
        # 检查是否有错误
        if 'error' in data:
            sections.append("  ⚠️ 数据获取失败\n")
            return "\n".join(sections)
        
        # 净流入
        net_inflows = data.get('net_inflows', [])
        if net_inflows:
            sections.append("💰 **净流入：**")
            sections.append(MessageFormatter.format_flow_list(net_inflows, 'inflow'))
        
        # 净流出
        net_outflows = data.get('net_outflows', [])
        if net_outflows:
            sections.append("📉 **净流出：**")
            sections.append(MessageFormatter.format_flow_list(net_outflows, 'outflow'))
        
        # 如果都没有数据
        if not net_inflows and not net_outflows:
            sections.append("  📭 24h内无明显流动变化\n")
        
        sections.append("")  # 空行分隔
        return "\n".join(sections)
    
    @staticmethod
    def format_report(report_data: Dict) -> str:
        """
        格式化完整报告（精简版）
        
        Args:
            report_data: 完整的监控报告数据
        
        Returns:
            格式化后的 Telegram 消息
        """
        # 报告头部
        timestamp = datetime.fromisoformat(report_data['timestamp'])
        time_str = timestamp.strftime('%Y-%m-%d %H:%M')
        
        message = [
            "📊 **聪明钱流动监控**",
            f"🕐 {time_str} | ⏱ 24小时数据",
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
            "📌 净流入 = 聪明钱增持金额",
            "📌 净流出 = 聪明钱减持金额",
            f"🔄 下次更新: {Config.REPORT_INTERVAL_HOURS}小时后"
        ])
        
        return "\n".join(message)
    
    @staticmethod
    def format_error_message(error: str) -> str:
        """格式化错误消息"""
        return f"⚠️ **错误**\n\n{error}\n\n请检查配置。"
    
    @staticmethod
    def format_status_message() -> str:
        """格式化状态消息"""
        chains = ", ".join(Config.CHAINS.values())
        
        return (
            "✅ **监控状态**\n\n"
            f"📡 监控链: {chains}\n"
            f"⏰ 数据范围: 24小时净流动\n"
            f"🔄 报告间隔: 每 {Config.REPORT_INTERVAL_HOURS} 小时\n"
            f"📊 每链显示: Top 5 流入 + Top 5 流出\n\n"
            "💡 自动运行中..."
        )
