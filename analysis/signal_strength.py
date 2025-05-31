# signal_strength.py

import os
import numpy as np
from binance.client import Client
import pandas as pd
import pandas_ta as ta
from dotenv import load_dotenv

load_dotenv()

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

client = Client(api_key=BINANCE_API_KEY, api_secret=BINANCE_API_SECRET)

def get_technical_analysis(symbol: str):
    klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1HOUR, limit=100)
    closes = np.array([float(kline[4]) for kline in klines])
    df = pd.DataFrame(closes, columns=["close"])

    rsi = ta.rsi(df["close"], length=14).iloc[-1]
    macd = ta.macd(df["close"])
    macd_signal = "bullish" if macd["MACD_12_26_9"].iloc[-1] > macd["MACDs_12_26_9"].iloc[-1] else "bearish"

    ema_now = ta.ema(df["close"], length=21).iloc[-1]
    ema_prev = ta.ema(df["close"], length=21).iloc[-2]
    ema_trend = "uptrend" if ema_now > ema_prev else "downtrend"

    signal = "BUY" if rsi > 50 and macd_signal == "bullish" else "SELL"

    return {
        "rsi": round(float(rsi), 2),
        "macd": macd_signal,
        "ema_trend": ema_trend,
        "signal": signal
    }

def generate_signal(symbol: str):
    tech = get_technical_analysis(symbol)
    entry_price = float(client.get_symbol_ticker(symbol=symbol)["price"])
    stop_loss = round(entry_price * 0.95, 2)
    take_profit = round(entry_price * 1.05, 2)
    volume = float(client.get_ticker_24hr(symbol=symbol)["quoteVolume"])

    return {
        "final_signal": tech["signal"],
        "entry": str(entry_price),
        "stop_loss": str(stop_loss),
        "take_profit": str(take_profit),
        "volume": volume,
        "leverage": "3x",
        "ai_comment": "Teknik göstergeler mevcut trende göre değerlendirilmiştir."
    }

def calculate_signal_strength(rsi, macd, ema_trend, volume, sentiment_score):
    score = 0
    if rsi > 50: score += 1
    if macd.lower() == "bullish": score += 1
    if ema_trend.lower() == "uptrend": score += 1
    if volume > 1_000_000: score += 1
    if sentiment_score > 0.2: score += 1
    return {"score": score}

def append_leverage_comment(_, ema_trend: str) -> str:
    if "up" in ema_trend.lower():
        return "Trend pozitif, 3x-5x kaldıraca uygun."
    elif "down" in ema_trend.lower():
        return "Trend zayıf, mümkünse kaldıraçsız işlem yap."
    return "Belirsiz trend, minimum kaldıraçla işlem yapılmalı."
