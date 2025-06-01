import numpy as np
import pandas as pd
import requests
import pickle
import ta

# Yüklenmiş modeller
with open("xgb_model.pkl", "rb") as f:
    model = pickle.load(f)

with open("xgb_encoder.pkl", "rb") as f:
    encoder = pickle.load(f)

def fetch_binance_data(symbol="XRPUSDT", interval="1h", limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()

    df = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base_volume", "taker_buy_quote_volume", "ignore"
    ])
    df["close"] = pd.to_numeric(df["close"])
    df["open"] = pd.to_numeric(df["open"])
    df["high"] = pd.to_numeric(df["high"])
    df["low"] = pd.to_numeric(df["low"])
    df["volume"] = pd.to_numeric(df["volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df

def get_technical_indicators(df):
    df["rsi"] = ta.momentum.RSIIndicator(close=df["close"]).rsi()
    df["ema"] = ta.trend.EMAIndicator(close=df["close"]).ema_indicator()
    df["macd"] = ta.trend.MACD(close=df["close"]).macd()
    df["trend"] = np.where(df["ema"] > df["close"], "downtrend", "uptrend")
    df["macd_signal"] = np.where(df["macd"] > 0, "bullish", "bearish")
    return df

def generate_signal(df):
    latest = df.iloc[-1]
    entry = round(latest["close"], 2)
    stop_loss = round(entry * 0.95, 2)
    take_profit = round(entry * 1.07, 2)
    leverage_advice = "Trend pozitif, 3x–5x kaldıraça uygun." if latest["trend"] == "uptrend" else "Dikkatli ol, trend zayıf."

    features = pd.DataFrame([{
        "rsi": latest["rsi"],
        "ema": latest["ema"],
        "macd": latest["macd"],
        "trend": latest["trend"],
        "macd_signal": latest["macd_signal"]
    }])

    features_encoded = encoder.transform(features)
    signal_strength = model.predict_proba(features_encoded)[0][1]
    strength_bar = get_signal_strength_bar(signal_strength)

    return {
        "symbol": "XRP",
        "sentiment": "Neutral",
        "sentiment_score": "0.00",
        "rsi": round(latest["rsi"], 2),
        "trend": "BUY" if latest["trend"] == "uptrend" else "SELL",
        "ema": latest["trend"],
        "macd": latest["macd_signal"],
        "entry": entry,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "volume": int(latest["volume"]),
        "leverage_advice": leverage_advice,
        "signal_strength": strength_bar
    }

def get_signal_strength_bar(score):
    filled = int(score * 5)
    return "🟩" * filled + "⬜" * (5 - filled)

def format_telegram_message(data):
    return f"""
🔍 *{data['symbol']} Genel Tarama*

🧠 *Duyarlılık:* {data['sentiment']}
🧠 *Duyarlılık Skoru:* {data['sentiment_score']}

📊 *RSI:* {data['rsi']}
📈 *Trend:* {data['trend']}
📐 *EMA:* {data['ema']}
📉 *MACD:* {data['macd']}

🎯 *Giriş:* {data['entry']}
❤️ *SL:* {data['stop_loss']}
🏁 *TP:* {data['take_profit']}
📦 *Hacim:* {data['volume']}

⚖️ *Kaldıraç:* {data['leverage_advice']}

⭐ *Sinyal Gücü:* {data['signal_strength']}
"""
