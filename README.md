# İkinci El Araç Fiyat Tahmini (Türkiye)

Türkiye ikinci el araç fiyatlarını tahmin etmeyi hedefleyen bir makine öğrenmesi projesi.
Klasik ML modelleri kullanılır; SHAP ile her özelliğin fiyata etkisi gösterilir ve
Streamlit arayüzü üzerinden tahmin yapılabilir.

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

# Ham veri incelemesi (Adım 1)
python -m arac_fiyat.inspect_raw
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
arabam.com'daki Haziran 2025 ilanlarından oluşan Kaggle veri seti (~50 bin ilan). Lisans çelişkili: Kaggle lisans alanı CC0, sayfa alt başlığı "Non-commercial use";
bu proje ticari değildir (ayrıntı `docs/DATA.md`).
Tam atıf ve veri sınırları Adım 7'de buraya taşınacak; şimdilik: [docs/DATA.md](docs/DATA.md).

## Sonuçlar
Henüz yok.
