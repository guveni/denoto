#!/usr/bin/env python
import argparse
import pandas as pd
import math

# # Define the function to update the price information
# def update_price_info(kargo_filename, ticimax_filename):
#     # Load the data from the provided filenames

#     # Rename columns in kargo_data to match those in ticimax_data
#     kargo_data.rename(columns={'Stok Kodu': 'Stock Kodu'}, inplace=True)

#     # Create a dictionary to map stock codes to prices
#     price_dict = dict(zip(kargo_data['Stock Kodu'], kargo_data['Fiyat']))

#     # Update the 'SATISFIYATI' column in ticimax_data based on the stock code
#     ticimax_data['SATISFIYATI'] = ticimax_data['Stock Kodu'].map(price_dict)

#     # Save the updated ticimax_data to a new file
#     output_filename = ticimax_filename.replace('.xls', '_updated.xls')
#     ticimax_data.to_excel(output_filename, index=False)

#     return output_filename

N11 = "N11"
HEPSIBURADA = "HEPSIBURADA"
PTTAVM = "PTTAVM"
TRENDYOL = "TRENDYOL"

KARGOAGIRLIGI = "KARGOAGIRLIGI"
STOKADEDI = "STOKADEDI"
BARKOD = "BARKOD"
STOK_KODU = "Stok Kodu"
HATA_KODU = "HATA"
KDV = 1.20


def read_files_to_df(
    stok_filename,
    kargo_filename,
    ticimax_filename,
    urunMarketYerleriKategorileri,
    marketyeriKomisyonlari,
):
    kargo_data = pd.read_excel(kargo_filename)
    try:
        stok_data = pd.read_excel(stok_filename)
    except Exception:
        stok_data = pd.read_csv(stok_filename, sep=";")
    ticimax_data = pd.read_excel(ticimax_filename)
    market_place_categories = pd.read_excel(urunMarketYerleriKategorileri)
    n11_categories = pd.read_excel(marketyeriKomisyonlari, sheet_name=N11)
    hepsiburada_categories = pd.read_excel(
        marketyeriKomisyonlari, sheet_name=HEPSIBURADA
    )
    pttavm_categories = pd.read_excel(marketyeriKomisyonlari, sheet_name=PTTAVM)
    trendyol_categories = pd.read_excel(marketyeriKomisyonlari, sheet_name=TRENDYOL)
    return (
        kargo_data,
        stok_data,
        ticimax_data,
        market_place_categories,
        n11_categories,
        hepsiburada_categories,
        pttavm_categories,
        trendyol_categories,
    )


def process_price_data(dolar_kuru, price_str):
    if "₺" in price_str:
        price = price_str.replace("₺", "").strip()
        price = price.replace(",", ".")
        price = float(price)
        return price
    if "$" in price_str:
        price = price_str.replace("$", "").strip()
        price = price.replace(",", ".")
        price = float(price) * dolar_kuru
        return price
    return 0


def process_stock_data(stok_data_lst, dolar_kuru):
    result = {}
    for stok_data in stok_data_lst:
        new_stok = dict()
        new_stok[BARKOD] = stok_data[BARKOD]
        new_stok["Miktar"] = stok_data["Miktar"]
        prices = [0]
        for i in [1, 3]:
            field_name = f"L.Fiy. {i}"
            if not stok_data[field_name].startswith("0,00"):
                stok_data[field_name] = process_price_data(
                    dolar_kuru, stok_data[field_name]
                )
                prices.append(stok_data[field_name])
            new_stok["Price"] = max(prices)
        result[new_stok[BARKOD]] = new_stok
    return result


def calculate_market_place_commission(
    satis_fiyati, desi, kargo_data, categories, stock_market_place_category, fieldName
):
    son_fiyat = (satis_fiyati + kargo_data.iloc[desi + 1][fieldName]) * KDV
    category = stock_market_place_category.iloc[0][fieldName]
    total_percentage = categories.iloc[3][category]
    total_fix_cost = categories.iloc[4][category]
    cost = (son_fiyat * total_percentage) / 100 + total_fix_cost
    return math.ceil(son_fiyat + cost)


def assign_stock_brackets(stock_num):
    if stock_num > 500:
        stock_num = math.floor(stock_num * 0.1)  # 10% of the stock
    elif stock_num > 100:
        stock_num = 20
    elif stock_num > 50:
        stock_num = 5
    elif stock_num > 10:
        stock_num = 3
    elif stock_num > 1:
        stock_num = 1
    else:
        stock_num = stock_num
    return stock_num


def main(
    stok,
    kargo,
    ticimax,
    dolar_kuru,
    urunMarketYerleriKategorileri,
    marketyeriKomisyonlari,
    website_comission,
    market_place_commission,
    output,
):
    """
    This function does something with the stok and kargo arguments.
    """
    (
        kargo_data_df,
        stok_data_df,
        ticimax_data_df,
        market_place_categories,
        n11_categories,
        hepsiburada_categories,
        pttavm_categories,
        trendyol_categories,
    ) = read_files_to_df(
        stok, kargo, ticimax, urunMarketYerleriKategorileri, marketyeriKomisyonlari
    )
    stok_data_df = stok_data_df.loc[
        :,
        [
            STOK_KODU,
            "L.Fiy. 1",
            "L.Fiy. 3",
            "Miktar",
        ],
    ]

    if STOK_KODU in stok_data_df.columns:
        stok_data_df = stok_data_df.rename(columns={STOK_KODU: BARKOD})
    stok_data_df[BARKOD] = stok_data_df[BARKOD].astype(str)
    ticimax_data_df[BARKOD] = ticimax_data_df[BARKOD].astype(str)
    market_place_categories[BARKOD] = market_place_categories[BARKOD].astype(str)
    stok_data = stok_data_df[stok_data_df[BARKOD].isin(ticimax_data_df[BARKOD])]
    stok_data_lst = stok_data.to_dict("records")
    stok_data_dict = process_stock_data(stok_data_lst, dolar_kuru)

    ticimax_data_lst = ticimax_data_df.to_dict("records")

    website_commission = 1 + website_comission / 100
    market_place_comission = 1 + market_place_commission / 100

    for ticimax_data in ticimax_data_lst:
        new_stok = stok_data_dict.get(ticimax_data[BARKOD])
        stock_market_place_category = market_place_categories[
            market_place_categories[BARKOD] == ticimax_data[BARKOD]
        ]
        ticimax_data[HATA_KODU] = ""
        if new_stok is None:
            ticimax_data[STOKADEDI] = -1
            ticimax_data[
                HATA_KODU
            ] = "Stok bulunamadi: --stok argumani ile verdigin dosyadaki stok kodlari ile ticimax barkod kodlari eslesmedi"
            continue
        if new_stok["Price"] == 0:
            ticimax_data[STOKADEDI] = -1
            ticimax_data[
                HATA_KODU
            ] = "Fiyat bulunamadi: --stok argumani ile verdigin dosyadaki fiyatlar dogru girilmemis"
            continue
        if stock_market_place_category.empty:
            ticimax_data[STOKADEDI] = -1
            ticimax_data[
                HATA_KODU
            ] = "Dogru kategori bulunamadi: --urunMarketYerleriKategorileri argumani ile verdigin dosyadaki kategoriler dogru girilmemis"
            continue

        website_price = math.ceil(new_stok["Price"] * website_commission * KDV)
        market_place_price_before_tax = math.ceil(
            new_stok["Price"] * market_place_comission
        )

        ticimax_data[STOKADEDI] = assign_stock_brackets(new_stok["Miktar"])
        desi = math.ceil(ticimax_data[KARGOAGIRLIGI])
        ticimax_data["SATISFIYATI"] = website_price
        ticimax_data["UYETIPIFIYAT1"] = calculate_market_place_commission(
            market_place_price_before_tax,
            desi,
            kargo_data_df,
            n11_categories,
            stock_market_place_category,
            N11,
        )
        ticimax_data["UYETIPIFIYAT2"] = calculate_market_place_commission(
            market_place_price_before_tax,
            desi,
            kargo_data_df,
            hepsiburada_categories,
            stock_market_place_category,
            HEPSIBURADA,
        )
        ticimax_data["UYETIPIFIYAT3"] = calculate_market_place_commission(
            market_place_price_before_tax,
            desi,
            kargo_data_df,
            trendyol_categories,
            stock_market_place_category,
            TRENDYOL,
        )
        ticimax_data["UYETIPIFIYAT4"] = calculate_market_place_commission(
            market_place_price_before_tax,
            desi,
            kargo_data_df,
            pttavm_categories,
            stock_market_place_category,
            PTTAVM,
        )

    ticimax_data = pd.DataFrame(ticimax_data_lst)

    ticimax_data = ticimax_data.sort_values(by=STOKADEDI, ascending=True)
    ticimax_data.to_excel(output, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # parser.add_argument("--stok", help="stock argument", default="stokListesi.xlsx")
    parser.add_argument("--stok", help="stock argument", default="sinirli_stoklar.csv")
    parser.add_argument("--kargo", help="cargo argument", default="kargoBilgileri.xlsx")
    parser.add_argument(
        "--ticimax", help="ticimax argument", default="TicimaxExport.xls"
    )
    parser.add_argument(
        "--marketyeriKomisyonlari",
        help="market yeri komisyonlari",
        default="MarketyeriKomisyonlari.xlsx",
    )
    parser.add_argument(
        "--urunMarketYerleriKategorileri",
        help="urunMarketYerleriKategorileri",
        default="UrunMarketYerleriKategorileri.xlsx",
    )
    parser.add_argument("--dolar_kuru", help="ticimax argument", default=30, type=float)
    parser.add_argument("--site_komisyonu", help="site komisyonu", default=15, type=int)
    parser.add_argument(
        "--market_yeri_ekstra_komisyon",
        help="marketyeri komisyonu",
        default=5,
        type=int,
    )
    parser.add_argument(
        "--output", help="output argument", default="TicimaxExport_updated.xlsx"
    )
    args = parser.parse_args()
    main(
        args.stok,
        args.kargo,
        args.ticimax,
        args.dolar_kuru,
        args.urunMarketYerleriKategorileri,
        args.marketyeriKomisyonlari,
        args.site_komisyonu,
        args.market_yeri_ekstra_komisyon,
        args.output,
    )
