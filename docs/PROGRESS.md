# İlerleme

## Yol haritası
- [x] Adım 0: İskelet, git init — **TAMAMLANDI**
- [ ] Adım 1: İki veri setini incele (şema, satır sayısı, eksikler, dönem); **kaynak, ülke ve lisansı doğrula, DATA.md atıf bölümünü doldur**; birleştirme kararını kullanıcıya sor. Doğrulanamayan veya Türkiye dışı veri kullanılmaz.
- [ ] Adım 2: Temizleme
- [ ] Adım 3: Özellik hazırlama, basit baseline model, hata ölçümü (aşağıdaki "Değerlendirme kuralları"na göre; test açılmaz)
- [ ] KONTROL: **Doğrulama (CV) MAPE'si** yaklaşık %20'nin üstündeyse dur, durumu anlat, birlikte karar verelim. Test MAPE'si bu kararda kullanılmaz.
- [ ] Adım 4: Model karşılaştırma ve ayar (CV ile); en sonda seçilen nihai model test setinde **bir kez** değerlendirilir
- [ ] Adım 5: SHAP ve grafikler
- [ ] Adım 6: Streamlit arayüzü
- [ ] Adım 7: README (atıfı DATA.md'den taşı), Streamlit Cloud yayını (yayında Python 3.13 seçilir; o an Cloud'da yoksa sürümler yeniden sabitlenir)

## Değerlendirme kuralları (Adım 3'ten itibaren geçerli)
**Test setinin kullanımı**
- Geliştirme boyunca (Adım 3-4) tüm kararlar — özellik seçimi, model seçimi, hiperparametre, %20 KONTROL'ü —
  yalnızca train içinden **doğrulama/CV** sonuçlarıyla verilir.
- Test seti Adım 4'ün sonunda, seçilmiş ve donmuş nihai model ile iki baseline için **bir kez** açılır.
- Test sonucu görüldükten sonra model değiştirilirse bu açıkça yazılır ve o test sonucu artık
  "tarafsız final değerlendirme" olarak sunulmaz.

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
- Yinelenen ilanlar bölmeden **önce** temizlenir; kalan çok benzer ilanların (aynı marka-model-yıl-km-fiyat) sayısı raporlanır.
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
  3. Kimlik yoksa, aynı marka-model-yıl-km-renk gibi "muhtemelen aynı araç" gruplarının train/test'e
     bölünme sayısı raporlanır (yeniden yayımlanmış ilan riski).
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
  - İkisi de yok: `KFold(shuffle=True, random_state=...)`.
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

**Sıradaki adım:** Adım 1 — veri setlerini incele.
