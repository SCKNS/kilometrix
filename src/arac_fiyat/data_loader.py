"""Ham CSV dosyalarını data/raw/ altından okuyan fonksiyonlar."""

import pandas as pd

from arac_fiyat.config import ARABAM_CSV, CAR_PRICES_TR_CSV


def load_arabam() -> pd.DataFrame:
    """arabam.com veri setini (car_price_prediction.csv) olduğu gibi okur."""
    return pd.read_csv(ARABAM_CSV, encoding="utf-8")


def load_car_prices_tr() -> pd.DataFrame:
    """Car Prices Turkey veri setini (car_prices_tr.csv) olduğu gibi okur.

    Not: bu dosyada 'kilometre(Km)' ve 'yıl' sütunlarının içerikleri yer değiştirmiş
    (bkz. docs/DATA.md). Burada düzeltilmez; düzeltme Adım 2'de temizlemede yapılır.
    """
    return pd.read_csv(CAR_PRICES_TR_CSV, encoding="utf-8")
