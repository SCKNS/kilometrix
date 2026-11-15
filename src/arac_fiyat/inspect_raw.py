"""Adım 1: iki ham veri setini inceleyen tek seferlik betik.

Çalıştırma (proje kökünden):
    PYTHONPATH=src .venv/Scripts/python.exe -m arac_fiyat.inspect_raw

Yalnızca özet basar (şema, eksikler, aralıklar, dönem, iki set arası örtüşme).
Hiçbir dosyayı değiştirmez; buradaki fiyat özetleri yalnızca tanıma amaçlıdır,
temizleme/eşik kararı bunlara dayanmaz (bkz. docs/PROGRESS.md "Değerlendirme kuralları").
"""

import sys

import pandas as pd

from arac_fiyat.data_loader import load_arabam, load_car_prices_tr

QUANTILES = [0, 0.01, 0.25, 0.5, 0.75, 0.99, 1]

# Türkçe ay adları -> ay numarası (ör. "07 Nisan 2025")
TR_MONTHS = {
    "Ocak": 1, "Şubat": 2, "Mart": 3, "Nisan": 4, "Mayıs": 5, "Haziran": 6,
    "Temmuz": 7, "Ağustos": 8, "Eylül": 9, "Ekim": 10, "Kasım": 11, "Aralık": 12,
}


def parse_tr_number(series: pd.Series) -> pd.Series:
    """B'deki '1.169.000 TL' / '120.000 km' metinlerini sayıya çevirir (yalnızca inceleme için).

    Sondaki ' TL' / ' km' atılır, noktalar binlik ayırıcı sayılıp silinir.
    Başka hiçbir karakter silinmez: eksi işareti korunur, virgüllü ondalık
    ('1,5') veya metin ('Otomatik') sessizce sayıya dönmez, NaN olur.
    """
    text = series.astype("string").str.strip()
    text = text.str.replace(r"\s*(TL|km)$", "", regex=True).str.replace(".", "", regex=False)
    return pd.to_numeric(text, errors="coerce").astype("float64")


def parse_tr_date(series: pd.Series) -> pd.Series:
    """'07 Nisan 2025' biçimindeki tarihleri datetime'a çevirir; çevrilemeyen NaT olur."""
    text = series.astype("string")
    for name, number in TR_MONTHS.items():
        text = text.str.replace(f" {name} ", f" {number:02d} ", regex=False)
    return pd.to_datetime(text, format="%d %m %Y", errors="coerce")


def duplicate_summary(df: pd.DataFrame) -> None:
    """Tamamen boş satırları ve boş olmayan yinelenen satırları ayrı sayar."""
    is_empty = df.isna().all(axis=1)
    filled = df[~is_empty]
    print("tamamen boş satır:", is_empty.sum())
    print("boş olmayan satırlarda fazladan kopya (ilki hariç):", filled.duplicated().sum())
    dup_groups = filled[filled.duplicated(keep=False)]
    print("boş olmayan tekrar gruplarındaki toplam satır (ilkler dahil):", len(dup_groups))
    print("boş olmayan tekrar grubu sayısı:", len(dup_groups.drop_duplicates()))


def section(title: str) -> None:
    """Çıktıda okunaklı bir başlık basar."""
    print(f"\n{'=' * 10} {title} {'=' * 10}")


def column_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Her sütun için tip, eksik sayısı, eksik yüzdesi ve farklı değer sayısı."""
    return pd.DataFrame({
        "tip": df.dtypes.astype(str),
        "eksik": df.isna().sum(),
        "eksik_%": (df.isna().mean() * 100).round(1),
        "farkli": df.nunique(),
    })


def quantiles(series: pd.Series) -> dict:
    """Yüzdelikleri yuvarlanmış sözlük olarak döndürür."""
    return series.quantile(QUANTILES).round(0).to_dict()


def inspect_arabam(df: pd.DataFrame) -> None:
    """arabam.com (Tanrıverdi) veri setine özgü kontroller."""
    section("A: car_price_prediction.csv (arabam.com, Tanrıverdi)")
    print("satır, sütun:", df.shape)
    print(column_summary(df))

    # id gerçek ilan numarası mı, yoksa satır sırası mı?
    is_row_number = df["id"].tolist() == list(range(1, len(df) + 1))
    print("\nid = 1..N satır sırası mı:", is_row_number)

    # Tekrar sayımı id hariç yapılır; boş satırlar birbirinin kopyası sayılmasın diye ayrı
    print("\n[id hariç tekrar analizi]")
    duplicate_summary(df.drop(columns="id"))

    print("\nyil aralığı:", df["yil"].min(), "-", df["yil"].max())
    print("yil dağılımı (son 5 yıl):", df["yil"].value_counts().sort_index().tail(5).to_dict())
    print("kilometre yüzdelikleri:", quantiles(df["kilometre"]))
    print("kilometre == 0 satır:", (df["kilometre"] == 0).sum())
    print("fiyat yüzdelikleri (TL):", quantiles(df["fiyat"]))
    print("fiyat <= 0:", (df["fiyat"] <= 0).sum(), "| fiyat boş:", df["fiyat"].isna().sum())

    brand_counts = df["marka"].value_counts()
    print(f"\nmarka sayısı: {len(brand_counts)}; marka başına ilan en çok {brand_counts.max()}, "
          f"2400 üstü marka sayısı: {(brand_counts > 2400).sum()}")
    print("en az ilanlı 5 marka:", brand_counts.tail(5).to_dict())
    for col in ["vites_tipi", "yakit_tipi", "kasa_tipi", "kimden"]:
        print(f"{col}:", df[col].value_counts(dropna=False).to_dict())


def inspect_car_prices_tr(df: pd.DataFrame) -> None:
    """Car Prices Turkey (Gülşen) veri setine özgü kontroller."""
    section("B: car_prices_tr.csv (Car Prices Turkey, Gülşen)")
    print("satır, sütun:", df.shape)
    print(column_summary(df))

    # Sütun kayması kontrolü: 'kilometre(Km)' yıl gibi, 'yıl' km metni gibi mi?
    km_col_looks_like_year = df["kilometre(Km)"].between(1950, 2026).mean()
    year_col_has_km_text = df["yıl"].astype("string").str.endswith(" km").mean()
    print(f"\n'kilometre(Km)' değerlerinin 1950-2026 arasında olma oranı: {km_col_looks_like_year:.4f}")
    print(f"'yıl' değerlerinin ' km' ile bitme oranı: {year_col_has_km_text:.4f}")

    price = parse_tr_number(df["fiyat(TRY)"])
    print("\nfiyat 'TL' ile bitmeyen:", (~df["fiyat(TRY)"].str.endswith(" TL")).sum())
    print("fiyat sayıya çevrilemeyen:", price.isna().sum(), "| fiyat <= 0:", (price <= 0).sum())
    print("fiyat yüzdelikleri (TL):", quantiles(price))
    km = parse_tr_number(df["yıl"])
    print("km ('yıl' sütunundan) yüzdelikleri:", quantiles(km))

    date = parse_tr_date(df["ilanTarihi"])
    print("\nilanTarihi çevrilemeyen:", date.isna().sum())
    print("ilanTarihi aralığı:", date.min().date(), "-", date.max().date())
    print("aylara göre ilan:", date.dt.to_period("M").value_counts().sort_index().to_dict())
    print("en yoğun 5 gün:", date.dt.date.value_counts().head(5).to_dict())

    print("\nilanID yinelenen:", df["ilanID"].duplicated().sum())
    print("ilanID hariç birebir yinelenen satır:", df.drop(columns="ilanID").duplicated().sum())
    print("il sayısı:", df["il"].nunique())

    # Motor hacmi/gücü bazen tam değer ('1598 cc'), bazen aralık ('1401 - 1600 cm3')
    for col in ["motorHacmi(Cc)", "motorGucu(HP)"]:
        is_range = df[col].astype("string").str.contains(" - |kadar|üzeri", regex=True)
        print(f"{col}: aralık/metin biçiminde {is_range.sum()} satır, boş {df[col].isna().sum()}")
    for col in ["vitesTipi", "yakitTuru", "kasaTipi", "cekisTipi", "saticiTuru", "takasUygunluk"]:
        print(f"{col}:", df[col].value_counts(dropna=False).to_dict())
    print("hasarGecmisi en sık 5:", df["hasarGecmisi"].value_counts(dropna=False).head(5).to_dict())


def compare_datasets(a: pd.DataFrame, b: pd.DataFrame) -> None:
    """İki set arasında marka adları ve olası ortak ilanlar."""
    section("A ile B karşılaştırma")
    brands_a, brands_b = set(a["marka"].dropna()), set(b["marka"].dropna())
    print("yalnızca B'de olan markalar:", sorted(brands_b - brands_a))
    print("A'da olup B'de olmayan marka sayısı:", len(brands_a - brands_b))

    # Ortak ilan tahmini: marka + yıl + km + fiyat birebir aynı
    b_keys = pd.DataFrame({
        "marka": b["marka"],
        "yil": b["kilometre(Km)"],  # sütunlar kaymış: yıl bu sütunda
        "kilometre": parse_tr_number(b["yıl"]),
        "fiyat": parse_tr_number(b["fiyat(TRY)"]),
    }).dropna()
    a_keys = a[["marka", "yil", "kilometre", "fiyat"]].dropna().drop_duplicates()
    matched = b_keys.merge(a_keys, on=["marka", "yil", "kilometre", "fiyat"], how="inner")
    print(f"B'deki {len(b_keys)} satırdan A'da marka+yıl+km+fiyat ile eşleşen: {len(matched)}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows konsolunda Türkçe karakterler için
    pd.set_option("display.width", 160)
    a = load_arabam()
    b = load_car_prices_tr()
    inspect_arabam(a)
    inspect_car_prices_tr(b)
    compare_datasets(a, b)


if __name__ == "__main__":
    main()
