"""
图片渲染模块
将 Smart Money 净流入数据渲染成深色主题表格图片
"""
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from datetime import datetime
from typing import List, Dict
import pytz
import os


# ── 颜色主题 ────────────────────────────────────────────
BG_COLOR        = (13, 17, 23)       # #0D1117  深黑背景
HEADER_BG       = (22, 27, 34)       # #161B22  表头背景
ROW_BG_1        = (13, 17, 23)       # 奇数行
ROW_BG_2        = (22, 27, 34)       # 偶数行
BORDER_COLOR    = (48, 54, 61)       # #30363D  边框
NANSEN_GREEN    = (0, 255, 163)      # #00FFA3  Nansen 品牌色
TEXT_WHITE      = (230, 237, 243)    # 主文字
TEXT_GRAY       = (139, 148, 158)    # 次要文字
GREEN_FLOW      = (63, 185, 80)      # 净流入绿色
TITLE_BG        = (0, 150, 95)       # 标题栏绿色

# ── 布局参数 ────────────────────────────────────────────
IMG_WIDTH   = 820
TITLE_H     = 56
HEADER_H    = 36
ROW_H       = 38
PADDING     = 20
FOOTER_H    = 32

# 列宽定义 [#, Token, Price, Chain, Traders, Net Flows]
COL_WIDTHS  = [36, 180, 130, 90, 90, 170]
COL_HEADERS = ['#', 'Token', 'Price', 'Chain', 'Traders', 'Net Flows ↓']

TIMEFRAME_LABELS = {
    '10m': '10 Min',
    '1h':  '1 Hour',
    '6h':  '6 Hours',
}


def _get_font(size: int, bold: bool = False):
    """尝试加载系统字体，失败时使用默认字体"""
    font_paths = [
        # Windows
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        # Linux (GitHub Actions)
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    ]
    bold_paths = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    search = bold_paths if bold else font_paths
    for path in search:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _format_price(price: float) -> str:
    if price is None:
        return 'N/A'
    if price >= 1:
        return f"${price:,.2f}"
    elif price >= 0.01:
        return f"${price:.4f}"
    elif price >= 0.0001:
        return f"${price:.6f}"
    else:
        return f"${price:.2e}"


def _format_flow(value: float) -> str:
    if value is None:
        return 'N/A'
    if value >= 1_000_000:
        return f"+${value/1_000_000:.2f}M"
    elif value >= 1_000:
        return f"+${value/1_000:.1f}K"
    else:
        return f"+${value:.0f}"


def _format_chain(chain: str) -> str:
    mapping = {
        'ethereum': 'ETH',
        'solana': 'SOL',
        'base': 'BASE',
        'bnb': 'BNB',
    }
    return mapping.get(chain, chain.upper()[:4])


def render_netflow_image(tokens: List[Dict], timeframe: str) -> BytesIO:
    """
    将 Token Screener 净流入数据渲染成图片
    
    Args:
        tokens: 代币列表（来自 NansenClient）
        timeframe: 时间段字符串 ('10m', '1h', '6h')
    
    Returns:
        PNG 图片的 BytesIO 对象
    """
    rows = max(len(tokens), 1)
    img_height = TITLE_H + HEADER_H + rows * ROW_H + FOOTER_H + 10
    
    img = Image.new('RGB', (IMG_WIDTH, img_height), color=BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # 字体
    font_title  = _get_font(16, bold=True)
    font_header = _get_font(12, bold=True)
    font_body   = _get_font(13)
    font_body_b = _get_font(13, bold=True)
    font_small  = _get_font(11)
    
    # ── 标题栏 ──────────────────────────────────────────
    draw.rectangle([0, 0, IMG_WIDTH, TITLE_H], fill=TITLE_BG)
    
    tf_label = TIMEFRAME_LABELS.get(timeframe, timeframe.upper())
    title_text = f"🔥 Smart Money 净流入 Top{len(tokens)}  |  {tf_label}"
    draw.text((PADDING, 14), title_text, font=font_title, fill=TEXT_WHITE)
    
    # 右上角时间（北京时间）
    tz = pytz.timezone('Asia/Shanghai')
    now = datetime.now(tz)
    time_str = now.strftime('%m-%d  %H:%M  CST')
    time_w = draw.textlength(time_str, font=font_small)
    draw.text((IMG_WIDTH - time_w - PADDING, 20), time_str, font=font_small, fill=TEXT_WHITE)
    
    # ── 表头 ────────────────────────────────────────────
    y = TITLE_H
    draw.rectangle([0, y, IMG_WIDTH, y + HEADER_H], fill=HEADER_BG)
    
    x = PADDING
    for i, (header, width) in enumerate(zip(COL_HEADERS, COL_WIDTHS)):
        align = 'right' if i >= 4 else 'left'
        tw = draw.textlength(header, font=font_header)
        if align == 'right':
            draw.text((x + width - tw - 4, y + 10), header, font=font_header, fill=TEXT_GRAY)
        else:
            draw.text((x + 4, y + 10), header, font=font_header, fill=TEXT_GRAY)
        x += width
    
    # 表头下分隔线
    draw.line([(0, y + HEADER_H), (IMG_WIDTH, y + HEADER_H)], fill=BORDER_COLOR, width=1)
    
    # ── 数据行 ──────────────────────────────────────────
    y = TITLE_H + HEADER_H
    
    if not tokens:
        draw.text((PADDING, y + 12), "暂无数据", font=font_body, fill=TEXT_GRAY)
    
    for idx, token in enumerate(tokens):
        row_bg = ROW_BG_1 if idx % 2 == 0 else ROW_BG_2
        draw.rectangle([0, y, IMG_WIDTH, y + ROW_H], fill=row_bg)
        
        # 行分隔线
        draw.line([(0, y + ROW_H - 1), (IMG_WIDTH, y + ROW_H - 1)], fill=BORDER_COLOR, width=1)
        
        # 列数据
        symbol    = token.get('token_symbol') or token.get('symbol', '???')
        price     = token.get('price_usd') or token.get('price', 0)
        chain     = token.get('chain', '')
        traders   = token.get('smart_money_traders') or token.get('traders', 0)
        net_flow  = token.get('net_flow') or token.get('smart_money_net_flow', 0)
        
        row_data = [
            str(idx + 1),
            symbol,
            _format_price(price),
            _format_chain(chain),
            str(traders),
            _format_flow(net_flow),
        ]
        
        x = PADDING
        for i, (cell, width) in enumerate(zip(row_data, COL_WIDTHS)):
            text_y = y + (ROW_H - 14) // 2
            
            # 颜色选择
            if i == 1:      # Token symbol → 白色加粗
                color = TEXT_WHITE
                font  = font_body_b
            elif i == 5:    # Net Flows → 绿色加粗
                color = GREEN_FLOW
                font  = font_body_b
            elif i == 0:    # Index → 灰色
                color = TEXT_GRAY
                font  = font_body
            else:
                color = TEXT_WHITE
                font  = font_body
            
            # 右对齐数值列
            if i >= 4:
                tw = draw.textlength(cell, font=font)
                draw.text((x + width - tw - 8, text_y), cell, font=font, fill=color)
            else:
                draw.text((x + 4, text_y), cell, font=font, fill=color)
            
            x += width
        
        y += ROW_H
    
    # ── 底部 footer ─────────────────────────────────────
    draw.rectangle([0, y, IMG_WIDTH, y + FOOTER_H], fill=HEADER_BG)
    draw.line([(0, y), (IMG_WIDTH, y)], fill=BORDER_COLOR, width=1)
    
    footer_text = "📊 Data: Nansen Smart Money  |  Chains: ETH · SOL · BASE"
    draw.text((PADDING, y + 9), footer_text, font=font_small, fill=TEXT_GRAY)
    
    # Nansen 绿色品牌点缀（右下角）
    brand = "nansen.ai"
    bw = draw.textlength(brand, font=font_small)
    draw.text((IMG_WIDTH - bw - PADDING, y + 9), brand, font=font_small, fill=NANSEN_GREEN)
    
    # ── 输出 BytesIO ─────────────────────────────────────
    output = BytesIO()
    img.save(output, format='PNG', optimize=True)
    output.seek(0)
    return output


# ── 测试入口 ─────────────────────────────────────────────
if __name__ == '__main__':
    # 用假数据测试图片渲染
    fake_tokens = [
        {'token_symbol': 'PUNCH',   'price_usd': 0.0305, 'chain': 'solana',   'smart_money_traders': 2, 'net_flow': 2880},
        {'token_symbol': 'GROK-1',  'price_usd': 0.0108, 'chain': 'solana',   'smart_money_traders': 1, 'net_flow': 931},
        {'token_symbol': 'YGG',     'price_usd': 0.0478, 'chain': 'ethereum', 'smart_money_traders': 1, 'net_flow': 1370},
        {'token_symbol': 'LOBSTAR', 'price_usd': 0.0118, 'chain': 'base',     'smart_money_traders': 1, 'net_flow': 2370},
        {'token_symbol': 'HFT',     'price_usd': 0.0158, 'chain': 'ethereum', 'smart_money_traders': 1, 'net_flow': 470},
        {'token_symbol': 'WAMA',    'price_usd': 0.0383, 'chain': 'solana',   'smart_money_traders': 3, 'net_flow': 401},
        {'token_symbol': 'CHUD',    'price_usd': 0.0032, 'chain': 'solana',   'smart_money_traders': 2, 'net_flow': 198},
        {'token_symbol': 'ONYC',    'price_usd': 1.08,   'chain': 'ethereum', 'smart_money_traders': 1, 'net_flow': 6000},
        {'token_symbol': 'REVV',    'price_usd': 0.0289, 'chain': 'ethereum', 'smart_money_traders': 1, 'net_flow': 1490},
        {'token_symbol': 'ALIENS',  'price_usd': 0.0133, 'chain': 'solana',   'smart_money_traders': 1, 'net_flow': 326},
    ]
    
    for tf in ['10m', '1h', '6h']:
        buf = render_netflow_image(fake_tokens, tf)
        fname = f'test_output_{tf}.png'
        with open(fname, 'wb') as f:
            f.write(buf.read())
        print(f"✅ 已生成 {fname}")
