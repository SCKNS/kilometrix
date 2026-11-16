"""Streamlit arayüzü: kullanıcı araç bilgilerini girer, tahmini fiyatı ve SHAP açıklamasını görür.

Çalıştırma (proje kökünden): streamlit run app/streamlit_app.py
Model yeniden eğitilmez; models/ altındaki dosyalar okunur (arac_fiyat.predict.load_artifacts).
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # ekran olmadan çizim
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# Kayıtlı model arac_fiyat paketine başvuruyor: src/ yolu eklenmeli (Streamlit Cloud dahil)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from arac_fiyat import predict as P  # noqa: E402

UP_COLOR, DOWN_COLOR = "#3b6ea5", "#b54a4a"  # Adım 5 grafikleriyle aynı renkler
# Formda girilebilecek en yüksek km (train'de 90 milyon gibi açıkça hatalı değerler var)
MAX_KM = 2_000_000
# Boş bırakılamayan alanlar (anahtar -> ekrandaki ad); "Ayrıntılar" bölümü isteğe bağlı
REQUIRED_FIELDS = {"marka": "Marka", "seri": "Seri", "model": "Model", "yil": "Model yılı",
                   "kilometre": "Kilometre", "yakit_tipi": "Yakıt", "vites_tipi": "Vites",
                   "kasa_tipi": "Kasa tipi", "renk": "Renk", "kimden": "Kimden"}


@st.cache_resource(show_spinner="Model yükleniyor…")
def get_artifacts() -> dict:
    return P.load_artifacts()


# kendi bekleme yazısı kapalı: bekleme göstergesi main() içinde düğmenin altında gösterilir
@st.cache_data(show_spinner=False)
def cached_explanation(values_items: tuple) -> tuple[pd.DataFrame, float]:
    """Aynı girdi için SHAP yeniden hesaplanmasın (girdi, sözlüğün sıralı demeti)."""
    art = get_artifacts()
    row = P.make_input_frame(dict(values_items))
    return P.explain_car(art["model"], art["background"], row)


def pick(column, label: str, choices: list, empty_text: str = "Seçin"):
    """Boş başlayan seçim kutusu (yer tutucu yazısıyla); seçenek yoksa kapalı durur."""
    return column.selectbox(label, choices, index=None, placeholder=empty_text,
                            disabled=not choices)


def car_inputs(options: dict) -> dict:
    """Formdaki alanlar; seçenekler yalnızca eğitim verisinden (models/form_options.json)."""
    cars, cats, num = options["cars"], options["categories"], options["numeric"]
    values = {}

    st.subheader("Araç")
    c1, c2, c3 = st.columns(3)
    values["marka"] = pick(c1, "Marka", sorted(cars))
    series = sorted(cars[values["marka"]]) if values["marka"] else []
    values["seri"] = pick(c2, "Seri", series, "Seçin" if series else "Önce marka seçin")
    models = sorted(cars[values["marka"]][values["seri"]]) if values["seri"] else []
    values["model"] = pick(c3, "Model", models, "Seçin" if models else "Önce seri seçin")

    # yıl ve km boş başlar; model seçiliyse yer tutucu o modelin train medyanını örnek gösterir
    # (yer tutucu değişince Streamlit alanı sıfırlar: model değişirse yıl/km yeniden girilir)
    car = cars[values["marka"]][values["seri"]][values["model"]] if values["model"] else None
    year_hint = f"ör. {car['yil_medyan']}" if car else "ör. 2015"
    km_hint = f"ör. {P.tr_number(min(car['km_medyan'], MAX_KM))}" if car else "ör. 150.000"
    c1, c2, c3 = st.columns(3)
    values["yil"] = c1.number_input("Model yılı", min_value=int(num["yil"]["min"]),
                                    max_value=options["data_year"], value=None, step=1,
                                    placeholder=year_hint)
    values["kilometre"] = c2.number_input("Kilometre", min_value=0, max_value=MAX_KM,
                                          value=None, step=1000, placeholder=km_hint)
    values["yakit_tipi"] = pick(c3, "Yakıt", cats["yakit_tipi"])

    c1, c2, c3 = st.columns(3)
    values["vites_tipi"] = pick(c1, "Vites", cats["vites_tipi"])
    values["kasa_tipi"] = pick(c2, "Kasa tipi", cats["kasa_tipi"])
    values["renk"] = pick(c3, "Renk", cats["renk"])

    st.subheader("Ayrıntılar (bilmiyorsanız boş bırakın)")
    st.caption("Boş alan modele \"bilinmiyor\" olarak gider; 0 ile aynı şey değildir. "
               "Biliyorsanız girin: tahmin buna göre değişebilir.")
    c1, c2, c3, c4 = st.columns(4)
    values["motor_hacmi"] = c1.number_input("Motor hacmi (cc)", min_value=0, max_value=10_000,
                                            value=None, step=100, placeholder="boş")
    values["motor_gucu"] = c2.number_input("Motor gücü (hp)", min_value=0, max_value=2_000,
                                           value=None, step=5, placeholder="boş")
    values["degisen_sayisi"] = c3.number_input("Değişen parça sayısı", min_value=0, max_value=20,
                                               value=None, step=1, placeholder="boş")
    values["boyali_sayisi"] = c4.number_input("Boyalı parça sayısı", min_value=0, max_value=20,
                                              value=None, step=1, placeholder="boş")
    values["kimden"] = pick(st, "Kimden", cats["kimden"])
    return values


def missing_fields(values: dict) -> list[str]:
    """Doldurulması zorunlu ama boş kalan alanların ekrandaki adları."""
    return [label for key, label in REQUIRED_FIELDS.items() if values[key] is None]


def contribution_chart(table: pd.DataFrame):
    """Özellik başına tahmin çarpanı exp(SHAP); çubuklar 1'den başlar, en büyük etki üstte."""
    data = table.iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 0.35 * len(data) + 1.2))
    colors = [UP_COLOR if c >= 1 else DOWN_COLOR for c in data["carpan"]]
    labels = [f"{name} = {value}" for name, value in zip(data["özellik"], data["değer"])]
    ax.barh(labels, data["carpan"] - 1, left=1, color=colors)
    ax.axvline(1, color="grey", lw=0.8)
    ax.ticklabel_format(axis="x", useOffset=False)
    ax.set_xlabel("tahmin çarpanı = exp(SHAP)   (1'den büyük: artırır, küçük: azaltır)")
    fig.tight_layout()
    return fig


def effect_text(multiplier: float) -> str:
    sign = "+" if multiplier >= 1 else "−"
    return f"{sign}%{P.tr_number(abs(multiplier - 1) * 100, 1)}"


def show_explanation(table: pd.DataFrame, base: float, price: float) -> None:
    st.subheader("Tahmin nasıl oluştu?")
    st.write(f"Başlangıç noktası **{P.tr_number(base)} TL**: modelin, eğitim verisinden seçilmiş 200 "
             "ilan için tahminlerinin **geometrik ortalaması** (log fiyat tahminlerinin ortalamasının "
             "TL karşılığı). Basit ortalama değildir; basit ortalama pahalı araçlar yüzünden daha "
             "yüksektir. Her özellik bu değeri bir **çarpanla** büyütür ya da küçültür; "
             "çarpanlar birbirleriyle **çarpılarak** birleşir (toplanmaz).")
    fig = contribution_chart(table)
    st.pyplot(fig)
    plt.close(fig)
    shown = pd.DataFrame({"Özellik": table["özellik"], "Değer": table["değer"],
                          "Çarpan": [f"×{P.tr_number(c, 3)}" for c in table["carpan"]],
                          "Etki": [effect_text(c) for c in table["carpan"]]})
    st.dataframe(shown, hide_index=True, width="stretch")
    st.caption(f"Kontrol: {P.tr_number(base)} TL × tüm çarpanlar = "
               f"{P.tr_number(base * table['carpan'].prod())} TL (tahmin {P.tr_number(price)} TL).")
    with st.expander("Bu açıklama nasıl okunmalı? (sınırlar)"):
        st.markdown(
            "- Değerler **yaklaşıktır**: permütasyonla tahmin edilir; tek bir çarpan birkaç yüzde "
            "oynayabilir (Adım 5 kararlılık kontrolü: tek değer en fazla ≈0,08 log ≈ %8).\n"
            "- Modelin **nasıl davrandığını** açıklar, **neden-sonuç değildir**. Örneğin \"renk\" "
            "çarpanı, o rengi boyatınca fiyatın değişeceği anlamına gelmez.\n"
            "- Birbirine bağlı özellikler (marka / seri / model, yaş / kilometre) etkiyi aralarında "
            "keyfi bölüşebilir; bu grupları **birlikte** okuyun.\n"
            "- \"seri\" ve \"model\" satırları, eğitim fiyatlarından öğrenilmiş bir koddur "
            "(o seri/modelin tipik fiyat düzeyi).\n"
            "- Teknik ad: interventional SHAP (Independent maskeleyici, eğitimden 200 satır arka plan), "
            "ön işleme sonrası 14 dönüştürülmüş girdi üzerinde.")


def show_sidebar(info: dict) -> None:
    metrics = info["test_metrikleri"]
    st.sidebar.header("Model hakkında")
    st.sidebar.markdown(
        f"- Veri: arabam.com ilanları, **Haziran 2025** (Kaggle, Tanrıverdi). Tahminler o tarihin "
        f"TL ilan fiyatı düzeyindedir; enflasyona göre güncellenmez.\n"
        f"- Kapsam: çoğunlukla binek otomobil; SUV ve pick-up çok az.\n"
        f"- Model: gradyan artırmalı ağaçlar (HistGradientBoosting), {P.tr_number(info['train_satir'])} "
        f"eğitim ilanı.\n"
        f"- Test hatası: ortalama %{P.tr_number(metrics['MAPE'], 1)}, medyan "
        f"%{P.tr_number(metrics['medyan_APE'], 1)}. Ucuz araçlarda ve eğitimde görülmemiş modellerde "
        f"daha yüksek.\n"
        f"- Bu test sonuçları **iyimser olabilir**: veride ilan numarası yok, aynı aracın tekrar "
        f"ilanları tam ayıklanamadı.\n"
        f"- Bu bir tahmindir; ekspertiz ve piyasa araştırmasının yerini tutmaz.")


def main() -> None:
    st.set_page_config(page_title="Kilometrix — Araç Fiyat Tahmini", layout="wide")
    st.title("Kilometrix")
    st.caption("İkinci el araç fiyat tahmini (Türkiye)")
    st.write("Araç bilgilerini girip **Tahmini göster** düğmesine tıklayın; model tahmini ilan "
             "fiyatını ve bu tahmine hangi özelliğin ne kadar etki ettiğini gösterir.")
    art = get_artifacts()
    show_sidebar(art["info"])

    values = car_inputs(art["options"])

    # Tahmin yalnızca düğmeye basılınca yapılır; basılan andaki girdiler saklanır.
    # Sonra bir alan değişirse eski tahmin gizlenir (yanlış araca ait sonuç görünmesin).
    # Alanlar boş başlar (yer tutucu); zorunlu alan eksikse tahmin yapılmaz.
    if st.button("Tahmini göster", type="primary"):
        missing = missing_fields(values)
        if missing:
            st.session_state.pop("submitted", None)
            st.warning("Lütfen şu alanları doldurun: " + ", ".join(missing) + ".")
            return
        st.session_state["submitted"] = values
    submitted = st.session_state.get("submitted")
    if submitted is None:
        st.info("Bilgileri girdikten sonra **Tahmini göster** düğmesine tıklayın.")
        return
    if submitted != values:
        st.info("Bilgiler değişti. Yeni tahmin için **Tahmini göster** düğmesine tekrar tıklayın.")
        return

    # Hesap (özellikle SHAP açıklaması) birkaç saniye sürebilir; kullanıcı beklediğini anlasın diye
    # düğmenin hemen altında süre sayan bir bekleme göstergesi çıkar. Sonuçlar hesap bitince birlikte görünür.
    with st.spinner("Tahmin hesaplanıyor, birkaç saniye sürebilir…", show_time=True):
        row = P.make_input_frame(values)
        price = P.predict_price(art["model"], row)
        table, base = cached_explanation(tuple(values.items()))
    low, high = P.error_range(price, art["info"]["test_metrikleri"]["medyan_APE"])

    st.divider()
    st.metric("Tahmini ilan fiyatı (Haziran 2025)", f"{P.tr_number(price)} TL")
    st.write(f"Testteki ilanların yaklaşık yarısında hata (gerçek fiyata oranla) "
             f"%{P.tr_number(art['info']['test_metrikleri']['medyan_APE'], 1)} veya daha azdı; kalan yarıda "
             f"daha büyüktü. Bu oran bu tahmine uygulanırsa: **{P.tr_number(low)} – {P.tr_number(high)} TL**. "
             "Bu, tüm testin ortalama davranışıdır; bu araca özel güven aralığı değildir "
             "(ucuz ve nadir araçlarda hata daha büyük).")
    for note in P.input_warnings(values, art["options"], price, art["info"]["test_metrikleri"]["MAPE"]):
        st.warning(note)

    st.divider()
    show_explanation(table, base, price)


main()
