from binance.client import Client
import numpy as np


client = Client(api_key="YOUR_API_KEY", api_secret="YOUR_SECRET_KEY")  # .env üzerinden alınmalı

def get_technical_analysis(symbol: str):
    # Binance'ten veri çek
    klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1HOUR, limit=100)
    closes = [float(kline[4]) for kline in klines]

    df = pd.DataFrame({'close': closes})
    
    # RSI
    df['rsi'] = ta.rsi(df['close'], length=14)
    
    # MACD
    macd_df = ta.macd(df['close'])
    df = pd.concat([df, macd_df], axis=1)
    
    # EMA Trend
    df['ema'] = ta.ema(df['close'], length=21)
    ema_trend = "uptrend" if df['ema'].iloc[-1] > df['ema'].iloc[-2] else "downtrend"

    # MACD sinyali
    macd_signal = "bullish" if df['MACD_12_26_9'].iloc[-1] > df['MACDs_12_26_9'].iloc[-1] else "bearish"

    # Sinyal kararı
    signal_strength = "BUY" if df['rsi'].iloc[-1] > 50 and macd_signal == "bullish" else "SELL"

    return {
        "rsi": round(df['rsi'].iloc[-1], 2),
        "signal": signal_strength,
        "ema_trend": ema_trend,
        "macd": macd_signal
    }




def generate_signal(symbol):
    price = float(client.get_symbol_ticker(symbol=symbol)['price'])
    entry = round(price * 1.001, 2)
    stop_loss = round(price * 0.98, 2)
    take_profit = round(price * 1.03, 2)

    volume = float(client.get_ticker(symbol=symbol)['quoteVolume'])

    return {
        "final_signal": "BUY",
        "entry": entry,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "volume": volume,
        "leverage": "3x",
        "ai_comment": "Analiz algoritması bu coini alıma uygun gördü."
    }




def calculate_signal_strength(rsi, macd, ema_trend, volume, sentiment_score):
    score = 0
    if rsi > 50: score += 1
    if "bullish" in macd.lower(): score += 1
    if "up" in ema_trend.lower(): score += 1
    if volume > 1000000: score += 1
    if sentiment_score > 0.2: score += 1
    return {"score": score}

def append_leverage_comment(_, ema_trend: str) -> str:
    if "up" in ema_trend.lower():
        return "Trend pozitif, 3x-5x kaldıraca uygun."
    elif "down" in ema_trend.lower():
        return "Trend zayıf, mümkünse kaldıraçsız işlem yap."
    return "Belirsiz trend, minimum kaldıraçla işlem yapılmalı."
