# weather_bot.py
# Requirements: pip install python-telegram-bot requests

import requests
from datetime import datetime
from collections import defaultdict
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ── CONFIG ────────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = "$TELEGRAM_TOKEN"
WEATHER_API_KEY = "$WEATHER_API_KEY"
DEFAULT_CITY = "Ypsonas,CY"   # your default city
# ─────────────────────────────────────────────────────────────────────────────


def get_weekly_weather(city: str) -> str:
    url = (
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?q={city}&appid={WEATHER_API_KEY}&units=metric"
    )
    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:
        return f"❌ Could not fetch weather for *{city}*. Check the city name."

    data = resp.json()

    # Group 3-hour slots by day
    days = defaultdict(lambda: {
        "temps": [], "rain_probs": [], "wind_speeds": [], "descriptions": []
    })
    for entry in data["list"]:
        date_str = entry["dt_txt"][:10]                       # "YYYY-MM-DD"
        days[date_str]["temps"].append(entry["main"]["temp"])
        days[date_str]["rain_probs"].append(entry.get("pop", 0) * 100)  # pop: 0–1 → %
        days[date_str]["wind_speeds"].append(entry["wind"]["speed"])
        days[date_str]["descriptions"].append(entry["weather"][0]["description"])

    lines = [f"🌍 *Weekly Weather — {city}*\n"]
    today = datetime.utcnow().date()

    for date_str, info in sorted(days.items())[:7]:
        date_obj  = datetime.strptime(date_str, "%Y-%m-%d").date()
        day_label = date_obj.strftime("%A, %d %b")
        if date_obj == today:
            day_label = f"Today ({date_obj.strftime('%d %b')})"

        temp_min  = round(min(info["temps"]), 1)
        temp_max  = round(max(info["temps"]), 1)
        rain_prob = round(max(info["rain_probs"]))   # peak % for the day
        wind_min  = round(min(info["wind_speeds"]), 1)
        wind_max  = round(max(info["wind_speeds"]), 1)
        desc = max(set(info["descriptions"]), key=info["descriptions"].count).capitalize()

        if   rain_prob >= 70: emoji = "🌧️"
        elif rain_prob >= 40: emoji = "🌦️"
        elif rain_prob >= 20: emoji = "⛅"
        else:                 emoji = "☀️"

        lines.append(
            f"{emoji} *{day_label}*\n"
            f"   🌡  Temp: {temp_min}°C – {temp_max}°C\n"
            f"   🌧  Rain chance: {rain_prob}%\n"
            f"   💨  Wind: {wind_min} – {wind_max} m/s\n"
            f"   📋  {desc}\n"
        )

    return "\n".join(lines)


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! I'm your *Weather Bot*.\n\n"
        "Commands:\n"
        "  /weather — weekly forecast for the default city\n"
        "  /weather <city> — forecast for any city\n\n"
        "Example: `/weather Athens`",
        parse_mode="Markdown"
    )

async def weather(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    city = " ".join(ctx.args) if ctx.args else DEFAULT_CITY
    await update.message.reply_text("⏳ Fetching forecast…")
    msg = get_weekly_weather(city)
    await update.message.reply_text(msg, parse_mode="Markdown")


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start",   start))
    app.add_handler(CommandHandler("weather", weather))
    print("✅ Bot is running… Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()