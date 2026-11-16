"""Adım 6: uygulamanın kullandığı tahmin ve tek ilan açıklaması fonksiyonları.

İki iş yapar:
1. main(): form seçeneklerini (marka -> seri -> model, kategori listeleri, sayısal aralıklar,
   fiyat çeyrek sınırı) YALNIZCA train'den çıkarıp models/form_options.json'a yazar.
   Uygulama veri dosyasını okumaz (data/ git'e girmez), bu JSON'u okur.
   Çalıştırma (proje kökünden): PYTHONPATH=src python -m arac_fiyat.predict
2. load_artifacts / make_input_frame / predict_price / explain_car / input_warnings:
   app/streamlit_app.py bunları çağırır. Model değişmez, yeniden eğitilmez.
"""

import hashlib
import json

import joblib
import numpy as np
import pandas as pd
import sklearn

from arac_fiyat.cleaning import TARGET
from arac_fiyat.config import MODELS_DIR
from arac_fiyat.evaluate import price_bin_edges
from arac_fiyat.explain import (BACKGROUND_PATH, FEATURES, LABELS, display_values, explain,
                                make_explainer, split_model)
from arac_fiyat.features import DATA_YEAR, MISSING_LABEL, add_features
from arac_fiyat.final import EXPECTED_TEST_SHA, INFO_JSON, MODEL_PATH, check_same_split
from arac_fiyat.split import holdout_split
from arac_fiyat.train import CLEAN_CSV

OPTIONS_JSON = MODELS_DIR / "form_options.json"

# Formdan gelen ham alanlar (temiz CSV'deki sütunlar; id ve fiyat hariç)
INPUT_COLS = ["marka", "seri", "model", "yil", "kilometre", "vites_tipi", "yakit_tipi",
              "kasa_tipi", "renk", "motor_hacmi", "motor_gucu", "degisen_sayisi",
              "boyali_sayisi", "kimden"]
SIMPLE_CATS = ["vites_tipi", "yakit_tipi", "kasa_tipi", "renk", "kimden"]
NUM_INPUTS = ["yil", "kilometre", "motor_hacmi", "motor_gucu", "degisen_sayisi", "boyali_sayisi"]
NUM_LABELS = {"yil": "yıl", "kilometre": "kilometre", "motor_hacmi": "motor hacmi (cc)",
              "motor_gucu": "motor gücü (hp)", "degisen_sayisi": "değişen parça",
              "boyali_sayisi": "boyalı parça"}

# "Nadir değer" uyarısı: train'in %0,1 - %99,9 aralığı dışı (Adım 3 ampirik sınırlarıyla aynı yüzdelikler)
RARE_LOW_Q, RARE_HIGH_Q = 0.001, 0.999
FEW_MODEL_ROWS = 5  # bu sayıdan az train ilanı olan marka+seri+model için uyarı
# Aşağıdaki sabit yalnızca bu model dosyası (sha256) için geçerlidir; model değişirse
# load_artifacts durur, sabit reports/adim4_test.txt'in yenisinden elle güncellenmelidir.
MODEL_SHA256 = "bf9e4f499da9d9d190b5a185d623307e3327eaec9d6879c13943d2b2dedb0a79"
# reports/adim4_test.txt: HGB'nin testte gerçek fiyatı ucuz çeyrekte (Q1) olan ilanlardaki MAPE'si
TEST_Q1_MAPE = 17.1


def tr_number(value: float, decimals: int = 0) -> str:
    """Türkçe sayı yazımı: binlik ayırıcı nokta, ondalık virgül (1.234.567,8)."""
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def car_tree(train: pd.DataFrame) -> dict:
    """marka -> seri -> model -> {ilan sayısı, yıl aralığı, medyan yıl ve km} (train'den).

    Boş seri/model "bilinmiyor" olur (add_features gibi). Medyanlar formun varsayılanıdır
    (ör. Tofaş Şahin için 2012 gibi var olmayan bir yıl gösterilmesin); yıl aralığı uyarı içindir.
    """
    cars = train[["marka", "seri", "model"]].astype(object).fillna(MISSING_LABEL)
    cars[["yil", "kilometre"]] = train[["yil", "kilometre"]].astype(float)
    stats = cars.groupby(["marka", "seri", "model"]).agg(
        ilan=("yil", "size"), yil_min=("yil", "min"), yil_max=("yil", "max"),
        yil_medyan=("yil", "median"), km_medyan=("kilometre", "median"))
    tree: dict = {}
    for (marka, seri, model), s in stats.iterrows():
        tree.setdefault(marka, {}).setdefault(seri, {})[model] = {
            "ilan": int(s["ilan"]), "yil_min": int(s["yil_min"]), "yil_max": int(s["yil_max"]),
            "yil_medyan": int(round(s["yil_medyan"])), "km_medyan": int(round(s["km_medyan"], -3))}
    return tree


def numeric_ranges(train: pd.DataFrame) -> dict:
    """Her sayısal alan için en küçük/büyük, medyan ve nadir değer sınırları (boşlar hariç)."""
    out = {}
    for col in NUM_INPUTS:
        values = train[col].dropna().astype(float)
        out[col] = {"min": values.min(), "max": values.max(), "median": values.median(),
                    "rare_low": values.quantile(RARE_LOW_Q), "rare_high": values.quantile(RARE_HIGH_Q)}
    return out


def build_form_options(train: pd.DataFrame) -> dict:
    """Formun seçenekleri; yalnızca train'den (test satırları kullanılmaz)."""
    return {
        "kaynak": "train (Adım 3 bölmesi); test yalnızca bölme kontrolünde (id sha256, grup kesişimi)",
        "data_year": DATA_YEAR,
        "cars": car_tree(train),
        # formun varsayılan aracı: train'de en sık görülen marka+seri+model
        "default_car": list(train[["marka", "seri", "model"]].astype(object).fillna(MISSING_LABEL)
                            .value_counts().index[0]),
        # en sık değer başta: formun varsayılanı olur
        "categories": {col: train[col].value_counts().index.tolist() for col in SIMPLE_CATS},
        "numeric": numeric_ranges(train),
        "price_q1": float(price_bin_edges(train[TARGET])[0]),
    }


def file_sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_artifacts() -> dict:
    """Model, model bilgisi, SHAP arka planı ve form seçeneklerini yükler; uyumluluğu doğrular."""
    model = joblib.load(MODEL_PATH)
    info = json.loads(INFO_JSON.read_text(encoding="utf-8"))
    bundle = joblib.load(BACKGROUND_PATH)
    options = json.loads(OPTIONS_JSON.read_text(encoding="utf-8"))
    if info["sklearn"] != sklearn.__version__:
        raise ValueError(f"model sklearn {info['sklearn']} ile kaydedildi, kurulu {sklearn.__version__}")
    model_sha = file_sha256(MODEL_PATH)
    if model_sha != MODEL_SHA256:
        raise ValueError("model dosyası değişmiş: predict.MODEL_SHA256 ve TEST_Q1_MAPE güncellenmeli")
    if bundle["model_sha256"] != model_sha:
        raise ValueError("SHAP arka planı başka bir model dosyası için üretilmiş (sha256 farklı)")
    if options.get("model_sha256") != model_sha or options.get("test_split_sha256") != EXPECTED_TEST_SHA:
        raise ValueError("form_options.json başka bir model veya bölme için üretilmiş;"
                         " PYTHONPATH=src python -m arac_fiyat.predict ile yeniden üretin")
    if bundle["features"] != FEATURES or bundle["model"] != info["model"]:
        raise ValueError("SHAP arka planının özellik sırası veya model adı uyuşmuyor")
    return {"model": model, "info": info, "background": bundle["background"], "options": options}


def make_input_frame(values: dict) -> pd.DataFrame:
    """Form değerlerinden tek satırlık ham tablo; boş (None) sayısal alanlar NaN olur."""
    missing = [c for c in INPUT_COLS if c not in values]
    if missing:
        raise ValueError(f"eksik alan: {missing}")
    row = {c: values[c] for c in INPUT_COLS}
    for col in NUM_INPUTS:
        row[col] = np.nan if row[col] is None else float(row[col])
    return pd.DataFrame([row], columns=INPUT_COLS)


def predict_price(model, row: pd.DataFrame) -> float:
    """Tahmini fiyat (TL, Haziran 2025 ilan fiyatları düzeyinde)."""
    return float(model.predict(row)[0])


def error_range(price: float, median_ape_pct: float) -> tuple[float, float]:
    """Gerçek fiyatın APE <= m olduğu aralık: |y - tahmin| / y <= m  <=>  tahmin/(1+m) <= y <= tahmin/(1-m)."""
    m = median_ape_pct / 100
    return price / (1 + m), price / (1 - m)


def shown_value(col: str, value) -> str:
    """Açıklama tablosunda okunur değer."""
    if isinstance(value, float) and np.isnan(value):
        return "girilmedi"
    if col == "yas":
        return f"{value:.0f} yıl"
    if isinstance(value, float):
        return tr_number(value)
    return str(value)


def explain_car(model, background: np.ndarray, row: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """Tek ilanın SHAP açıklaması (Adım 5 ile aynı yöntem ve arka plan).

    Döndürür: |SHAP|'a göre sıralı tablo (özellik, değer, shap_log, carpan) ve taban fiyat (TL).
    Taban = exp(arka plandaki 200 satırın ortalama LOG tahmini) = tahminlerin GEOMETRİK ortalaması;
    TL tahminlerinin aritmetik ortalaması değildir (o daha yüksektir).
    taban * çarpanların çarpımı = tahmin (log birimde toplamlılık, aşağıda kontrol edilir).
    Açıklayıcı her çağrıda aynı tohumla kurulur: aynı girdi hep aynı açıklamayı verir.
    """
    preprocess, hgb = split_model(model)
    X = preprocess.transform(row)
    expl = explain(make_explainer(hgb, background), X)
    values = expl.values[0]
    base = float(expl.base_values[0])
    gap = abs(base + values.sum() - float(hgb.predict(X)[0]))
    if gap > 1e-3:
        raise ValueError(f"SHAP toplamlılığı tutmadı (fark {gap:.1e} log)")
    raw = display_values(add_features(row).iloc[0])
    raw[FEATURES.index("log_km")] = f"{tr_number(row['kilometre'].iloc[0])} km"  # Türkçe yazım
    table = pd.DataFrame({"özellik": [LABELS[f] for f in FEATURES],
                          "değer": [shown_value(f, v) for f, v in zip(FEATURES, raw)],
                          "shap_log": values, "carpan": np.exp(values)})
    order = np.argsort(-np.abs(values))
    return table.iloc[order].reset_index(drop=True), float(np.exp(base))


def input_warnings(values: dict, options: dict, price: float, test_mape: float) -> list[str]:
    """Tahminin daha az güvenilir olabileceği durumlar için kullanıcıya gösterilecek notlar."""
    notes = []
    for col in NUM_INPUTS:
        value = values[col]
        limits = options["numeric"][col]
        # yıl binlik ayırıcısız yazılır (1978, 1.978 değil)
        fmt = str if col == "yil" else tr_number
        if value is not None and not limits["rare_low"] <= value <= limits["rare_high"]:
            notes.append(f"{NUM_LABELS[col]} = {fmt(int(value))}: eğitim verisindeki ilanların"
                         f" %99,8'i {fmt(int(limits['rare_low']))} – {fmt(int(limits['rare_high']))}"
                         " aralığında; bu değerde tahmin güvenilmez olabilir.")
    car = options["cars"][values["marka"]][values["seri"]][values["model"]]
    if car["ilan"] < FEW_MODEL_ROWS:
        notes.append(f"Bu marka/seri/model eğitim verisinde yalnızca {car['ilan']} ilanda var;"
                     " modelin bu araç hakkındaki bilgisi sınırlı.")
    # az ilanlı modelde yıl aralığı birkaç ilandan gelir, anlamsız uyarı üretir (yukarıdaki not yeter)
    elif not car["yil_min"] <= values["yil"] <= car["yil_max"]:
        notes.append(f"Bu marka/seri/model eğitim verisinde yalnızca {car['yil_min']} – {car['yil_max']}"
                     " model yıllarında var;"
                     f" {values['yil']} için tahmin güvenilmez olabilir (yıl veya model yanlış seçilmiş olabilir).")
    if price < options["price_q1"]:
        notes.append(f"Tahmin ucuz fiyat diliminde (< {tr_number(options['price_q1'])} TL). Testte gerçek"
                     f" fiyatı bu dilimde olan ilanlarda ortalama hata %{tr_number(TEST_Q1_MAPE, 1)}"
                     f" (tüm testte %{tr_number(test_mape, 1)}). Uyarı tahmine, bu oran gerçek fiyata"
                     " göre gruplanmıştır; yaklaşık bir göstergedir.")
    return notes


def main() -> None:
    train, test = holdout_split(pd.read_csv(CLEAN_CSV))
    check_same_split(train, test)  # Adım 3-4 ile aynı bölme; test başka hiçbir yerde kullanılmaz
    # parmak izi: uygulama, JSON'un bu model dosyası ve bu bölme için üretildiğini doğrular
    options = {"model_sha256": file_sha256(MODEL_PATH), "test_split_sha256": EXPECTED_TEST_SHA,
               **build_form_options(train)}
    # sıkışık yazım (girintisiz): ~4 000 modelle dosya küçük kalsın
    OPTIONS_JSON.write_text(json.dumps(options, ensure_ascii=False, separators=(",", ":")) + "\n",
                            encoding="utf-8")
    cars = options["cars"]
    n_seri = sum(len(s) for s in cars.values())
    n_model = sum(len(m) for s in cars.values() for m in s.values())
    print(f"form seçenekleri yazıldı: {OPTIONS_JSON.name} ({OPTIONS_JSON.stat().st_size / 1e3:.0f} KB),"
          f" train {len(train)} satır")
    print(f"marka {len(cars)}, marka+seri {n_seri}, marka+seri+model {n_model}")
    print("kategoriler:", {c: len(v) for c, v in options["categories"].items()})
    print("fiyat Q1 sınırı (train):", f"{options['price_q1']:,.0f} TL")
    for col, r in options["numeric"].items():
        print(f"  {col}: " + ", ".join(f"{k} {v:,.0f}" for k, v in r.items()))


if __name__ == "__main__":
    main()
