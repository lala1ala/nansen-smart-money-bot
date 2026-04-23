import sqlite3
from datetime import datetime
from typing import List, Dict

class DailyStatsDB:
    def __init__(self, db_path: str = "data_history.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS token_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    source TEXT,
                    token TEXT,
                    rank INTEGER,
                    value REAL
                )
            ''')
            # Add index for fast querying
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_date_token ON token_stats(date, token)')
            conn.commit()

    def save_daily_snapshot(self, date: str, source: str, tokens: List[Dict]):
        """
        保存每日快照
        tokens: [{'token': 'ETH', 'rank': 1, 'value': 12345.0}, ...]
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 避免重复插入同一天的同源数据，先删除旧的
            cursor.execute('DELETE FROM token_stats WHERE date = ? AND source = ?', (date, source))
            
            records = [
                (date, source, t['token'].upper(), t.get('rank', 0), t.get('value', 0.0))
                for t in tokens
            ]
            cursor.executemany('''
                INSERT INTO token_stats (date, source, token, rank, value)
                VALUES (?, ?, ?, ?, ?)
            ''', records)
            conn.commit()

    def get_overlapping_tokens(self, date: str, sources: List[str], min_overlap: int = 2) -> Dict[str, List[str]]:
        """
        获取某个日期下，在多个榜单中重合的代币
        返回: {'ETH': ['nansen_sm', 'hyperliquid'], ...}
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 获取指定日期的所有指定来源数据
            placeholders = ','.join(['?'] * len(sources))
            query = f'''
                SELECT token, source 
                FROM token_stats 
                WHERE date = ? AND source IN ({placeholders})
            '''
            params = [date] + sources
            cursor.execute(query, params)
            rows = cursor.fetchall()

            # 聚合数据
            token_sources = {}
            for token, source in rows:
                if token not in token_sources:
                    token_sources[token] = []
                token_sources[token].append(source)
            
            # 过滤
            return {k: v for k, v in token_sources.items() if len(v) >= min_overlap}

    def get_longitudinal_tokens(self, end_date: str, days: int, min_appearances: int = 2) -> Dict[str, Dict]:
        """
        纵向追踪：过去 N 天内，某个代币在某个 source 中出现的次数
        返回: {'ETH': {'nansen_sm': 3, 'hyperliquid': 2}, ...}
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            query = '''
                SELECT token, source, COUNT(DISTINCT date) as days_appeared
                FROM token_stats
                WHERE date <= ? AND date > date(?, '-' || ? || ' days')
                GROUP BY token, source
            '''
            cursor.execute(query, (end_date, end_date, days))
            rows = cursor.fetchall()
            
            result = {}
            for token, source, days_cnt in rows:
                if days_cnt >= min_appearances:
                    if token not in result:
                        result[token] = {}
                    result[token][source] = days_cnt
            
            return result

if __name__ == "__main__":
    db = DailyStatsDB()
    print("DB Initialized")
