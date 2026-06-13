import os
import requests
import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")


def get_weather():
    city = "Kochi"

    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    )

    response = requests.get(url).json()

    if response.get("cod") != 200:
        return f"Weather Error: {response}"

    temp = response["main"]["temp"]
    description = response["weather"][0]["description"]

    return (
        f"🌤 Weather Update\n\n"
        f"City: {city}\n"
        f"Temperature: {temp}°C\n"
        f"Condition: {description}"
    )


def get_news():
    url = (
        f"https://newsapi.org/v2/top-headlines"
        f"?country=in&pageSize=5&apiKey={NEWS_API_KEY}"
    )

    response = requests.get(url).json()

    if "articles" not in response:
        return f"News API Error:\n{response}"

    articles = response["articles"]

    news_text = "\n\n📰 Top News Headlines\n\n"

    for i, article in enumerate(articles, start=1):
        title = article.get("title", "No Title")
        source = article.get("source", {}).get("name", "Unknown")

        news_text += f"{i}. {title}\nSource: {source}\n\n"

    return news_text


def send_email(content):
    msg = MIMEMultipart()

    msg["From"] = EMAIL_ADDRESS
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = "Daily Weather & News Update"

    msg.attach(MIMEText(content, "plain"))

    print("Connecting to Gmail...")

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()

    print("Logging in...")

    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

    print("Sending email...")

    server.send_message(msg)

    server.quit()

    print("Email Sent Successfully!")


def main():
    weather = get_weather()
    news = get_news()

    email_content = weather + "\n\n" + news

    send_email(email_content)


if __name__ == "__main__":
    main()
