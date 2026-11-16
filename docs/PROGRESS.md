# İlerleme

## Yol haritası
- [x] Adım 0: İskelet, git init — **TAMAMLANDI**
- [x] Adım 1: İki veri setini incele (şema, satır sayısı, eksikler, dönem); **kaynak, ülke ve lisansı doğrula, DATA.md atıf bölümünü doldur**; birleştirme kararını kullanıcıya sor. Doğrulanamayan veya Türkiye dışı veri kullanılmaz. — **TAMAMLANDI**
- [x] Adım 2: Temizleme — **TAMAMLANDI**
- [x] Adım 3: Özellik hazırlama, basit baseline model, hata ölçümü (aşağıdaki "Değerlendirme kuralları"na göre; test açılmaz) — **TAMAMLANDI**
- [x] KONTROL (Adım 3 sonucu: Ridge CV MAPE %11,8 → eşiğin altında; kullanıcı onayladı): **Doğrulama (CV) MAPE'si** yaklaşık %20'nin üstündeyse dur, durumu anlat, birlikte karar verelim. Test MAPE'si bu kararda kullanılmaz.
- [x] Adım 4: Model karşılaştırma ve ayar (CV ile); en sonda seçilen nihai model test setinde **bir kez** değerlendirilir — **TAMAMLANDI**
- [x] Adım 5: SHAP ve grafikler — **TAMAMLANDI**
- [x] Adım 6: Streamlit arayüzü — **TAMAMLANDI**
- [x] Adım 7: README (atıfı DATA.md'den taşı), Streamlit Cloud yayını (yayında Python 3.13 seçilir; o an Cloud'da yoksa sürümler yeniden sabitlenir) — **TAMAMLANDI** (Cloud yayını kullanıcıda)

## Değerlendirme kuralları (Adım 3'ten itibaren geçerli)
**Test setinin kullanımı**
- Geliştirme boyunca (Adım 3-4) tüm kararlar — özellik seçimi, model seçimi, hiperparametre, %20 KONTROL'ü —
  yalnızca train içinden **doğrulama/CV** sonuçlarıyla verilir.
- Test seti Adım 4'ün sonunda, seçilmiş ve donmuş nihai model ile iki baseline için **bir kez** açılır.
- Test sonucu görüldükten sonra model değiştirilirse bu açıkça yazılır ve o test sonucu artık
  "tarafsız final değerlendirme" olarak sunulmaz.
- **Adım 5'ten sonra test seti "dokunulmamış" değildir:** SHAP açıklamaları test satırlarının özellikleriyle
  (fiyatsız) üretildi. Adım 4 test metrikleri o anda hesaplandığı için geçerli kalır; fakat bundan sonra
  "test yalnızca bir kez açıldı / hiç dokunulmadı" denmez. Adım 5 SHAP sonuçlarına dayanarak model veya
  özellik değiştirilirse, bu test seti o değişikliği tarafsız ölçemez (yeni değerlendirme gerekir).

**Metrikler** — TL cinsinden fiyat üzerinden (log hedef kullanılırsa geri dönüştürülerek):
- **MAPE** (ortalama mutlak yüzde hata): ana metrik, %20 eşiği buna uygulanır.
- **Medyan APE**: MAPE'yi şişiren düşük fiyatlı/uç ilanların etkisini görmek için.
- **MAE** ve **RMSE** (TL): mutlak hata büyüklüğü; RMSE ≫ MAE ise büyük hatalı uç ilanlar var demektir.
- Fiyat dilimlerine göre (ör. çeyrekler) MAPE: hatanın ucuz araçlarda mı toplandığını gösterir.
- Her metrik train ve doğrulama (CV) için ayrı raporlanır; test yalnızca final değerlendirmede eklenir.
  Hepsi iki baseline ile yan yana:
  - **Genel medyan**: train fiyatlarının medyanı, her araca aynı tahmin.
  - **Marka-model medyanı**: medyanlar **yalnızca train'den** (CV'de her fold'un train kısmından)
    hesaplanır. Değerlendirilen kümede train'de olmayan marka-model → marka medyanı, o da yoksa
    genel medyan. Kaç satırın geri düşüşe (fallback) gittiği raporlanır.

**Geçersiz fiyat temizliği**
- Amaç geçersiz kaydı atmak, metriği iyileştirmek değil. "MAPE'yi düşürsün" diye satır atılmaz.
- İki tür kural ayrı tutulur:
  1. **Geçerlilik kuralı** (anlamca kesin, veriye bakmadan bugünden yazılı): fiyat boş, sayıya
     çevrilemiyor ya da ≤ 0. Tek istisna: **veri kaynağının kendi belgesinde** "fiyat yok" anlamı
     taşıdığı yazılı bir değer (ör. kaynak "1 = fiyat sorunuz" diyorsa); belge Adım 1'de DATA.md'ye
     alıntılanır. Bu kurallar train, doğrulama ve teste aynı şekilde uygulanır.
  2. **Ampirik kural** — pozitif ama şüpheli fiyatlar (ör. 1, 111111, 999999 gibi "yer tutucu
     görünümlü" değerler) ve eşikler (train fiyat yüzdeliği, sabit TL alt/üst sınırı): geçersizlik
     kanıtı değildir; 111111 TL gerçek bir fiyat da olabilir. Yalnızca **model eğitim verisini**
     temizlemek için kullanılabilir. Değerlendirme kümesinden (doğrulama, test) bu kurallarla satır
     **atılmaz**.
- Ana metrikler, yalnızca geçerlilik kuralıyla süzülmüş tam değerlendirme kümesinde raporlanır.
  Ampirik kurallarla süzülmüş kümedeki metrikler gerekirse ayrıca, "duyarlılık analizi" başlığıyla verilir.
- Ampirik kuralların listesi ve eşikleri **yalnızca train'e bakılarak** (bölmeden sonra) belirlenir;
  doğrulama/test fiyatları bu karar için incelenmez. Adım 1-2'deki tüm-veri fiyat özetleri yalnızca
  tanıma amaçlıdır; değerlendirme kümesini değiştiren hiçbir karar bunlara dayanmaz.
- Kurallar model sonucu görülmeden yazılıp sabitlenir; eşik ve gerekçe raporda yer alır.
  Test hedeflerine ve metriklerine bakılarak seçilmez veya sonradan değiştirilmez.
- Train ve testten atılan satır sayısı ayrı ayrı raporlanır.

**Sızıntı önlemleri**
- Yinelenen ilanlar bölmeden **önce** temizlenir (A'da: id hariç tüm sütunlar, fiyat dahil, birebir aynı;
  fiyatın dahil olması kuralı daraltır, fiyat değerine/eşiğe göre seçim yapmaz. Bu satırlar `GROUP_KEY`
  altında zaten aynı gruptadır; silmek bölmeyi değil yalnızca ağırlığı etkiler); kalan çok benzer ilanların (aynı marka-model-yıl-km-fiyat) sayısı raporlanır.
- **Bölme türü (bu sırayla karar verilir):**
  1. Geçerli bir ilan tarihi sütunu varsa **varsayılan zaman bazlı holdout**: eski → train, en yeni dilim → test.
     Rastgele bölmeye ancak tarih güvenilmezse (çoğu boş, tek gün vb.) dönülür; gerekçe yazılır.
  2. İlan/araç kimliği (ilan no, şasi no vb.) varsa aynı kimlik hem train'de hem testte olamaz:
     **grup bazlı bölme** (`GroupShuffleSplit`). Zaman bazlı bölmeyle birlikteyse test ilanları
     **iki alt kümeye etiketlenir** (silinmez):
     - **Yeni kimlik**: kimliği train'de hiç görülmemiş ilanlar.
     - **Yeniden ilan**: kimliği train'de de bulunan ilanlar (aynı aracın daha sonraki ilanı).
     Bu doğrudan hedef sızıntısı değildir (eski ilan geçmiş bilgidir), ama model aynı aracın eski
     fiyatını görmüştür; bu yüzden iki alt küme ayrı ölçülür.
  3. Kimlik yoksa **"muhtemelen aynı araç" grubu kimlik yerine geçer ve grup bazlı bölme zorunludur**
     (yeniden yayımlanmış ilan riski). A için grup anahtarı: `marka+seri+model+yil+kilometre`
     (`cleaning.GROUP_KEY`; renk ve fiyat bilerek dışarıda, böylece hem "çok benzer ilan" hem
     "muhtemelen aynı araç" grupları bölünmez). Holdout `GroupShuffleSplit`, CV `GroupKFold`
     (`shuffle=True`, sabit `random_state`); aynı grup hem train'de hem doğrulama/testte olamaz.
     **Sınır:** Bu anahtar yaklaşıktır; gerçek yeniden ilan sızıntısını **garanti engellemez** (km'si
     güncellenmiş, seri/model alanı farklı yazılmış aynı araç başka gruba düşer). Bu yüzden dal 3'teki
     metrikler "daha önce görülmemiş araç" hatası olarak değil, **iyimser olabilecek bir tahmin** olarak
     sunulur ve her raporda bu sınır adıyla yazılır.
     Ana metrikler bu grup bazlı bölmeden raporlanır. Rastgele (grupsuz) bölme ana değerlendirme
     olarak kullanılmaz; istenirse yalnızca kıyas için, adıyla ayrıca verilir. Test ve her CV fold'u
     için grup ve satır sayıları raporlanır.
  4. Hiçbiri yoksa rastgele bölme + sabit `random_state`, gerekçesi yazılır.
- **Değerlendirme kapsamı (tarih + kimlik birlikteyse):** Uygulamanın kullanım senaryosu, kullanıcının
  modelin daha önce görmediği bir aracı girmesidir. Bu yüzden:
  - **Ana metrik = yeni kimlik alt kümesi.** Ölçülen soru: "gelecekteki, daha önce görülmemiş bir araç
    için tahmin hatası". %20 KONTROL'ü ve model seçimi buna göre yapılır. Raporlarda bu kapsam her
    seferinde adıyla yazılır; "tüm gelecek ilanlar" denmez.
  - **Ayrıca raporlanır:** yeniden ilan alt kümesinin metrikleri ve tüm değerlendirme kümesinin
    (iki alt küme birlikte) metrikleri; her alt kümenin satır sayısı ve oranı.
  - Yeniden ilan oranı yüksekse (ör. %20'den fazla) kullanıcıyla konuşulur; bu durumda "tümü"
    metriği de gerçek kullanım için anlamlı olabilir.
  - Kimlik yoksa (dal 3) bu ayrım yapılamaz; yalnızca "muhtemelen aynı araç" sayısı raporlanır.
- Tüm ön işleme (doldurma, kodlama, ölçekleme, hedef kodlama) sklearn `Pipeline` içinde, **yalnızca train'e fit** edilir.
- Hiperparametre ayarı yalnızca train üzerinde çapraz doğrulama ile; test seti sona kadar dokunulmaz.
  CV, holdout bölmesiyle aynı kuralı izler:
  - Yalnızca tarih: `TimeSeriesSplit` (ileri-zincir; doğrulama hep eğitimden sonraki dönem).
  - Yalnızca kimlik: `GroupKFold`.
  - **Tarih + kimlik birlikte:** ileri-zincir zaman fold'ları kullanılır; her fold'un doğrulama
    satırları, holdout'taki gibi "yeni kimlik" / "yeniden ilan" olarak etiketlenir. Model seçimi ve
    ayar **yeni kimlik** doğrulama satırlarıyla yapılır: fold'lar küçük bir fonksiyonla
    `(train_idx, val_idx_yeni_kimlik)` listesi olarak üretilip `cv=` parametresine verilir. Yeniden
    ilan satırları atılmaz; aynı fold modelleriyle ayrıca skorlanıp raporlanır. Her fold için iki alt
    kümenin satır sayısı raporlanır. `GroupKFold` burada kullanılmaz (kronolojiyi bozar); düz
    `TimeSeriesSplit` da tek başına kullanılmaz (iki alt kümeyi karıştırır).
  - Kimlik yerine "muhtemelen aynı araç" grubu (dal 3): `GroupKFold` (grup = `GROUP_KEY`).
  - Hiçbiri yok: `KFold(shuffle=True, random_state=...)`.
- Fiyattan türetilen veya ilan sonrası bilgi taşıyan sütunlar (ör. "fiyat/km", "satıldı mı") özellik olarak kullanılmaz.

## Denetçi promptu (her adım sonunda N yerine adım numarası)
```
Bu bir ikinci el araç fiyat tahmin projesi (klasik ML, LLM yok). Proje klasöründe `docs/REVIEW.md` dosyası Adım N'in raporudur, `docs/review_diff.patch` dosyası ise henüz commit edilmemiş kod farkıdır. İkisini de oku. Raporu ve kodu eleştirel denetle: (1) Rapordaki iddialar çıktılarla tutarlı mı? (2) Veri sızıntısı, aşırı öğrenme, yanlış metrik, mantıksız sonuç var mı? (3) Gereksiz karmaşıklık veya riskli kod var mı? Sorunları önem sırasıyla listele. Sorun yoksa gerekçesiyle söyle, zorla bulma. Kodu DEĞİŞTİRME.
```

---

## Günlük

### Adım 0 — İskelet, git init
**Durum:** TAMAMLANDI (kullanıcı onayıyla commit edildi, private GitHub reposuna gönderildi)
**Commit mesajı:** `Adım 0: proje iskeleti`

**Yapılanlar**
- Klasör yapısı kuruldu (data/raw, data/processed, data/sample, notebooks, src/arac_fiyat, app, models, reports/figures, docs).
- `src/arac_fiyat/` altında 8 modül + `__init__.py`, `app/streamlit_app.py`: yalnızca tek satırlık docstring, iş mantığı yok.
- `.gitignore`, `requirements.txt`, `README.md` (iskelet), yerel ajan kuralları dosyası (git dışı), `docs/DATA.md`, `docs/PROGRESS.md` yazıldı.
- İki CSV kökten `data/raw/` altına taşındı: `car_price_prediction.csv`, `car_prices_tr.csv` (içeriğe bakılmadı).
- Boş klasörlerin git'te görünmesi için `.gitkeep`: data/sample, notebooks, models, reports/figures.
- `git init -b main` yapıldı; değişiklikler `git add -A` ile hazırlandı, commit atılmadı.

**Ortam**
- Sistem Python: 3.13.14 (Microsoft Store kurulumu, `WindowsApps\python`). Başta sanal ortam yoktu.
- `.venv` oluşturuldu (Python 3.13.14), `requirements.txt` kuruldu; `pip check`: "No broken requirements found."
- Kurulu sürümler requirements.txt'e `==` ile sabitlendi: pandas 3.1.1, numpy 2.5.4, scikit-learn 1.9.1, xgboost 3.4.1, shap 0.54.1, matplotlib 3.11.2, streamlit 1.67.0, joblib 1.6.0, jupyter 1.1.1.

**Kararlar**
- Proje kökü mevcut klasör (`araba tahmin`); ayrı bir `arac-fiyat-tahmin/` alt klasörü açılmadı, çünkü CSV'ler burada ve iç içe klasör gereksiz. GitHub repo adı `arac-fiyat-tahmin` olabilir.
- Ajan kuralları dosyası ve ajan ayar klasörü `.gitignore` yerine yerel `.git/info/exclude` dosyasında yok sayılıyor. Neden: `.gitignore` herkese açıktır ve bu satırlar oradayken commit öncesi yasaklı kelime taraması hiç boş dönemez.
- Satır sonu: `core.autocrlf=true` (Windows varsayılanı); git CRLF/LF uyarıları veriyor, zararsız.
- `models/` git'e girer (Streamlit Cloud'un modeli okuyabilmesi için); 100 MB sınırı Adım 4'te kontrol edilecek.

**Denetim 1 düzeltmeleri** (4 bulgunun 4'ü kabul edildi)
1. Import testi: çalışma koşulu eksikti. Kökten PYTHONPATH olmadan `ModuleNotFoundError`, `PYTHONPATH=src` ile başarılı; REVIEW ve README'ye koşul yazıldı.
2. README'deki "Türkiye ilanları / açık veri" iddiaları yumuşatıldı; kaynak-ülke-lisans doğrulaması Adım 7'den Adım 1'e çekildi (DATA.md'de zorunlu kontrol listesi).
3. Yol haritasına "Değerlendirme kuralları" eklendi: MAPE tanımı, medyan APE, MAE/RMSE, fiyat dilimi kırılımı, sızıntı önlemleri.
4. `jupyter` `requirements-dev.txt`'ye taşındı; `requirements.txt` yalnızca uygulama paketleri (8).

**Denetim 2 düzeltmeleri** (5 bulgunun 5'i kabul edildi; yalnızca belge değişikliği)
1. Geçersiz fiyat temizliği: kural önceden yazılı iş kuralı ya da yalnızca train'den türetilmiş olmalı; test hedefine/metriğine bakılarak seçilmez. Train/test'ten atılan satırlar ayrı raporlanır.
2. Bölme protokolü bağlayıcı yapıldı: geçerli tarih varsa zaman bazlı holdout varsayılan; kimlik varsa grup bazlı bölme; CV bölme türüne uyar (`TimeSeriesSplit` / `GroupKFold` / `KFold`).
3. Baseline: genel medyan eklendi; marka-model medyanı yalnızca train'den, görülmeyen gruplar için marka → genel medyan geri düşüşü.
4. README ve DATA.md'de Kaggle kökeni "kullanıcının beyanı" olarak yazıldı.
5. README'ye Python 3.13 gereksinimi, Adım 7'ye Cloud'da Python sürümü seçimi notu eklendi.

**Denetim 3 düzeltmeleri** (4 bulgunun 4'ü kabul edildi; yalnızca PROGRESS.md değişti)
1. %20 KONTROL'ü test MAPE'sinden doğrulama/CV MAPE'sine çevrildi; test Adım 4 sonunda nihai modelde bir kez açılır.
2. Tarih + kimlik birlikteyken CV protokolü: ileri-zincir fold'lar + her fold'da eğitimde görülen kimliklerin doğrulamadan çıkarılması.
3. Ampirik fiyat eşikleri (yüzdelik, sabit TL sınırı) yalnızca eğitim verisine; değerlendirme kümesi yalnızca geçerlilik kuralıyla süzülür, eşikli metrikler duyarlılık analizi olur.
4. Tur farkı denetlenebilir yapıldı: düzeltmelerden önce `git write-tree` ile staged ağacın kimliği alınıp REVIEW.md'ye yazıldı.

**Denetim 4 düzeltmeleri** (3 bulgunun 3'ü kabul edildi; 2'si yalnızca PROGRESS.md'de, 1'i kullanıcıda)
1. Pozitif "yer tutucu görünümlü" fiyatlar (1, 111111 vb.) geçerlilik kuralından çıkarıldı. Geçerlilik
   yalnızca boş / sayı değil / ≤ 0 ve kaynak belgesiyle kanıtlanan değerler. Şüpheli pozitifler ampirik
   kural: yalnızca train'e bakılarak belirlenir, yalnızca eğitim verisini temizler, değerlendirmede kalır.
2. Tarih + kimlik birlikteyken testten/doğrulamadan satır silinmiyor; "yeni kimlik" ve "yeniden ilan"
   olarak etiketleniyor. Ana metrik kapsamı açıkça "daha önce görülmemiş araç" olarak tanımlandı;
   yeniden ilan ve tümü ayrıca raporlanır.
3. Git kimliği boş: değiştirilmedi, commit öncesi kullanıcıdan alınacak.

**Açık sorunlar**
- Denetim 4 düzeltmeleri denetçiye verilmeden kullanıcı onayıyla commit edildi; Adım 1 denetiminde
  değerlendirme kuralları da göz önünde tutulmalı.
- `car_price_prediction.csv` adı Gürcistan verisi olan Kaggle "Car Price Prediction Challenge" ile aynı; Türkiye verisi olmayabilir. Adım 1'de kontrol.
- Git kimliği yalnızca bu repoya (yerel) ayarlandı; global ayar boş.
- `origin`: private GitHub reposu `arac-fiyat-tahmin`.

### Adım 1 — Veri setlerinin incelenmesi ve kaynak doğrulama
**Durum:** TAMAMLANDI (denetim 1 düzeltmelerinden sonra kullanıcı onayıyla commit edildi)
**Commit mesajı:** `Adım 1: veri setleri incelendi`

**Yapılanlar**
- `config.py`: proje kökü, veri/rapor yolları, iki ham dosya yolu, `RANDOM_STATE = 42`.
- `data_loader.py`: `load_arabam()`, `load_car_prices_tr()` — ham CSV'yi olduğu gibi okur.
- `parse_tr_number()`, `parse_tr_date()`: yalnızca B'yi incelemek için, `inspect_raw.py` içinde
  (denetim sonrası `cleaning.py`'den taşındı; `cleaning.py` Adım 0 hâline döndü).
- `inspect_raw.py`: tek seferlik inceleme betiği; çıktısı `reports/adim1_veri_inceleme.txt`.
- Kaynaklar Kaggle'ın herkese açık Croissant meta verisinden (kimlik bilgisi olmadan) doğrulandı;
  `docs/DATA.md` dolduruldu (kaynak, yazar, lisans, dönem, sütunlar, sınırlar, atıf).
- README'deki "henüz doğrulanmadı" notu kaldırıldı, veri cümlesi güncellendi.

**Bulgular (özet; ayrıntı DATA.md)**
- A `car_price_prediction.csv` = Tanrıverdi, arabam.com, Haziran 2025. 50 755 × 16.
  Lisans çelişkili: lisans alanı CC0, alt başlık "Non-commercial use".
  158 tamamen boş satır; boş olmayanlarda 138 fazladan kopya (270 satır, 132 grup).
  Gürcistan verisi **değil** (Adım 0 açık sorunu kapandı). Satır tarihi ve ilan no yok (`id` = satır sırası).
- B `car_prices_tr.csv` = Gülşen, CC BY-SA 4.0, 6 675 × 28, 2024-12-30 – 2025-04-17 (%97,7 Nisan).
  Belirttiği üst kaynak Kaggle'da 404; ilan sitesi yazılı değil. `kilometre(Km)` ↔ `yıl` kaymış.

**Kararlar**
- **Yalnızca A kullanılır** (kullanıcı kararı bana bıraktı: "CV için, en mantıklı hangisiyse").
  Gerekçe DATA.md "Karar" bölümünde: B doğrulanamıyor, getirisi küçük (~%13), dönem ve biçim farkı gürültü.
- A'da tarih ve kimlik olmadığından bölme kuralı **dal 3** (Adım 2 denetiminde bağlayıcı yapıldı:
  `GROUP_KEY` ile grup bazlı bölme zorunlu).
- Geçerlilik kuralı için kaynak belgesinde özel "fiyat yok" değeri yok → yalnızca boş / sayı değil / ≤ 0.
- Uygulama kapsamı binek otomobil (SUV/pick-up çok az); README'ye Adım 7'de yazılacak.

**Açık sorunlar**
- A'da marka başına ~2 500 tavanı: örnekleme kotası izlenimi veriyor; piyasa paylarını temsil ettiği
  varsayılamaz (yorum, kanıt değil).
- A'nın lisansı çelişkili (CC0 ↔ "Non-commercial use"); proje ticari değil, ticari kullanımda yazara sorulmalı.
- A'da km en büyük 90 000 000, fiyat en büyük 595 000 000 TL: Adım 2-3'te ampirik kurala aday
  (eşikler yalnızca train'den, bölmeden sonra).
- `degisen_sayisi`/`boyali_sayisi` %20,5 boş; "boş = 0 mı, bilinmiyor mu" Adım 2'de karar.

**Denetim 1 düzeltmeleri** (2 zorunlu + 2 isteğe bağlı bulgunun 4'ü kabul edildi)
1. Lisans: "temiz" ifadesi kaldırıldı; CC0 ↔ "Non-commercial use" çelişkisi DATA.md ve REVIEW.md'de
   (meta verinin `alternateName` alanından doğrulandı).
2. Tekrar sayımı ayrıştırıldı: 158 boş / 138 dolu kopya / 270 satır (132 grup); betik ayrı basıyor.
3. Marka dağılımı ifadesi "örnekleme kotası izlenimi; piyasa payı varsayılamaz" oldu.
4. Ayrıştırıcılar `inspect_raw.py`'ye taşındı; sayı ayrıştırıcı artık eksi/ondalığı silmiyor (NaN veya korunur).

### Adım 2 — Temizleme (yalnızca A)
**Durum:** TAMAMLANDI (kullanıcı onayıyla commit edildi)
**Commit mesajı:** `Adım 2: veri temizlendi`

**Yapılanlar**
- `cleaning.py`: küçük fonksiyonlar + `main()`. Çalıştırma: `PYTHONPATH=src python -m arac_fiyat.cleaning`.
- Çıktılar: `data/processed/arabam_clean.csv` (git dışı), `reports/adim2_temizleme.txt` (git'e girer).
- Sıra: tamamen boş satır → fiyat geçerlilik kuralı → `-`/boş metin → NaN → birebir kopya (id hariç) → tam sayı tipleri.
- Her adım satır farkı **ve NaN hücre farkı** yazar; sonda `check_clean` son koşulları doğrular (`ValueError`; `python -O` ile kapanmaz).
- Sonuç: 50 755 → 50 459 satır (−158 boş, −0 geçersiz fiyat, −138 kopya).

**Kararlar**
- Yalnızca anlamca kesin işler yapıldı. km/fiyat aykırıları (km 90 000 000, fiyat 595 000 000) **dokunulmadı**:
  ampirik kural, Adım 3'te bölmeden sonra yalnızca train'den belirlenecek.
- `degisen_sayisi`/`boyali_sayisi` boşları **bilinmiyor** sayıldı, 0 yapılmadı. Gerekçe: veride gerçek 0 çok
  (değişen 26 546, boyalı 17 362); iki sütun hep birlikte boş (10 231); boşların %72'si "Sahibinden"; boş
  satırların fiyat medyanı daha düşük (425 bin ↔ 650 bin, ham veri, yalnızca tanıma amaçlı). Boşluk bilgi
  taşıyor → Adım 3'te eksiklik göstergesi + Pipeline içinde doldurma.
- Elektrikli araçlarda `motor_hacmi` çoğunlukla boş (207/222, ham veri): yapısal boşluk, Adım 3'te ele alınacak.
- `id` tutuldu (ham veriye geri izleme için); özellik olarak kullanılmayacak.

**Adım 3'e devredilenler**
- Çok benzer ilan (marka+seri+model+yıl+km+fiyat): 149 grup, 302 satır — atılmadı, raporlandı.
- Muhtemelen aynı araç (marka+seri+model+yıl+km+renk): 797 grup, 1 727 satır; 732 grubunda fiyat farklı.
- id ve fiyat dışında tamamen aynı, fiyatı farklı: 127 grup, 274 satır (yeniden ilan izi).
- **Grup bazlı bölme zorunlu**, anahtar `GROUP_KEY` = marka+seri+model+yıl+km: 48 235 grup;
  2+ satırlı 1 812 grup / 4 036 satır; en büyük grup 15 (Tofaş Şahin 1994, 100 000 km gibi yuvarlak km;
  farklı araçları da birleştirebilir, bu yalnızca bölmeyi daha temkinli yapar). Anahtar yaklaşıktır:
  km'si güncellenmiş / model alanı farklı yeniden ilanları yakalayamaz, sızıntıyı garanti engellemez.
- Seyrek kategoriler: Pick-up 16, Rent a Car 4, tek ilanlı markalar.

**Açık sorunlar**
- Birim testi (pytest) yok; yerine her çalıştırmada `check_clean` son koşulları denetliyor. Şema
  değişirse hata çalışma anında çıkar. Test altyapısı gerekirse Adım 3'te özellik kodlarıyla eklenebilir.

**Denetim 1 düzeltmeleri** (4 bulgunun 4'ü kabul edildi)
1. (Orta) Grup bazlı bölme "değerlendirilecek" değil, **zorunlu** yapıldı (yukarıdaki dal 3 ve CV kuralı).
   Denetçinin 127 grup / 274 satır ve 732/797 sayıları yeniden hesaplandı, aynı çıktı; artık betik basıyor.
2. (Düşük) "Sızıntı önlemi / birebir yinelenen" kesinliği kaldırıldı: docstring ve DATA.md'de "olası kopya,
   ilan no olmadan kanıtlanamaz".
3. (Düşük) Günlük her adımda NaN hücre farkını ve sonda Int64 tiplerini yazıyor; yer tutucu adımı
   NaN +88 gösteriyor (= 88 `kasa_tipi == "-"`).
4. (Düşük) `check_clean` son koşul kontrolü eklendi (id tekil, fiyat > 0, yer tutucu yok, Int64,
   id hariç kopya yok). pytest eklenmedi (yeni paket, bu adımda gerekmedi).

**Denetim 2 düzeltmeleri** (3 bulgunun 3'ü kabul edildi; tur öncesi staged ağaç `c28cef00add1a0d8d290cb6e2f8b13f1922a9c02`)
1. (Orta) 138 olası kopyanın fiyat dahil karşılaştırılıp bölmeden önce silinmesi: **silme korunur**, karar
   gerekçelendi. Fiyat anahtarda olunca kural daralır (fiyatı farklı yeniden ilanlar silinmez, hangi fiyatın
   tutulacağı seçilmez); fiyat değerine/eşiğe göre seçim yok. Bu satırlar `GROUP_KEY`'de zaten aynı gruptadır,
   silinmeseler de train/test'e bölünemezdi; silme yalnızca çift sayımı (eğitimde ağırlık, değerlendirmede
   aynı ilanın iki kez ölçülmesi) kaldırır. Profil: 91 Sahibinden / 46 Galeriden / 1 Yetkili Bayi; ≤ 100 km
   hiç yok → "aynı özellikli farklı sıfır araç" açıklaması zayıf. Betik bu profili artık basıyor.
2. (Orta) Grup anahtarının sızıntıyı **garanti engellemediği** PROGRESS.md dal 3, DATA.md, `cleaning.py`
   yorumu ve REVIEW.md'de açıkça yazıldı; dal 3 metrikleri "iyimser olabilecek tahmin" olarak sunulacak.
3. (Düşük) `check_clean` içindeki `assert`'ler `require()` → `ValueError` ile değiştirildi; `python -O`
   altında bozuk veri hata veriyor (doğrulandı). Temiz CSV değişmedi (SHA-256 aynı).

### Adım 3 — Özellikler, baseline'lar, CV ile hata ölçümü (test açılmadı)
**Durum:** TAMAMLANDI (kullanıcı onayıyla commit edildi)
**Commit mesajı:** `Adım 3: özellikler ve baseline modeller`

**Yapılanlar**
- `split.py` (yeni): `holdout_split` (GroupShuffleSplit, test ≈ %20 grup), `cv_folds` (GroupKFold 5 kat,
  `shuffle=True`, `RANDOM_STATE`), `count_shared_groups` (sızıntı kontrolü). Grup = `GROUP_KEY` (dal 3).
- `features.py`: `add_features` (durumsuz: yas = 2025 − yıl, log_km, marka / marka_seri /
  marka_seri_model birleşik kategorileri, boş kategori → "bilinmiyor") + `build_preprocessor`
  (sayısal: medyan doldurma + eksiklik göstergesi + ölçekleme; kategorik: one-hot, görülmeyen → sıfır).
  Hepsi Pipeline içinde, yalnızca fold-train'e fit.
- `evaluate.py`: MAPE, medyan APE, MAE, RMSE (TL), fiyat çeyreğine göre MAPE (çeyrek sınırı fold-train'den).
- `train.py`: iki baseline (genel medyan, marka+seri+model → marka+seri → marka → genel medyan) +
  `ridge_log` (log fiyat üzerinde Ridge, alpha=1 ayarsız). Çalıştırma: `PYTHONPATH=src python -m arac_fiyat.train`.
  Çıktı: `reports/adim3_baseline.txt`. Model dosyası kaydedilmedi (Adım 4'te).

**Bölme** (dal 3; metrikler "iyimser olabilecek tahmin", anahtar sızıntıyı garanti engellemez)
- Train 40 391 satır / 38 588 grup; test 10 068 satır / 9 647 grup; ortak grup 0. Test **açılmadı**;
  test id listesinin SHA-256'sı rapora yazıldı (Adım 4'te aynı bölme kontrolü).
- 5 fold: her biri ~32 300 train / ~8 070 doğrulama satırı, 7 717-7 718 doğrulama grubu, ortak grup 0.

**Ampirik eğitim süzgeci — ana sonuçta KULLANILMIYOR** (denetim 1 sonrası)
- Sınırlar (her fold'un train kısmından fiyat %0,1 / %99,9, km %99,9) yalnızca iki yerde: "doğrulama_süzülmüş"
  duyarlılık analizi ve süzgeçli **karşılaştırma** koşusu (eğitimden fold başına 92-98 satır çıkar).
- Gerekçe: süzgeç Ridge CV MAPE'yi yalnızca 0,035 puan düşürüyor (11,824 → 11,789), MAE/RMSE'yi kötüleştiriyor;
  süzülen satırların geçersiz olduğuna dair kanıt da yok.
- "Tekrar rakamlı" fiyatlar (train'de 999999 ×10, 99999 ×3 vb. 17 satır) gerçek fiyat olabilir; atılmadı.

**CV sonuçları** (süzgeçsiz eğitim; doğrulama = ana metrik, 5 fold ortalaması)
| model | train MAPE | doğrulama MAPE | medyan APE | MAE (TL) | RMSE (TL) |
|---|---|---|---|---|---|
| genel medyan | 73,5 | 73,5 | 48,5 | 573 970 | 4,42 M |
| marka-model medyanı | 13,6 | 17,7 | 11,6 | 214 660 | 4,08 M |
| ridge_log | 10,4 | 11,8 ± 0,3 | 7,9 | 166 127 | 4,04 M |
- Süzgeçli karşılaştırma (doğrulama): ridge 11,8 MAPE / 169 954 MAE / 4,08 M RMSE.
- KONTROL: doğrulama MAPE %11,8 < %20 → durma gerekmiyor (denetim sonrası kesinleşir).

**Kararlar**
- "Marka-model" = marka+seri+model (veride en özel araç tanımı); arada marka+seri düzeyi eklendi
  (baseline'ı güçlendirir, kıyası zorlaştırır). Doğrulamada fold başına ~%96 satır en özel düzeyden.
- Marka-model medyanının gücü büyük ölçüde model bilgisinden geliyor (model adı nesli kodluyor; train'de
  model içi yıl std'si 1,56, tüm train 8,53). Bu, yaklaşık grup anahtarı yüzünden yeniden ilan
  sızıntısının **katkısını dışlamaz**.

**Açık sorunlar**
- RMSE çok büyük (≈4 M TL): 595 M TL gibi uç fiyatlar; süzülmüş doğrulamada ≈0,42 M. Ana metrik MAPE.
- Ucuz çeyrekte (Q1) hata en yüksek (Ridge %18,3); toplam APE'ye en büyük katkı Q1'den (%38,5, satırların %24,9'u).
- Ridge alpha ayarlanmadı; Adım 4'te CV ile.

**Denetim 1 düzeltmeleri** (5 bulgunun 5'i kabul edildi; tur öncesi staged ağaç `97f3eb28515b223acbcdabd97c8bc3c22604b081`)
1. (Orta) Eğitim süzgeci ana sonuçtan çıkarıldı; süzgeçli koşu betikte karşılaştırma olarak duruyor.
2. (Düşük) "Marka-model medyanının gücü sızıntı değil" ifadesi yumuşatıldı: yıl std kontrolü model bilgisinin
   yararlı olduğunu gösterir, yeniden ilan sızıntısını dışlamaz.
3. (Düşük) Train-test ortak grup > 0 ise artık `ValueError` (önceden yalnızca raporlanıyordu).
4. (Düşük) "MAPE'nin çoğu ucuz çeyrekten" → "en büyük katkı ucuz çeyrekten" (%38,5; çoğunluk değil).
5. Çıktılar ve `review_diff.patch` yeniden üretildi.

### Adım 4 — Model karşılaştırma (CV), nihai model, tek test değerlendirmesi
**Durum:** TAMAMLANDI (kullanıcı onayıyla commit edildi)
**Commit mesajı:** `Adım 4: model seçimi ve test değerlendirmesi`

**Yapılanlar**
- `features.py`: `build_tree_preprocessor` (sayısallar olduğu gibi; az değerli kategoriler sıra numarası,
  `marka_seri` / `marka_seri_model` hedef kodlama `TargetEncoder`, kendi içinde 5 katlı çapraz uydurma) +
  `tree_categorical_indices`.
- `train.py`: `evaluate_fold` / `run_cv` isteğe bağlı `models` sözlüğü alıyor (varsayılan Adım 3 modelleri;
  Adım 3 raporu yeniden üretildi, fark 0 satır).
- `compare.py` (yeni): 17 aday (Ridge alpha ×5, HGB yaprak×ağaç ×6, XGBoost derinlik×ağaç ×6; ağaçlarda
  öğrenme oranı 0,05) + 2 baseline, Adım 3'teki aynı 5 grup fold'unda. Seçim kuralı sonuçlardan önce
  docstring'e yazıldı. Çıktı `reports/adim4_karsilastirma.txt`. Test açılmaz.
- Ek kontrol (kuralın dışında, testten önce): XGBoost'un en iyisi ızgara kenarındaydı; 3 büyük ayar daha
  denendi, en iyisi 10,75 (HGB 10,56'yı geçmedi). `reports/adim4_xgb_ek_kontrol.txt`.
- `final.py` (yeni): seçilen model sabit (`FINAL_NAME`), bölme SHA-256 ile Adım 3'e karşı doğrulanır, tüm
  train'e eğitilir, test **bir kez** açılır; test raporu zaten varsa betik çalışmaz.
  Çıktılar `reports/adim4_test.txt`, `models/arac_fiyat_model.joblib` (2,40 MB), `models/model_info.json`.

**Seçim** (CV doğrulama MAPE, 5 fold ortalaması): HGB `hgb_l31_n1500` 10,56 ± 0,2 · XGBoost `xgb_d8_n1500`
10,91 · Ridge `ridge_a1.0` 11,82 · marka-model medyanı 17,7 · genel medyan 73,5. HGB 5 fold'un hepsinde en iyi.

**Test (bir kez; dal 3, iyimser olabilecek tahmin)**
| model | train MAPE | test MAPE | medyan APE | MAE (TL) | RMSE (TL) |
|---|---|---|---|---|---|
| genel medyan | 73,7 | 73,9 | 48,8 | 529 198 | 1,78 M |
| marka-model medyanı | 13,8 | 16,8 | 11,6 | 156 755 | 0,79 M |
| hgb_l31_n1500 | 7,7 | 10,4 | 6,7 | 98 096 | 0,81 M |
- Test fiyat çeyrekleri (HGB): Q1 17,1 · Q2 9,5 · Q3 7,3 · Q4 7,4. Train'de görülmemiş marka+seri+model:
  294 satır, MAPE 22,4 (görülmüş 9 774 satır: 10,0).
- Duyarlılık (ampirik sınır dışı 33 test satırı hariç): HGB 10,2 MAPE, RMSE 0,33 M.

**Açık sorunlar / Adım 5-6'ya devredilenler**
- HGB'de kategorik bölmeler var; SHAP TreeExplainer desteklemeyebilir → Adım 5'te kontrol, gerekirse ham
  özellikler üzerinde modelden bağımsız açıklayıcı.
- Model dosyası `arac_fiyat.features.add_features`'a başvuruyor ve sklearn 1.9.1'e bağlı: uygulamada paket
  yolu ve sürüm aynı olmalı.
- Görülmemiş araç modelinde ve ucuz araçlarda hata yüksek; arayüzde kullanıcıya belirtilmeli.

**Denetim 1 düzeltmeleri** (4 bulgunun 4'ü kabul edildi; tur öncesi staged ağaç `1c3424048279b57ac31d1312062e68a9fdb21b2c`)
1. (Orta) HGB train MAPE'si temiz değil (TargetEncoder train'i tam-train kodlarıyla tahmin eder). Tanı
   (`reports/adim4_te_train_kontrol.txt`, yalnızca train): çapraz kodla 7,45, olağan 7,70 → train-test farkı
   iyimser değil, ≈3,0 puan; aşırı uyum yorumu korunuyor. `compare.py` uyarı satırı ekliyor (yeniden çalıştırıldı,
   tek fark bu satır), `features.py` docstring notu.
2. (Orta) Yeniden ilan sızıntısı ölçülemiyor: zaten yazılı sınır; "CV-test tutarlılığı bunu dışlamaz" eklendi.
3. (Düşük) Tek test açılışı kanıtlanamıyor: iddia yumuşatıldı; `final.py` rapor dosyasını test açılmadan önce
   yazıyor (çökmeye dayanıklı koruma). Koşudan sonra değişti, final yeniden çalıştırılmadı.
4. (Düşük) Ridge farkı 1,1-1,4 puan; yeniden yükleme kontrolü "ilk 200 test satırı" olarak düzeltildi.

### Adım 5 — SHAP ve grafikler
**Durum:** TAMAMLANDI (denetim 1 ve 2 düzeltmelerinden sonra kullanıcı onayıyla commit edildi)
**Commit mesajı:** `Adım 5: SHAP açıklamaları ve grafikler`

**Yapılanlar**
- `explain.py` (Adım 0'da tek satırlık docstring'di): kayıtlı modeli açıklar. Çalıştırma:
  `PYTHONPATH=src python -m arac_fiyat.explain` (~12 dk). Model **değişmedi**, yeniden eğitilmedi.
- Çıktılar: `reports/adim5_shap.txt`, `reports/figures/shap_{onem,beeswarm,bagimlilik,kategoriler,ornek_ilan}.png`,
  `models/shap_background.joblib` (23 KB; arka plan + model sha256 + özellik sırası + sürümler).
- Yeni paket yok (`shap`, `matplotlib` zaten requirements.txt'te).

**TreeExplainer kullanılamadı (Adım 4'ten devredilen risk doğrulandı)**
- HGB'nin 45 000 bölmesinin 10 916'sı kategorik (bit kümesi). SHAP bu modeli **hata vermeden** yükledi ama iç
  tahmini modelden 2,66 log birimine kadar sapıyor. Toplamlılık tutmadığı için sonuçlar yanlış olurdu.
- Modeli kategoriksiz yeniden eğitmek, açılmış test sonucunu geçersiz kılardı. Bunun yerine modelden bağımsız
  **PermutationExplainer** kullanıldı.

**Ne açıklanıyor (yorum sınırı)**
- Açıklanan: ön işlemeden sonraki 14 sütun → HGB'nin log(fiyat) tahmini. Sütunlar ham alan değil, temsil:
  yaş = 2025 − yıl (Adım 6'da "2020" yazım hatası düzeltildi; kod hep 2025 kullandı), km = log(1+km), sıra kodları, seri/model = hedef kodu ("model" = marka|seri|model kodu).
- **Dönüştürülmüş girdiler üzerinde, `shap.maskers.Independent` ile interventional SHAP**; arka plan train'den
  200 satır, satır başına 10 permütasyon. Ham özellik etkisi, koşullu katkı veya nedensellik değildir.
  Bu not rapor dosyasının ilk satırında ve her grafik başlığında yazıyor.
- Özetler **geometrik ortalama çarpan**: kategori `geo_carpan` = exp(ort SHAP), önem `geo_abs_carpan` =
  exp(ort|SHAP|). Yüzdelerin aritmetik ortalaması kullanılmıyor.
- Açıklanan satırlar: testten 1000 satırın **yalnızca özellikleri**. Bu yüzden test artık tamamen
  "dokunulmamış" sayılmaz (değerlendirme kurallarına madde; rapor dosyasının ikinci satırı).

**Kontroller**
- Toplamlılık ≤ 9,2e-05 log; exp(HGB log tahmini) = kayıtlı modelin TL tahmini.
- Kararlılık (100 satır, ikinci tohum): genel göreli fark 0,047; özellik bazında 0,026 (yaş) – 0,44 (kimden);
  önem sırasında bir komşu yer değişimi (Spearman 0,996); tek hücre farkı %95'lik 0,010, en fazla 0,08 log.
- Grup maskeleme (marka+seri+model ve yaş+km birlikte, 200 satır): paylar sonradan toplamayla aynı
  (%37,3 → %37,4; %36,7 → %36,8), satır korelasyonu 0,998.
- Yön: değer–SHAP Spearman: yaş −0,99, km −0,99, motor gücü +0,96, motor hacmi +0,91, değişen −0,83, boyalı −0,87.

**Sonuçlar** (ortalama |SHAP|, log birimi): yaş 0,221 · model 0,169 · km 0,108 · marka 0,078 · seri 0,068 ·
vites 0,048 · motor gücü 0,044 · … · kimden 0,001 (geometrik ort. mutlak çarpan: yaş 1,25 · model 1,18 ·
km 1,11). Araç tanımı (marka+seri+model) payı %37,9, yaş+km %39,5.
Vites geometrik ortalama çarpanı: otomatik 1,056, düz 0,957; kimden ≈ 1,000.

**Denetim 1 düzeltmeleri** (7 bulgunun 7'si kabul edildi; ayrıntı `docs/REVIEW.md`)
1. (Orta) Bağımsız maskeleme → `group_shap` kontrolü eklendi, paylar değişmedi; sonuçlar interventional diye sınırlandı.
2. (Orta) "Ham özellik" iddiası fazla güçlüydü → kaldırıldı, temsil/hedef kodu açıkça yazıldı.
3. (Orta) Test artık dokunulmamış değil → değerlendirme kurallarına madde.
4. (Düşük) exp(ort. SHAP)−1 aritmetik ortalama değil → `etki_%` = ort(exp(SHAP)−1), önemde ort(|exp(SHAP)−1|).
5. (Düşük) Kararlılık sınırlı → 100 satır, özellik bazında oynaklık, sıra ve hücre dağılımı raporlanıyor.
6. (Düşük) Arka plan dosyası kendini tanımlamıyor → sha256, özellik sırası, sürümler; ad model_info.json'dan.
7. (Düşük) Tanı kodu sürüme kırılgan → try/except, hata olursa rapora "YAPILAMADI".

**Denetim 2 düzeltmeleri** (3 bulgunun 3'ü kabul edildi; denetçi kritik sızıntı bulmadı, yorum fazla kesindi)
1. Interventional SHAP / Independent maskeleyici / dönüştürülmüş girdiler → rapor ilk satırı, grafik başlıkları,
   REVIEW başı; iddialar bu tanıma bağlandı.
2. "Ortalama yüzde etki" → geometrik ortalama çarpan (`geo_carpan`, `geo_abs_carpan`); grafikler çarpan ekseninde.
3. Test tamamen dokunulmamış değil → rapor dosyasının ikinci satırı (kural denetim 1'de eklenmişti).
SHAP değerleri değişmedi (eski raporla `diff`: yalnızca başlık, özet sütunları ve süreler farklı).

**Açık sorunlar / Adım 6'ya devredilenler**
- Uygulama arka plan dosyasını yüklerken `model_sha256` ve `features` sırasını doğrulamalı.
- Tek ilan açıklaması ~0,7 sn; tek hücre ±0,08 log oynayabilir → katkılar "yaklaşık" diye gösterilmeli.
- SHAP model davranışını açıklar, nedensellik değil. Marka/seri/model ve yaş/km katkıyı aralarında keyfi
  bölüşebilir. Arayüzde "etkiler çarpılarak birleşir" ve bu sınır yazılmalı.
- Arka plan train satırlarından; bu satırların hedef kodları kendi fiyatlarını içerir (Adım 4 denetim 1).

### Adım 6 — Streamlit arayüzü
**Durum:** TAMAMLANDI (denetim 1 düzeltmelerinden sonra kullanıcı onayıyla commit edildi ve push'landı)
**Commit mesajı:** `Adım 6: Streamlit tahmin ve SHAP arayüzü`

**Yapılanlar**
- `predict.py` (Adım 0'dan beri tek satırlık docstring'di):
  - `main()`: form seçeneklerini **yalnızca train'den** üretir (bölme `check_same_split` ile Adım 3-4'e karşı
    doğrulanır) → `models/form_options.json` (398 KB, git'e girer; uygulama veri dosyasını okumaz).
    İçerik: marka → seri → model ağacı (model başına ilan sayısı, yıl aralığı, medyan yıl ve km), kategori
    listeleri (en sık önce), sayısal alanların %0,1/%99,9 sınırları, train fiyat Q1 sınırı (365 000 TL),
    varsayılan araç (train'de en sık marka+seri+model: Tofaş Şahin 1.6). Çalıştırma:
    `PYTHONPATH=src python -m arac_fiyat.predict`.
  - `load_artifacts()`: model + model_info + SHAP arka planı + form seçenekleri; sklearn sürümü, arka planın
    `model_sha256`'sı, özellik sırası ve model adı doğrulanır, uymazsa `ValueError` (Adım 5'ten devredilen madde).
  - `make_input_frame`, `predict_price`, `error_range`, `explain_car` (Adım 5'le aynı PermutationExplainer, aynı
    arka plan ve tohum; toplamlılık > 1e-3 log ise hata), `input_warnings`, `tr_number` (Türkçe sayı yazımı).
- `app/streamlit_app.py`: bağımlı seçim kutuları (marka → seri → model), yıl/km varsayılanı seçilen modelin
  train medyanı; motor hacmi/gücü ve değişen/boyalı boş bırakılabilir (= "bilinmiyor", 0 değil). Çıktı:
  tahmini fiyat, medyan APE'den türetilen tipik hata aralığı, uyarılar, SHAP çarpan grafiği + tablo,
  "nasıl okunmalı" sınırlar bölümü, kenar çubuğunda veri/model/hata bilgisi. Model yeniden eğitilmedi.
- `explain.py` docstring ve Adım 5 günlüğünde "yaş = 2020 − yıl" yazım hatası "2025" yapıldı (kod hep 2025).
- Yeni paket yok.

**Kontroller** (AppTest = Streamlit'in tarayıcısız test aracı; betikler repo dışında, komutlar REVIEW.md'de)
- Varsayılan açılış hatasız (3,8 sn ilk yükleme); tahmin 151 229 TL; taban 653 383 TL × çarpanlar = tahmin
  (taban = arka plan tahminlerinin geometrik ortalaması; aritmetik ortalama 1 004 546 TL, denetim 1).
- 6 train satırı (4 dolu, 2 motor hacmi boş) formdan girildi: uygulamanın tahmini 6/6 `model.predict` ile aynı.
- Uyarılar: yıl 1970 / km 1 500 000 (train %0,1-%99,9 dışı), model yıl aralığı dışı (Şahin 2015), ucuz dilim
  (< Q1) çıktı. Marka değişince seri/model ilk seçeneğe düşüyor, hata yok.
- Aynı girdi iki kez açıklanınca birebir aynı; tek açıklama 0,64 sn (uygulamada ~1,1 sn yeniden çalıştırma).
- Arka plan sha256'sı bozulunca `load_artifacts` duruyor. `streamlit run`: sağlık "ok", ana sayfa HTTP 200.

**Kararlar**
- Form yalnızca train'de görülen marka+seri+model birleşimlerini sunar → "görülmemiş model" (testte MAPE %22,4)
  arayüzden girilemez; ama 2 426 / 4 113 modelin train'de 5'ten az ilanı var → "az ilan" uyarısı.
- Hata aralığı = tahmin/(1+m) … tahmin/(1−m), m = test medyan APE (%6,671); APE tanımıyla tutarlı. Araca özel
  güven aralığı değil; arayüzde böyle yazıyor. m için test satırlarına yeniden bakılmadı (yalnızca model_info.json).
- Test parçası `predict.main()`'de yalnızca `check_same_split`'e gider (id SHA-256 + train/test grup kesişimi);
  test özellikleri ve fiyatları seçenek üretiminde kullanılmaz.
- Ucuz dilim uyarısı **tahmine** göre (gerçek fiyat bilinmiyor); testteki %17,1 gerçek fiyata göre Q1'di.
- Tahmin ve açıklama her girdi değişiminde canlı (buton yok); açıklama girdi demetine göre önbellekte.

**Açık sorunlar**
- Fiyatlar Haziran 2025 TL düzeyinde; enflasyon düzeltmesi yok (arayüzde yazıyor).
- Kategori listeleri Python sırasıyla sıralı (Ş, Ö gibi harfler Z'den sonra gelir).
- `models/form_options.json` sıkışık tek satır JSON: diff'te okunmaz, `predict.py` ile yeniden üretilir.
- Birim testi yok; doğrulama AppTest betikleriyle yapıldı (repo dışı). Streamlit Cloud yayını Adım 7.
- Model değişirse `predict.MODEL_SHA256` ve `TEST_Q1_MAPE` elle güncellenmeli (uygulama o zamana kadar açılmaz).

**Denetim 1 düzeltmeleri** (4 bulgunun 4'ü kabul edildi; denetçi kritik ML kusuru bulmadı; tur öncesi staged ağaç
`78acbcc75bc8bacc37fae72f6d09366abc3da51f`)
1. (Orta) SHAP tabanı "ortalama tahmin" diye anlatılıyordu; aslında exp(ort. log tahmin) = geometrik ortalama
   (653 383 TL; aritmetik 1 004 546 TL, medyan tahmin 664 807 TL — yeniden hesaplandı). Arayüz metni ve
   `explain_car` docstring'i düzeltildi; sayılar ve çarpanlar değişmedi.
2. (Düşük/Orta) `form_options.json` artık `model_sha256` ve `test_split_sha256` taşıyor; `load_artifacts` ikisini
   denetliyor. `TEST_Q1_MAPE` sabiti `MODEL_SHA256` sabitine bağlandı: model dosyası değişirse uygulama durur.
   JSON yeniden üretildi; parmak izi dışındaki içerik `build_form_options(train)` ile birebir aynı.
3. (Düşük) "Test satırlarına hiç bakılmadı" → "test yalnızca bölme kontrolünde; özellik/fiyatları seçeneklere girmedi"
   (REVIEW, JSON `kaynak` alanı).
4. (Düşük) Ucuz dilim uyarısı tahmine, %17,1 gerçek fiyata göre: zaten şüphelerde yazılıydı; uyarı metnine
   "yaklaşık bir göstergedir" eklendi. Eşdeğer bir oran için testi yeniden açmak gerekirdi, yapılmadı.

### Adım 7 — README ve Streamlit Cloud hazırlığı
**Durum:** TAMAMLANDI (denetim 1–3 düzeltmelerinden sonra kullanıcı onayıyla commit edildi ve push'landı)
**Önerilen commit mesajı:** `Adım 7: README ve yayın hazırlığı`

**Yapılanlar**
- `README.md` baştan yazıldı: sonuç tablosu (test, iki baseline ile), CV ile seçim, ucuz/görülmemiş araç
  hataları, "iyimser olabilir" sınırı, SHAP önem grafiği ve okuma sınırları, veri atıfı + lisans çelişkisi,
  veri sınırları, yöntem özeti, uygulamayı çalıştırma, Cloud ayarı, sonuçları yeniden üretme komutları.
  Sayılar `reports/adim4_test.txt`, `reports/adim5_shap.txt` ve bu günlükten; yeni hesap yok.
- Atıf `docs/DATA.md`'den README'ye **taşındı**; DATA.md'de yalnızca yönlendirme kaldı.
- **xgboost uygulama bağımlılığından çıkarıldı:** `requirements.txt` → `requirements-dev.txt`. Neden: nihai
  model HGB; xgboost yalnızca `compare.py`'de aday olarak kullanılıyor, ama uygulama onu dolaylı içe aktarıyordu
  (`predict → final → compare → xgboost`). Linux'ta xgboost 3.4.1 `nvidia-nccl-cu13` paketini de çekiyor
  (`platform_system == "Linux"`): Cloud kurulumu gereksiz büyürdü. `compare.py`'de import, xgb dalının içine
  alındı (davranış aynı). Yeni paket yok.

**Kontroller**
- Linux + Python 3.13 için `requirements.txt` tekerlek uyumluluk kontrolü (`pip install --dry-run --platform
  manylinux… --only-binary=:all:`, xgboost'suz, Windows'ta koşturuldu): 7 sabit paketin her biri için Python
  3.13/Linux ile uyumlu ikili (pandas, numpy, scikit-learn, matplotlib cp313; shap abi3) ya da platformdan
  bağımsız (streamlit, joblib py3-none-any) tekerlek bulundu; 49 paket. pip ortam işaretlerini Windows'a göre
  değerlendirdiği için grafik ayrıca Linux işaretleriyle yeniden yürüdü (repo dışı betik): Linux'ta gereken
  48 paketin hepsi çözümde, sürüm kısıtları uyuyor; fazladan olan yalnızca `colorama`. Linux'ta gerçek
  kurulum yapılmadı.
- Yalnızca git'e girecek dosyalar (`git checkout-index` ile staged ağaç) repo dışına kopyalandı; **sıfırdan**
  Python 3.13.14 sanal ortamına yalnızca `requirements.txt` kuruldu (xgboost yok, `pip check` temiz).
  AppTest: hatasız açılış, tahmin 151.229 TL ve taban 653.383 TL (Adım 6 ile aynı), paket temiz kopyadan
  yüklendi, xgboost hiç içe aktarılmadı, marka değişimi hatasız. `streamlit run`: sağlık "ok", HTTP 200.
- Geliştirme ortamında `compare.build_model("xgb", …)` hâlâ `XGBRegressor` kuruyor.

**Açık sorunlar**
- **Cloud yayını yapılmadı:** Streamlit hesabıyla giriş gerektiriyor, kullanıcı yapacak (adımlar REVIEW.md'de).
  Linux tarafı yalnızca tekerlek uyumluluğu + meta veri denetimiyle sınandı (gerçek Linux çözümlemesi ve kurulumu yok); gerçek kurulum Windows'ta. Cloud'da Python 3.13
  seçeneği olup olmadığı görülmedi.
- Yayın adresi README'ye henüz yazılmadı; yayından sonra eklenecek.
- Repo private: Cloud'un private repoya erişimi ve uygulamanın kimlere açık olacağı yayın ekranında seçilir.
- Gerçek tarayıcıda (mobil dahil) görsel düzen hâlâ görülmedi.

**Denetim 1 düzeltmeleri** (2 bulgunun 2'si kabul edildi; denetçi kritik ML kusuru bulmadı; tur öncesi staged ağaç
`7173727962da9b6ce8ba299dfd1d826f4ff2a8f1`)
1. (Orta) Linux çözümlemesi kanıtladığından güçlü anlatılıyordu: pip işaretleri Windows'a göre değerlendirdi,
   xgboost çıkınca yeniden koşturulmadı, "hepsinin cp313 tekerleği var" yanlıştı (shap abi3; streamlit, joblib
   py3-none-any). Çözümleme xgboost'suz yeniden koşturuldu (49 paket, çıkış 0) ve grafik Linux işaretleriyle
   ayrıca yürüdü: Linux'ta gereken 48 paketin hepsi çözümde, sürümler uyuyor, fazlası yalnızca `colorama`.
   PROGRESS, REVIEW iddia 2 ve şüphe 3 buna göre yazıldı. Linux'ta gerçek kurulum hâlâ yok.
2. (Düşük) README "≈3 puanlık aşırı uyum farkı" → "yaklaşık 3 puanlık eğitim–test (genelleme) farkı"; eğitim
   MAPE'sinin tam-train kodlarıyla %7,70, çapraz kodlarla %7,45 olduğu (`reports/adim4_te_train_kontrol.txt`)
   eklendi. Sayılar değişmedi. (İlk yazımdaki "eğitim değeri iyimser" ifadesi Denetim 3'te düzeltildi.)

**Denetim 2:** kod uygun, commit'e engel yok. Kalan tek madde ("Linux bağımlılık çözümlemesi" ifadesi) REVIEW
ve bu günlükte "tekerlek uyumluluk kontrolü + meta veri denetimi" olarak düzeltildi; diğer maddeler Denetim 1'de
yapılmıştı. Tur öncesi staged ağaç `95a609600abbfdfe5c6f3f9cbee70259b93728bb`.

**Denetim 3** (1 düşük bulgu, kabul edildi): README'de eğitim MAPE'si %7,70 için "biraz iyimser" deniyordu;
tanı çıktısıyla ters (çapraz kodlarla %7,45 daha düşük, yani %7,70 iyimser değil). README maddesi "tam-train
kodlarıyla %7,70; çapraz kodlarla %7,45; test %10,4 → yaklaşık 3 puanlık eğitim–test (genelleme) farkı" olarak
yeniden yazıldı; PROGRESS ve REVIEW'daki aynı ifade düzeltildi. Yeniden ilan sızıntısı yüzünden test
sonuçlarının iyimser olabileceği uyarısı ayrı konu, değişmedi. Kod, model, veri, metrik, requirements değişmedi.
