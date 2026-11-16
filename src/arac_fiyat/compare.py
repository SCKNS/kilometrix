"""Adım 4a: aday modelleri ve ayarlarını train içinde grup bazlı CV ile karşılaştırır.

Test seti burada AÇILMAZ. Bölme ve fold'lar Adım 3 ile aynıdır (split.py).

Seçim kuralı (sonuçlar görülmeden önce yazıldı):
1. Ölçüt: 5 fold'un ortalama doğrulama MAPE'si (ana metrik, satır atılmamış doğrulama kümesi).
2. Her aile (ridge, hgb, xgb) içinde en düşük MAPE'li ayar o ailenin adayıdır.
3. Genel en düşük MAPE bulunur; basitlik sırasıyla (ridge < hgb < xgb) bakılır ve
   en iyiye 0,1 puandan yakın olan ilk aile seçilir (fark gürültü düzeyindeyse basit model).
Seçilen ayar final.py içine elle sabitlenir; test yalnızca orada, bir kez açılır.

Çalıştırma (proje kökünden): PYTHONPATH=src python -m arac_fiyat.compare
"""

import numpy as np
import pandas as pd
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline

from arac_fiyat.config import RANDOM_STATE, REPORTS_DIR
from arac_fiyat.features import (build_preprocessor, build_tree_preprocessor, feature_step,
                                 tree_categorical_indices)
from arac_fiyat.split import holdout_split
from arac_fiyat.train import CLEAN_CSV, make_models, run_cv, summarize_cv, format_table

REPORT_TXT = REPORTS_DIR / "adim4_karsilastirma.txt"
LEARNING_RATE = 0.05  # ağaç modellerinde sabit; ağaç sayısı ayarlanır
FAMILY_ORDER = ["ridge", "hgb", "xgb"]  # basitten karmaşığa
TIE_MARGIN = 0.1  # MAPE puanı

# Ad -> (aile, parametreler). Izgara küçük tutuldu: 5 + 6 + 6 = 17 aday.
CANDIDATES = {
    **{f"ridge_a{a}": ("ridge", {"alpha": a}) for a in [0.1, 0.3, 1.0, 3.0, 10.0]},
    **{f"hgb_l{leaves}_n{n}": ("hgb", {"max_leaf_nodes": leaves, "max_iter": n})
       for leaves in [15, 31, 63] for n in [500, 1500]},
    **{f"xgb_d{depth}_n{n}": ("xgb", {"max_depth": depth, "n_estimators": n})
       for depth in [4, 6, 8] for n in [500, 1500]},
}


def build_model(family: str, params: dict) -> TransformedTargetRegressor:
    """Ham ilan satırından TL fiyat tahmin eden Pipeline; model log(fiyat) üzerinde eğitilir."""
    if family == "ridge":
        pipe = make_pipeline(feature_step(), build_preprocessor(), Ridge(**params))
    elif family == "hgb":
        hgb = HistGradientBoostingRegressor(
            learning_rate=LEARNING_RATE, categorical_features=tree_categorical_indices(),
            early_stopping=False, random_state=RANDOM_STATE, **params)
        pipe = make_pipeline(feature_step(), build_tree_preprocessor(), hgb)
    elif family == "xgb":
        # xgboost yalnızca model karşılaştırmasında gerekir (requirements-dev.txt); burada içe
        # aktarılınca uygulama (predict -> final -> compare) xgboost olmadan da açılır
        from xgboost import XGBRegressor

        # one-hot (seyrek) girdi; Ridge ile aynı ön işleme
        xgb = XGBRegressor(learning_rate=LEARNING_RATE, random_state=RANDOM_STATE, **params)
        pipe = make_pipeline(feature_step(), build_preprocessor(), xgb)
    else:
        raise ValueError(f"bilinmeyen aile: {family}")
    return TransformedTargetRegressor(regressor=pipe, func=np.log, inverse_func=np.exp)


def all_models() -> dict:
    """İki baseline + tüm adaylar."""
    baselines = make_models()
    models = {"genel_medyan": baselines["genel_medyan"],
              "marka_model_medyan": baselines["marka_model_medyan"]}
    for name, (family, params) in CANDIDATES.items():
        models[name] = build_model(family, params)
    return models


def select_model(val_mape: pd.Series) -> tuple[str, pd.DataFrame]:
    """Docstring'deki kurala göre seçilen aday adını ve aile özet tablosunu döndürür."""
    rows = []
    for family in FAMILY_ORDER:
        names = [n for n, (fam, _) in CANDIDATES.items() if fam == family]
        best = val_mape[names].idxmin()
        rows.append({"aile": family, "en_iyi_ayar": best, "MAPE": val_mape[best]})
    families = pd.DataFrame(rows).set_index("aile")
    overall = families["MAPE"].min()
    chosen = families[families["MAPE"] <= overall + TIE_MARGIN].index[0]  # FAMILY_ORDER sırasında ilk
    return families.loc[chosen, "en_iyi_ayar"], families


def main() -> None:
    log: list[str] = []
    df = pd.read_csv(CLEAN_CSV)
    train, test = holdout_split(df)
    log.append(f"train: {len(train)} satır; test {len(test)} satır (AÇILMADI)")
    log.append(f"aday sayısı: {len(CANDIDATES)} (+2 baseline); öğrenme oranı (ağaçlar) {LEARNING_RATE}")
    log.append("")

    results = run_cv(train, log, use_filter=False, models=all_models())
    table = summarize_cv(results)
    val_mape = table.loc["doğrulama", "MAPE"]

    log.append("")
    log.append("CV sonuçları (5 fold ortalaması; yüzdeler %, MAE/RMSE TL; Q1-Q4 = fiyat çeyreğine göre MAPE)")
    log.append("ana metrik: 'doğrulama' (yalnızca geçerlilik kuralı, hiç satır atılmadı)")
    for set_name in ["train", "doğrulama", "doğrulama_süzülmüş"]:
        log.append("")
        log.append(f"--- {set_name} ---")
        log.append(format_table(table.loc[set_name].sort_values("MAPE")))

    log.append("")
    log.append("train - doğrulama MAPE farkı (aşırı öğrenme göstergesi; negatif = train daha iyi):")
    log.append("not: hgb train MAPE'si temiz değil (TargetEncoder train'i tam-train kodlarıyla"
               " tahmin eder); hgb için fark yalnızca kaba gösterge")
    gap = table.loc["train", "MAPE"] - val_mape
    log.append(gap.sort_values().round(1).to_string())

    chosen, families = select_model(val_mape)
    log.append("")
    log.append("fold başına doğrulama MAPE (aile en iyileri + baseline):")
    cols = ["genel_medyan", "marka_model_medyan", *families["en_iyi_ayar"]]
    per_fold = results[results["küme"] == "doğrulama"].pivot(index="fold", columns="model", values="MAPE")
    log.append(per_fold[cols].round(2).to_string())

    log.append("")
    log.append(f"aile en iyileri (seçim kuralı: en iyiye {TIE_MARGIN} puandan yakın ilk basit aile):")
    log.append(families.round(3).to_string())
    log.append(f"SEÇİLEN: {chosen} -> {CANDIDATES[chosen]}")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    text = "\n".join(log)
    REPORT_TXT.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
