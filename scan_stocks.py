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
    "2609.TW", "2615.TW", "1519.TW", "1513.TW", "6669.TW",
    "2379.TW", "3034.TW", "4958.TW", "2027.TW", "2031.TW",
    "1609.TW", "1708.TW", "2066.TWO", "2258.TW", "2327.TW",
    "2354.TW", "2449.TW", "3005.TW", "3010.TW", "3088.TWO",
    "3213.TWO", "3227.TWO", "3416.TW", "3479.TWO", "3665.TW",
    "3701.TW", "3717.TW", "4137.TW", "4162.TWO", "6883.TWO",
    "1504.TW", "2308.TW", "2383.TW", "6274.TWO", "6213.TW",
    "2376.TW", "2377.TW", "2368.TW", "2345.TW", "3661.TW",
    "2301.TW", "3653.TW", "3017.TW", "3324.TWO", "2357.TW",
    "2353.TW", "8996.TW", "3035.TW", "6643.TWO", "6533.TW",
    "3443.TW", "6510.TWO", "6679.TWO", "6196.TW", "2395.TW",
    "7799.TW", "3014.TW", "8299.TWO", "4536.TW", "4549.TWO",
    "4585.TW", "4771.TW", "4909.TWO", "5203.TW", "5243.TW",
    "5289.TWO", "5306.TW", "5607.TW" , "5871.TW", "6245.TWO",
    "6282.TW", "6285.TW", "6446.TW", "6491.TW", "6525.TW",
    "6550.TW", "6585.TW", "6591.TW", "6605.TW", "6703.TWO",
    "6782.TW", "6793.TWO", "6883.TWO", "6965.TW", "8016.TW",
    "8114.TW", "8183.TWO", "8213.TW", "9802.TW", "9939.TW",
    "9941.TW", "9957.TWO", "9945.TW", "2915.TW", "6753.TW",
    "2634.TW", "2645.TW", "3178.TWO", "1342.TW", "5222.TW", 
    "6416.TW", "6414.TW", "3289.TWO", "6526.TW", "7714.TWO",
    "2328.TW", "5274.TWO", "2360.TW", "6841.TWO", "3004.TW",
    "3213.TWO", "3005.TW", "6732.TWO", "7734.TWO", "3693.TWO",
    "7769.TW", "2481.TW", "2347.TW", "1720.TW", "4129.TWO",
    "1707.TW", "1736.TW", "1785.TWO", "8358.TWO", "1584.TWO",
    "5009.TWO", "2211.TW", "8341.TW", "3019.TW", "6239.TW",
    "1786.TW", "1785.TWO", "3706.TW", "6664.TWO", "8016.TW",
    "5225.TW", "4763.TW", "7749.TW", "3583.TW", "6290.TWO",
    "6789.TW", "2476.TW", "5263.TWO", "2457.TW", "8021.TW",
    "3529.TWO", "3105.TWO", "8086.TWO", "2455.TW", "6202.TW",
    "5629.TW", "6515.TW", "6789.TW", "3526.TWO", "6677.TWO",
    "3413.TW", "4966.TWO", "8227.TWO", "6235.TW", "3645.TW", 
    "2049.TW", "1319.TW", "8064.TWO", "6683.TWO", "5439.TWO",
    "6104.TWO", "3189.TW", "2313.TW", "3037.TW", "8046.TW",
    "3305.TW", "2436.TW", "2337.TW", "3006.TW", "3715.TW",
    "2408.TW", "2344.TW", "3260.TWO", "2451.TW", "6579.TW",
    "3711.TW", "1558.TW", "6862.TW", "6869.TW", "4760.TWO"
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