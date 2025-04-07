import requests
import json
from datetime import datetime
import time
import urllib.parse
import sys

# API key
API_KEY = input("Lütfen geçerli bir Riot API keyi girin: ")

# Hesap bilgileri
GAME_NAME = input("Lütfen hesap adını girin: ")
TAG_LINE = input("Lütfen hesap tag'ini girin: ")

REGION = "tr1"  
ROUTING = "europe"  
MAX_MATCHES = 500  

def get_account_by_riot_id(game_name, tag_line):
    """Riot ID kullanarak hesap bilgilerini alır (PUUID dahil)"""
    encoded_game_name = urllib.parse.quote(game_name)
    encoded_tag_line = urllib.parse.quote(tag_line)
    url = f"https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{encoded_game_name}/{encoded_tag_line}"
    headers = {"X-Riot-Token": API_KEY}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching account by Riot ID: {response.status_code}")
        print(response.text)
        return None
    return response.json()

def get_summoner_by_puuid(puuid):
    """PUUID kullanarak summoner bilgilerini alır"""
    url = f"https://{REGION}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
    headers = {"X-Riot-Token": API_KEY}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching summoner by PUUID: {response.status_code}")
        print(response.text)
        return None
    return response.json()

def get_match_history(puuid, count=500):
    """PUUID kullanarak maç geçmişini alır (maksimum 500 maç)"""
    url = f"https://{ROUTING}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
    headers = {"X-Riot-Token": API_KEY}
    
    # Riot API bir seferde maksimum 100 maç döndürür
    # 500 maç almak için birden fazla istek yapmamız gerekiyor
    
    match_ids = []
    max_batch = 100  # Tek seferde alınabilecek maksimum maç sayısı
    
    # Toplam 500 maç veya daha az alana kadar döngü
    for i in range(0, count, max_batch):
        batch_size = min(max_batch, count - i)
        params = {
            "count": batch_size,
            "start": i
        }
        
        print(f"Maç geçmişi alınıyor: {i+1}-{i+batch_size}/{count}")
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error fetching match history: {response.status_code}")
            print(response.text)
            break
        
        batch_matches = response.json()
        if not batch_matches:  
            break
            
        match_ids.extend(batch_matches)
        
        # Rate limiti aşmamak için her büyük istekten sonra bekleme
        if i + max_batch < count:
            time.sleep(1.5)
    
    return match_ids

def get_match_details(match_id):
    """Maç ID'si kullanarak maç detaylarını alır"""
    url = f"https://{ROUTING}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    headers = {"X-Riot-Token": API_KEY}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching match details: {response.status_code}")
        print(response.text)
        return None
    return response.json()

def main():
    # Adım 1: Riot ID'den hesap bilgilerini al (PUUID dahil)
    print(f"Riot ID için bilgiler: {GAME_NAME}#{TAG_LINE}")
    account_data = get_account_by_riot_id(GAME_NAME, TAG_LINE)
    
    if not account_data:
        print("Hesap bilgileri alınamadı. Riot ID bilgileri yanlış olabilir.")
        return
        
    print("Account data:", json.dumps(account_data, indent=2))
    puuid = account_data.get('puuid')
    
    if not puuid:
        print("PUUID bulunamadı!")
        return
    
    print(f"PUUID: {puuid}")
    
    # Adım 2: PUUID kullanarak summoner bilgilerini al
    summoner_data = get_summoner_by_puuid(puuid)
    
    if not summoner_data:
        print("Summoner bilgileri alınamadı")
        return
        
    print("Summoner data:", json.dumps(summoner_data, indent=2))
    
    # Adım 3: Maç geçmişini al (maksimum 500 maç)
    print(f"Maksimum {MAX_MATCHES} maç alınıyor...")
    match_ids = get_match_history(puuid, MAX_MATCHES)
    
    if not match_ids:
        print("Maç geçmişi bulunamadı veya oyuncu maç oynamamış")
        return
    
    print(f"{len(match_ids)} maç bulundu")
    
    # Tüm maçları indir
    print(f"Tüm maç verileri indiriliyor ({len(match_ids)} maç)...")
    
    # Adım 4: Maç detaylarını topla
    matches_data = []
    for i, match_id in enumerate(match_ids):
        try:
            print(f"Maç verileri alınıyor {i+1}/{len(match_ids)}: {match_id}")
            match_data = get_match_details(match_id)
            if match_data:
                matches_data.append(match_data)
            
            time.sleep(1.2)
        except Exception as e:
            print(f"Maç {match_id} alınırken hata: {e}")
    
    # Adım 5: Verileri dosyaya kaydet
    if matches_data:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"matches_{GAME_NAME.replace(' ', '_')}_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(matches_data, f, ensure_ascii=False, indent=2)
        print(f"Veriler {filename} dosyasına kaydedildi!")
    else:
        print("Hiç maç verisi toplanamadı")

if __name__ == "__main__":
    main() 