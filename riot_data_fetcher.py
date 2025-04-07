import requests
import json
import pandas as pd
from datetime import datetime
import time
import urllib.parse
import sys
import os

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

def extract_player_data(match_data, puuid):
    """Belirli bir oyuncunun bir maçtaki verilerini çıkarır."""
    match_id = match_data['metadata']['matchId']
    game_creation = match_data['info']['gameCreation']
    game_duration = match_data['info']['gameDuration']
    game_duration_minutes = game_duration / 60
    queue_id = match_data['info']['queueId']
    
    # Oyuncuyu bul
    player_data = None
    for participant in match_data['info']['participants']:
        if participant.get('puuid') == puuid:
            player_data = participant
            break
    
    if not player_data:
        print(f"PUUID {puuid} maç {match_id} içinde bulunamadı, bu maç atlanıyor.")
        return None
    
    # Temel özellikleri çıkar
    extracted_data = {
        'match_id': match_id,
        'game_creation': game_creation,
        'game_duration': game_duration,
        'game_duration_minutes': game_duration_minutes,
        'queue_id': queue_id,
        'win': 1 if player_data.get('win', False) else 0,
        'champion': player_data.get('championName', ''),
        'position': player_data.get('teamPosition', ''),
        'kills': player_data.get('kills', 0),
        'deaths': player_data.get('deaths', 0),
        'assists': player_data.get('assists', 0),
        'kda': compute_kda(player_data.get('kills', 0), player_data.get('deaths', 0), player_data.get('assists', 0)),
        'champion_level': player_data.get('champLevel', 0),
        'vision_score': player_data.get('visionScore', 0),
        'vision_wards_bought': player_data.get('visionWardsBoughtInGame', 0),
        'wards_placed': player_data.get('wardsPlaced', 0),
        'wards_killed': player_data.get('wardsKilled', 0),
        'first_blood': 1 if player_data.get('firstBloodKill', False) or player_data.get('firstBloodAssist', False) else 0,
        'gold_earned': player_data.get('goldEarned', 0),
        'total_damage_dealt': player_data.get('totalDamageDealt', 0),
        'total_damage_to_champions': player_data.get('totalDamageDealtToChampions', 0),
        'total_damage_taken': player_data.get('totalDamageTaken', 0),
        'objective_damage': player_data.get('damageDealtToObjectives', 0),
        'turret_kills': player_data.get('turretKills', 0),
        'inhibitor_kills': player_data.get('inhibitorKills', 0),
        'total_minions_killed': player_data.get('totalMinionsKilled', 0) + player_data.get('neutralMinionsKilled', 0),
        'neutral_minions_killed': player_data.get('neutralMinionsKilled', 0),
    }
    
    # KDA ve diğer oranları hesapla
    extracted_data['cs_per_minute'] = extracted_data['total_minions_killed'] / game_duration_minutes if game_duration_minutes > 0 else 0
    extracted_data['damage_per_minute'] = extracted_data['total_damage_to_champions'] / game_duration_minutes if game_duration_minutes > 0 else 0
    
    # Takım bazlı istatistikleri hesapla
    team_id = player_data.get('teamId', 0)
    team_kills = 0
    for p in match_data['info']['participants']:
        if p.get('teamId', 0) == team_id:
            team_kills += p.get('kills', 0)
    
    # Kill katılım oranı
    extracted_data['kill_participation'] = (extracted_data['kills'] + extracted_data['assists']) / team_kills if team_kills > 0 else 0
    
    return extracted_data

def compute_kda(kills, deaths, assists):
    """KDA hesaplar (K+A)/D"""
    if deaths == 0:
        return (kills + assists)  # Ölmeden bitmişse deaths 0 olduğu için bölünemez
    return (kills + assists) / deaths

def convert_to_csv(matches_data, puuid, csv_filename):
    """Maç verilerini CSV formatına dönüştürür"""
    print("Veriler CSV formatına dönüştürülüyor...")
    
    # Tüm maçlardan oyuncu verilerini çıkar
    player_matches = []
    for match in matches_data:
        player_match = extract_player_data(match, puuid)
        if player_match:
            player_matches.append(player_match)
    
    print(f"İşlenen maç sayısı: {len(player_matches)}")
    
    df = pd.DataFrame(player_matches)
    
    df = df.sort_values('game_creation', ascending=False)
    
    # CSV'ye kaydet
    df.to_csv(csv_filename, index=False)
    print(f"Veriler {csv_filename} dosyasına kaydedildi!")

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
        json_filename = f"matches_{GAME_NAME.replace(' ', '_')}_{timestamp}.json"
        csv_filename = f"player_matches_{GAME_NAME.replace(' ', '_')}_{timestamp}.csv"
        
        # JSON olarak kaydet
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(matches_data, f, ensure_ascii=False, indent=2)
        print(f"Ham veriler {json_filename} dosyasına kaydedildi!")
        
        # CSV olarak da kaydet
        try:
            convert_to_csv(matches_data, puuid, csv_filename)
        except Exception as e:
            print(f"CSV dönüşümü sırasında hata: {e}")
            print("CSV oluşturma başarısız oldu, ama JSON veriler kaydedildi.")
    else:
        print("Hiç maç verisi toplanamadı")

if __name__ == "__main__":
    main() 