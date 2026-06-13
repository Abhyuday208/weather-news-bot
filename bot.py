import requests
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Environment Variables
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

CITY = "Thiruvananthapuram"


def get_weather():
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={CITY}&appid={OPENWEATHER_API_KEY}&units=metric"
    )

    response = requests.get(url).json()

    temp = response["main"]["temp"]
    description = response["weather"][0]["description"]

    return f"""
🌤 Weather Report

City: {CITY}
Temperature: {temp}°C
Condition: {description}
"""


def get_news():
    url = (
        f"https://newsapi.org/v2/top-headlines"
        f"?country=in&pageSize=5&apiKey={NEWS_API_KEY}"
    )

    response = requests.get(url).json()

    articles = response["articles"]

    news_summary = "\n📰 Top Headlines\n\n"

    for i, article in enumerate(articles, start=1):
        news_summary += (
            f"{i}. {article['title']}\n"
            f"Source: {article['source']['name']}\n\n"
        )

    return news_summary


def send_email(content):
    msg = MIMEMultipart()

    msg["From"] = EMAIL_ADDRESS
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = "Daily Weather & News Update"

    msg.attach(MIMEText(content, "plain"))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()

    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

    server.send_message(msg)

    server.quit()


def main():
    weather = get_weather()
    news = get_news()

    email_content = weather + "\n\n" + news

    send_email(email_content)

    print("Email Sent Successfully!")


if __name__ == "__main__":
    main()
