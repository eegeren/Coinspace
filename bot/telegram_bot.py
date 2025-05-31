import os
import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from analysis.signal_strength import generate_signal, get_technical_analysis, calculate_signal_strength
from analysis.news_analyzer import analyze_news
from utils.premium_manager import is_premium
from utils.helpers import format_signal_result
from config.config import PREMIUM_IDS, SUMMARY_CHAT_ID
from utils.watchlist_manager import (
    add_coin_to_watchlist,
    remove_coin_from_watchlist,
    get_user_watchlist
)


load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

async def follow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    coin = context.args[0].upper() if context.args else None
    if not coin:
        await update.message.reply_text("⚠️ Please specify a coin to follow (e.g., /follow BTCUSDT).")
        return

    if add_coin_to_watchlist(user_id, coin):
        await update.message.reply_text(f"✅ {coin} added to your watchlist.")
    else:
        await update.message.reply_text(f"ℹ️ {coin} is already in your watchlist.")

async def unfollow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    coin = context.args[0].upper() if context.args else None
    if not coin:
        await update.message.reply_text("⚠️ Please specify a coin to remove (e.g., /unfollow BTCUSDT).")
        return

    if remove_coin_from_watchlist(user_id, coin):
        await update.message.reply_text(f"🗑️ {coin} removed from your watchlist.")
    else:
        await update.message.reply_text(f"⚠️ {coin} is not in your watchlist.")

async def watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    coins = get_user_watchlist(user_id)
    if coins:
        coin_list = "\n".join([f"• {c}" for c in coins])
        await update.message.reply_text(f"📋 Your Watchlist:\n{coin_list}")
    else:
        await update.message.reply_text("🔍 Your watchlist is empty.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ /start komutu geldi")
    user_id = update.effective_chat.id
    msg = (
        "🛰️ Welcome to Coinspace!\nUse /help to see available commands.\n\n"
        f"👤 *Your Chat ID:* `{user_id}`"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Welcome message\n"
        "/help - Command list\n"
        "/deep COIN - Full analysis\n"
        "/news COIN - News analysis only\n"
        "/tech COIN - Technical analysis only\n"
        "/signal COIN - Signal summary\n"
        "/summary - Market Summary on Demand\n"
        "/realtime - Most Volatile Coins\n"
        "/follow COIN - Add coin to your watchlist\n"
        "/unfollow COIN - Remove coin from your watchlist\n"
        "/watchlist - Show your watchlist\n"
        "/premium - VIP Access – Unlock Full Power"
    )

async def deep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_premium(update.effective_chat.id):
        await update.message.reply_text("🔒 Bu özellik yalnızca premium kullanıcılar içindir.")
        return

    coin = context.args[0].upper() if context.args else "BTC"
    allowed_coins = {"BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "AVAX", "MATIC", "DOT"}
    if coin not in allowed_coins:
        await update.message.reply_text("❌ Geçersiz coin sembolü. Örnek: /deep BTC")
        return

    try:
        signal = generate_signal(coin)
        tech = get_technical_analysis(coin)
        news = analyze_news(coin)

        rsi = tech.get("rsi", 50)
        ema = tech.get("ema_trend", "N/A")
        macd = tech.get("macd", "N/A")
        sentiment = news.get("sentiment", "N/A")
        sentiment_score = news.get("sentiment_score", 0)
        volume = signal.get("volume", 0)
        trend = tech.get("signal", "Belirsiz")

        strength = calculate_signal_strength(
            rsi=rsi,
            macd=macd,
            ema_trend=ema,
            volume=volume,
            sentiment_score=sentiment_score
        )

        bar = "🟩" * strength["score"] + "⬜" * (5 - strength["score"])
        explanation = []

        if macd.lower() == "bearish" and trend.startswith("BUY"):
            explanation.append("• MACD düşüşteyken alış sinyali verilmiş.")
        if ema.lower() == "downtrend" and trend.startswith("BUY"):
            explanation.append("• EMA düşüş eğilimindeyken alış sinyali verilmiş.")

        explanation_text = "\n".join(explanation)

        msg = f"""
🔎 *{coin} Genel Tarama*

🧠 Duyarlılık: {sentiment}
🧠 Duyarlılık Skoru: {sentiment_score:.2f}
📊 RSI: {rsi}
📈 Trend: {trend}
📐 EMA: {ema}
📉 MACD: {macd}
📥 Giriş: {signal.get('entry', 'Veri yok')}
🛑 SL: {signal.get('stop_loss', 'Veri yok')}
🎯 TP: {signal.get('take_profit', 'Veri yok')}
📈 Hacim: {volume}
⚖️ Kaldıraç: {append_leverage_comment('', ema)}

⭐ *Sinyal Gücü:* {bar}
{explanation_text}
"""
        await update.message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text("⚠️ Derin analiz sırasında bir hata oluştu. Lütfen daha sonra tekrar deneyin.")
        print(f"Error in /deep command: {e}")


async def tech(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coin = context.args[0].upper() if context.args else None
    if not coin:
        await update.message.reply_text("⚠️ Please provide a coin symbol (e.g., /tech BTCUSDT).")
        return
    result = get_technical_analysis(coin)
    msg = f"📊 RSI: {result['rsi']}\n📈 Signal: {result['signal']}"
    await update.message.reply_text(msg)

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coin = context.args[0].upper() if context.args else None
    if not coin:
        await update.message.reply_text("⚠️ Please provide a coin symbol (e.g., /signal BTCUSDT).")
        return
    result = generate_signal(coin)
    await update.message.reply_text(f"✅ Final Signal: {result['final_signal']}")

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("💳 VIP Satın Al", url="https://your-payment-link.com")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = (
        "🎟 *Coinspace VIP Subscription Plans:*\n"
        "• 1 Month  – $29.99\n"
        "• 3 Months – $69.99\n"
        "• Lifetime – $299.99\n\n"
        "🪙 *Accepted Payments:*\n"
        "USDT (TRC20), BTC, DOGE\n\n"
        "🔐 VIP access is granted automatically after purchase."
    )
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=reply_markup)

def get_market_summary():
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        response = requests.get(url, timeout=10)
        data = response.json()
        sorted_data = sorted(data, key=lambda x: float(x["priceChangePercent"]), reverse=True)
        top_gainers = sorted_data[:3]
        top_losers = sorted_data[-3:]
        return top_gainers, top_losers
    except Exception:
        return [], []

def format_market_summary(gainers, losers):
    message = "📊 *Daily Market Summary*\n\n"
    message += "🚀 *Top Gainers:*\n"
    for coin in gainers:
        message += f"• {coin['symbol']}: +{float(coin['priceChangePercent']):.2f}%\n"
    message += "\n📉 *Top Losers:*\n"
    for coin in losers:
        message += f"• {coin['symbol']}: {float(coin['priceChangePercent']):.2f}%\n"
    return message

async def send_market_summary(bot):
    gainers, losers = get_market_summary()
    message = format_market_summary(gainers, losers)
    if SUMMARY_CHAT_ID:
        await bot.send_message(chat_id=SUMMARY_CHAT_ID, text=message, parse_mode="Markdown")

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gainers, losers = get_market_summary()
    message = format_market_summary(gainers, losers)
    await update.message.reply_text(message, parse_mode="Markdown")

async def realtime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    is_premium = str(user_id) in PREMIUM_IDS
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        response = requests.get(url, timeout=10)
        data = response.json()
        sorted_data = sorted(data, key=lambda x: abs(float(x["priceChangePercent"])), reverse=True)
        volatile_coins = sorted_data[:10]
        public_list = volatile_coins[:2]
        premium_list = volatile_coins[2:]
        message = "🌪 *Most Volatile Coins Today:*\n\n"
        for coin in public_list:
            message += f"• {coin['symbol']}: {float(coin['priceChangePercent']):.2f}%\n"
        if is_premium:
            message += "\n💎 *Premium Insights:*\n"
            for coin in premium_list:
                message += f"• {coin['symbol']}: {float(coin['priceChangePercent']):.2f}%\n"
        else:
            message += "\n🔒 Unlock 8 more coins with /premium"
        await update.message.reply_text(message, parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("⚠️ Couldn't fetch real-time data. Try again later.")

def setup_handlers(app: Application):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("deep", deep))
    app.add_handler(CommandHandler("news", analyze_news))
    app.add_handler(CommandHandler("tech", tech))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("premium", premium))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("realtime", realtime))
    app.add_handler(CommandHandler("follow", follow))
    app.add_handler(CommandHandler("unfollow", unfollow))
    app.add_handler(CommandHandler("watchlist", watchlist))

    print("📌 Komutlar başarıyla yüklendi")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: app.create_task(send_market_summary(app.bot)), "cron", hour=21, minute=0)
    scheduler.start()

    print("✅ Handlers and scheduler loaded (Webhook mode)")
