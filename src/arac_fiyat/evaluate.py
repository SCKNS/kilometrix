"""Model değerlendirme metrikleri (hepsi TL cinsinden fiyat üzerinden).

- MAPE: ortalama mutlak yüzde hata (ana metrik)
- medyan APE: uç ilanların MAPE'yi ne kadar şişirdiğini görmek için
- MAE, RMSE: TL cinsinden mutlak hata; RMSE >> MAE ise büyük hatalı uç ilanlar var
- fiyat dilimine göre MAPE: hata ucuz araçlarda mı toplanıyor
"""

import numpy as np

BIN_NAMES = ["Q1 (ucuz)", "Q2", "Q3", "Q4 (pahalı)"]


def regression_metrics(y_true, y_pred) -> dict[str, float]:
    """MAPE, medyan APE (yüzde), MAE ve RMSE (TL) döndürür."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    ape = np.abs(y_pred - y_true) / y_true  # fiyat > 0 (geçerlilik kuralı)
    return {
        "MAPE": 100 * ape.mean(),
        "medyan_APE": 100 * np.median(ape),
        "MAE": np.abs(y_pred - y_true).mean(),
        "RMSE": np.sqrt(((y_pred - y_true) ** 2).mean()),
    }


def price_bin_edges(y_train) -> np.ndarray:
    """Fiyat çeyrek sınırları; yalnızca train fiyatlarından hesaplanır."""
    return np.quantile(np.asarray(y_train, dtype=float), [0.25, 0.5, 0.75])


def mape_by_price_bin(y_true, y_pred, edges) -> dict[str, float]:
    """Gerçek fiyatın düştüğü çeyreğe göre MAPE (yüzde)."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    bins = np.digitize(y_true, edges)  # 0..3
    ape = np.abs(y_pred - y_true) / y_true
    return {name: 100 * ape[bins == i].mean() for i, name in enumerate(BIN_NAMES)}
