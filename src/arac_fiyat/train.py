"""Adım 3: iki baseline + basit doğrusal model, train içinde grup bazlı CV ile ölçülür.

Test seti burada yalnızca ayrılır ve boyutu raporlanır; fiyatlarına bakılmaz,
hiçbir model testte değerlendirilmez (docs/PROGRESS.md, değerlendirme kuralları).

Çalıştırma (proje kökünden): PYTHONPATH=src python -m arac_fiyat.train
"""

import hashlib

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.compose import TransformedTargetRegressor
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline

from arac_fiyat.cleaning import TARGET
from arac_fiyat.config import PROCESSED_DIR, REPORTS_DIR
from arac_fiyat.evaluate import mape_by_price_bin, price_bin_edges, regression_metrics
from arac_fiyat.features import build_preprocessor, feature_step
from arac_fiyat.split import count_shared_groups, cv_folds, group_labels, holdout_split

CLEAN_CSV = PROCESSED_DIR / "arabam_clean.csv"
REPORT_TXT = REPORTS_DIR / "adim3_baseline.txt"

# Ampirik sınırlar (yalnızca train dağılımına bakılarak sabitlendi). Her fold'un train
# kısmından hesaplanır. İki yerde kullanılır:
# - "doğrulama_süzülmüş" duyarlılık analizi (doğrulamadan satır atılmaz, ayrıca ölçülür),
# - karşılaştırma koşusu: eğitim satırlarını süzmek (ana sonuç süzgeçsizdir; denetimde süzgecin
#   CV MAPE'yi yalnızca ~0,04 puan değiştirdiği, MAE/RMSE'yi kötüleştirdiği görüldü).
PRICE_LOW_Q = 0.001
PRICE_HIGH_Q = 0.999
KM_HIGH_Q = 0.999


class HierarchicalMedian(BaseEstimator, RegressorMixin):
    """Marka-model medyanı baseline'ı.

    En özel düzeyden başlar: marka+seri+model -> marka+seri -> marka -> genel medyan.
    Medyanlar yalnızca fit'e verilen (train) satırlardan hesaplanır.
    """

    levels = [["marka", "seri", "model"], ["marka", "seri"], ["marka"]]

    def fit(self, X: pd.DataFrame, y):
        data = X.assign(_y=np.asarray(y, dtype=float))
        self.global_median_ = float(np.median(data["_y"]))
        self.medians_ = [data.groupby(cols)["_y"].median() for cols in self.levels]
        return self

    def predict_with_level(self, X: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        """Tahmini ve her satırın hangi düzeyden geldiğini döndürür."""
        pred = np.full(len(X), np.nan)
        level = np.full(len(X), "genel", dtype=object)
        for cols, medians in zip(self.levels, self.medians_):
            todo = np.isnan(pred)
            keys = pd.MultiIndex.from_frame(X[cols]) if len(cols) > 1 else pd.Index(X[cols[0]])
            found = medians.reindex(keys).to_numpy()
            fill = todo & ~np.isnan(found)
            pred[fill] = found[fill]
            level[fill] = "+".join(cols)
        pred[np.isnan(pred)] = self.global_median_
        return pred, level

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self.predict_with_level(X)[0]


def make_models() -> dict:
    """Karşılaştırılan modeller. Ridge log(fiyat) üzerinde eğitilir, tahmin TL'ye döner."""
    ridge = make_pipeline(feature_step(), build_preprocessor(), Ridge(alpha=1.0))
    return {
        "genel_medyan": DummyRegressor(strategy="median"),
        "marka_model_medyan": HierarchicalMedian(),
        "ridge_log": TransformedTargetRegressor(regressor=ridge, func=np.log, inverse_func=np.exp),
    }


def fit_train_filter(train: pd.DataFrame) -> dict[str, float]:
    """Ampirik eğitim kuralının sınırlarını verilen train parçasından hesaplar."""
    return {
        "fiyat_alt": float(train[TARGET].quantile(PRICE_LOW_Q)),
        "fiyat_ust": float(train[TARGET].quantile(PRICE_HIGH_Q)),
        "km_ust": float(train["kilometre"].quantile(KM_HIGH_Q)),
    }


def keep_mask(df: pd.DataFrame, bounds: dict[str, float]) -> pd.Series:
    """Sınırlar içindeki satırlar için True."""
    price_ok = df[TARGET].between(bounds["fiyat_alt"], bounds["fiyat_ust"])
    return price_ok & (df["kilometre"] <= bounds["km_ust"])


def evaluate_fold(train: pd.DataFrame, val: pd.DataFrame, log: list[str],
                  use_filter: bool, models: dict | None = None) -> list[dict]:
    """Bir fold'da tüm modelleri eğitir; train ve doğrulama metriklerini satır listesi döndürür.

    use_filter=True ise ampirik sınırlar dışındaki train satırları eğitimden çıkarılır.
    models verilmezse Adım 3'ün modelleri (make_models) kullanılır.
    """
    models = make_models() if models is None else models
    bounds = fit_train_filter(train)
    fit_rows = train[keep_mask(train, bounds)] if use_filter else train
    val_kept = keep_mask(val, bounds)
    log.append(f"  ampirik sınırlar: {bounds} -> eğitimden -{len(train) - len(fit_rows)} satır;"
               f" doğrulamada sınır dışı (atılmadı) {int((~val_kept).sum())} satır")

    edges = price_bin_edges(train[TARGET])
    rows = []
    for name, model in models.items():
        model = clone(model).fit(fit_rows, fit_rows[TARGET])
        # train metrikleri tüm fold-train üzerinde (doğrulamayla aynı tanım: yalnızca geçerlilik kuralı)
        sets = {"train": train, "doğrulama": val, "doğrulama_süzülmüş": val[val_kept]}
        for set_name, part in sets.items():
            pred = model.predict(part)
            row = {"model": name, "küme": set_name, "satır": len(part)}
            row.update(regression_metrics(part[TARGET], pred))
            row.update(mape_by_price_bin(part[TARGET], pred, edges))
            rows.append(row)
        if name == "marka_model_medyan":
            _, level = model.predict_with_level(val)
            counts = pd.Series(level).value_counts().to_dict()
            log.append(f"  marka_model_medyan doğrulama düzeyleri: {counts}")
        if name == "ridge_log":
            seen = set(fit_rows["marka"] + "|" + fit_rows["seri"] + "|" + fit_rows["model"].fillna(""))
            val_keys = val["marka"] + "|" + val["seri"] + "|" + val["model"].fillna("")
            log.append(f"  ridge_log: doğrulamada eğitimde görülmemiş marka+seri+model"
                       f" {int((~val_keys.isin(seen)).sum())} satır")
    return rows


def run_cv(train: pd.DataFrame, log: list[str], use_filter: bool,
           models: dict | None = None) -> pd.DataFrame:
    """Train içinde grup bazlı CV; her fold için grup/satır sayısını ve sızıntı kontrolünü yazar."""
    all_rows = []
    for i, (tr_idx, val_idx) in enumerate(cv_folds(train), start=1):
        tr, val = train.iloc[tr_idx], train.iloc[val_idx]
        n_tr_groups = len(np.unique(group_labels(tr)))
        n_val_groups = len(np.unique(group_labels(val)))
        shared = count_shared_groups(tr, val)
        log.append(f"fold {i}: train {len(tr)} satır / {n_tr_groups} grup,"
                   f" doğrulama {len(val)} satır / {n_val_groups} grup, ortak grup {shared}")
        if shared:
            raise ValueError(f"fold {i}: train ve doğrulama grup paylaşıyor")
        for row in evaluate_fold(tr, val, log, use_filter, models):
            all_rows.append({"fold": i, **row})
    return pd.DataFrame(all_rows)


def summarize_cv(results: pd.DataFrame) -> pd.DataFrame:
    """Fold'ların ortalaması (MAPE için standart sapma da) — model x küme tablosu."""
    metric_cols = ["MAPE", "medyan_APE", "MAE", "RMSE", "Q1 (ucuz)", "Q2", "Q3", "Q4 (pahalı)"]
    grouped = results.groupby(["küme", "model"], sort=False)
    table = grouped[metric_cols].mean()
    table.insert(1, "MAPE_std", grouped["MAPE"].std())
    return table


def format_table(table: pd.DataFrame) -> str:
    """Yüzdeleri 1 ondalık, TL değerlerini binlik ayraçla yazar."""
    out = table.copy()
    for col in out.columns:
        if col in ("MAE", "RMSE"):
            out[col] = out[col].map(lambda v: f"{v:,.0f}")
        else:
            out[col] = out[col].map(lambda v: f"{v:.1f}")
    return out.to_string()


def main() -> None:
    log: list[str] = []
    df = pd.read_csv(CLEAN_CSV)
    train, test = holdout_split(df)
    test_ids = ",".join(map(str, sorted(test["id"])))
    shared = count_shared_groups(train, test)
    log.append(f"temiz veri: {len(df)} satır, {len(np.unique(group_labels(df)))} grup")
    log.append(f"train: {len(train)} satır / {len(np.unique(group_labels(train)))} grup")
    log.append(f"test (AÇILMADI, yalnızca boyut): {len(test)} satır /"
               f" {len(np.unique(group_labels(test)))} grup;"
               f" train-test ortak grup {shared}")
    if shared:
        raise ValueError("train ve test grup paylaşıyor")
    log.append(f"test id listesinin SHA-256'sı (Adım 4'te aynı bölme kontrolü):"
               f" {hashlib.sha256(test_ids.encode()).hexdigest()}")
    log.append("")

    log.append("=== ANA SONUÇ: eğitim süzgeci YOK (fold-train'in tüm satırlarıyla eğitim) ===")
    results = run_cv(train, log, use_filter=False)
    table = summarize_cv(results)
    log.append("")
    log.append("CV sonuçları (5 fold ortalaması; yüzdeler %, MAE/RMSE TL; Q1-Q4 = fiyat çeyreğine göre MAPE)")
    log.append("ana metrik: 'doğrulama' (yalnızca geçerlilik kuralı, hiç satır atılmadı)")
    log.append("'doğrulama_süzülmüş' = duyarlılık analizi (ampirik sınırlar doğrulamaya uygulanmış)")
    log.append(format_table(table))

    log.append("")
    log.append("fold başına doğrulama MAPE:")
    per_fold = results[results["küme"] == "doğrulama"].pivot(index="fold", columns="model", values="MAPE")
    log.append(per_fold.round(1).to_string())

    log.append("")
    log.append("=== KARŞILAŞTIRMA: ampirik eğitim süzgeciyle (fiyat %0,1/%99,9, km %99,9 dışı eğitimden çıkar) ===")
    filtered = summarize_cv(run_cv(train, log, use_filter=True))
    log.append("")
    log.append("doğrulama (ana metrik kümesi), süzgeçsiz / süzgeçli:")
    compare = pd.concat({"süzgeçsiz": table.loc["doğrulama"], "süzgeçli": filtered.loc["doğrulama"]})
    log.append(format_table(compare[["MAPE", "MAPE_std", "medyan_APE", "MAE", "RMSE"]]))

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    text = "\n".join(log)
    REPORT_TXT.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
