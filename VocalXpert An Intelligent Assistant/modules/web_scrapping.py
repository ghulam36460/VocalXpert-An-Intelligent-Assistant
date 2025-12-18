"""
Web Scrapping Module - External Data Services

Provides web scraping functionality for fetching external data:
    - Wikipedia search and summaries
    - Weather information (from weather.com)
    - Latest news headlines (from indianexpress.com)
    - YouTube video search and playback
    - Email sending functionality
    - WhatsApp message automation
    - Distance calculation between locations

Dependencies:
    - beautifulsoup4: HTML parsing
    - requests: HTTP requests
    - wikipedia: Wikipedia API wrapper
    - geopy: Geographic calculations
"""

import wikipedia
import webbrowser
import requests
from bs4 import BeautifulSoup
import smtplib
import urllib.request
import os
from pathlib import Path
from geopy.geocoders import Nominatim
from geopy.distance import great_circle
import datetime
import logging

# Module logger
logger = logging.getLogger("VocalXpert.web_scrapping")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)

# Load environment variables
try:
    from dotenv import load_dotenv

    _module_dir = Path(__file__).parent
    _project_dir = _module_dir.parent
    load_dotenv(_project_dir / ".env")
except ImportError:
    pass

# API Keys from environment
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")


def wikiResult(query):
    """Search Wikipedia and return summary."""
    try:
        import wikipedia
        import webbrowser

        # Clean the query
        query = (
            query.replace(
                "wikipedia",
                "").replace(
                "search",
                "").replace(
                "wiki",
                "").strip())

        if not query or query.lower() in ["wikipedia", "wiki"]:
            # If no specific query, just open Wikipedia homepage
            webbrowser.open("https://www.wikipedia.org")
            return "Opening Wikipedia homepage. What would you like to search for?"

        print(f"Searching Wikipedia for: {query}")

        # Try to get summary with timeout
        try:
            import wikipedia
            import time

            # Set rate limiting
            wikipedia.set_rate_limiting(True,
                                        min_wait=datetime.timedelta(
                                            0, 0, 100000))

            # Simple timeout mechanism
            start_time = time.time()
            timeout = 10  # 10 seconds

            try:
                summary = wikipedia.summary(query,
                                            sentences=3,
                                            auto_suggest=True)

                if time.time() - start_time > timeout:
                    raise TimeoutError("Request took too long")

                # Also open the page in browser
                try:
                    page = wikipedia.page(query, auto_suggest=True)
                    if time.time() - start_time > timeout:
                        raise TimeoutError("Request took too long")
                    webbrowser.open(page.url)
                    return (
                        f"Wikipedia: {summary[:200]}... (Opening full page in browser)"
                    )
                except BaseException:
                    return f"Wikipedia: {summary}"

            except TimeoutError:
                raise TimeoutError("Wikipedia request timed out")

        except wikipedia.exceptions.DisambiguationError as e:
            # Multiple results, take the first one
            try:
                page = wikipedia.page(e.options[0], auto_suggest=True)
                webbrowser.open(page.url)
                summary = wikipedia.summary(e.options[0], sentences=2)
                return f"Wikipedia (disambiguation): {summary[:200]}... (Opening page in browser)"
            except BaseException:
                webbrowser.open(
                    f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}")
                return f"Opening Wikipedia search for: {query}"

        except wikipedia.exceptions.PageError:
            # Page doesn't exist, open search
            webbrowser.open(
                f"https://en.wikipedia.org/wiki/Special:Search?search={query.replace(' ', '+')}"
            )
            return f"No exact Wikipedia page found. Opening search results for: {query}"

        except TimeoutError:
            # Timeout occurred, fallback to opening search
            webbrowser.open(
                f"https://en.wikipedia.org/wiki/Special:Search?search={query.replace(' ', '+')}"
            )
            return f"Wikipedia request timed out. Opening search for: {query}"

    except ImportError:
        return "Wikipedia library not available. Please install wikipedia package."
    except Exception as e:
        print(f"Wikipedia error: {e}")
        # Fallback: open Wikipedia search
        try:
            import webbrowser

            webbrowser.open(
                f"https://en.wikipedia.org/wiki/Special:Search?search={query.replace(' ', '+')}"
            )
            return f"Opening Wikipedia search for: {query}"
        except BaseException:
            return f"Unable to search Wikipedia for: {query}. Error: {str(e)}"


class WEATHER:

    def __init__(self):
        self.tempValue = ""
        self.city = ""
        self.currCondition = ""
        self.speakResult = ""

    def updateWeather(self):
        """Update weather using OpenWeatherMap API or fallback to scraping."""
        try:
            # First, get user's city from IP
            res = requests.get("https://ipinfo.io/", timeout=5)
            data = res.json()
            self.city = data.get("city", "Unknown")

            # Try OpenWeatherMap API if key is available
            if WEATHER_API_KEY:
                api_url = f"https://api.openweathermap.org/data/2.5/weather?q={self.city}&appid={WEATHER_API_KEY}&units=metric"
                api_res = requests.get(api_url, timeout=5)
                if api_res.status_code == 200:
                    weather_data = api_res.json()
                    self.tempValue = str(round(weather_data["main"]["temp"]))
                    self.currCondition = weather_data["weather"][0][
                        "description"].title()
                    return

            # Fallback to web scraping
            URL = "https://weather.com/en-IN/weather/today/"
            result = requests.get(URL, timeout=10)
            src = result.content

            soup = BeautifulSoup(src, "html.parser")

            for h in soup.find_all("h1"):
                cty = h.text
                cty = cty.replace("Weather", "")
                self.city = cty[:cty.find(",")] if "," in cty else cty.strip()
                break

            spans = soup.find_all("span")
            for span in spans:
                try:
                    if span.get("data-testid") == "TemperatureValue":
                        self.tempValue = span.text[:-1]
                        break
                except Exception:
                    pass

            divs = soup.find_all(
                "div", class_="CurrentConditions--phraseValue--2xXSr")
            for div in divs:
                self.currCondition = div.text
                break

        except Exception as e:
            print(f"Weather update error: {e}")
            self.city = "Unknown"
            self.tempValue = "N/A"
            self.currCondition = "Unable to fetch weather"

    def weather(self):
        from datetime import datetime

        time = datetime.today().strftime("%A")
        if not self.tempValue:
            self.updateWeather()
        self.speakResult = ("Currently in " + self.city + ", its " +
                            self.tempValue + " degrees, with " +
                            self.currCondition)
        return [
            self.tempValue, self.currCondition, time, self.city,
            self.speakResult
        ]


w = WEATHER()


def dataUpdate():

    w.updateWeather()


##### WEATHER #####
def weather():
    return w.weather()


def latestNews(news=5):
    """Get latest news headlines using NewsAPI or fallback to scraping."""
    headlines = []
    headlineLinks = []

    try:
        # Try NewsAPI first if key is available
        if NEWS_API_KEY:
            api_url = (
                f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"
            )
            api_res = requests.get(api_url, timeout=10)
            if api_res.status_code == 200:
                data = api_res.json()
                articles = data.get("articles", [])[:news]
                for article in articles:
                    headlines.append(article.get("title", ""))
                    headlineLinks.append(article.get("url", ""))
                if headlines:
                    return headlines, headlineLinks

        # Fallback to web scraping
        URL = "https://indianexpress.com/latest-news/"
        result = requests.get(URL, timeout=10)
        src = result.content

        soup = BeautifulSoup(src, "html.parser")
        divs = soup.find_all("div", {"class": "title"})

        count = 0
        for div in divs:
            count += 1
            if count > news:
                break
            a_tag = div.find("a")
            if a_tag:
                headlineLinks.append(a_tag.attrs.get("href", ""))
                headlines.append(a_tag.text)

    except Exception as e:
        print(f"News fetch error: {e}")
        headlines = ["Unable to fetch news at this time"]
        headlineLinks = []

    return headlines, headlineLinks


def maps(text):
    text = text.replace("maps", "")
    text = text.replace("map", "")
    text = text.replace("google", "")
    openWebsite("https://www.google.com/maps/place/" + text)


def giveDirections(startingPoint, destinationPoint):

    geolocator = Nominatim(user_agent="assistant")
    if "current" in startingPoint:
        res = requests.get("https://ipinfo.io/")
        data = res.json()
        startinglocation = geolocator.reverse(data["loc"])
    else:
        startinglocation = geolocator.geocode(startingPoint)

    destinationlocation = geolocator.geocode(destinationPoint)
    startingPoint = startinglocation.address.replace(" ", "+")
    destinationPoint = destinationlocation.address.replace(" ", "+")

    openWebsite("https://www.google.co.in/maps/dir/" + startingPoint + "/" +
                destinationPoint + "/")

    startinglocationCoordinate = (startinglocation.latitude,
                                  startinglocation.longitude)
    destinationlocationCoordinate = (
        destinationlocation.latitude,
        destinationlocation.longitude,
    )
    total_distance = great_circle(startinglocationCoordinate,
                                  destinationlocationCoordinate).km  # .mile
    return str(round(total_distance, 2)) + "KM"


def openWebsite(url="https://www.google.com/"):
    webbrowser.open(url)


def jokes():
    URL = "https://icanhazdadjoke.com/"
    result = requests.get(URL)
    src = result.content

    soup = BeautifulSoup(src, "html.parser")

    try:
        p = soup.find("p")
        return p.text
    except Exception as e:
        raise e


def youtube(query):
    try:
        from youtubesearchpython import VideosSearch
        import webbrowser

        # Clean the query
        query = query.replace("play", " ")
        query = query.replace("on youtube", " ")
        query = query.replace("youtube", " ")
        query = query.strip()

        if not query:
            return "Please specify what to search for on YouTube."

        print(f"Searching YouTube for: {query}")

        # Try different approach to avoid proxy issues
        try:
            videosSearch = VideosSearch(query, limit=1)
            results = videosSearch.result()

            if results and "result" in results and results["result"]:
                video_id = results["result"][0]["id"]
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                print(f"Opening: {video_url}")
                webbrowser.open(video_url)
                return f"Playing {query} on YouTube..."
            else:
                return "Sorry, I couldn't find any videos for that search."

        except Exception as search_error:
            print(f"YouTube search error: {search_error}")
            # Fallback: just open YouTube search page
            search_url = f"https://www.youtube.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(search_url)
            return f"Opening YouTube search for: {query}"

    except Exception as e:
        print(f"YouTube error: {e}")
        # Final fallback
        try:
            webbrowser.open("https://www.youtube.com")
            return "Opening YouTube homepage due to technical issues."
        except BaseException:
            return "Unable to open YouTube. Please check your internet connection."


# Alias for playonYT
playonYT = youtube

# def youtube(query):
# 	query = query.replace('play',' ')
# 	query = query.replace('on youtube',' ')
# 	query = query.replace('youtube',' ')

# 	print("Searching for videos...")
# 	from youtubesearchpython import VideosSearch
# 	videosSearch = VideosSearch(query, limit = 1)
# 	results = videosSearch.result()['result']
# 	print("Finished searching!")

# 	webbrowser.open('https://www.youtube.com/watch?v=' + results[0]['id'])
# 	return "Enjoy..."


def googleSearch(query):
    if "image" in query:
        query += "&tbm=isch"
    query = query.replace("images", "")
    query = query.replace("image", "")
    query = query.replace("search", "")
    query = query.replace("show", "")
    webbrowser.open("https://www.google.com/search?q=" + query)
    return "Here you go..."


def sendWhatsapp(phone_no="", message=""):
    phone_no = "+92" + str(phone_no)
    webbrowser.open("https://web.whatsapp.com/send?phone=" + phone_no +
                    "&text=" + message)
    import time
    from pynput.keyboard import Key, Controller

    time.sleep(10)
    k = Controller()
    k.press(Key.enter)


def email(rec_email=None,
          text="Hello, It's VocalXpert here...",
          sub="VocalXpert"):
    """Send email using Outlook SMTP server."""
    USERNAME = os.getenv("MAIL_USERNAME")  # Outlook email address
    PASSWORD = os.getenv("MAIL_PASSWORD")
    if not USERNAME or not PASSWORD:
        raise Exception(
            "MAIL_USERNAME or MAIL_PASSWORD are not loaded in environment, create a .env file and add these 2 values"
        )

    if not rec_email or "@" not in rec_email:
        print("Invalid recipient email")
        return False

    try:
        # Outlook SMTP Configuration
        s = smtplib.SMTP("smtp.office365.com", 587)
        s.starttls()
        s.login(USERNAME, PASSWORD)
        message = "Subject: {}\n\n{}".format(sub, text)
        s.sendmail(USERNAME, rec_email, message)
        print("Email Sent Successfully!")
        s.quit()
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False


def downloadImage(query, n=4):
    query = query.replace("images", "")
    query = query.replace("image", "")
    query = query.replace("search", "")
    query = query.replace("show", "")
    URL = "https://www.google.com/search?tbm=isch&q=" + query
    result = requests.get(URL)
    src = result.content

    soup = BeautifulSoup(src, "html.parser")
    imgTags = soup.find_all("img", class_="yWs4tf")  # old class name -> t0fcAb

    if os.path.exists("Downloads") == False:
        os.mkdir("Downloads")

    count = 0
    for i in imgTags:
        if count == n:
            break
        try:
            urllib.request.urlretrieve(i["src"],
                                       "Downloads/" + str(count) + ".jpg")
            count += 1
            print("Downloaded", count)
        except Exception as e:
            raise e


# Add headers to mimic browser for better scraping success
HEADERS = {
    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def enhanced_google_search(query, num_results=5):
    """Enhanced Google search that fetches and returns top results with titles, links, and snippets.

    Returns a list of dicts: [{'title':..., 'link':..., 'snippet':...}, ...]
    Returns empty list when no structured results found or on error (browser search still opened).
    """
    query = query.replace("search", "").replace("google", "").strip()
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num={num_results}"
    try:
        logger.info(f"Performing Google search for: {query}")
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        # Google's DOM can vary; look for common result containers
        for g in soup.find_all("div", class_="g"):
            title_el = g.find("h3")
            link = ""
            a = g.find("a")
            if a and a.has_attr("href"):
                link = a["href"]
            snippet_el = g.find("span", class_="st") or g.find("div",
                                                               class_="IsZvec")
            if title_el:
                title = title_el.text.strip()
                snippet = snippet_el.text.strip() if snippet_el else ""
                results.append({
                    "title": title,
                    "link": link,
                    "snippet": snippet
                })

        if results:
            logger.info(f"Found {len(results)} results for query: {query}")
            try:
                webbrowser.open(url)
            except Exception:
                logger.debug("Could not open browser for search URL")
            return results

        # No structured results parsed — open browser and return empty list
        logger.info(
            f"No structured results found for query: {query}. Opening browser search."
        )
        try:
            webbrowser.open(url)
        except Exception:
            logger.debug("Could not open browser for search URL")
        return []

    except Exception as e:
        logger.error(f"Google search error for '{query}': {e}")
        try:
            webbrowser.open(url)
        except Exception:
            logger.debug("Could not open browser for search URL")
        return []


def search_on_site(query, site, num_results=5):
    """Search Google restricted to a specific site using site: operator and return results."""
    enhanced_query = f"site:{site} {query}"
    return enhanced_google_search(enhanced_query, num_results)


def search_mozilla(query, num_results=5):
    """Search on Mozilla.org via Google."""
    return search_on_site(query, "mozilla.org", num_results)


def search_facebook(query, num_results=5):
    """Search on Facebook.com via Google (note: may be limited due to Facebook's restrictions)."""
    return search_on_site(query, "facebook.com", num_results)


def search_twitter(query, num_results=5):
    """Search on Twitter.com (X.com) via Google."""
    return search_on_site(query, "twitter.com", num_results)


def search_reddit(query, num_results=5):
    """Search on Reddit.com via Google as an additional site."""
    return search_on_site(query, "reddit.com", num_results)


def search_yahoo(query, num_results=5):
    """Search on Yahoo.com via Google as an additional site."""
    return search_on_site(query, "yahoo.com", num_results)


def search_bing(query, num_results=5):
    """Directly search on Bing and fetch results (as an alternative to Google)."""
    url = f"https://www.bing.com/search?q={query.replace(' ', '+')}&count={num_results}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        for li in soup.find_all("li", class_="b_algo"):
            title = li.find("h2")
            link = li.find("a")["href"] if li.find("a") else ""
            snippet = li.find("p")
            if title:
                results.append({
                    "title": title.text,
                    "link": link,
                    "snippet": snippet.text if snippet else "",
                })
        if results:
            webbrowser.open(url)
            return results
        else:
            return "No results found on Bing."
    except Exception as e:
        print(f"Bing search error: {e}")
        webbrowser.open(url)
        return "Error fetching Bing results, opening browser search."


def multi_platform_search(query, num_results=3):
    """Perform search across multiple platforms: Google, Mozilla, Facebook, Twitter, Reddit, Yahoo, and Bing."""
    platforms = {
        "Google": enhanced_google_search(query, num_results),
        "Mozilla": search_mozilla(query, num_results),
        "Facebook": search_facebook(query, num_results),
        "Twitter": search_twitter(query, num_results),
        "Reddit": search_reddit(query, num_results),
        "Yahoo": search_yahoo(query, num_results),
        "Bing": search_bing(query, num_results),
    }
    return platforms


# Additional enhancements: Add logging for searches

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


def log_search(query, platform):
    logging.info(f"Search performed: {query} on {platform}")


# Wrap existing googleSearch to use enhanced version optionally
def original_googleSearch(query):
    return googleSearch(query)  # Keep original as alias if needed


# Enhance youtube to also search via Google if needed
def enhanced_youtube(query):
    result = youtube(query)
    if "couldn't find" in result:
        return enhanced_google_search(f"{query} site:youtube.com")
    return result


# Enhance latestNews to include news from multiple sources
def enhanced_latestNews(news=5):
    original = latestNews(news)
    google_news = enhanced_google_search("latest news", news)
    return {"Original": original, "Google": google_news}


# Enhance jokes to fetch from multiple sites
def enhanced_jokes():
    original = jokes()
    more_jokes = enhanced_google_search("dad jokes", 3)
    return {"Original": original, "More": more_jokes}


# Enhance downloadImage to download from multiple search engines
def enhanced_downloadImage(query, n=4):
    downloadImage(query, n)
    bing_url = f"https://www.bing.com/images/search?q={query.replace(' ', '+')}"
    response = requests.get(bing_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    img_tags = soup.find_all("img", class_="mimg")
    count = 0
    for img in img_tags:
        if count == n:
            break
        src = img.get("src")
        if src:
            try:
                urllib.request.urlretrieve(src, f"Downloads/bing_{count}.jpg")
                count += 1
                print(f"Downloaded from Bing: {count}")
            except BaseException:
                pass
