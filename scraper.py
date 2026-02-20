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
        self.base_series_url = "https://ak.sv/series?section=29&category=87&rating=0&year=2026&language=1&formats=0&quality=0"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
            'Referer': 'https://ak.sv/',
        }
        self.data_file = 'series_data.json'
        self.stats_file = 'stats.json'
        
    def fetch_page(self, url):
        """جلب محتوى الصفحة"""
        try:
            print(f"📡 جلب: {url}")
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"❌ خطأ في جلب الصفحة: {e}")
            return None
    
    def extract_series_from_page(self, html, page_num):
        """استخراج المسلسلات من صفحة واحدة"""
        soup = BeautifulSoup(html, 'html.parser')
        series_list = []
        
        # البحث عن عناصر المسلسلات - حسب هيكل موقع ak.sv
        series_cards = soup.find_all('div', class_='MovieBlock') or \
                      soup.find_all('div', class_='SeriesCard') or \
                      soup.find_all('article', class_='movie-item') or \
                      soup.find_all('div', class_='col-lg-2 col-md-3 col-sm-4 col-6') or \
                      soup.find_all('div', class_='Thumb--GridItem')
        
        print(f"  📄 صفحة {page_num}: تم العثور على {len(series_cards)} عنصر")
        
        for card in series_cards:
            try:
                # استخراج رابط المسلسل
                link_tag = card.find('a')
                if not link_tag:
                    continue
                    
                series_url = link_tag.get('href', '')
                if series_url and not series_url.startswith('http'):
                    series_url = self.base_url + series_url
                
                # استخراج اسم المسلسل
                title_tag = card.find('h3') or card.find('h4') or card.find('h5') or \
                           card.find('div', class_='Title') or card.find('span', class_='name')
                title = title_tag.text.strip() if title_tag else "غير معروف"
                
                # استخراج الصورة
                img_tag = card.find('img')
                img_url = img_tag.get('src', '') if img_tag else ''
                if img_url and not img_url.startswith('http'):
                    img_url = self.base_url + img_url
                
                # تنظيف اسم المسلسل من الأرقام الزائدة
                title = re.sub(r'\d+\s*:\s*', '', title)  # شيل الأرقام زي "45 :"
                title = re.sub(r'^\d+\s*', '', title)     # شيل الأرقام في البداية
                
                series_list.append({
                    'id': f"page{page_num}_{len(series_list)}",
                    'title': title.strip(),
                    'url': series_url,
                    'image': img_url,
                    'year': '2026',
                    'episodes': [],
                    'last_updated': datetime.now().isoformat(),
                    'source_page': page_num,
                    'status': 'مستمر'
                })
                
            except Exception as e:
                print(f"    ⚠️ خطأ في استخراج بيانات مسلسل: {e}")
                continue
        
        return series_list
    
    def scrape_all_pages(self, start_page=1, end_page=5):
        """جلب المسلسلات من كل الصفحات"""
        all_series = []
        
        for page in range(start_page, end_page + 1):
            # بناء رابط الصفحة
            if page == 1:
                url = self.base_series_url
            else:
                url = f"{self.base_series_url}&page={page}"
            
            print(f"\n📑 جلب صفحة {page}/{end_page}")
            html = self.fetch_page(url)
            
            if html:
                page_series = self.extract_series_from_page(html, page)
                all_series.extend(page_series)
                print(f"  ✅ تم العثور على {len(page_series)} مسلسل في الصفحة {page}")
            else:
                print(f"  ❌ فشل في جلب الصفحة {page}")
            
            # انتظار بين الصفحات عشان ما نضغطش على السيرفر
            if page < end_page:
                print("  ⏳ انتظار 2 ثانية...")
                time.sleep(2)
        
        return all_series
    
    def extract_episodes(self, series_url):
        """استخراج حلقات المسلسل"""
        print(f"  📥 جلب حلقات...")
        html = self.fetch_page(series_url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        episodes = []
        
        # البحث عن روابط الحلقات
        episode_elements = soup.find_all('a', href=re.compile(r'/episode/')) or \
                          soup.find_all('div', class_='Episode') or \
                          soup.find_all('li', class_='episode-item') or \
                          soup.find_all('a', class_='watch-episode')
        
        for i, episode in enumerate(episode_elements[:30], 1):  # حد أقصى 30 حلقة
            try:
                # استخراج رابط الحلقة
                link = episode if episode.name == 'a' else episode.find('a')
                if not link:
                    continue
                    
                episode_url = link.get('href', '')
                if episode_url and not episode_url.startswith('http'):
                    episode_url = self.base_url + episode_url
                
                # استخراج رابط المشاهدة
                watch_url = self.extract_watch_url(episode_url)
                
                episodes.append({
                    'number': i,
                    'title': f"الحلقة {i}",
                    'url': episode_url,
                    'watch_url': watch_url,
                    'added_date': datetime.now().isoformat()
                })
                
                if watch_url:
                    print(f"    ✅ الحلقة {i}: تم العثور على رابط")
                else:
                    print(f"    ⚠️ الحلقة {i}: لا يوجد رابط مشاهدة")
                    
                time.sleep(0.3)  # تجنب الضغط على السيرفر
                
            except Exception as e:
                print(f"    ❌ خطأ في الحلقة {i}: {e}")
                continue
        
        return episodes
    
    def extract_watch_url(self, episode_url):
        """استخراج رابط المشاهدة المباشر"""
        html = self.fetch_page(episode_url)
        if not html:
            return None
        
        # البحث عن روابط .m3u8
        m3u8_pattern = r'https?://[^\s"\']+\.m3u8[^\s"\']*'
        m3u8_matches = re.findall(m3u8_pattern, html)
        
        if m3u8_matches:
            return m3u8_matches[0]
        
        # البحث عن روابط .mp4
        mp4_pattern = r'https?://[^\s"\']+\.mp4[^\s"\']*'
        mp4_matches = re.findall(mp4_pattern, html)
        
        if mp4_matches:
            return mp4_matches[0]
        
        # البحث عن iframe
        soup = BeautifulSoup(html, 'html.parser')
        iframe = soup.find('iframe')
        if iframe and iframe.get('src'):
            return iframe.get('src')
        
        # البحث عن video source
        video = soup.find('video')
        if video:
            source = video.find('source')
            if source and source.get('src'):
                return source.get('src')
        
        return None
    
    def load_existing_data(self):
        """تحميل البيانات الموجودة"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {'series': [], 'last_update': None, 'total_series': 0, 'total_pages': 0}
        return {'series': [], 'last_update': None, 'total_series': 0, 'total_pages': 0}
    
    def save_data(self, data):
        """حفظ البيانات في ملف JSON"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 تم حفظ {len(data['series'])} مسلسل في {self.data_file}")
    
    def save_stats(self, data, pages_scraped):
        """حفظ الإحصائيات"""
        total_episodes = sum(len(s['episodes']) for s in data['series'])
        episodes_with_links = sum(1 for s in data['series'] for e in s['episodes'] if e.get('watch_url'))
        
        stats = {
            'total_series': len(data['series']),
            'total_episodes': total_episodes,
            'episodes_with_links': episodes_with_links,
            'pages_scraped': pages_scraped,
            'last_update': data['last_update'],
            'source_url': self.base_series_url,
            'next_update': 'كل 6 ساعات'
        }
        
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"📊 تم حفظ الإحصائيات في {self.stats_file}")
    
    def merge_series_data(self, old_data, new_series_list):
        """دمج البيانات الجديدة مع القديمة"""
        if not old_data.get('series'):
            old_data['series'] = []
        
        old_series_dict = {s['url']: s for s in old_data['series']}
        new_count = 0
        updated_count = 0
        
        for new_series in new_series_list:
            if new_series['url'] in old_series_dict:
                # مسلسل موجود - نتحقق من الحلقات الجديدة
                old_series = old_series_dict[new_series['url']]
                old_episodes = {e['number']: e for e in old_series.get('episodes', [])}
                
                new_episodes = []
                for ep in new_series['episodes']:
                    if ep['number'] not in old_episodes:
                        new_episodes.append(ep)
                
                if new_episodes:
                    old_series['episodes'].extend(new_episodes)
                    old_series['last_updated'] = datetime.now().isoformat()
                    updated_count += len(new_episodes)
            else:
                # مسلسل جديد
                old_data['series'].append(new_series)
                new_count += 1
        
        old_data['last_update'] = datetime.now().isoformat()
        old_data['total_series'] = len(old_data['series'])
        
        print(f"📊 ملخص: {new_count} مسلسل جديد، {updated_count} حلقة جديدة")
        
        return old_data
    
    def run(self):
        """تشغيل السكريبت"""
        print("=" * 60)
        print("🚀 بدء جلب المسلسلات العربية 2026 من ak.sv")
        print("=" * 60)
        
        # تحديد عدد الصفحات
        start_page = 1
        end_page = 5
        print(f"📑 جلب الصفحات من {start_page} إلى {end_page}")
        print("-" * 60)
        
        # جلب كل المسلسلات من كل الصفحات
        all_series = self.scrape_all_pages(start_page, end_page)
        
        print("\n" + "=" * 60)
        print(f"📺 إجمالي المسلسلات قبل جلب الحلقات: {len(all_series)}")
        print("=" * 60)
        
        # جلب حلقات كل مسلسل (أول 10 مسلسلات فقط للاختبار)
        # لو عاوز الكل، غير range(len(all_series))
        max_series_to_process = min(10, len(all_series))  # للاختبار، هجيب أول 10 بس
        print(f"📥 جاري جلب حلقات أول {max_series_to_process} مسلسل...")
        
        for i in range(max_series_to_process):
            series = all_series[i]
            print(f"\n[{i+1}/{max_series_to_process}] 📺 {series['title'][:50]}")
            series['episodes'] = self.extract_episodes(series['url'])
            print(f"   ✅ {len(series['episodes'])} حلقة")
            time.sleep(1)  # تأخير بين المسلسلات
        
        # تحميل البيانات الموجودة ودمجها
        print("\n" + "-" * 60)
        print("🔄 دمج البيانات...")
        old_data = self.load_existing_data()
        updated_data = self.merge_series_data(old_data, all_series)
        
        # حفظ البيانات
        self.save_data(updated_data)
        self.save_stats(updated_data, end_page)
        
        print("\n" + "=" * 60)
        print("✅ تم الانتهاء بنجاح!")
        print(f"📊 إجمالي المسلسلات: {updated_data['total_series']}")
        print(f"📊 إجمالي الحلقات: {sum(len(s['episodes']) for s in updated_data['series'])}")
        print("=" * 60)
        print("⏱️  التحديث القادم: بعد 6 ساعات")
        print("=" * 60)

if __name__ == "__main__":
    scraper = SeriesScraper()
    scraper.run()
