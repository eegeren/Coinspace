# signal_strength.py

def generate_signal(coin):
    # Sinyal üretme mantığı burada olacak
    return {
        "final_signal": "BUY",
        "entry": "42,000",
        "stop_loss": "40,000",
        "take_profit": "45,000",
        "volume": 1200000,
        "leverage": "3x",
        "ai_comment": "Trend olumlu, hacim destekliyor."
    }


def get_technical_analysis(coin):
    # Teknik analiz mantığı burada olacak
    return {
        "rsi": 58.2,
        "signal": "BUY",
        "ema_trend": "uptrend",
        "macd": "bullish"
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
