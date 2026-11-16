"""Proje genelindeki ayarlar: dosya yolları, rastgelelik tohumu (random seed), sabitler."""

from pathlib import Path

# Proje kökü: bu dosya src/arac_fiyat/ altında, iki üst klasör yukarısı kök
PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
MODELS_DIR = PROJECT_ROOT / "models"

# Ham dosyalar (kaynakları docs/DATA.md'de)
ARABAM_CSV = RAW_DIR / "car_price_prediction.csv"  # Tanrıverdi, arabam.com, Haziran 2025
CAR_PRICES_TR_CSV = RAW_DIR / "car_prices_tr.csv"  # Gülşen, Aralık 2024 - Nisan 2025

RANDOM_STATE = 42
