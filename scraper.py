import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time
import re

class SeriesScraper:
    def __init__(self):
        self.base_url = "https://ak.sv"
        self.series_url = "https://ak.sv/series?section=29&category=87&rating=0&year=2026&language=1&formats=0&quality=0"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.data_file = 'series_data.json'
        
    def fetch_page(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            return response.text
        except:
            return None
    
    def extract_series_list(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        series_list = []
        
        # Ïí ãÌÑÏ ãËÇá - åÊÚÏáåÇ ÈÚÏíä ÍÓÈ ãæŞÚ ak.sv
        series_cards = soup.find_all('div', class_='series-card')
        
        for card in series_cards:
            try:
                title = card.text[:50]
                series_list.append({
                    'title': title,
                    'url': 'https://ak.sv/series/1',
                    'episodes': []
                })
            except:
                continue
        
        return series_list
    
    def run(self):
        print("?? ÈÏÁ ÇáÊÍÏíË...")
        html = self.fetch_page(self.series_url)
        
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
        else:
            old_data = {'series': []}
        
        new_data = {'series': self.extract_series_list(html)}
        new_data['last_update'] = datetime.now().isoformat()
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
        
        print(f"? Êã ÇáÊÍÏíË - {len(new_data['series'])} ãÓáÓá")

if __name__ == "__main__":
    scraper = SeriesScraper()
    scraper.run()