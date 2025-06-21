import os
import requests
from flask import Flask, request, jsonify
from datetime import datetime
import subprocess
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv # <<< BU SATIR .env dosyasını yükler

# .env dosyasındaki ortam değişkenlerini yükle
load_dotenv()

app = Flask(__name__)

# --- YAPILANDIRMA ---
# World News API Anahtarınız
# API anahtarını doğrudan koda yazmak yerine ortam değişkeni kullanmak en iyisidir.
# 'WORLD_NEWS_API_KEY' ortam değişkeninden değeri alır.
WORLD_NEWS_API_KEY = os.environ.get("WORLD_NEWS_API_KEY")

# Eğer API anahtarı yüklenememişse uygulama başlamadan hata ver
if not WORLD_NEWS_API_KEY:
    raise ValueError("WORLD_NEWS_API_KEY ortam değişkeni ayarlanmadı. Lütfen .env dosyanızı veya ortam değişkenlerinizi kontrol edin.")

# Hugo sitenizin content klasöründeki haberlerin kaydedileceği yol
# os.path.join ile doğru path'i sağlarız, işletim sisteminden bağımsız.
HUGO_CONTENT_PATH = os.path.join(os.path.dirname(__file__), 'static_site', 'content', 'posts')

# Haberlerin kaydedileceği kategori (Hugo'da kullanılır)
NEWS_CATEGORY = "news" 

# İşlenmiş haber ID'lerini takip etmek için dosya
PROCESSED_NEWS_IDS_FILE = os.path.join(os.path.dirname(__file__), 'processed_news_ids.txt')

# 'posts' klasörü yoksa oluştur
os.makedirs(HUGO_CONTENT_PATH, exist_ok=True)


# Yardımcı Fonksiyon: İşlenmiş haber ID'lerini kaydetme ve yükleme
def load_processed_news_ids():
    """Daha önce işlenmiş haber ID'lerini dosyadan yükler."""
    if os.path.exists(PROCESSED_NEWS_IDS_FILE):
        with open(PROCESSED_NEWS_IDS_FILE, 'r') as f:
            return set(f.read().splitlines())
    return set()

def save_processed_news_ids(news_ids):
    """İşlenmiş haber ID'lerini dosyaya kaydeder."""
    with open(PROCESSED_NEWS_IDS_FILE, 'w') as f:
        for news_id in news_ids:
            f.write(f"{news_id}\n")

# Haberleri Çekme Fonksiyonu
def fetch_news(query="Global", number=15): # Çekilecek haber sayısı varsayılan olarak 15
    """World News API'den haberleri çeker."""
    url = "https://api.worldnewsapi.com/search-news"
    params = {
        "text": query,
        "number": number,
        "language": "en", # İngilizce haberler için ayarlandı
        "location": "PL",
        "api-key": WORLD_NEWS_API_KEY # Anahtar ortam değişkeninden çekiliyor
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status() # HTTP hatalarını (4xx veya 5xx) yakala
        data = response.json()
        return data.get("news", [])
    except requests.exceptions.RequestException as e:
        print(f"Haberler çekilirken hata oluştu: {e}")
        return []

# Markdown Dosyası Oluşturma Fonksiyonu
def create_hugo_markdown_file(news_item, processed_ids):
    """Gelen haber öğesinden Hugo uyumlu Markdown dosyası oluşturur."""

    # Haber başlığını dosya adı (slug) için uygun hale getirir
    slug = news_item.get('title', 'no-title').lower()
    # Sadece alfanümerik karakterleri ve boşlukları tut, boşlukları tire ile değiştir
    slug = ''.join(c for c in slug if c.isalnum() or c == ' ').strip()
    slug = slug.replace(' ', '-')

    # news_item['id']'yi benzersiz bir tanımlayıcı olarak kullanırız. Yoksa zaman damgası.
    news_id = str(news_item.get('id', datetime.now().strftime("%Y%m%d%H%M%S%f")))

    # Eğer bu haber zaten işlenmişse, atla
    if news_id in processed_ids:
        print(f"Haber zaten işlenmiş: {news_item.get('title', 'N/A')}")
        return False

    # Tarih formatı dönüşümü
    try:
        publish_date_str = news_item.get('publish_date', '')
        if 'T' in publish_date_str and '+' in publish_date_str:
            dt_obj = datetime.strptime(publish_date_str, "%Y-%m-%dT%H:%M:%S%z")
        elif 'T' in publish_date_str:
            dt_obj = datetime.strptime(publish_date_str, "%Y-%m-%dT%H:%M:%S")
        else:
            # Sadece tarih kısmı varsa
            dt_obj = datetime.strptime(publish_date_str.split(' ')[0], "%Y-%m-%d")
    except ValueError:
        print(f"Uyarı: '{publish_date_str}' tarih formatı tanınmadı. Mevcut zaman kullanılacak.")
        dt_obj = datetime.now() 

    # Hugo için uygun tarih formatı (ör: 2023-10-27T10:00:00+03:00)
    # Varsayılan olarak Türkiye saati dilimi (+03:00) eklendi.
    date_formatted = dt_obj.strftime("%Y-%m-%dT%H:%M:%S+03:00")

    # Markdown dosyasının tam yolu
    file_path = os.path.join(HUGO_CONTENT_PATH, f"{slug}-{news_id}.md")

    # YAML değerlerini güvenli hale getiren yardımcı fonksiyon
    def escape_for_yaml(text):
        if text is None:
            return ""
        # Çift tırnakları ve ters slash'leri kaçır
        return str(text).replace('\\', '\\\\').replace('"', '\\"')

    # Başlık ve diğer değerleri YAML için kaçırılmış versiyonlarını oluştururuz.
    escaped_title = escape_for_yaml(news_item.get('title', 'No Title'))
    escaped_description = escape_for_yaml(news_item.get('description', ''))
    escaped_author = escape_for_yaml(news_item.get('author', 'Anonymous')) 
    escaped_image = escape_for_yaml(news_item.get('image', ''))
    escaped_url = escape_for_yaml(news_item.get('url', ''))
    escaped_source_name = escape_for_yaml(news_item.get('source_name', 'Unknown Source')) # Haber kaynağı adı eklendi

    # Etiketler için liste oluşturma (sentiment, vb.)
    tags_list = []
    sentiment_tags = news_item.get('sentiment', '') 
    
    if isinstance(sentiment_tags, str) and sentiment_tags:
        for tag in sentiment_tags.split(', '): # Virgülle ayrılmış etiketler için
            stripped_tag = tag.strip()
            if stripped_tag:
                tags_list.append(f'"{escape_for_yaml(stripped_tag)}"') # Her etiketi tırnak içinde ekle
    tags_string = ', '.join(tags_list) 

    # Front Matter (YAML formatında meta veri)
    front_matter = f"""---
title: "{escaped_title}"
date: "{date_formatted}"
draft: false
categories: ["{NEWS_CATEGORY}"]
tags: [{tags_string}]
image: "{escaped_image}"
author: "{escaped_author}"
description: "{escaped_description}"
source_url: "{escaped_url}"
source_name: "{escaped_source_name}" # Front Matter'a source_name eklendi
---
"""
    # Haber içeriği
    # İçerik boşsa açıklamayı kullan, yoksa boş string
    content = news_item.get('text', news_item.get('description', ''))
    # İçerikteki çift tırnakları ve ters slash'leri kaçır (Markdown uyumluluğu için)
    content = str(content).replace('"', '\\"').replace('\\', '\\\\')

    # Markdown dosyasını oluşturur ve içeriği yazar
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(front_matter)
            f.write(content)
        print(f"'{news_item.get('title', 'N/A')}' başlıklı haber dosyası oluşturuldu: {file_path}")
        return news_id
    except Exception as e:
        print(f"Dosya oluşturulurken hata: {e}")
        return False

# Hugo Sitesini Yeniden Derleme Fonksiyonu
def build_hugo_site():
    """Hugo statik sitesini yeniden derler."""
    print("Hugo sitesi yeniden derleniyor...")
    # Hugo'nun çalışacağı dizin (static_site klasörü)
    hugo_root_path = os.path.join(os.path.dirname(__file__), 'static_site')
    try:
        # subprocess.run ile Hugo komutunu çalıştır
        # '-s' bayrağı ile Hugo'nun site kök dizinini belirtiriz.
        # '-D' bayrağı ile draft (taslak) sayfaları da derleriz.
        result = subprocess.run(["hugo", "-s", hugo_root_path, "-D"], capture_output=True, text=True, check=True)
        print("--- Hugo Derleme Çıktısı ---")
        print(result.stdout)
        if result.stderr:
            print("--- Hugo Derleme Hataları/Uyarıları ---")
            print(result.stderr)
        print("Hugo sitesi başarıyla derlendi.")
        return True
    except subprocess.CalledProcessError as e:
        # Hugo komutu bir hata kodu ile dönerse
        print(f"Hugo derlenirken hata oluştu: {e}")
        print("Stdout:", e.stdout)
        print("Stderr:", e.stderr)
        return False
    except FileNotFoundError:
        # 'hugo' komutu bulunamazsa
        print("Hata: 'hugo' komutu bulunamadı. Hugo'nun sistem PATH'inizde olduğundan emin olun.")
        return False


# Flask Rotası: Haberleri çek ve siteyi derle
@app.route('/fetch_and_build', methods=['GET'])
def fetch_and_build_news():
    """API'den haberleri çeker, Markdown dosyalarını oluşturur ve Hugo'yu derler."""
    query = request.args.get('query', 'Global') 
    number = int(request.args.get('number', 15)) 

    processed_ids = load_processed_news_ids()
    newly_processed_ids = set()

    news_items = fetch_news(query, number)
    if not news_items:
        return jsonify({"status": "error", "message": "Haber çekilemedi veya API hatası."})

    for news_item in news_items:
        news_id = create_hugo_markdown_file(news_item, processed_ids)
        if news_id: 
            newly_processed_ids.add(news_id)

    if newly_processed_ids:
        processed_ids.update(newly_processed_ids)
        save_processed_news_ids(processed_ids)
        print(f"{len(newly_processed_ids)} yeni haber işlendi.")
    else:
        print("Yeni haber bulunamadı veya hepsi daha önce işlenmişti.")

    if build_hugo_site():
        return jsonify({"status": "success", "message": "Haberler çekildi, dosyalar oluşturuldu ve Hugo sitesi yeniden derlendi."})
    else:
        return jsonify({"status": "error", "message": "Haberler çekildi, ancak Hugo derlenirken hata oluştu. Hugo terminalini kontrol edin."})


# GitHub Actions'ta doğrudan çağrılacak ana işlem fonksiyonu
def run_news_processing_and_build():
    """Haber çekme, markdown oluşturma ve Hugo derleme sürecini bir kez çalıştırır."""
    print("Haber işleme ve Hugo derleme süreci başlatılıyor...")
    
    # 'posts' klasörünün var olduğundan emin olalım (GitHub Actions ortamında da)
    os.makedirs(HUGO_CONTENT_PATH, exist_ok=True)

    processed_ids = load_processed_news_ids()
    newly_processed_ids = set()

    news_items = fetch_news("Turkish Community", 125) # Varsayılan query ve number
    if not news_items:
        print("Haber çekilemedi veya API hatası. İşlem durduruluyor.")
        return # Hata durumunda çık

    for news_item in news_items:
        news_id = create_hugo_markdown_file(news_item, processed_ids)
        if news_id:
            newly_processed_ids.add(news_id)

    if newly_processed_ids:
        processed_ids.update(newly_processed_ids)
        save_processed_news_ids(processed_ids)
        print(f"{len(newly_processed_ids)} yeni haber işlendi ve kaydedildi.")
    else:
        print("Yeni haber bulunamadı veya hepsi daha önce işlenmişti.")

    if build_hugo_site():
        print("Hugo sitesi başarıyla derlendi.")
    else:
        print("Hugo derlenirken hata oluştu.")


# Flask uygulamasını çalıştırma (yerel ortam için)
if __name__ == '__main__':
    # Flask uygulamasını başlatmadan önce 'posts' klasörünün var olduğundan emin olalım
    os.makedirs(HUGO_CONTENT_PATH, exist_ok=True)

    # Yerel olarak botu Flask sunucusu olarak çalıştırmak için scheduler'ı başlat
    #scheduler = BackgroundScheduler()
    # Flask test istemcisini kullanarak '/fetch_and_build' endpoint'ini belirli aralıklarla çağırır.
    #scheduler.add_job(
    #    func=lambda: app.test_client().get('/fetch_and_build'), 
    #    trigger='interval',
    #    minutes=30 # Her 1 dakika bir çalıştır.
    #)
    #print("Haber çekme ve site derleme görevi zamanlayıcıya eklendi.")
    #scheduler.start()
    
    # Flask uygulamasını başlat (debug modu açık, tüm ağ arayüzlerinde dinler)
    #app.run(debug=True, host='0.0.0.0', port=5000)

    # Haber çekme ve site derleme sürecini doğrudan çalıştır
    run_news_processing_and_build()