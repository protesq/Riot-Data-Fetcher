# Riot Games League of Legends Maç Verisi Toplayıcı

Bu araç, Riot Games API'sini kullanarak bir League of Legends oyuncusunun maç geçmişini toplamaya yarayan basit bir Python scriptidir.

## Gereksinimler

- Python 3.6+
- `requests` kütüphanesi

```bash
pip install requests
```

## Riot API Key Alımı

Scripti kullanabilmek için bir Riot Games API anahtarına ihtiyacınız var. API anahtarı almak için:

1. [Riot Developer Portal](https://developer.riotgames.com/) adresine gidin
2. League of Legends hesabınızla giriş yapın
3. Sağ üst köşedeki takma adınıza tıklayın
4. Dashboard'a girin.
5. "Development API Key" kısmına geldikten sonra api keyinizi kopyalayabilirsiniz.


## Kullanım

1. Scripti çalıştırın:
```bash
python riot_data_fetcher.py
```

2. Script sırasıyla şu bilgileri isteyecektir:
   - **API Key:** Riot Developer Portal'dan aldığınız API anahtarı
   - **Hesap Adı:** League of Legends oyuncu adınız (örn. "Best Janna")
   - **Tag Line:** Riot ID'nizin # işaretinden sonra gelen kısmı (örn. "EUW" veya "TR1")

```
Lütfen geçerli bir Riot API keyi girin: RGAPI-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Lütfen hesap adını girin: Best Janna
Lütfen hesap tag'ini girin: TR1
```

3. Script çalıştıktan sonra, belirtilen hesabın son 500 maçını (veya hesapta bulunan tüm maçları) indirip JSON formatında kaydedecektir.

## Nasıl Çalışır?

Script, şu adımları izler:

1. Riot ID (Oyuncu Adı + Tag Line) kullanarak hesap bilgilerini alır
2. Hesap bilgilerinden PUUID (Permanent User ID) elde eder
3. PUUID kullanarak hesabın maç geçmişini alır (maksimum 500 maç)
4. Her maç için detaylı verileri indirir
5. Tüm maç verilerini JSON formatında bir dosyaya kaydeder

## Dosya Çıktısı

Script, maç verilerini aşağıdaki formatta bir dosyaya kaydeder:
```
matches_[OYUNCU_ADI]_[ZAMAN_DAMGASI].json
```

Örnek: `matches_Best_Janna_20230421_153045.json`

## Önemli Notlar

- Bu script, Riot Games API'sinin rate limit'ine uygun şekilde tasarlanmıştır.
- Bölge olarak varsayılan değer TR1 (Türkiye) ve yönlendirme bölgesi olarak EUROPE kullanılmaktadır.
- Farklı bölgeler için kodda REGION ve ROUTING değişkenlerini değiştirebilirsiniz.
- Scriptın çalışma süresi, toplanan maç sayısına bağlı olarak değişir. 500 maç için yaklaşık 15-30 dakika sürebilir.

## Hata Giderme

- **"Error fetching account by Riot ID":** Hesap adı veya tag hatalı olabilir
- **"Error fetching match history":** API Key geçersiz veya süresi dolmuş olabilir
- **"PUUID bulunamadı":** Hesap bulunamadı veya API yanıtında beklenen veri yok
