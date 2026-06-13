import os
import requests
import feedparser
import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ======================
# CONFIG
# ======================

CITY = "Kochi"

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

# ======================
# WEATHER
# ======================

def get_weather():

    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={CITY}"
        f"&appid={OPENWEATHER_API_KEY}"
        f"&units=metric"
    )

    response = requests.get(url).json()

    if response.get("cod") != 200:
        return "Weather data unavailable."

    temp = response["main"]["temp"]
    condition = response["weather"][0]["description"]

    alerts = []

    if temp > 35:
        alerts.append("🔥 HIGH TEMPERATURE ALERT")

    if "rain" in condition.lower():
        alerts.append("☔ RAIN ALERT")

    report = (
        f"WEATHER REPORT\n"
        f"City: {CITY}\n"
        f"Temperature: {temp}°C\n"
        f"Condition: {condition}\n\n"
    )

    if alerts:
        report += "\n".join(alerts)

    return report


# ======================
# RSS NEWS
# ======================

def get_rss_news():

    feeds = {
        "BBC":
        "https://feeds.bbci.co.uk/news/rss.xml",

        "Reuters":
        "https://feeds.reuters.com/reuters/topNews",

        "The Hindu":
        "https://www.thehindu.com/news/feeder/default.rss"
    }

    news_text = "\n\nTOP NEWS HEADLINES\n\n"

    for source, url in feeds.items():

        news_text += f"\n===== {source} =====\n\n"

        feed = feedparser.parse(url)

        entries = feed.entries[:3]

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
                f"Link: {link}\n\n"
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
