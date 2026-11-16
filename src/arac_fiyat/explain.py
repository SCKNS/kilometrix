"""Adım 5: SHAP ile model açıklama — hangi özelliğin fiyatı ne kadar etkilediği.

Neden TreeExplainer değil: modelin HGB ağaçlarında kategorik (bit kümesi) bölmeler var ve
SHAP'ın ağaç dönüştürücüsü bunları okumuyor; hata vermeden yanlış sonuç üretiyor
(main() bunu ölçüp rapora yazar). Bu yüzden modelden bağımsız PermutationExplainer kullanılır.

Ne açıklanır: ön işlemeden ÇIKAN 14 sütun -> HGB'nin log(fiyat) tahmini. Ön işleme açıklamanın
dışındadır. Sütunlar ham ilan alanlarının kendisi değil, temsilleridir: "yaş" = 2025 - yıl,
"kilometre" = log(1 + km), marka/vites/... = sıra kodu, "seri" ve "model" = train fiyatlarından
öğrenilmiş hedef kodu ("model" sütunu marka|seri|model birleşik kategorisinin kodudur).
SHAP değerleri log birimindedir; exp(değer) çarpandır:
tahmin_TL = exp(taban) * exp(shap_1) * ... * exp(shap_14).
"Taban" = arka plan (train'den 200 satır) üzerindeki ortalama log tahmin.
Özetlerde yüzdelerin aritmetik ortalaması yerine GEOMETRİK ORTALAMA ÇARPAN kullanılır:
exp(ort SHAP) = exp(SHAP) çarpanlarının geometrik ortalamasıdır (log modelde doğal ortalama).
Maskeleme bağımsızdır (shap.maskers.Independent -> interventional SHAP): eksik sayılan sütun arka
plandan tek başına gelir, bu yüzden gerçekte olmayan karışımlar (ör. Kia markası + Mercedes seri kodu)
oluşur. Sonuçlar bu tanım altındaki model açıklamasıdır, ham özellik etkisi değildir; group_shap()
bunun grup paylarına etkisini ayrıca ölçer.
Açıklanan satırlar: test setinden örnek, yalnızca özellikler (fiyat kullanılmaz, model değişmez).
Bu yüzden test seti bu adımdan sonra tamamen dokunulmamış holdout sayılmaz.

Çalıştırma (proje kökünden): PYTHONPATH=src python -m arac_fiyat.explain
"""

import hashlib
import json
import time

import joblib
import matplotlib

matplotlib.use("Agg")  # ekran olmadan dosyaya çizim
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
import sklearn

from arac_fiyat.cleaning import TARGET
from arac_fiyat.config import MODELS_DIR, RANDOM_STATE, REPORTS_DIR
from arac_fiyat.features import HIGH_CARD_CATS, LOW_CARD_CATS, NUM_FEATURES, add_features
from arac_fiyat.final import FINAL_NAME, INFO_JSON, MODEL_PATH
from arac_fiyat.split import holdout_split
from arac_fiyat.train import CLEAN_CSV

N_BACKGROUND = 200    # arka plan satırı (train'den)
N_EXPLAIN = 1000      # açıklanan satır (test özelliklerinden)
N_PERMUTATIONS = 10   # satır başına permütasyon sayısı
N_STABILITY = 100     # kararlılık kontrolü için satır
N_GROUP_CHECK = 200   # grup maskeleme kontrolü için satır

# Birlikte maskelenen gruplar (group_shap): grup içi sütunlar hep aynı arka plan satırından gelir
GROUPS = {"araç tanımı (marka+seri+model)": ["marka", "marka_seri", "marka_seri_model"],
          "kullanım (yaş+kilometre)": ["yas", "log_km"]}

FEATURES = NUM_FEATURES + LOW_CARD_CATS + HIGH_CARD_CATS  # ön işleme çıktı sırası
LABELS = {
    "yas": "yaş", "log_km": "kilometre", "motor_hacmi": "motor hacmi",
    "motor_gucu": "motor gücü", "degisen_sayisi": "değişen parça",
    "boyali_sayisi": "boyalı parça", "marka": "marka", "vites_tipi": "vites",
    "yakit_tipi": "yakıt", "kasa_tipi": "kasa", "renk": "renk", "kimden": "kimden",
    "marka_seri": "seri", "marka_seri_model": "model",
}
# Sıra numarasıyla kodlanmış kategoriler: kod büyüklüğü anlam taşımaz, bu yüzden
# arı kovanı (beeswarm) grafiğine girmez; kategori bazında ayrı grafik çizilir.
CATEGORY_PLOT_COLS = ["yakit_tipi", "vites_tipi", "kasa_tipi", "kimden"]
MIN_CATEGORY_ROWS = 20

# Her rapor ve grafikte yazılan yöntem notu (sonuçların ne olduğu / ne olmadığı)
METHOD_NOTE = ("interventional SHAP (Independent maskeleyici, train'den 200 satır arka plan),"
               " ön işleme sonrası 14 dönüştürülmüş girdi üzerinde; ham özellik etkisi değil")
FIG_NOTE = "interventional SHAP, Independent maskeleyici, dönüştürülmüş girdiler"

FIG_DIR = REPORTS_DIR / "figures"
REPORT_TXT = REPORTS_DIR / "adim5_shap.txt"
BACKGROUND_PATH = MODELS_DIR / "shap_background.joblib"


def split_model(model):
    """Kayıtlı modeli (TransformedTargetRegressor) ön işleme ve HGB olarak ayırır."""
    pipe = model.regressor_
    return pipe[:-1], pipe[-1]


def make_explainer(hgb, background: np.ndarray, seed: int = RANDOM_STATE) -> shap.PermutationExplainer:
    """HGB'nin log tahmini için permütasyon tabanlı SHAP açıklayıcısı.

    Not: shap tohumu yalnızca burada, global np.random.seed ile ayarlar; tekrar üretilebilir
    sonuç için explain() açıklayıcı oluşturulduktan hemen sonra çağrılmalı.
    """
    masker = shap.maskers.Independent(background, max_samples=len(background))
    return shap.PermutationExplainer(hgb.predict, masker, seed=seed,
                                     feature_names=[LABELS[f] for f in FEATURES])


def explain(explainer, X: np.ndarray) -> shap.Explanation:
    """X satırlarının SHAP değerleri (log birimi)."""
    max_evals = N_PERMUTATIONS * (2 * len(FEATURES) + 1)
    return explainer(X, max_evals=max_evals, silent=True)


def tree_explainer_check(hgb, X: np.ndarray) -> str:
    """TreeExplainer'ın iç tahmini modelden ne kadar sapıyor (yalnızca tanı, sonuçlara girmez).

    sklearn'ün özel `_predictors` alanını ve SHAP'ın iç modelini kullanır; requirements.txt'teki
    sabit sürümlerde (sklearn 1.9.1, shap 0.54.1) denendi. Sürüm değişip kırılırsa betik durmaz,
    rapora "yapılamadı" yazılır.
    """
    try:
        internal = shap.TreeExplainer(hgb).model.predict(X)
        error = float(np.abs(internal - hgb.predict(X)).max())
        nodes = [tree[0].nodes for tree in hgb._predictors]
        n_cat = sum(int(n["is_categorical"][n["is_leaf"] == 0].sum()) for n in nodes)
        n_split = sum(int((n["is_leaf"] == 0).sum()) for n in nodes)
    except Exception as err:  # tanı amaçlı: hata açıkça rapora yazılır
        return f"TreeExplainer kontrolü YAPILAMADI ({type(err).__name__}: {err})"
    return (f"TreeExplainer kontrolü: {n_cat}/{n_split} bölme kategorik; SHAP'ın iç tahmini"
            f" modelden en fazla {error:.2f} log birimi sapıyor -> kullanılmadı")


def importance_table(expl: shap.Explanation) -> pd.DataFrame:
    """Özellik başına ortalama |SHAP| (log) ve geometrik ortalama mutlak çarpan: exp(ort|SHAP|).

    exp(|SHAP|) = çarpan 1'in üstündeyse kendisi, altındaysa 1/çarpan; yani yön atılmış büyüklük.
    Ör. 1.25 = "tipik olarak tahmini 1,25 ile çarpıyor ya da 1,25'e bölüyor".
    """
    mean_abs = np.abs(expl.values).mean(axis=0)
    table = pd.DataFrame({"ort_abs_shap": mean_abs, "geo_abs_carpan": np.exp(mean_abs)},
                         index=expl.feature_names)
    return table.sort_values("ort_abs_shap", ascending=False)


def direction_table(expl: shap.Explanation, raw: pd.DataFrame) -> pd.Series:
    """Sayısal özellikler için değer ile SHAP arasındaki Spearman sıra korelasyonu (yön kontrolü)."""
    out = {}
    for i, col in enumerate(NUM_FEATURES):
        values = raw[col]
        ok = values.notna().to_numpy()
        out[LABELS[col]] = pd.Series(values[ok].to_numpy()).corr(
            pd.Series(expl.values[ok, i]), method="spearman")
    return pd.Series(out)


def category_effects(expl: shap.Explanation, raw: pd.DataFrame, col: str) -> pd.DataFrame:
    """Bir kategorik sütunda kategori başına satır sayısı, ortalama SHAP (log) ve
    geometrik ortalama çarpan: exp(ort SHAP) (1'den büyükse tahmini artırır)."""
    shap_col = pd.Series(expl.values[:, FEATURES.index(col)], index=raw.index)
    table = pd.DataFrame({"satir": shap_col.groupby(raw[col]).size(),
                          "ort_shap": shap_col.groupby(raw[col]).mean()})
    table["geo_carpan"] = np.exp(table["ort_shap"])
    table = table[table["satir"] >= MIN_CATEGORY_ROWS]
    return table.sort_values("ort_shap")


def group_shap(hgb, background: np.ndarray, X: np.ndarray, seed: int = RANDOM_STATE) -> pd.DataFrame:
    """Gruplu permütasyon SHAP (log birimi): GROUPS'taki sütunlar birlikte, diğerleri tek tek maskelenir.

    Her permütasyonda arka plandan başlanır, oyuncular (grup veya tek sütun) sırayla açıklanan satırın
    değerine çevrilir; her adımda ortalama tahmindeki artış o oyuncuya yazılır. Grup içi sütunlar aynı
    arka plan satırından geldiği için (ör.) marka ile seri kodu kendi aralarında tutarlı kalır.
    """
    in_group = {c for cols in GROUPS.values() for c in cols}
    players = {name: [FEATURES.index(c) for c in cols] for name, cols in GROUPS.items()}
    players |= {LABELS[c]: [FEATURES.index(c)] for c in FEATURES if c not in in_group}
    names = list(players)
    rng = np.random.default_rng(seed)
    out = np.zeros((len(X), len(names)))
    n_bg = len(background)
    for r, x in enumerate(X):
        # tüm permütasyonların tüm adımları tek predict çağrısında (hız için)
        orders = [rng.permutation(len(names)) for _ in range(N_PERMUTATIONS)]
        blocks = []
        for order in orders:
            data = background.copy()
            blocks.append(data.copy())
            for p in order:
                data[:, players[names[p]]] = x[players[names[p]]]
                blocks.append(data.copy())
        means = hgb.predict(np.vstack(blocks)).reshape(-1, n_bg).mean(axis=1)
        step = len(names) + 1
        for k, order in enumerate(orders):
            diffs = np.diff(means[k * step:(k + 1) * step])
            out[r, order] += diffs
    return pd.DataFrame(out / N_PERMUTATIONS, columns=names)


def group_report(expl: shap.Explanation, grouped: pd.DataFrame) -> list[str]:
    """Bağımsız maskeleme (sonradan toplanan) ile grup maskeleme arasındaki fark."""
    n = len(grouped)
    single = pd.DataFrame(expl.values[:n], columns=expl.feature_names)
    # tek tek SHAP'ları aynı oyunculara topla: grup sütunu = üyelerin SHAP toplamı
    collapsed = pd.DataFrame({name: single[[LABELS[c] for c in cols]].sum(axis=1)
                              for name, cols in GROUPS.items()})
    collapsed = collapsed.join(single[[c for c in grouped.columns if c in single.columns]])
    lines = [f"Grup maskeleme kontrolü (ilk {n} satır, {N_PERMUTATIONS} permütasyon; log birimi):",
             "  A = tek tek maskeleme, grup üyeleri sonradan toplanmış; B = grup birlikte maskelenmiş",
             "  pay = oyuncunun ort|değer|'i / tüm oyuncuların toplamı (A ve B aynı tanımla)",
             "  grup | ort|A| | ort|B| | A-B satır korelasyonu | pay A | pay B"
             " | pay (rapordaki tanım: üyelerin ort|SHAP| toplamı)"]
    single_total = single.abs().mean().sum()
    for name, cols in GROUPS.items():
        share_a = collapsed[name].abs().mean() / collapsed.abs().mean().sum() * 100
        share_b = grouped[name].abs().mean() / grouped.abs().mean().sum() * 100
        share_old = single[[LABELS[c] for c in cols]].abs().mean().sum() / single_total * 100
        corr = np.corrcoef(collapsed[name], grouped[name])[0, 1]
        lines.append(f"  {name} | {collapsed[name].abs().mean():.4f} | {grouped[name].abs().mean():.4f}"
                     f" | {corr:.3f} | %{share_a:.1f} | %{share_b:.1f} | %{share_old:.1f}")
    return lines


def plot_importance(table: pd.DataFrame, path) -> None:
    """Genel önem: ortalama |SHAP| çubuk grafiği."""
    fig, ax = plt.subplots(figsize=(7, 5))
    data = table.iloc[::-1]
    ax.barh(data.index, data["ort_abs_shap"], color="#3b6ea5")
    ax.set_xlabel("ortalama |SHAP| (log fiyat birimi)")
    ax.set_title(f"Ortalama |SHAP|\n({FIG_NOTE})", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_beeswarm(expl: shap.Explanation, path) -> None:
    """Sırası anlamlı özellikler (sayısal + hedef kodlu seri/model) için arı kovanı grafiği."""
    keep = [FEATURES.index(c) for c in NUM_FEATURES + HIGH_CARD_CATS]
    shap.plots.beeswarm(expl[:, keep], max_display=len(keep), show=False)
    fig = plt.gcf()
    fig.set_size_inches(8, 5.5)
    plt.title(f"Girdi değeri (renk) ve SHAP\n({FIG_NOTE})", fontsize=10)
    plt.xlabel("SHAP değeri (log fiyat birimi)")
    plt.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_dependence(expl: shap.Explanation, raw: pd.DataFrame, rows: pd.DataFrame, path) -> None:
    """Yaş, kilometre ve motor gücü değerine karşı satır başına çarpan exp(SHAP) (ortalama değil)."""
    specs = [("yas", raw["yas"], "yaş (yıl)", False),
             ("log_km", rows["kilometre"].astype(float), "kilometre (log eksen)", True),
             ("motor_gucu", raw["motor_gucu"], "motor gücü (hp)", False)]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for ax, (col, x, xlabel, log_x) in zip(axes, specs):
        multiplier = np.exp(expl.values[:, FEATURES.index(col)])
        if log_x:
            x = x.clip(lower=1)  # 0 km log eksende çizilemez
            ax.set_xscale("log")
        ax.scatter(x, multiplier, s=6, alpha=0.4, color="#3b6ea5")
        ax.axhline(1, color="grey", lw=0.8)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("tahmin çarpanı exp(SHAP), satır başına")
        ax.set_title(LABELS[col])
    fig.suptitle(FIG_NOTE, fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_categories(effects: dict[str, pd.DataFrame], path) -> None:
    """Kategori başına geometrik ortalama çarpan exp(ort SHAP), 2x2 grafik (çubuklar 1'den başlar)."""
    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    for ax, (col, table) in zip(axes.ravel(), effects.items()):
        colors = ["#b54a4a" if v < 1 else "#3b6ea5" for v in table["geo_carpan"]]
        labels = [f"{name} (n={n})" for name, n in zip(table.index, table["satir"])]
        ax.barh(labels, table["geo_carpan"] - 1, left=1, color=colors)
        ax.axvline(1, color="grey", lw=0.8)
        # çarpan 1'e çok yakınsa (kimden) eksen "+1" kaydırmalı ve sık etiketli çizilmesin
        ax.ticklabel_format(axis="x", useOffset=False)
        ax.locator_params(axis="x", nbins=4)
        ax.set_title(LABELS[col])
        ax.set_xlabel("geometrik ortalama çarpan = exp(ort SHAP)")
    fig.suptitle(FIG_NOTE, fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def display_values(row: pd.Series) -> np.ndarray:
    """Grafikte kodlanmış sayılar yerine okunur ham değerler (FEATURES sırasıyla)."""
    shown = {"yas": row["yas"], "log_km": f"{np.expm1(row['log_km']):,.0f} km",
             "marka_seri": row["marka_seri"].split(" | ")[-1],
             "marka_seri_model": row["marka_seri_model"].split(" | ")[-1]}
    return np.array([shown.get(col, row[col]) for col in FEATURES], dtype=object)


def plot_waterfall(expl_row: shap.Explanation, raw_row: pd.Series, title: str, path) -> None:
    """Tek bir ilanın tahmininin özelliklere dağılımı (log birimi)."""
    expl_row.display_data = display_values(raw_row)
    shap.plots.waterfall(expl_row, max_display=len(FEATURES), show=False)
    fig = plt.gcf()
    fig.set_size_inches(8, 6)
    plt.title(f"{title}\n({FIG_NOTE})", fontsize=9)
    plt.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def stability_report(explainer_other_seed, X: np.ndarray, expl: shap.Explanation) -> list[str]:
    """Aynı satırlar farklı tohumla yeniden açıklanır: genel ve özellik bazında oynaklık,
    önem sırası değişimi ve tek hücre farkının dağılımı."""
    first = expl.values[: len(X)]
    second = explain(explainer_other_seed, X).values
    diff = np.abs(first - second)
    per_feature = pd.DataFrame({"ort_abs_shap": np.abs(first).mean(axis=0),
                                "ort_abs_fark": diff.mean(axis=0)}, index=expl.feature_names)
    per_feature["goreli_fark"] = per_feature["ort_abs_fark"] / per_feature["ort_abs_shap"]
    order_1 = list(per_feature["ort_abs_shap"].sort_values(ascending=False).index)
    order_2 = list(pd.Series(np.abs(second).mean(axis=0), index=expl.feature_names)
                   .sort_values(ascending=False).index)
    rank_corr = pd.Series([order_1.index(f) for f in expl.feature_names]).corr(
        pd.Series([order_2.index(f) for f in expl.feature_names]), method="spearman")
    q50, q95, qmax = np.quantile(diff, [0.5, 0.95, 1.0])
    return [f"Kararlılık (ilk {len(X)} satır, başka tohum):",
            f"  genel: ortalama |fark| / ortalama |SHAP| = {diff.mean() / np.abs(first).mean():.3f}",
            f"  tek hücre |fark| (log): medyan {q50:.4f}, %95'lik {q95:.4f}, en fazla {qmax:.4f}",
            f"  önem sırası: iki tohumda aynı mı = {order_1 == order_2}; sıra korelasyonu {rank_corr:.3f}",
            "  özellik bazında:",
            per_feature.sort_values("ort_abs_shap", ascending=False).round(4).to_string()]


def model_fingerprint() -> dict:
    """Arka plan dosyasının hangi model ve ön işleme ile uyumlu olduğunu belirten bilgiler."""
    info = json.loads(INFO_JSON.read_text(encoding="utf-8"))
    return {"model": info["model"],
            "model_sha256": hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest(),
            "features": FEATURES,
            "versions": {"sklearn": sklearn.__version__, "shap": shap.__version__,
                         "numpy": np.__version__}}


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    log: list[str] = []
    model = joblib.load(MODEL_PATH)
    preprocess, hgb = split_model(model)
    train, test = holdout_split(pd.read_csv(CLEAN_CSV))

    background = preprocess.transform(train.sample(N_BACKGROUND, random_state=RANDOM_STATE))
    # test fiyatı kullanılmaz: yalnızca özellik sütunları açıklanır
    rows = test.drop(columns=TARGET).sample(N_EXPLAIN, random_state=RANDOM_STATE)
    X = preprocess.transform(rows)
    raw = add_features(rows)
    fingerprint = model_fingerprint()
    if fingerprint["model"] != FINAL_NAME:
        raise ValueError(f"model_info.json'daki model {fingerprint['model']}, beklenen {FINAL_NAME}")
    log.append(f"YÖNTEM: {METHOD_NOTE}")
    log.append("TEST SETİ: açıklanan satırlar test özelliklerinden (fiyatsız); test seti artık tamamen"
               " dokunulmamış holdout değil (Adım 4 metrikleri geçerli, sonraki değişiklikleri tarafsız ölçemez)")
    log.append(f"model: {fingerprint['model']} (model_info.json; dosya sha256"
               f" {fingerprint['model_sha256'][:12]}…); arka plan: train'den {N_BACKGROUND} satır;"
               f" açıklanan: testten {N_EXPLAIN} satır (yalnızca özellikler, fiyat kullanılmadı)")

    log.append(tree_explainer_check(hgb, X))

    explainer = make_explainer(hgb, background)
    start = time.time()
    expl = explain(explainer, X)
    seconds = time.time() - start
    pred_log = hgb.predict(X)
    additivity = float(np.abs(expl.values.sum(axis=1) + expl.base_values - pred_log).max())
    log.append(f"PermutationExplainer: {N_PERMUTATIONS} permütasyon/satır, {seconds:.0f} sn"
               f" ({seconds / N_EXPLAIN:.2f} sn/satır)")
    log.append(f"toplamlılık: |taban + toplam SHAP - model log tahmini| en fazla {additivity:.1e}")
    base = float(expl.base_values[0])
    log.append(f"taban (arka plan ortalama log tahmini): {base:.4f} -> {np.exp(base):,.0f} TL")
    # tahmin zinciri: ön işleme + HGB + exp = kayıtlı modelin TL tahmini olmalı
    chain_ok = np.allclose(np.exp(pred_log), model.predict(rows))
    log.append(f"exp(HGB log tahmini) = kayıtlı modelin TL tahmini: {chain_ok}")

    other = make_explainer(hgb, background, seed=RANDOM_STATE + 1)
    log.append("")
    log.extend(stability_report(other, X[:N_STABILITY], expl))

    table = importance_table(expl)
    log.append("")
    log.append("Genel önem (bağımsız maskeleme; ortalama |SHAP| log birimi;"
               " geo_abs_carpan = exp(ort|SHAP|), geometrik ortalama mutlak çarpan):")
    log.append(table.round(4).to_string())
    for name, cols in GROUPS.items():
        labels = [LABELS[c] for c in cols]
        share = table.loc[labels, "ort_abs_shap"].sum() / table["ort_abs_shap"].sum() * 100
        log.append(f"  {name}: toplam ortalama |SHAP| içindeki payı %{share:.1f}")

    start = time.time()
    grouped = group_shap(hgb, background, X[:N_GROUP_CHECK])
    log.append("")
    log.extend(group_report(expl, grouped))
    log.append(f"  (süre {time.time() - start:.0f} sn)")

    log.append("")
    log.append("Yön kontrolü (sayısal özellik değeri ile SHAP arasındaki Spearman korelasyonu; boşlar hariç):")
    log.append(direction_table(expl, raw).round(3).to_string())

    effects = {col: category_effects(expl, raw, col) for col in CATEGORY_PLOT_COLS}
    for col, eff in effects.items():
        log.append("")
        log.append(f"{LABELS[col]}: kategori başına (en az {MIN_CATEGORY_ROWS} satır);"
                   " geo_carpan = exp(ort SHAP), geometrik ortalama çarpan")
        log.append(eff.round(3).to_string())

    # örnek ilan: tahmini medyan tahmine en yakın satır (fiyata bakılmadan seçilir)
    pred_tl = np.exp(pred_log)
    pick = int(np.abs(pred_tl - np.median(pred_tl)).argmin())
    car = rows.iloc[pick]
    title = (f"{car['marka']} {car['seri']} {car['model']}, {car['yil']}, {car['kilometre']:,} km"
             f" -> tahmin {pred_tl[pick]:,.0f} TL")
    log.append("")
    log.append(f"örnek ilan (waterfall): id {car['id']}; {title}")

    plot_importance(table, FIG_DIR / "shap_onem.png")
    plot_beeswarm(expl, FIG_DIR / "shap_beeswarm.png")
    plot_dependence(expl, raw, rows, FIG_DIR / "shap_bagimlilik.png")
    plot_categories(effects, FIG_DIR / "shap_kategoriler.png")
    plot_waterfall(expl[pick], raw.iloc[pick], title, FIG_DIR / "shap_ornek_ilan.png")
    log.append("")
    log.append("grafikler: " + ", ".join(sorted(p.name for p in FIG_DIR.glob("shap_*.png"))))

    # uygulama (Adım 6) tek ilanı açıklarken aynı arka planı kullansın diye kaydedilir;
    # uygulama model dosyasının sha256'sını ve özellik sırasını buna karşı doğrulamalı
    joblib.dump({**fingerprint, "background": background}, BACKGROUND_PATH)
    log.append(f"arka plan kaydedildi: {BACKGROUND_PATH.relative_to(MODELS_DIR.parent)}"
               f" ({BACKGROUND_PATH.stat().st_size / 1e3:.0f} KB; anahtarlar:"
               f" {', '.join(joblib.load(BACKGROUND_PATH))})")

    text = "\n".join(log)
    REPORT_TXT.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
