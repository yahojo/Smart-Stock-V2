import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime, timedelta

# --- 設定要掃描的觀察名單 ---
# 為了示範，這裡列出幾檔熱門權值股與強勢股
# 您可以在這個列表中自由增加想監控的股票代號 (台股請務必加上 .TW)
tickers = [
    "2330.TW", "2454.TW", "2317.TW", "2603.TW", "3008.TW", 
    "3231.TW", "2382.TW", "2303.TW", "2881.TW", "2882.TW",
    "2609.TW", "2615.TW", "1519.TW", "1513.TW", "6669.TW"
]

print(f"啟動智慧選股掃描，共 {len(tickers)} 檔股票...")
results = []

for ticker in tickers:
    try:
        # 1. 抓取資料 (取得過去 1 年的歷史數據)
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        
        # 如果資料太少(新上市或暫停交易)，就跳過
        if len(df) < 200:
            print(f"跳過 {ticker}: 交易天數不足 200 天")
            continue

        # 2. 計算基礎數據
        current_price = df['Close'].iloc[-1]   # 最新收盤價
        prev_close = df['Close'].iloc[-2]      # 昨日收盤價
        change_percent = ((current_price - prev_close) / prev_close) * 100 # 漲幅%
        
        volume = df['Volume'].iloc[-1]         # 當日成交量
        avg_vol_20 = df['Volume'].rolling(window=20).mean().iloc[-1] # 20日均量
        
        # 3. 計算均線 (MA)
        ma5 = df['Close'].rolling(window=5).mean().iloc[-1]
        ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
        ma60 = df['Close'].rolling(window=60).mean().iloc[-1]
        ma200 = df['Close'].rolling(window=200).mean().iloc[-1]
        
        # 4. 計算 52 週高點 (VCP 策略需要)
        high_52w = df['High'].rolling(window=252).max().iloc[-1]
        
        # 5. 計算 KD 指標 (9日 RSV)
        # 這是簡化版算法，用於捕捉大致趨勢
        low_min = df['Low'].rolling(window=9).min()
        high_max = df['High'].rolling(window=9).max()
        rsv = (df['Close'] - low_min) / (high_max - low_min) * 100
        
        # 簡單平滑處理 (K=3日平均, D=3日平均)
        k_val = rsv.rolling(window=3).mean().iloc[-1]
        d_val = k_val # 這裡簡化處理，實戰可再做一次平滑
        prev_k = rsv.rolling(window=3).mean().iloc[-2]
        prev_d = prev_k # 簡化

        # 6. 打包資料
        # 注意：这里的欄位名稱必須跟 App.js 裡讀取的一模一樣
        stock_data = {
            "id": ticker.replace(".TW", ""),
            "name": ticker, # 免費 API 抓中文名較不穩，先顯示代號
            "price": round(current_price, 2),
            "changePercent": round(change_percent, 2),
            "volume": int(volume),
            "avgVolume20": int(avg_vol_20),
            "ma5": round(ma5, 2),
            "ma20": round(ma20, 2),
            "ma60": round(ma60, 2),
            "ma200": round(ma200, 2),
            "high52w": round(high_52w, 2),
            "kVal": round(k_val, 2),
            "dVal": round(d_val, 2),
            "prevK": round(prev_k, 2),
            "prevD": round(prev_d, 2),
            "winRate": 70, # 模擬的高勝率分數
            
            # 敗部復活所需的模擬交易紀錄
            # (真實情況這部分應該讀取您的交易帳本，這裡先留空)
            "lastTransaction": None 
        }
        
        results.append(stock_data)
        print(f"✅ 已處理: {ticker} | 股價: {current_price}")

    except Exception as e:
        print(f"❌ 錯誤 {ticker}: {e}")

# --- 輸出結果 ---
# 確保 public 資料夾存在 (因為 React 是讀取 public/data.json)
os.makedirs('public', exist_ok=True)

# 將結果寫入 JSON 檔案
json_path = 'public/data.json'
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n🎉 掃描完成！共產出 {len(results)} 筆資料。")
print(f"檔案已儲存至: {json_path}")