import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==================================
# CONFIG
# ==================================

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

CITY = "Kochi"

# ==================================
# WEATHER
# ==================================

def get_weather():

    try:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={CITY}"
            f"&appid={OPENWEATHER_API_KEY}"
            f"&units=metric"
        )

        response = requests.get(url, timeout=20).json()

        if response.get("cod") != 200:
            return "Unable to fetch weather."

        temp = response["main"]["temp"]
        condition = response["weather"][0]["description"]

        alert_text = ""

        if temp > 35:
            alert_text += "\n🔥 HIGH TEMPERATURE ALERT\n"

        if "rain" in condition.lower():
            alert_text += "\n☔ RAIN ALERT\n"

        return (
            f"WEATHER REPORT\n"
            f"-------------------------\n"
            f"City: {CITY}\n"
            f"Temperature: {temp}°C\n"
            f"Condition: {condition}\n"
            f"{alert_text}\n"
        )

    except Exception as e:
        return f"Weather Error: {str(e)}"


# ==================================
# NEWS
# ==================================

def get_news():

    try:

        url = (
            f"https://newsapi.org/v2/top-headlines"
            f"?country=in"
            f"&pageSize=10"
            f"&apiKey={NEWS_API_KEY}"
        )

        response = requests.get(url, timeout=20).json()

        print("News API Response:", response)

        if response.get("status") != "ok":
            return (
                "NEWS ERROR\n"
                f"{response}\n"
            )

        articles = response.get("articles", [])

        if len(articles) == 0:
            return "No news articles available."

        news_text = (
            "\nTOP NEWS HEADLINES\n"
            "-------------------------\n\n"
        )

        for i, article in enumerate(articles[:10], start=1):

            title = article.get(
                "title",
                "No Title"
            )

            source = article.get(
                "source",
                {}
            ).get(
                "name",
                "Unknown"
            )

            published = article.get(
                "publishedAt",
                "Unknown"
            )

            link = article.get(
                "url",
                "No Link"
            )

            news_text += (
                f"{i}. {title}\n"
                f"Source: {source}\n"
                f"Published: {published}\n"
                f"Link: {link}\n\n"
            )

        return news_text

    except Exception as e:
        return f"News Error: {str(e)}"


# ==================================
# EMAIL
# ==================================

def send_email(content):

    try:

        msg = MIMEMultipart()

        msg["From"] = EMAIL_ADDRESS
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = (
            "Daily Weather & News Report"
        )

        msg.attach(
            MIMEText(
                content,
                "plain"
            )
        )

        print("Connecting to Gmail...")

        server = smtplib.SMTP(
            "smtp.gmail.com",
            587
        )

        server.starttls()

        print("Logging in...")

        server.login(
            EMAIL_ADDRESS,
            EMAIL_PASSWORD
        )

        print("Sending email...")

        server.send_message(msg)

        server.quit()

        print(
            "Email Sent Successfully!"
        )

    except Exception as e:

        print(
            "Email Error:",
            str(e)
        )


# ==================================
# MAIN
# ==================================

def main():

    print("Fetching weather...")

    weather_report = get_weather()

    print("Fetching news...")

    news_report = get_news()

    final_report = (
        weather_report
        + "\n"
        + "=" * 50
        + "\n"
        + news_report
    )

    send_email(final_report)


if __name__ == "__main__":
    main()
