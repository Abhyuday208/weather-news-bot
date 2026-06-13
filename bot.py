Daily Morning Bot — Weather Alert + News Digest
================================================
Fetches weather from OpenWeatherMap and scrapes top headlines
from 3 news sites, then sends a formatted HTML email every morning.
Sends an extra ALERT email if temp > 35°C or rain is predicted.

Required environment variables (set as GitHub Actions secrets):
  OPENWEATHER_API_KEY  — free key from openweathermap.org
  CITY_NAME            — e.g. "London" or "Mumbai,IN"
  EMAIL_SENDER         — Gmail address you're sending FROM
  EMAIL_PASSWORD       — Gmail App Password (not your login password)
  EMAIL_RECIPIENT      — address to deliver to (can be the same)
"""

import os
import smtplib
import urllib.request
import json
import re
import html
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.error import URLError

# ── third-party (all pip-installable, listed in requirements.txt) ──────────
try:
    from bs4 import BeautifulSoup
    import requests
except ImportError as exc:
    raise SystemExit(
        f"Missing dependency: {exc}. Run: pip install -r requirements.txt"
    )


# ╔══════════════════════════════════════════════════════════╗
# ║                    CONFIGURATION                         ║
# ╚══════════════════════════════════════════════════════════╝

OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
CITY_NAME           = os.environ.get("CITY_NAME", "London")
EMAIL_SENDER        = os.environ.get("EMAIL_SENDER", "")
EMAIL_PASSWORD      = os.environ.get("EMAIL_PASSWORD", "")
EMAIL_RECIPIENT     = os.environ.get("EMAIL_RECIPIENT", EMAIL_SENDER)

HEAT_THRESHOLD_C    = 35          # °C above which an alert fires
ALERT_RAIN_KEYWORDS = {"rain", "drizzle", "thunderstorm", "shower"}

# News sources — (display_name, url, article_css_selector, link_prefix)
NEWS_SOURCES = [
    {
        "name": "BBC News",
        "url": "https://www.bbc.com/news",
        "article_selector": "h3",
        "link_prefix": "https://www.bbc.com",
        "link_selector": "a",
    },
    {
        "name": "Reuters",
        "url": "https://www.reuters.com",
        "article_selector": "a[data-testid='Heading']",
        "link_prefix": "https://www.reuters.com",
        "link_selector": None,          # headline IS the <a>
    },
    {
        "name": "Al Jazeera",
        "url": "https://www.aljazeera.com",
        "article_selector": "h3.article-card__title, h2.article-card__title, .article-card h3",
        "link_prefix": "https://www.aljazeera.com",
        "link_selector": "a",
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}


# ╔══════════════════════════════════════════════════════════╗
# ║                    WEATHER MODULE                        ║
# ╚══════════════════════════════════════════════════════════╝

def fetch_weather(city: str, api_key: str) -> dict:
    """Return current weather dict from OpenWeatherMap free tier."""
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={requests.utils.quote(city)}&appid={api_key}&units=metric"
    )
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()


def parse_weather(data: dict) -> dict:
    """Extract the fields we care about."""
    condition = data["weather"][0]["description"].lower()
    return {
        "city":        data.get("name", CITY_NAME),
        "temp_c":      data["main"]["temp"],
        "feels_like":  data["main"]["feels_like"],
        "humidity":    data["main"]["humidity"],
        "condition":   condition,
        "wind_kph":    round(data["wind"]["speed"] * 3.6, 1),
        "icon_code":   data["weather"][0]["icon"],
        "is_hot":      data["main"]["temp"] > HEAT_THRESHOLD_C,
        "has_rain":    any(kw in condition for kw in ALERT_RAIN_KEYWORDS),
    }


def weather_icon_url(icon_code: str) -> str:
    return f"https://openweathermap.org/img/wn/{icon_code}@2x.png"


# ╔══════════════════════════════════════════════════════════╗
# ║                    NEWS SCRAPER MODULE                   ║
# ╚══════════════════════════════════════════════════════════╝

def scrape_headlines(source: dict, max_items: int = 6) -> list[dict]:
    """
    Scrape up to `max_items` headlines from a news source.
    Returns list of {"title": str, "url": str, "time": str}.
    """
    try:
        resp = requests.get(source["url"], headers=HEADERS, timeout=12)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        items = []
        seen  = set()

        tags = soup.select(source["article_selector"])
        for tag in tags:
            # ── Extract headline text ──────────────────────────────
            title = tag.get_text(separator=" ", strip=True)
            title = re.sub(r"\s+", " ", title).strip()
            if not title or len(title) < 15 or title in seen:
                continue

            # ── Extract URL ────────────────────────────────────────
            if source["link_selector"] is None:
                # The tag itself is the <a>
                href = tag.get("href", "")
            else:
                a = tag.find("a")
                href = a.get("href", "") if a else ""

            if not href:
                continue

            if href.startswith("/"):
                href = source["link_prefix"] + href
            elif not href.startswith("http"):
                continue

            seen.add(title)
            items.append({
                "title": html.escape(title),
                "url":   href,
                "time":  datetime.now(timezone.utc).strftime("%H:%M UTC"),
            })

            if len(items) >= max_items:
                break

        return items

    except Exception as exc:
        print(f"[WARN] Could not scrape {source['name']}: {exc}")
        return []


def gather_all_news() -> list[dict]:
    """Return list of {source, headlines[]} dicts."""
    results = []
    for src in NEWS_SOURCES:
        print(f"  Scraping {src['name']} …")
        headlines = scrape_headlines(src)
        results.append({"source": src["name"], "url": src["url"], "headlines": headlines})
    return results


# ╔══════════════════════════════════════════════════════════╗
# ║                  HTML EMAIL BUILDER                      ║
# ╚══════════════════════════════════════════════════════════╝

_CSS = """
  body{margin:0;padding:0;background:#f0f2f5;font-family:'Segoe UI',Arial,sans-serif}
  .wrap{max-width:640px;margin:30px auto;background:#fff;border-radius:12px;
        overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.10)}
  .hdr{background:linear-gradient(135deg,#1a73e8,#0d47a1);color:#fff;
       padding:28px 32px 20px}
  .hdr h1{margin:0 0 4px;font-size:22px;letter-spacing:.4px}
  .hdr p{margin:0;opacity:.85;font-size:13px}
  .alert-bar{background:#e53935;color:#fff;padding:12px 32px;
             font-weight:700;font-size:14px;text-align:center}
  .weather{display:flex;align-items:center;gap:16px;
           background:#e8f0fe;padding:20px 32px}
  .weather img{width:64px;height:64px}
  .winfo h2{margin:0 0 4px;font-size:28px;color:#1a237e}
  .winfo p{margin:2px 0;font-size:13px;color:#444}
  .section{padding:24px 32px}
  .section h3{margin:0 0 14px;font-size:15px;color:#1a73e8;
              text-transform:uppercase;letter-spacing:.8px;
              border-bottom:2px solid #e8f0fe;padding-bottom:6px}
  .source-name{font-size:12px;color:#888;margin:18px 0 8px;font-weight:700;
               text-transform:uppercase;letter-spacing:.6px}
  .source-name a{color:#888;text-decoration:none}
  ul.headlines{margin:0 0 4px;padding:0;list-style:none}
  ul.headlines li{padding:7px 0;border-bottom:1px solid #f5f5f5;
                  font-size:14px;line-height:1.45}
  ul.headlines li:last-child{border-bottom:none}
  ul.headlines li a{color:#1a237e;text-decoration:none;font-weight:500}
  ul.headlines li a:hover{text-decoration:underline}
  .meta{font-size:11px;color:#aaa;margin-left:6px}
  .ftr{background:#f8f9fa;padding:14px 32px;font-size:11px;
       color:#aaa;text-align:center}
"""

def build_html(weather: dict, news: list[dict], is_alert: bool = False) -> str:
    date_str   = datetime.now().strftime("%A, %B %d %Y")
    icon_url   = weather_icon_url(weather["icon_code"])
    alert_bar  = ""

    if is_alert:
        reasons = []
        if weather["is_hot"]:
            reasons.append(f"🌡️ High temp {weather['temp_c']:.1f}°C > {HEAT_THRESHOLD_C}°C")
        if weather["has_rain"]:
            reasons.append(f"🌧️ Rain predicted ({weather['condition']})")
        alert_bar = f'<div class="alert-bar">⚠️ WEATHER ALERT — {" &nbsp;|&nbsp; ".join(reasons)}</div>'

    # ── News sections ──────────────────────────────────────────────────────
    news_html = ""
    for src in news:
        if not src["headlines"]:
            continue
        news_html += f'<p class="source-name"><a href="{src["url"]}" target="_blank">{src["source"]}</a></p>'
        news_html += '<ul class="headlines">'
        for h in src["headlines"]:
            news_html += (
                f'<li>'
                f'<a href="{h["url"]}" target="_blank">{h["title"]}</a>'
                f'<span class="meta">{h["time"]}</span>'
                f'</li>'
            )
        news_html += "</ul>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Morning Briefing — {date_str}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="wrap">

  <!-- Header -->
  <div class="hdr">
    <h1>☀️ Morning Briefing</h1>
    <p>{date_str} &nbsp;·&nbsp; Auto-generated daily digest</p>
  </div>

  {alert_bar}

  <!-- Weather -->
  <div class="weather">
    <img src="{icon_url}" alt="weather icon">
    <div class="winfo">
      <h2>{weather['temp_c']:.1f}°C &nbsp;<small style="font-size:16px;color:#555">{weather['city']}</small></h2>
      <p>Feels like {weather['feels_like']:.1f}°C &nbsp;·&nbsp; {weather['condition'].title()}</p>
      <p>💧 Humidity {weather['humidity']}% &nbsp;·&nbsp; 💨 Wind {weather['wind_kph']} km/h</p>
    </div>
  </div>

  <!-- News -->
  <div class="section">
    <h3>📰 Top Headlines</h3>
    {news_html if news_html else "<p style='color:#999'>No headlines found today.</p>"}
  </div>

  <!-- Footer -->
  <div class="ftr">
    Delivered automatically via GitHub Actions &nbsp;·&nbsp;
    Weather by <a href="https://openweathermap.org" style="color:#aaa">OpenWeatherMap</a>
  </div>

</div>
</body>
</html>"""


# ╔══════════════════════════════════════════════════════════╗
# ║                    EMAIL SENDER                          ║
# ╚══════════════════════════════════════════════════════════╝

def send_email(subject: str, html_body: str) -> None:
    msg                    = MIMEMultipart("alternative")
    msg["Subject"]         = subject
    msg["From"]            = EMAIL_SENDER
    msg["To"]              = EMAIL_RECIPIENT
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())
        print(f"  ✅ Email sent → {EMAIL_RECIPIENT}")


# ╔══════════════════════════════════════════════════════════╗
# ║                       MAIN FLOW                          ║
# ╚══════════════════════════════════════════════════════════╝

def validate_env() -> None:
    missing = [v for v in
               ["OPENWEATHER_API_KEY", "CITY_NAME",
                "EMAIL_SENDER", "EMAIL_PASSWORD", "EMAIL_RECIPIENT"]
               if not os.environ.get(v)]
    if missing:
        raise SystemExit(f"Missing environment variables: {', '.join(missing)}")


def main() -> None:
    validate_env()
    today = datetime.now().strftime("%A, %b %d")

    # ── 1. Weather ─────────────────────────────────────────────────────────
    print("🌤  Fetching weather …")
    raw_weather = fetch_weather(CITY_NAME, OPENWEATHER_API_KEY)
    weather     = parse_weather(raw_weather)
    print(f"    {weather['city']}: {weather['temp_c']:.1f}°C, {weather['condition']}")

    # ── 2. News ────────────────────────────────────────────────────────────
    print("📰 Scraping headlines …")
    news = gather_all_news()
    total = sum(len(s["headlines"]) for s in news)
    print(f"    Collected {total} headlines from {len(news)} sources")

    # ── 3. Build & send daily digest ───────────────────────────────────────
    is_alert  = weather["is_hot"] or weather["has_rain"]
    prefix    = "⚠️ WEATHER ALERT + " if is_alert else ""
    subject   = f"{prefix}Morning Briefing — {today}"
    html_body = build_html(weather, news, is_alert=is_alert)

    print("📧 Sending daily digest …")
    send_email(subject, html_body)

    # ── 4. Extra alert email if conditions warrant ─────────────────────────
    if is_alert:
        alert_reasons = []
        if weather["is_hot"]:
            alert_reasons.append(f"Temperature {weather['temp_c']:.1f}°C exceeds {HEAT_THRESHOLD_C}°C")
        if weather["has_rain"]:
            alert_reasons.append(f"Rain predicted ({weather['condition']})")

        alert_subject = f"⚠️ Weather Alert for {weather['city']} — {today}"
        alert_html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  body{{font-family:Arial,sans-serif;background:#fff3e0;margin:0;padding:30px}}
  .box{{max-width:520px;margin:auto;background:#fff;border-radius:10px;
       border-left:6px solid #e53935;padding:28px 32px;
       box-shadow:0 2px 12px rgba(0,0,0,.1)}}
  h2{{color:#c62828;margin-top:0}}
  ul{{color:#333;font-size:15px;line-height:1.7}}
  .footer{{margin-top:20px;font-size:12px;color:#999}}
</style></head>
<body>
<div class="box">
  <h2>⚠️ Weather Alert — {weather['city']}</h2>
  <p style="font-size:14px;color:#555">Triggered at {datetime.now().strftime("%H:%M")} local time</p>
  <ul>{''.join(f"<li>{r}</li>" for r in alert_reasons)}</ul>
  <p><strong>Current conditions:</strong> {weather['temp_c']:.1f}°C,
     {weather['condition'].title()}, humidity {weather['humidity']}%</p>
  <div class="footer">Sent automatically by your Morning Bot via GitHub Actions.</div>
</div>
</body></html>"""

        print("🚨 Sending separate weather alert …")
        send_email(alert_subject, alert_html)

    print("✅ All done.")


if __name__ == "__main__":
    main()
