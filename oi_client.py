import requests
import json
import time
from typing import List, Dict, Optional

class CoinalyzeClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.coinalyze.net/v1"
        self.headers = {'api_key': self.api_key}

    # ─────────────────────────────────────────
    # Low-level: GET with Retry-After backoff
    # ─────────────────────────────────────────

    def _get(self, endpoint: str, params: Dict = None,
             max_retries: int = 4, base_delay: float = 15.0) -> Optional[requests.Response]:
        """
        GET with automatic retry on 429.
        Reads 'Retry-After' header (seconds) if present; otherwise uses
        exponential back-off starting from base_delay.
        Returns None if all retries are exhausted.
        """
        if params is None:
            params = {}
        params['api_key'] = self.api_key
        url = f"{self.base_url}/{endpoint}"

        for attempt in range(max_retries + 1):
            try:
                res = requests.get(url, headers=self.headers, params=params, timeout=20)
                if res.status_code == 200:
                    return res
                if res.status_code == 429:
                    if attempt >= max_retries:
                        print(f"[Coinalyze] {endpoint}: 429 after {max_retries} retries – giving up.")
                        return None
                    # Honour server-supplied Retry-After; fall back to doubling delay
                    retry_after = res.headers.get("Retry-After")
                    if retry_after:
                        wait = float(retry_after)
                    else:
                        wait = base_delay * (2 ** attempt)       # 15 → 30 → 60 → 120 s
                    print(f"[Coinalyze] 429 on {endpoint} (attempt {attempt+1}). "
                          f"Waiting {wait:.0f}s …")
                    time.sleep(wait)
                    continue
                # Any other error – log and give up immediately
                print(f"[Coinalyze] {endpoint} error {res.status_code}: {res.text[:200]}")
                return None
            except Exception as e:
                print(f"[Coinalyze] {endpoint} exception: {e}")
                return None
        return None

    # ─────────────────────────────────────────
    # Public helpers
    # ─────────────────────────────────────────

    def get_supported_markets(self) -> List[Dict]:
        res = self._get("future-markets")
        return res.json() if res else []

    def get_current_oi(self, symbols: str) -> List[Dict]:
        res = self._get("open-interest", params={"symbols": symbols})
        return res.json() if res else []

    def get_oi_history(self, symbols: str, interval: str = "daily") -> List[Dict]:
        now = int(time.time())
        five_days_ago = now - (5 * 24 * 3600)
        params = {
            "symbols": symbols,
            "interval": interval,
            "from": five_days_ago,
            "to": now,
        }
        res = self._get("open-interest-history", params=params)
        return res.json() if res else []

    # ─────────────────────────────────────────
    # Main strategy
    # ─────────────────────────────────────────

    def get_top_oi_gainers(self, limit: int = 20) -> List[Dict]:
        """
        Conservative fetch strategy designed to avoid 429:
          1. Pull market list → keep only Binance USDT-perps (exchange == 'A')
          2. Fetch current OI in small batches (10 symbols each) with 5s gaps
             Cap at 40 symbols to minimise request count
          3. Sort by OI value, take top 20 for history lookup
          4. Fetch history in batches of 10 with 15s gaps
        """
        # ── Step 1: markets ──────────────────
        markets = self.get_supported_markets()
        if not markets:
            return []

        binance_perps = [
            m['symbol'] for m in markets
            if m.get('exchange') == 'A' and 'USDT' in m.get('symbol', '')
        ]
        if not binance_perps:
            return []

        # ── Step 2: current OI (small batches) ───────────────
        CURRENT_BATCH  = 10          # symbols per request
        CURRENT_CAP    = 40          # max symbols we look at
        CURRENT_SLEEP  = 6           # seconds between batches

        current_oi_data: List[Dict] = []
        candidates = binance_perps[:CURRENT_CAP]

        for i in range(0, len(candidates), CURRENT_BATCH):
            batch = candidates[i : i + CURRENT_BATCH]
            data  = self.get_current_oi(",".join(batch))
            if data:
                current_oi_data.extend(data)
            if i + CURRENT_BATCH < len(candidates):          # no sleep after last batch
                time.sleep(CURRENT_SLEEP)

        if not current_oi_data:
            print("[Coinalyze] No current OI data obtained.")
            return []

        # ── Step 3: pick top symbols by OI value ────────────
        HISTORY_SYMBOLS = 20         # run history only on top-N
        HISTORY_BATCH   = 10         # symbols per history request
        HISTORY_SLEEP   = 20         # seconds between history batches

        top_symbols = [
            x['symbol']
            for x in sorted(current_oi_data, key=lambda x: x.get('value', 0), reverse=True)
        ][:HISTORY_SYMBOLS]

        # ── Step 4: history ──────────────────────────────────
        results: List[Dict] = []
        for i in range(0, len(top_symbols), HISTORY_BATCH):
            batch  = top_symbols[i : i + HISTORY_BATCH]
            symbol_query = ",".join(batch)
            history_list = self.get_oi_history(symbol_query)

            if history_list:
                for item in history_list:
                    sym    = item.get('symbol', '').replace('USDT_PERP.A', '')
                    h_data = item.get('history', [])
                    if len(h_data) >= 2:
                        try:
                            # Support both [ts,o,h,l,c] and [ts,val] formats
                            entry = h_data[-1]
                            prev  = h_data[-2]
                            curr_c = entry[4] if len(entry) >= 5 else entry[1]
                            prev_c = prev[4]  if len(prev)  >= 5 else prev[1]
                            if prev_c > 0:
                                change_pct = (curr_c - prev_c) / prev_c * 100
                                results.append({
                                    'symbol':        sym,
                                    'oi_change_pct': change_pct,
                                    'oi_value':      curr_c,
                                })
                        except Exception:
                            pass
            else:
                print(f"[Coinalyze] History empty for batch starting {batch[0]}")

            if i + HISTORY_BATCH < len(top_symbols):
                time.sleep(HISTORY_SLEEP)

        results.sort(key=lambda x: x['oi_change_pct'], reverse=True)
        return results[:limit]


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    key = os.getenv("COINALYZE_API_KEY", "")
    client = CoinalyzeClient(key)
    print("Fetching OI gainers …")
    gainers = client.get_top_oi_gainers(limit=10)
    for g in gainers:
        print(g)
