# Veri Setleri

Ham dosyalar `data/raw/` altındadır ve git'e girmez. Kullanıcı Kaggle'dan elle indirmiştir.
Adım 1'de (2026-11-15) iki dosya Kaggle sayfalarının herkese açık meta verisiyle (Croissant JSON,
kimlik bilgisi olmadan) eşleştirildi.

## Karar (Adım 1)
**Model yalnızca A (arabam.com, Tanrıverdi) ile kurulur. B kullanılmaz.**
Kullanıcı kararı bana bıraktı ("CV için, en mantıklı hangisiyse"). Gerekçe:
- A'nın kaynağı (arabam.com) ve dönemi (Haziran 2025) Kaggle sayfasında yazılı. Lisans alanı CC0,
  ama sayfa alt başlığı "Non-commercial use" diyor (aşağıda "Lisans çelişkisi").
- B'nin Kaggle sayfası başka bir Kaggle setinden türetildiğini söylüyor; o üst kaynak sayfası
  404 dönüyor, ilan sitesi hiçbir yerde yazmıyor. Proje kuralı: doğrulanamayan veri kullanılmaz.
- B yalnızca ~%13 ek satır getirir; buna karşılık farklı dönem (Nisan vs Haziran 2025, yüksek
  enflasyon), sütun kayması ve aralık metni biçimindeki motor bilgisi ek gürültü ve iş demektir.
- B, `data/raw/` altında durur ve `arac_fiyat.inspect_raw` içinde yalnızca inceleme için okunur.

## A — `car_price_prediction.csv` (KULLANILIYOR)
| Alan | Değer | Doğrulama |
|---|---|---|
| Kaggle başlığı | Used Car Prices Dataset (Turkey - arabam.com) | Croissant meta verisi |
| Bağlantı | https://www.kaggle.com/datasets/mehmettanriverdi/used-car-prices-dataset-turkey-arabam-com | sürüm 1 |
| Yazar | Mehmet Tanrıverdi (Kaggle: `mehmettanriverdi`) | meta veri |
| Lisans | Lisans alanı: CC0: Public Domain. Alt başlık: "(Non-commercial use)" → **çelişkili** | meta veri (`license`, `alternateName`) |
| Ülke / site | Türkiye / arabam.com | sayfa açıklaması |
| Toplanma | "The data was collected in June 2025." | sayfa açıklaması (satır bazında tarih yok) |
| Yayın tarihi | 2025-08-31 | meta veri |
| Dosya | `car_price_prediction.csv`, 6 088 499 bayt, 50 755 satır × 16 sütun | yerel dosya |
| Yazarın GitHub'ı | https://github.com/mehmettanriverdii/Otomobil-Fiyat-Tahmin | sayfa açıklaması |

**Lisans çelişkisi:** Kaggle sayfasının lisans alanı "CC0: Public Domain", ama aynı sayfanın alt
başlığı "50K used car listings with features for price prediction (Non-commercial use)".
İkisi birbiriyle çelişiyor (CC0 ticari kullanımı kısıtlamaz). Hangisinin geçerli olduğu
doğrulanamadı; bu proje ticari olmayan portfolyo çalışması olduğu için iki okumada da kullanım
uygun görünüyor, ama **lisans "temiz" sayılmaz**. Ticari kullanım düşünülürse yazara sorulmalı.

**Not:** Dosya adı Gürcistan verisi olan "Car Price Prediction Challenge" ile aynıdır ama içerik
o veri değildir: sütunlar Türkçe, markalarda Tofaş/Anadol/Ikco, `kimden` alanında
"Galeriden/Sahibinden" var ve Kaggle sayfasındaki sütun listesiyle birebir uyuşuyor.

**Fiyat için kaynak belgesi:** Sayfada "fiyat yok" anlamına gelen özel bir değer (ör. 1 = fiyat
sorunuz) **tanımlanmamış**. Bu yüzden geçerlilik kuralı yalnızca: fiyat boş / sayı değil / ≤ 0.

### Sütunlar (A)
Açıklamalar Kaggle sayfasından çevrildi; gözlemler `reports/adim1_veri_inceleme.txt`'ten.

| Sütun | Anlam | Gözlem |
|---|---|---|
| `id` | "Her araç için benzersiz numara" | Aslında 1..50755 satır sırası; ilan no değil, gruplamada kullanılamaz |
| `marka` | Marka | 76 marka; 16 markada 2 400'ün üstünde, en çok 2 491 ilan (marka başına örnekleme kotası izlenimi veriyor) |
| `seri` | Seri | 542 farklı |
| `model` | Model/donanım | 3 302 farklı; 331 boş |
| `yil` | Üretim yılı | 1951-2025; 2025 yalnızca 65 satır |
| `kilometre` | Km | medyan 189 000; 0 km 39 satır; en büyük 90 000 000 (hatalı görünüyor) |
| `vites_tipi` | Düz / Otomatik / Yarı Otomatik | 183 boş |
| `yakit_tipi` | Benzin, LPG & Benzin, Dizel, Hibrit, Elektrik | |
| `kasa_tipi` | Sedan, Hatchback/5 ... | 88 satırda `-` (fiilen boş); SUV yalnızca 167 |
| `renk` | Renk | 24 farklı |
| `motor_hacmi` | cm³ | %3,2 boş |
| `motor_gucu` | hp | %3,3 boş |
| `degisen_sayisi` | Değişen parça sayısı | %20,5 boş |
| `boyali_sayisi` | Boyalı parça sayısı | %20,5 boş |
| `kimden` | Sahibinden / Galeriden / Yetkili Bayiden / Rent a Car | Rent a Car 4 satır |
| `fiyat` | Fiyat (TL) | min 10 000, medyan 608 000, en büyük 595 000 000; ≤ 0 yok |

Diğer (tekrar sayımı `id` hariç):
- Tamamen boş satır: **158** (bunlar birbirinin kopyası sayılırsa 157 "yinelenen" gibi görünür).
- Boş olmayan satırlarda fazladan kopya (her grubun ilki hariç): **138**.
- Boş olmayan tekrar gruplarındaki toplam satır (ilkler dahil): **270**, 132 grupta.
- Önceki raporda yazan "295 yinelenen satır" = 157 boş + 138 dolu kopya; yanıltıcıydı.

### A'nın sınırları (README'ye taşınacak)
- **İlan fiyatıdır**, gerçekleşen satış fiyatı değildir.
- **Tek dönem** (Haziran 2025): enflasyon nedeniyle tahminler o tarihin TL seviyesindedir.
- **Satır bazında tarih ve ilan no yok** → zaman bazlı ve kimlik bazlı bölme yapılamaz
  (PROGRESS.md bölme kuralı dal 3: "muhtemelen aynı araç" grupları raporlanır).
- **Marka dağılımı örnekleme kotası izlenimi veriyor** (büyük markalarda ~2 500 civarında tavan);
  piyasa paylarını temsil ettiği varsayılamaz.
- **Kapsam binek otomobil**: SUV/arazi/pick-up çok az; uygulama bu araçlar için güvenilir değildir.
- Veri arabam.com ilanlarından kazınmıştır; lisans yükleyenin beyanıdır ve kendi içinde çelişkilidir
  (CC0 ↔ "Non-commercial use"). Ham veri bu repoda
  yeniden dağıtılmaz (`data/raw/` git dışı).

## B — `car_prices_tr.csv` (KULLANILMIYOR)
| Alan | Değer |
|---|---|
| Kaggle başlığı | Car Prices Turkey |
| Bağlantı | https://www.kaggle.com/datasets/omrfrk125/car-prices-turkey (sürüm 1, 2025-09-04) |
| Yazar | Ömer Faruk Gülşen (Kaggle: `omrfrk125`) |
| Lisans | CC BY-SA 4.0 |
| Belirtilen kaynak | "Used Car Prices in Türkiye 2025" — https://www.kaggle.com/datasets/bahridgr/used-car-prices-in-trkiye-2025-entr → **2026-11-15'te meta veri adresi 404** |
| Ülke / site | Türkiye (81 il). İlan sitesi **yazmıyor**; model adları ve parça şeması arabam.com ile aynı (çıkarım, doğrulanmadı) |
| Dönem | `ilanTarihi` 2024-12-30 – 2025-04-17; %97,7'si Nisan 2025 |
| Dosya | 3 558 303 bayt, 6 675 satır × 28 sütun |

Bilinen sorunlar: `kilometre(Km)` ve `yıl` sütunlarının içeriği yer değiştirmiş (6 674/6 675 satır);
1 satır bir sütun daha kaymış; fiyat ve km metin ("1.169.000 TL", "120.000 km"); motor hacmi/gücü
~857/869 satırda aralık metni ("1401 - 1600 cm3"); `renk` %37, `saticiTuru` %46 boş.
A ile marka+yıl+km+fiyat birebir aynı 123 satır var (olası ortak ilan).

## Atıf
Adım 7'de README'ye taşınacak:

> Veri: Mehmet Tanrıverdi, "Used Car Prices Dataset (Turkey - arabam.com)", Kaggle, 2025.
> https://www.kaggle.com/datasets/mehmettanriverdi/used-car-prices-dataset-turkey-arabam-com
> Kaggle lisans alanı: CC0 1.0; sayfa alt başlığı: "Non-commercial use". Kaynak site: arabam.com,
> Haziran 2025 ilanları. Bu proje ticari değildir.

(Lisans çelişkili olduğu için atıf her durumda yazılır ve README'de çelişki de belirtilir.)
