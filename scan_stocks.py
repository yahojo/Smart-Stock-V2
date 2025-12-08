import yfinance as yf
import pandas as pd
import json
import os
import math
from datetime import datetime, timedelta

# --- 設定要掃描的觀察名單 ---
tickers = [
    "2330.TW", "2454.TW", "2317.TW", "2603.TW", "3008.TW", 
    "3231.TW", "2382.TW", "2303.TW", "2881.TW", "2882.TW",
    "2609.TW", "2615.TW", "1519.TW", "1513.TW", "6669.TW"
]

print(f"啟動智慧選股掃描，共 {len(tickers)} 檔股票...")
results = []

# --- 數據淨化函式 (關鍵修改) ---
def safe_num(val):
    """
    將 NaN 或無限大 (inf) 轉換為 0，
    避免 JSON 輸出時發生語法錯誤。
    """
    if pd.isna(val) or math.isinf(val):
        return 0
    return round(float(val), 2)

for ticker in tickers:
    try:
        # 1. 抓取資料
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        
        if len(df) < 20: # 至少要有20天資料才能算基礎均線
            print(f"跳過 {ticker}: 資料嚴重不足")
            continue

        # 2. 計算基礎數據
        current_price = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2]
        change_percent = ((current_price - prev_close) / prev_close) * 100
        
        volume = df['Volume'].iloc[-1]
        avg_vol_20 = df['Volume'].rolling(window=20).mean().iloc[-1]
        
        # 3. 計算均線 (MA) - 如果天數不足，rolling 會產生 NaN，稍後由 safe_num 處理
        ma5 = df['Close'].rolling(window=5).mean().iloc[-1]
        ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
        ma60 = df['Close'].rolling(window=60).mean().iloc[-1]
        ma200 = df['Close'].rolling(window=200).mean().iloc[-1]
        
        # 4. 計算 52 週高點 (VCP 策略需要)
        high_52w = df['High'].rolling(window=252).max().iloc[-1]
        
        # 5. 計算 KD 指標 (9日 RSV)
        low_min = df['Low'].rolling(window=9).min()
        high_max = df['High'].rolling(window=9).max()
        rsv = (df['Close'] - low_min) / (high_max - low_min) * 100
        
        k_val = rsv.rolling(window=3).mean().iloc[-1]
        d_val = k_val # 簡化
        prev_k = rsv.rolling(window=3).mean().iloc[-2]
        prev_d = prev_k # 簡化

        # 6. 打包資料 (使用 safe_num 過濾所有數值)
        stock_data = {
            "id": ticker.replace(".TW", ""),
            "name": ticker,
            "price": safe_num(current_price),
            "changePercent": safe_num(change_percent),
            "volume": int(volume) if not pd.isna(volume) else 0,
            "avgVolume20": int(avg_vol_20) if not pd.isna(avg_vol_20) else 0,
            "ma5": safe_num(ma5),
            "ma20": safe_num(ma20),
            "ma60": safe_num(ma60),
            "ma200": safe_num(ma200),
            "high52w": safe_num(high_52w), # 這裡是這次錯誤的主因 (NaN)
            "kVal": safe_num(k_val),
            "dVal": safe_num(d_val),
            "prevK": safe_num(prev_k),
            "prevD": safe_num(prev_d),
            "winRate": 70,
            "lastTransaction": None 
        }
        
        results.append(stock_data)
        print(f"✅ 已處理: {ticker}")

    except Exception as e:
        print(f"❌ 錯誤 {ticker}: {e}")

# --- 輸出結果 ---
os.makedirs('public', exist_ok=True)
json_path = 'public/data.json'

with open(json_path, 'w', encoding='utf-8') as f:
    # 這裡加入 allow_nan=False 是雙保險，如果有漏網之魚會直接報錯提醒
    json.dump(results, f, ensure_ascii=False, indent=2, allow_nan=False)

print(f"\n🎉 掃描完成！共產出 {len(results)} 筆資料。")