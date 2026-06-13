import os
import requests
import feedparser
import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ======================
# CONFIG
# ======================


OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

# ======================
# WEATHER
# ======================

def get_weather():
    cities = [
        "Kochi",
        "Thiruvananthapuram",
        "Bengaluru",
        "Delhi",
        "Chennai",
        "Mumbai",
        "Hyderabad",
        "Kolkata"
    ]

    report = "🌤 DAILY WEATHER REPORT\n\n"
    all_alerts = []

    for city in cities:
        try:
            url = (
                f"https://api.openweathermap.org/data/2.5/weather"
                f"?q={city}"
                f"&appid={OPENWEATHER_API_KEY}"
                f"&units=metric"
            )
            data = requests.get(url).json()

            if data.get("cod") != 200:
                report += f"❌ Weather data unavailable for {city}\n\n"
                continue

            temp = data["main"]["temp"]
            condition = data["weather"][0]["description"]

            # Per-city alerts
            city_alerts = []
            if temp > 35:
                city_alerts.append("🔥 HIGH TEMPERATURE ALERT")
            if "rain" in condition.lower():
                city_alerts.append("☔ RAIN ALERT")

            report += (
                f"📍 {city}\n"
                f"🌡 Temperature: {temp}°C\n"
                f"☁ Condition: {condition}\n"
            )

            if city_alerts:
                report += "⚠ " + " | ".join(city_alerts) + "\n"
                all_alerts.append(f"{city}: {' | '.join(city_alerts)}")

            report += "\n"

        except Exception:
            report += f"❌ Could not fetch weather for {city}\n\n"

    # Summary alert block at the end
    if all_alerts:
        report += "━━━━━━━━━━━━━━━━━━━━\n"
        report += "🚨 ALERT SUMMARY\n"
        for alert in all_alerts:
            report += f"  • {alert}\n"

    return report


# ======================
# RSS NEWS
# ======================

def get_rss_news():

    feeds = {
        "BBC":
        "https://feeds.bbci.co.uk/news/rss.xml",

        "The IndianExpress":
        "https://indianexpress.com/section/india/feed/",

        "The Hindu":
        "https://www.thehindu.com/news/feeder/default.rss"
    }

    news_text = "\n\nTOP NEWS HEADLINES\n"

    for source, url in feeds.items():

        news_text += f"\n===== {source} =====\n"

        feed = feedparser.parse(url)

        entries = feed.entries[:2]

        for item in entries:

            title = item.get("title", "No Title")

            link = item.get("link", "")

            published = item.get(
                "published",
                "No Date"
            )

            news_text += (
                f"• {title}\n"
                f"Published: {published}\n"
                f"Link: {link}\n"
            )

    return news_text


# ======================
# EMAIL
# ======================

def send_email(content):

    msg = MIMEMultipart()

    msg["From"] = EMAIL_ADDRESS
    msg["To"] = RECEIVER_EMAIL

    msg["Subject"] = (
        "Daily Weather & News Report"
    )

    msg.attach(
        MIMEText(content, "plain")
    )

    server = smtplib.SMTP(
        "smtp.gmail.com",
        587
    )

    server.starttls()

    server.login(
        EMAIL_ADDRESS,
        EMAIL_PASSWORD
    )

    server.send_message(msg)

    server.quit()

    print("Email Sent Successfully!")


# ======================
# MAIN
# ======================

def main():

    weather = get_weather()

    news = get_rss_news()

    report = (
        weather
        + "\n\n"
        + "=" * 50
        + "\n\n"
        + news
    )

    send_email(report)


if __name__ == "__main__":
    main()
