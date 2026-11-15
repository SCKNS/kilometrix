# İkinci El Araç Fiyat Tahmini (Türkiye)

Türkiye ikinci el araç fiyatlarını tahmin etmeyi hedefleyen bir makine öğrenmesi projesi.
Klasik ML modelleri kullanılır; SHAP ile her özelliğin fiyata etkisi gösterilir ve
Streamlit arayüzü üzerinden tahmin yapılabilir.

> Not: Kullanılacak veri setlerinin kaynağı, ülkesi ve lisansı henüz doğrulanmadı
> (Adım 1). Bkz. [docs/DATA.md](docs/DATA.md).

> Proje geliştirme aşamasındadır. İlerleme için [docs/PROGRESS.md](docs/PROGRESS.md).

## Özellikler (planlanan)
- Veri temizleme ve özellik hazırlama
- Baseline ve ağaç tabanlı modellerin karşılaştırılması
- SHAP ile model açıklaması
- Streamlit ile etkileşimli tahmin arayüzü

## Kurulum
Gerekli Python sürümü: **3.13** (paket sürümleri bu sürümle sabitlendi; başka sürümde
`requirements.txt` kurulamayabilir).

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt        # uygulama için yeterli
pip install -r requirements-dev.txt    # geliştirme: + jupyter
```

Kod `src/` altında olduğundan betikler proje kökünden şöyle çalıştırılır:
```bash
# Windows PowerShell
$env:PYTHONPATH = "src"
# macOS / Linux / Git Bash
export PYTHONPATH=src
```

## Klasör yapısı
```
data/        raw (git dışı), processed (git dışı), sample (örnek veri)
notebooks/   keşifsel analiz defterleri
src/arac_fiyat/  veri, özellik, eğitim, değerlendirme, açıklama, tahmin kodu
app/         Streamlit arayüzü
models/      eğitilmiş model dosyaları
reports/     grafikler
docs/        ilerleme ve veri belgeleri
```

## Veri
Proje sahibinin Kaggle'dan indirdiğini belirttiği iki veri seti kullanılacaktır. Kaynak, ülke ve lisans Adım 1'de
doğrulanacak; lisansı kullanıma uygun olmayan veya Türkiye dışı veri kullanılmayacak.
Ayrıntılar: [docs/DATA.md](docs/DATA.md).

## Sonuçlar
Henüz yok.
