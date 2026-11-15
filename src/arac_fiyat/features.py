"""Özellik hazırlama: türetilmiş sütunlar ve ön işleme (doldurma, kodlama, ölçekleme).

Durumsuz (veriden bir şey öğrenmeyen) türetmeler add_features içinde yapılır.
Veriden öğrenen her şey (doldurma medyanı, kategori listesi, ölçek) build_preprocessor
içindedir ve Pipeline'da yalnızca train'e fit edilir.
"""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

# Veri Haziran 2025'te toplandı (docs/DATA.md); araç yaşı bu yıla göre hesaplanır
DATA_YEAR = 2025
MISSING_LABEL = "bilinmiyor"

RAW_CAT_COLS = ["marka", "seri", "model", "vites_tipi", "yakit_tipi", "kasa_tipi", "renk", "kimden"]

# "model" alanı tek başına belirsiz ("1.6" pek çok seride var), bu yüzden marka ve
# seriyle birleştirilir. Üç düzey birlikte verilir: görülmemiş model gelirse
# marka ve marka_seri katsayıları yine çalışır.
CAT_FEATURES = ["marka", "marka_seri", "marka_seri_model",
                "vites_tipi", "yakit_tipi", "kasa_tipi", "renk", "kimden"]
# Boşluğu bilgi taşıyan sayısal sütunlar: medyanla doldurulur + "boştu" göstergesi eklenir
NUM_FEATURES = ["yas", "log_km", "motor_hacmi", "motor_gucu", "degisen_sayisi", "boyali_sayisi"]


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Ham sütunlardan model özelliklerini üretir (fiyat kullanılmaz)."""
    out = pd.DataFrame(index=df.index)
    cats = df[RAW_CAT_COLS].astype(object).fillna(MISSING_LABEL)
    out["marka"] = cats["marka"]
    out["marka_seri"] = cats["marka"] + " | " + cats["seri"]
    out["marka_seri_model"] = out["marka_seri"] + " | " + cats["model"]
    for col in ["vites_tipi", "yakit_tipi", "kasa_tipi", "renk", "kimden"]:
        out[col] = cats[col]

    out["yas"] = DATA_YEAR - df["yil"].astype(float)
    out["log_km"] = np.log1p(df["kilometre"].astype(float))
    for col in ["motor_hacmi", "motor_gucu", "degisen_sayisi", "boyali_sayisi"]:
        out[col] = df[col].astype(float)
    return out


def build_preprocessor() -> ColumnTransformer:
    """Kategorikleri one-hot, sayısalları doldur + ölçekle (yalnızca train'e fit edilir)."""
    numeric = make_pipeline(
        SimpleImputer(strategy="median", add_indicator=True),
        StandardScaler(),
    )
    # train'de görülmeyen kategori sıfır vektör olur (hata vermez)
    categorical = OneHotEncoder(handle_unknown="ignore")
    return ColumnTransformer([
        ("num", numeric, NUM_FEATURES),
        ("cat", categorical, CAT_FEATURES),
    ])


def feature_step() -> FunctionTransformer:
    """add_features'ı Pipeline'ın ilk adımı yapar; uygulama ham girdiyi verebilsin diye."""
    return FunctionTransformer(add_features)
