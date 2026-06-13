def get_news():
    url = (
        f"https://newsapi.org/v2/top-headlines"
        f"?country=in&pageSize=5&apiKey={NEWS_API_KEY}"
    )

    response = requests.get(url).json()

    print("News API Response:", response)

    if "articles" not in response:
        return f"News API Error:\n{response}"

    articles = response["articles"]

    news_summary = "\n📰 Top Headlines\n\n"

    for i, article in enumerate(articles, start=1):
        news_summary += (
            f"{i}. {article['title']}\n"
            f"Source: {article['source']['name']}\n\n"
        )

    return news_summary
def main():
    weather = get_weather()
    news = get_news()

    email_content = weather + "\n\n" + news

    send_email(email_content)

    print("Email Sent Successfully!")

if __name__ == "__main__":
    main()
