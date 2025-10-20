import time
import re
from urllib.parse import urljoin, urlparse
import urllib.robotparser as robotparser

import requests
from bs4 import BeautifulSoup
import pandas as pd

BASE = "https://ngosindia.org"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; NGOsIndia-RajasthanScraper/1.0)"}

def can_fetch(url):
    parsed = urlparse(url)
    robots_url = urljoin(f"{parsed.scheme}://{parsed.netloc}", "/robots.txt")
    rp = robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(HEADERS["User-Agent"], url)
    except Exception:
        return False

def safe_get(url, session, timeout=15):
    if not can_fetch(url):
        print(f"[robots] skipping (disallowed): {url}")
        return None, None
    try:
        r = session.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return r.url, r.text
    except Exception as e:
        print(f"[error] failed to fetch {url}: {e}")
        return None, None

def find_emails(text):
    return list(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)))

def find_phones(text):
    phones = re.findall(r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{5,10}", text)
    return list(set([p.strip() for p in phones if len(re.sub('[^0-9]', '', p)) >= 6]))

def extract_from_profile(html, page_url):
    soup = BeautifulSoup(html, "lxml")
    text = " ".join(soup.stripped_strings)

    name = soup.find("h1").get_text(strip=True) if soup.find("h1") else soup.title.get_text(strip=True) if soup.title else ""

    contact_person = re.search(r"Contact Person[:\s-]+([^\n<]{2,200})", text, flags=re.I)
    contact_person = contact_person.group(1).strip() if contact_person else ""

    address = re.search(r"Add\.?[:\s-]+([^\n]{5,250})", text, flags=re.I)
    address = address.group(1).strip() if address else (soup.find("address").get_text(separator=" ", strip=True) if soup.find("address") else "")

    purpose = re.search(r"Purpose[:\s-]+([^\n]{5,500})", text, flags=re.I)
    if purpose:
        purpose = purpose.group(1).strip()
    else:
        aim = re.search(r"Aims/Objectives/Mission[:\s-]+([^\n]{5,500})", text, flags=re.I)
        purpose = aim.group(1).strip() if aim else ""

    emails = find_emails(text)
    phones = find_phones(text)

    website = ""
    site_match = soup.find("a", href=True, text=re.compile(r"Website", flags=re.I))
    if site_match:
        website = site_match["href"]
    else:
        m = re.search(r"Website[:\s-]+(https?://\S+)", text, flags=re.I)
        if m:
            website = m.group(1).strip()

    return {
        "ngo_name": name,
        "page_url": page_url,
        "address": address,
        "purpose_or_services": purpose,
        "contact_person": contact_person,
        "contact_numbers": ", ".join(phones),
        "emails": ", ".join(emails),
        "website": website,
    }

def collect_ngo_links_from_rajasthan():
    session = requests.Session()
    rajasthan_page = urljoin(BASE + '/', 'rajasthan-ngos/')
    print(f"Scraping Rajasthan NGOs from: {rajasthan_page}")

    _, html = safe_get(rajasthan_page, session)
    if not html:
        print("Could not fetch Rajasthan page.")
        return []

    soup = BeautifulSoup(html, "lxml")
    links = []
    for a in soup.find_all("a", href=True):
        href = a['href']
        if href.startswith('/'):
            href = urljoin(BASE, href)
        if re.search(r"rajasthan-ngos/[-a-z0-9]+", href):
            links.append(href)

    print(f"Found {len(links)} NGO profile links for Rajasthan.")
    return sorted(set(links))

def scrape_rajasthan_top5():
    session = requests.Session()
    ngo_links = collect_ngo_links_from_rajasthan()
    if not ngo_links:
        print("No NGO links found for Rajasthan.")
        return

    print(f"Extracting details of the first {min(5, len(ngo_links))} NGOs...")
    rows = []
    for i, link in enumerate(ngo_links[:5], 1):
        print(f"[{i}] Fetching: {link}")
        final, html = safe_get(link, session)
        if not html:
            print(f"  -> skipped {link}")
            continue
        data = extract_from_profile(html, final)
        rows.append(data)
        time.sleep(1.0)

    if not rows:
        print("No NGO profiles scraped.")
        return

    df = pd.DataFrame(rows)
    out_file = "ngos_rajasthan_top5.xlsx"
    df.to_excel(out_file, index=False)
    print(f"Saved {len(df)} records to {out_file}")
    print(df)

if __name__ == "__main__":
    print("Rajasthan NGO Scraper - Scrapes top 5 profiles from ngosindia.org")
    scrape_rajasthan_top5()
