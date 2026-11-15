"""Veri temizleme (yalnızca A: arabam.com).

Bu adımda yalnızca anlamca kesin işler yapılır:
- tamamen boş satırlar atılır,
- fiyat geçerlilik kuralı uygulanır (boş / sayı değil / <= 0),
- '-' gibi fiilen boş değerler NaN yapılır,
- id dışında birebir aynı satırlar atılır (bölmeden ÖNCE). İlan no olmadığından
  bunların hepsinin gerçekten aynı ilan olduğu kanıtlanamaz; olası kopya sayılır.
  Fiyat da karşılaştırmaya dahildir: bu kuralı daraltır (fiyatı farklı satırlar
  atılmaz), fiyat değerine veya eşiğe göre seçim yapmaz.

Ampirik kurallar (aşırı km/fiyat eşikleri vb.) burada YOK: onlar bölmeden sonra
yalnızca train'e bakılarak Adım 3'te belirlenir (bkz. docs/PROGRESS.md).

Çalıştırma (proje kökünden): PYTHONPATH=src python -m arac_fiyat.cleaning
"""

import pandas as pd

from arac_fiyat.config import PROCESSED_DIR, REPORTS_DIR
from arac_fiyat.data_loader import load_arabam

CLEAN_CSV = PROCESSED_DIR / "arabam_clean.csv"
REPORT_TXT = REPORTS_DIR / "adim2_temizleme.txt"

# id satır sırasıdır (ilan no değil); tekrar karşılaştırmasında kullanılmaz
ID_COL = "id"
TARGET = "fiyat"
CAT_COLS = ["marka", "seri", "model", "vites_tipi", "yakit_tipi", "kasa_tipi", "renk", "kimden"]
INT_COLS = ["yil", "kilometre", "fiyat"]

# "Muhtemelen aynı araç" anahtarları (Adım 3'teki bölme raporu için)
NEAR_DUP_KEY = ["marka", "seri", "model", "yil", "kilometre", "fiyat"]
SAME_CAR_KEY = ["marka", "seri", "model", "yil", "kilometre", "renk"]
# Adım 3'te grup bazlı bölmenin anahtarı: yukarıdaki iki anahtarı da kapsar
# (ikisi de bu anahtarın alt kırılımı), yani aynı gruptaki satırlar ayrılmaz.
# DİKKAT: Bu bir yaklaşık anahtardır, gerçek yeniden ilan sızıntısını GARANTİ
# ENGELLEMEZ. km'si güncellenmiş ya da seri/model alanı farklı yazılmış aynı araç
# başka gruba düşer ve train/test'e bölünebilir; bunun sayısı ölçülemez.
GROUP_KEY = ["marka", "seri", "model", "yil", "kilometre"]


def drop_empty_rows(df: pd.DataFrame) -> pd.DataFrame:
    """id dışındaki tüm sütunları boş olan satırları atar."""
    data_cols = df.columns.drop(ID_COL)
    return df.dropna(how="all", subset=data_cols)


def apply_price_validity(df: pd.DataFrame) -> pd.DataFrame:
    """Geçerlilik kuralı: fiyat boş, sayıya çevrilemiyor ya da <= 0 ise satır atılır."""
    price = pd.to_numeric(df[TARGET], errors="coerce")
    valid = price.notna() & (price > 0)
    out = df[valid].copy()
    out[TARGET] = price[valid]
    return out


def fix_placeholders(df: pd.DataFrame) -> pd.DataFrame:
    """'-' gibi fiilen boş metin değerlerini NaN yapar ve metinlerin baş/son boşluğunu siler."""
    out = df.copy()
    for col in CAT_COLS:
        out[col] = out[col].str.strip().replace({"-": pd.NA, "": pd.NA})
    return out


def drop_exact_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """id hariç tüm sütunları aynı olan satırlardan yalnızca ilkini tutar."""
    data_cols = df.columns.drop(ID_COL).tolist()
    return df.drop_duplicates(subset=data_cols, keep="first")


def log_duplicate_profile(df: pd.DataFrame, log: list[str]) -> None:
    """Atılacak olası kopyaların kimden dağılımını ve sıfır km sayısını log'a yazar."""
    data_cols = df.columns.drop(ID_COL).tolist()
    dropped = df[df.duplicated(subset=data_cols, keep="first")]
    zero_km = int((pd.to_numeric(dropped["kilometre"], errors="coerce") <= 100).sum())
    log.append(f"  atılan olası kopyalar: kimden {dropped['kimden'].value_counts().to_dict()};"
               f" km <= 100: {zero_km}")


def cast_int_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Yıl, km ve fiyatı tam sayıya çevirir (boş varsa Int64 ile NaN korunur)."""
    out = df.copy()
    for col in INT_COLS:
        out[col] = out[col].astype("Int64")
    return out


def count_groups(df: pd.DataFrame, key: list[str]) -> tuple[int, int]:
    """Anahtarda 2+ satırı olan grup sayısını ve bu gruplardaki toplam satırı döndürür."""
    sizes = df.groupby(key, dropna=False).size()
    multi = sizes[sizes > 1]
    return int(len(multi)), int(multi.sum())


def count_price_varying_groups(df: pd.DataFrame, key: list[str]) -> tuple[int, int]:
    """2+ satırlı gruplardan fiyatı farklı olanların grup ve satır sayısını döndürür."""
    stats = df.groupby(key, dropna=False)[TARGET].agg(["size", "nunique"])
    varying = stats[(stats["size"] > 1) & (stats["nunique"] > 1)]
    return int(len(varying)), int(varying["size"].sum())


def clean_arabam(df: pd.DataFrame, log: list[str]) -> pd.DataFrame:
    """Tüm temizlik adımlarını sırayla uygular; her adımın satır sayısını log'a yazar."""
    log.append(f"ham: {len(df)} satır")

    steps = [
        ("tamamen boş satırlar", drop_empty_rows),
        ("fiyat geçerlilik kuralı", apply_price_validity),
        ("'-' ve boş metin -> NaN", fix_placeholders),
        ("birebir yinelenen (id hariç)", drop_exact_duplicates),
        ("tam sayı tipleri", cast_int_columns),
    ]
    for name, func in steps:
        before = df
        rows_before, nan_before = len(df), int(df.isna().sum().sum())
        df = func(df)
        nan_after = int(df.isna().sum().sum())
        log.append(f"{name}: -{rows_before - len(df)} satır -> {len(df)}"
                   f" | NaN hücre: {nan_before} -> {nan_after}")
        if func is drop_exact_duplicates:
            log_duplicate_profile(before, log)
    log.append(f"tam sayı sütun tipleri: {df[INT_COLS].dtypes.astype(str).to_dict()}")
    return df.reset_index(drop=True)


def require(condition: bool, message: str) -> None:
    """Koşul yanlışsa ValueError verir (assert'ün aksine python -O ile kapanmaz)."""
    if not condition:
        raise ValueError(message)


def check_clean(df: pd.DataFrame) -> None:
    """Temiz verinin son koşullarını doğrular; biri bozuksa hata verir."""
    require(df[ID_COL].is_unique, "id tekil değil")
    require(df[TARGET].notna().all() and (df[TARGET] > 0).all(), "geçersiz fiyat kaldı")
    for col in CAT_COLS:
        require(not df[col].isin(["-", ""]).any(), f"{col} sütununda yer tutucu kaldı")
    for col in INT_COLS:
        require(str(df[col].dtype) == "Int64", f"{col} tipi Int64 değil")
    data_cols = df.columns.drop(ID_COL)
    require(not df.duplicated(subset=data_cols).any(), "id hariç kopya kaldı")


def summarize(df: pd.DataFrame, log: list[str]) -> None:
    """Temiz verinin eksik değer özetini ve tekrar benzeri grup sayılarını log'a yazar."""
    log.append("")
    log.append(f"temiz veri: {df.shape[0]} satır x {df.shape[1]} sütun")
    missing = df.isna().sum()
    log.append("eksik değerler (yalnızca > 0):")
    for col, n in missing[missing > 0].items():
        log.append(f"  {col}: {n} ({n / len(df):.1%})")

    both_missing = (df["degisen_sayisi"].isna() & df["boyali_sayisi"].isna()).sum()
    log.append(f"degisen ve boyali birlikte boş: {both_missing}")
    log.append(f"kasa_tipi değerleri: {df['kasa_tipi'].value_counts(dropna=False).to_dict()}")

    groups, rows = count_groups(df, NEAR_DUP_KEY)
    log.append("")
    log.append(f"çok benzer ilan ({'+'.join(NEAR_DUP_KEY)}): {groups} grup, {rows} satır")
    groups, rows = count_groups(df, SAME_CAR_KEY)
    log.append(f"muhtemelen aynı araç ({'+'.join(SAME_CAR_KEY)}): {groups} grup, {rows} satır")
    groups, rows = count_price_varying_groups(df, SAME_CAR_KEY)
    log.append(f"  bunlardan fiyatı farklı olan: {groups} grup, {rows} satır")
    all_but_price = df.columns.drop([ID_COL, TARGET]).tolist()
    groups, rows = count_price_varying_groups(df, all_but_price)
    log.append(f"id ve fiyat dışında tamamen aynı, fiyatı farklı: {groups} grup, {rows} satır")
    groups, rows = count_groups(df, GROUP_KEY)
    n_groups = df.groupby(GROUP_KEY, dropna=False).ngroups
    log.append(f"bölme grup anahtarı ({'+'.join(GROUP_KEY)}): {n_groups} grup;"
               f" 2+ satırlı {groups} grup, {rows} satır; en büyük grup"
               f" {int(df.groupby(GROUP_KEY, dropna=False).size().max())} satır")


def main() -> None:
    log: list[str] = []
    df = clean_arabam(load_arabam(), log)
    check_clean(df)
    log.append("son koşullar (id tekil, fiyat > 0, yer tutucu yok, Int64, kopya yok): geçti")
    summarize(df, log)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(CLEAN_CSV, index=False, encoding="utf-8")
    log.append("")
    log.append(f"yazıldı: {CLEAN_CSV.relative_to(PROCESSED_DIR.parents[1])}")

    text = "\n".join(log)
    REPORT_TXT.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
