import os
import requests
import feedparser
import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ======================
# CONFIG
# ======================

CITY = [
    "Kochi",
    "Thiruvananthapuram",
    "Bengaluru",
    "Chennai",
    "Hyderabad",
    "Mumbai",
    "Delhi"
]

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
        "Mumbai"
    ]

    weather_report = "🌤 DAILY WEATHER REPORT\n\n"
    alerts = []

    for city in cities:

        try:
            url = (
                f"https://api.openweathermap.org/data/2.5/weather"
                f"?q={city}&appid={API_KEY}&units=metric"
            )

            response = requests.get(url, timeout=10)
            data = response.json()

            temp = data["main"]["temp"]
            condition = data["weather"][0]["description"]

            weather_report += (
                f"📍 {city}\n"
                f"🌡 Temperature: {temp}°C\n"
                f"☁ Condition: {condition}\n\n"
            )

            # Alert Conditions

            if temp > 35:
                alerts.append(
                    f"🔥 Heat Alert: {city} temperature is {temp}°C"
                )

            if "rain" in condition.lower():
                alerts.append(
                    f"🌧 Rain Alert: Rain detected in {city}"
                )

        except Exception as e:

            weather_report += (
                f"❌ Could not fetch weather for {city}\n\n"
            )

    return weather_report, alerts


# ======================
# RSS NEWS
# ======================

def get_rss_news():
    feeds = {
        "Indian Express": 
          "https://indianexpress.com/section/india/feed/",
        
        "The Hindu": 
           "https://www.thehindu.com/news/feeder/default.rss",
        
         "BBC": 
           "https://feeds.bbci.co.uk/news/rss.xml"
    }

    news_text = "\n📰 TOP NEWS HEADLINES\n\n"

    for source, url in feeds.items():
        try:
            feed = feedparser.parse(url)

            news_text += f"\n🔹 {source}\n"

            for entry in feed.entries[:5]:
                news_text += f"• {entry.title}\n"

            news_text += "\n"

        except Exception:
            news_text += f"❌ Unable to fetch news from {source}\n\n"

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

    weather_report, alerts = get_weather()

    email_body = f"""
Good Morning!

{weather_report}

Generated automatically by GitHub Actions.
"""

    # Daily weather email
    send_email(
        "Daily Weather Report",
        email_body
    )

    # Alert email if any city exceeds conditions
    if alerts:

        alert_body = "\n".join(alerts)

        send_email(
            "⚠️ Weather Alert",
            alert_body
        )

    print("Email sent successfully.")
if __name__ == "__main__":
    main()
