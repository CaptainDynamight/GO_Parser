import requests
from bs4 import BeautifulSoup
import time
import csv
import random

categories = [
    "general-aptitude",
    "mathematics",
    "digital-logic",
    "programming-in-c",
    "algorithms",
    "theory-of-computation",
    "compiler-design",
    "operating-system",
    "databases",
    "co-and-architecture",
    "computer-networks",
    "artificial-intelligence",
    "machine-learning",
    "data-mining-and-warehousing",
]

base_url = "https://gateoverflow.in"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

with open('url/go_question_urls.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Subject", "Question_URL"])

    for category in categories:
        print(f"Harvesting: {category}")
        start = 0
        
        while True:
            cat_url = f"{base_url}/questions/{category}?start={start}"
            response = requests.get(cat_url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            question_links = soup.select('.qa-q-item-title a')

            if not question_links:
                break
                
            for link in question_links:
                href = link.get('href')
                full_url = base_url + href[2:]
                writer.writerow([category, full_url])
                
            print(f"  Scraped up to start={start}...")
            start += 20 
            time.sleep(random.uniform(1, 3)) 