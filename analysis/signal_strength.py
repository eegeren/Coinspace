from binance.client import Client
import numpy as np
import talib

client = Client()

def get_technical_analysis(symbol):
    klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1HOUR, limit=100)
    closes = np.array([float(kline[4]) for kline in klines])

    rsi = float(talib.RSI(closes, timeperiod=14)[-1])
    macd, macdsignal, _ = talib.MACD(closes)
    macd_signal = "bullish" if macd[-1] > macdsignal[-1] else "bearish"

    ema_current = talib.EMA(closes, timeperiod=21)[-1]
    ema_prev = talib.EMA(closes, timeperiod=21)[-2]
    ema_trend = "uptrend" if ema_current > ema_prev else "downtrend"

    signal_strength = "BUY" if rsi > 50 and macd_signal == "bullish" else "SELL"

    return {
        "rsi": round(rsi, 2),
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
