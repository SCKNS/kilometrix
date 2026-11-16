"""Adım 4b: seçilen modeli tüm train'e eğitir, test setinde BİR KEZ değerlendirir, kaydeder.

Model seçimi compare.py'de yalnızca CV ile yapıldı (reports/adim4_karsilastirma.txt) ve
aşağıda FINAL_NAME olarak sabitlendi. Bu betik test raporu zaten varsa çalışmaz:
test sonucu görüldükten sonra model değiştirilirse bu açıkça yazılmalıdır
(docs/PROGRESS.md, değerlendirme kuralları).

Çalıştırma (proje kökünden): PYTHONPATH=src python -m arac_fiyat.final
"""

import hashlib
import json

import joblib
import numpy as np
import pandas as pd
import sklearn

from arac_fiyat.cleaning import TARGET
from arac_fiyat.compare import CANDIDATES, build_model
from arac_fiyat.config import MODELS_DIR, REPORTS_DIR
from arac_fiyat.evaluate import mape_by_price_bin, price_bin_edges, regression_metrics
from arac_fiyat.split import count_shared_groups, holdout_split
from arac_fiyat.train import CLEAN_CSV, fit_train_filter, format_table, keep_mask, make_models

FINAL_NAME = "hgb_l31_n1500"  # compare.py seçimi; CV doğrulama MAPE %10,56
# Adım 3 raporundaki test id listesi özeti; bölme değiştiyse durulur
EXPECTED_TEST_SHA = "fdb1c155beaf439498115f148f6725a77d47aa2b591b9bf736f7f17c7b943873"

REPORT_TXT = REPORTS_DIR / "adim4_test.txt"
MODEL_PATH = MODELS_DIR / "arac_fiyat_model.joblib"
INFO_JSON = MODELS_DIR / "model_info.json"


def check_same_split(train: pd.DataFrame, test: pd.DataFrame) -> None:
    """Bölmenin Adım 3'tekiyle aynı ve grupların ayrık olduğunu doğrular."""
    test_ids = ",".join(map(str, sorted(test["id"])))
    if hashlib.sha256(test_ids.encode()).hexdigest() != EXPECTED_TEST_SHA:
        raise ValueError("test bölmesi Adım 3'tekinden farklı")
    if count_shared_groups(train, test):
        raise ValueError("train ve test grup paylaşıyor")


def fit_models(train: pd.DataFrame) -> dict:
    """İki baseline ve seçilen model, tüm train ile eğitilir."""
    baselines = make_models()
    family, params = CANDIDATES[FINAL_NAME]
    models = {"genel_medyan": baselines["genel_medyan"],
              "marka_model_medyan": baselines["marka_model_medyan"],
              FINAL_NAME: build_model(family, params)}
    return {name: model.fit(train, train[TARGET]) for name, model in models.items()}


def metrics_table(models: dict, sets: dict, edges) -> pd.DataFrame:
    """Her model x küme için metrikler ve fiyat çeyreğine göre MAPE."""
    rows = []
    for set_name, part in sets.items():
        for name, model in models.items():
            pred = model.predict(part)
            row = {"küme": set_name, "model": name, "satır": len(part)}
            row.update(regression_metrics(part[TARGET], pred))
            row.update(mape_by_price_bin(part[TARGET], pred, edges))
            rows.append(row)
    return pd.DataFrame(rows).set_index(["küme", "model"])


def unseen_model_report(model, train: pd.DataFrame, test: pd.DataFrame) -> str:
    """Testte, train'de görülmemiş marka+seri+model satırlarının sayısı ve MAPE'si."""
    def key(df):
        return df["marka"] + "|" + df["seri"] + "|" + df["model"].fillna("")
    unseen = ~key(test).isin(set(key(train)))
    lines = []
    for label, mask in [("görülmüş", ~unseen), ("görülmemiş", unseen)]:
        part = test[mask]
        mape = regression_metrics(part[TARGET], model.predict(part))["MAPE"]
        lines.append(f"  {label} marka+seri+model: {len(part)} satır, MAPE {mape:.1f}")
    return "\n".join(lines)


def save_model(model, train: pd.DataFrame, test_metrics: dict) -> None:
    """Modeli joblib ile, özet bilgisini JSON olarak models/ altına yazar."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH, compress=3)
    family, params = CANDIDATES[FINAL_NAME]
    info = {
        "model": FINAL_NAME, "aile": family, "parametreler": params,
        "hedef": "log(fiyat), tahmin TL'ye geri çevrilir",
        "train_satir": len(train),
        "test_metrikleri": {k: round(float(v), 3) for k, v in test_metrics.items()},
        "sklearn": sklearn.__version__,
    }
    INFO_JSON.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    if REPORT_TXT.exists():
        raise SystemExit(f"{REPORT_TXT.name} zaten var: test bir kez açıldı. Yeniden açmak"
                         " bilinçli bir karar olmalı; dosyayı silmeden önce kullanıcıya sor.")
    log: list[str] = []
    train, test = holdout_split(pd.read_csv(CLEAN_CSV))
    check_same_split(train, test)
    log.append(f"bölme Adım 3 ile aynı (SHA-256 eşleşti); train {len(train)}, test {len(test)} satır,"
               " ortak grup 0")
    log.append(f"seçilen model (CV ile, test görülmeden): {FINAL_NAME} -> {CANDIDATES[FINAL_NAME]}")
    # test açılmadan önce rapor dosyası oluşturulur; süreç yarıda kesilse de
    # yukarıdaki koruma ikinci çalıştırmayı durdurur
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_TXT.write_text("test açıldı; çalışma tamamlanmadı\n", encoding="utf-8")

    models = fit_models(train)
    bounds = fit_train_filter(train)
    test_kept = keep_mask(test, bounds)
    log.append(f"ampirik sınırlar (tüm train'den, yalnızca duyarlılık analizi): {bounds};"
               f" testte sınır dışı {int((~test_kept).sum())} satır (atılmadı)")
    _, level = models["marka_model_medyan"].predict_with_level(test)
    log.append(f"marka_model_medyan test düzeyleri: {pd.Series(level).value_counts().to_dict()}")

    sets = {"train": train, "test": test, "test_süzülmüş": test[test_kept]}
    table = metrics_table(models, sets, price_bin_edges(train[TARGET]))
    log.append("")
    log.append("Sonuçlar (yüzdeler %, MAE/RMSE TL; Q1-Q4 = train çeyrek sınırlarına göre MAPE)")
    log.append("ana metrik: 'test' (yalnızca geçerlilik kuralı, hiç satır atılmadı);"
               " 'test_süzülmüş' = duyarlılık analizi")
    log.append("sınır: grup anahtarı yaklaşık, yeniden ilan sızıntısını garanti engellemez;"
               " bu yüzden test metrikleri iyimser olabilir")
    log.append(format_table(table.drop(columns="satır")))
    log.append("")
    log.append(f"{FINAL_NAME}, testte görülmüş / görülmemiş araç modeli:")
    log.append(unseen_model_report(models[FINAL_NAME], train, test))

    final = models[FINAL_NAME]
    test_metrics = table.loc[("test", FINAL_NAME), ["MAPE", "medyan_APE", "MAE", "RMSE"]].to_dict()
    save_model(final, train, test_metrics)
    reloaded = joblib.load(MODEL_PATH)
    same = np.allclose(reloaded.predict(test.head(200)), final.predict(test.head(200)))
    size_mb = MODEL_PATH.stat().st_size / 1e6
    log.append("")
    log.append(f"model kaydedildi: {MODEL_PATH.relative_to(MODELS_DIR.parent)} ({size_mb:.2f} MB);"
               f" yeniden yüklenince tahminler aynı: {same}")

    text = "\n".join(log)
    REPORT_TXT.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
