import React, { useState, useMemo, useEffect } from 'react';
import { 
  TrendingUp, Activity, RefreshCcw, BarChart2, ArrowUpCircle, 
  AlertTriangle, CheckCircle2, Clock, DollarSign, Loader2
} from 'lucide-react';

// --- 備用數據 (FALLBACK) ---
// 當抓不到雲端 data.json 時 (例如 Python 還沒跑)，會顯示這組資料，確保網頁不會壞掉
const FALLBACK_STOCKS = [
  {
    id: '0000', name: '範例-尚未連線', price: 0, changePercent: 0, volume: 0, avgVolume20: 0,
    ma5: 0, ma20: 0, ma60: 0, ma200: 0, high52w: 0,
    kVal: 50, dVal: 50, prevK: 50, prevD: 50, winRate: 0,
    lastTransaction: null
  },
  {
    id: '2330', name: '台積電(模擬)', price: 820, changePercent: 3.5, volume: 65000, avgVolume20: 30000,
    ma5: 800, ma20: 780, ma60: 750, ma200: 600, high52w: 830,
    kVal: 85, dVal: 70, prevK: 65, prevD: 68, winRate: 75,
    lastTransaction: null
  }
];

// --- 策略定義 (維持原本邏輯) ---
const STRATEGIES = [
  {
    id: 'original_golden_cross',
    name: '原始金叉死叉',
    icon: <Activity className="w-5 h-5" />,
    color: 'text-blue-600',
    description: 'KD 指標低檔黃金交叉，視為短線買進訊號。',
    filter: (stock) => stock.kVal > stock.dVal && stock.prevK < stock.prevD
  },
  {
    id: 'ma_bullish',
    name: '均線多頭排列',
    icon: <TrendingUp className="w-5 h-5" />,
    color: 'text-green-600',
    description: '短、中、長期均線依序排列 (MA5 > MA20 > MA60)。',
    filter: (stock) => stock.ma5 > stock.ma20 && stock.ma20 > stock.ma60 && stock.ma60 > stock.ma200
  },
  {
    id: 'high_win_rate',
    name: '高勝率精選',
    icon: <BarChart2 className="w-5 h-5" />,
    color: 'text-purple-600',
    description: '系統回測過去一年勝率超過 70% 的個股。',
    filter: (stock) => stock.winRate >= 70
  },
  {
    id: 'scenario_a_vcp',
    name: '情境A：VCP動能突破',
    icon: <ArrowUpCircle className="w-5 h-5" />,
    color: 'text-red-600',
    description: '捕捉新一波漲勢起點，需符合長線多頭、強勢區間、爆量長紅。',
    requirements: ['股價 > 年線', '接近52週高點', '漲幅 > 3%', '量增 1.5倍'],
    filter: (stock) => {
      // 加上 || 0 是為了防止資料缺漏時導致當機
      const ma200 = stock.ma200 || 0;
      const high52w = stock.high52w || 99999;
      const avgVol = stock.avgVolume20 || 99999999;

      const isLongTermBull = stock.price > ma200;
      const isNearHigh = stock.price >= (high52w * 0.85);
      const isStrongDay = stock.changePercent > 3.0;
      const isVolumeSpike = stock.volume > (avgVol * 1.5);
      
      return isLongTermBull && isNearHigh && isStrongDay && isVolumeSpike;
    }
  },
  {
    id: 'scenario_b_reentry',
    name: '情境B：敗部復活',
    icon: <RefreshCcw className="w-5 h-5" />,
    color: 'text-orange-600',
    description: '停損後短期轉強，強制買回機制。',
    requirements: ['停損 < 20天', '現價 > 買進成本', '站上均線'],
    filter: (stock) => {
      if (!stock.lastTransaction || stock.lastTransaction.action !== 'STOP_LOSS') return false;
      
      const lastTxDate = new Date(stock.lastTransaction.date);
      const daysDiff = (new Date() - lastTxDate) / (1000 * 60 * 60 * 24);
      const ma20 = stock.ma20 || 0;

      return daysDiff <= 20 && stock.price > stock.lastTransaction.buyCost && stock.price > ma20;
    }
  }
];

const StockCard = ({ stock, strategyId }) => {
  const isPositive = stock.changePercent >= 0;
  
  const renderStrategyDetails = () => {
    if (strategyId === 'scenario_a_vcp') {
      return (
        <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-600 space-y-1">
          <div className="flex justify-between"><span>年線位置:</span><span className="font-medium text-gray-800">{stock.ma200?.toFixed(1)}</span></div>
          <div className="flex justify-between"><span>52週高點:</span><span className="font-medium text-gray-800">{stock.high52w}</span></div>
          <div className="flex justify-between"><span>量能倍數:</span><span className="font-medium text-red-600">{(stock.volume / (stock.avgVolume20 || 1)).toFixed(1)}x</span></div>
        </div>
      );
    }
    if (strategyId === 'scenario_b_reentry') {
      const daysAgo = Math.floor((new Date() - new Date(stock.lastTransaction.date)) / (1000 * 60 * 60 * 24));
      return (
        <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-600 space-y-1">
          <div className="flex justify-between"><span>上次停損:</span><span className="font-medium text-gray-800">{daysAgo} 天前</span></div>
          <div className="flex justify-between"><span>原始成本:</span><span className="font-medium text-gray-800">{stock.lastTransaction.buyCost}</span></div>
          <div className="text-orange-600 font-bold mt-1 text-center">狀態: 已收復成本</div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="text-lg font-bold text-gray-900">{stock.name}</h3>
          <span className="text-sm text-gray-500 font-mono">{stock.id}</span>
        </div>
        <div className={`text-right ${isPositive ? 'text-red-500' : 'text-green-500'}`}>
          <div className="text-lg font-bold">{stock.price}</div>
          <div className="text-sm">{isPositive ? '▲' : '▼'} {Math.abs(stock.changePercent)}%</div>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2 text-sm text-gray-600 mt-2">
        <div>Vol: {stock.volume.toLocaleString()}</div>
        <div>MA20: {stock.ma20?.toFixed(1)}</div>
      </div>
      {renderStrategyDetails()}
    </div>
  );
};

export default function App() {
  const [activeStrategy, setActiveStrategy] = useState(STRATEGIES[0].id);
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dataSource, setDataSource] = useState('loading'); // 狀態: 'cloud' (雲端) 或 'fallback' (備用)

  // --- 關鍵修改：嘗試讀取外部 JSON ---
  // 這段程式碼會去尋找網站根目錄下的 'data.json' 檔案
  useEffect(() => {
    const fetchData = async () => {
      try {
        // 1. 嘗試讀取 data.json (由 Python 產生)
        const response = await fetch('./data.json');
        
        // 2. 如果讀取失敗 (例如檔案不存在)，就丟出錯誤，跳到 catch
        if (!response.ok) throw new Error('Data file not found');
        
        // 3. 如果成功，將資料存入 stocks
        const data = await response.json();
        setStocks(data);
        setDataSource('cloud'); // 標記為雲端數據
      } catch (error) {
        // 4. 如果失敗，使用備用數據 (Fallback)
        console.log("尚無雲端資料，使用備用數據");
        setStocks(FALLBACK_STOCKS);
        setDataSource('fallback'); // 標記為備用數據
      } finally {
        setLoading(false); // 讀取完成 (無論成功失敗)
      }
    };
    fetchData();
  }, []);

  const currentStrategy = STRATEGIES.find(s => s.id === activeStrategy);
  
  const filteredStocks = useMemo(() => {
    return stocks.filter(currentStrategy.filter);
  }, [activeStrategy, currentStrategy, stocks]);

  return (
    <div className="min-h-screen bg-gray-50 font-sans text-gray-900 pb-10">
      <header className="bg-gradient-to-r from-blue-900 to-indigo-900 text-white p-6 shadow-lg mb-6">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <TrendingUp className="w-8 h-8 text-yellow-400" />
            智慧選股 APP <span className="text-xs bg-yellow-400 text-blue-900 px-2 py-1 rounded ml-2">v2.0</span>
          </h1>
          <div className="flex items-center gap-2 text-sm mt-1 text-blue-200">
             {/* 根據資料來源顯示不同的燈號 */}
             <span>
               {dataSource === 'cloud' 
                 ? '🟢 雲端數據連線正常 (最新)' 
                 : '🟡 展示模式 (使用模擬數據)'}
             </span>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto p-4">
        {loading ? (
          <div className="flex justify-center py-20">
            <div className="text-center">
              <Loader2 className="animate-spin text-blue-600 w-10 h-10 mx-auto mb-2"/>
              <p className="text-gray-500">正在掃描市場數據...</p>
            </div>
          </div>
        ) : (
          <>
            <div className="flex overflow-x-auto pb-4 gap-2 mb-4 scrollbar-hide">
              {STRATEGIES.map((strategy) => (
                <button
                  key={strategy.id}
                  onClick={() => setActiveStrategy(strategy.id)}
                  className={`
                    flex-shrink-0 flex items-center gap-2 px-4 py-3 rounded-lg border transition-all text-sm font-medium
                    ${activeStrategy === strategy.id 
                      ? 'bg-white border-blue-500 shadow-md text-blue-800 ring-1 ring-blue-500' 
                      : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'}
                  `}
                >
                  {strategy.icon}
                  {strategy.name}
                </button>
              ))}
            </div>

            <div className="bg-white rounded-xl p-6 mb-6 border border-gray-200 shadow-sm">
              <div className="flex items-start gap-4">
                <div className={`p-3 rounded-full bg-opacity-10 ${currentStrategy.color.replace('text', 'bg')}`}>
                  {React.cloneElement(currentStrategy.icon, { className: `w-6 h-6 ${currentStrategy.color}` })}
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900 mb-1">{currentStrategy.name}</h2>
                  <p className="text-gray-600 mb-4">{currentStrategy.description}</p>
                  {currentStrategy.requirements && (
                    <div className="bg-gray-50 rounded-lg p-4 border border-gray-100">
                      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">策略條件</h4>
                      <ul className="space-y-2">
                        {currentStrategy.requirements.map((req, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                            <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                            {req}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="flex justify-between items-center mb-4 px-2">
              <h3 className="font-bold text-gray-800">選股結果 ({filteredStocks.length})</h3>
            </div>

            {filteredStocks.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredStocks.map(stock => (
                  <StockCard key={stock.id} stock={stock} strategyId={activeStrategy} />
                ))}
              </div>
            ) : (
              <div className="text-center py-12 bg-gray-50 border-2 border-dashed border-gray-200 rounded-xl">
                <div className="text-gray-400 mb-2"><AlertTriangle className="w-10 h-10 mx-auto" /></div>
                <h3 className="text-lg font-medium text-gray-600">無符合標的</h3>
                <p className="text-sm text-gray-500">
                   {dataSource === 'fallback' 
                    ? '目前顯示模擬數據，請等待雲端更新。' 
                    : '目前市場沒有符合此嚴格條件的股票。'}
                </p>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}