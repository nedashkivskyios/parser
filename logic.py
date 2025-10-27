import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from bs4 import XMLParsedAsHTMLWarning
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random
import pandas as pd

# Додаємо, щоб ігнорувати ворнінг
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/141.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Connection": "keep-alive"
}

def fetch_url_info(url, fields, retries=3):
    """Отримує необхідні поля зі сторінки URL"""
    result = {"URL": url}
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code == 503:
                time.sleep(random.uniform(1, 3))
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            if "status_code" in fields:
                result["Status Code"] = resp.status_code
            if "h1" in fields:
                h1_tag = soup.find("h1")
                result["H1"] = h1_tag.get_text(strip=True) if h1_tag else ""
            if "title" in fields:
                title_tag = soup.find("title")
                result["Title"] = title_tag.get_text(strip=True) if title_tag else ""
            if "description" in fields:
                desc_tag = soup.find("meta", attrs={"name": "description"})
                result["Description"] = desc_tag["content"].strip() if desc_tag and desc_tag.get("content") else ""
            if "canonical" in fields:
                canon_tag = soup.find("link", attrs={"rel": "canonical"})
                result["Canonical"] = canon_tag["href"].strip() if canon_tag and canon_tag.get("href") else ""
            if "og_title" in fields:
                og_title_tag = soup.find("meta", property="og:title")
                result["OG Title"] = og_title_tag["content"].strip() if og_title_tag and og_title_tag.get("content") else ""
            if "og_description" in fields:
                og_desc_tag = soup.find("meta", property="og:description")
                result["OG Description"] = og_desc_tag["content"].strip() if og_desc_tag and og_desc_tag.get("content") else ""

            return result
        except Exception:
            time.sleep(random.uniform(1, 3))

    # Якщо не вдалося
    for field in fields:
        if field not in ["status_code"]:
            key_name = field.replace("_", " ").title()
            result[key_name] = ""
        else:
            result["Status Code"] = "Error/503"
    return result

def get_namespace(root):
    return {'ns': root.tag.split('}')[0].strip('{')} if '}' in root.tag else {}

def parse_sitemap_recursive(sitemap_url, visited=None):
    if visited is None:
        visited = set()
    if sitemap_url in visited:
        return []
    visited.add(sitemap_url)

    urls = []
    try:
        response = requests.get(sitemap_url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return urls

        root = ET.fromstring(response.content)
        ns = get_namespace(root)

        # sitemap-index
        for sitemap in root.findall(".//ns:sitemap", ns) if ns else root.findall(".//sitemap"):
            loc = sitemap.find("ns:loc", ns) if ns else sitemap.find("loc")
            if loc is not None:
                urls += parse_sitemap_recursive(loc.text, visited)

        # звичайний sitemap
        for loc in root.findall(".//ns:loc", ns) if ns else root.findall(".//loc"):
            urls.append(loc.text)

    except:
        pass

    return urls

def process_urls(urls, fields, threads=5, progress_callback=None):
    """Обробка списку URL і повернення результату у вигляді словників"""
    data = []
    urls = list(set(urls))
    with ThreadPoolExecutor(max_workers=threads) as executor:
        future_to_url = {executor.submit(fetch_url_info, url, fields): url for url in urls}
        for future in as_completed(future_to_url):
            result = future.result()
            data.append(result)
            if progress_callback:
                progress_callback(result)
    return data

def save_to_excel(data, output_file):
    if data:
        df = pd.DataFrame(data)
        df.to_excel(output_file, index=False)
