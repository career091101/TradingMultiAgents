import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import random
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_result,
)


def is_rate_limited(response):
    """Check if the response indicates rate limiting (status code 429)"""
    return response.status_code == 429


def is_overloaded(response):
    """Check if the response indicates server overload (status code 529)"""
    return response.status_code == 529


def is_retryable_error(response):
    """Check if the response indicates a retryable error"""
    return response.status_code in [429, 529, 500, 502, 503, 504]


@retry(
    retry=(retry_if_result(is_retryable_error)),
    wait=wait_exponential(multiplier=2, min=5, max=120),  # より長い待機時間
    stop=stop_after_attempt(10),  # 最大10回試行
)
def make_request(url, headers):
    """Make a request with enhanced retry logic for rate limiting and overload"""
    # ランダム遅延を増加（2-8秒）
    time.sleep(random.uniform(2, 8))
    response = requests.get(url, headers=headers)
    
    # エラーログ
    if response.status_code != 200:
        print(f"⚠️ API Error ({response.status_code} {response.text}) · Retrying in {random.uniform(2, 8):.1f} seconds…")
    
    return response


def getNewsData(query, start_date, end_date):
    """
    Scrape Google News search results for a given query and date range.
    query: str - search query
    start_date: str - start date in the format yyyy-mm-dd or mm/dd/yyyy
    end_date: str - end date in the format yyyy-mm-dd or mm/dd/yyyy
    """
    if "-" in start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        start_date = start_date.strftime("%m/%d/%Y")
    if "-" in end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        end_date = end_date.strftime("%m/%d/%Y")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/101.0.4951.54 Safari/537.36"
        )
    }

    news_results = []
    page = 0
    while True:
        offset = page * 10
        url = (
            f"https://www.google.com/search?q={query}"
            f"&tbs=cdr:1,cd_min:{start_date},cd_max:{end_date}"
            f"&tbm=nws&start={offset}"
        )

        try:
            response = make_request(url, headers)
            soup = BeautifulSoup(response.content, "html.parser")
            results_on_page = soup.select("div.SoaBEf")

            if not results_on_page:
                break  # No more results found

            for el in results_on_page:
                try:
                    # リンクの取得
                    link_element = el.find("a")
                    if not link_element or "href" not in link_element.attrs:
                        continue
                    link = link_element["href"]
                    
                    # タイトルの取得（Noneチェック付き）
                    title_element = el.select_one("div.MBeuO")
                    title = title_element.get_text() if title_element else "No title"
                    
                    # スニペットの取得（Noneチェック付き）
                    snippet_element = el.select_one(".GI74Re")
                    snippet = snippet_element.get_text() if snippet_element else "No snippet"
                    
                    # 日付の取得（Noneチェック付き）
                    date_element = el.select_one(".LfVVr")
                    date = date_element.get_text() if date_element else "No date"
                    
                    # ソースの取得（Noneチェック付き）
                    source_element = el.select_one(".NUnG9d span")
                    source = source_element.get_text() if source_element else "Unknown source"
                    
                    news_results.append(
                        {
                            "link": link,
                            "title": title,
                            "snippet": snippet,
                            "date": date,
                            "source": source,
                        }
                    )
                except Exception as e:
                    print(f"Error processing result: {e}")
                    # If one of the fields is not found, skip this result
                    continue

            # Update the progress bar with the current count of results scraped

            # Check for the "Next" link (pagination)
            next_link = soup.find("a", id="pnnext")
            if not next_link:
                break

            page += 1

        except Exception as e:
            print(f"Failed after multiple retries: {e}")
            break

    return news_results
