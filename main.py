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


def read_files_to_df(stok_filename, kargo_filename, ticimax_filename):
    kargo_data = pd.read_excel(kargo_filename)
    stok_data = pd.read_excel(stok_filename)
    ticimax_data = pd.read_excel(ticimax_filename)
    return kargo_data, stok_data, ticimax_data


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


def process_stock_data(stok_data_lst):
    result = {}
    for stok_data in stok_data_lst:
        new_stok = dict()
        new_stok["BARKOD"] = stok_data["BARKOD"]
        for i in [1, 3]:
            field_name = f"L.Fiy. {i}"
            if stok_data[field_name] != "0,00 ₺":
                new_stok["Price"] = stok_data[field_name]
        if new_stok.get("Price") is None:
            new_stok["Price"] = ""
        result[new_stok["BARKOD"]] = new_stok
    return result


def main(stok, kargo, ticimax, dolar_kuru, output):
    """
    This function does something with the stok and kargo arguments.
    """
    kargo_data, stok_data, ticimax_data = read_files_to_df(stok, kargo, ticimax)
    stok_data = stok_data.loc[
        :,
        [
            "Stok Kodu",
            "L.Fiy. 1",
            "L.Fiy. 3",
        ],  # ["Stok Kodu", "L.Fiy. 1", "L.Fiy. 2", "L.Fiy. 3", "L.Fiy. 4", "L.Fiy. 5"]
    ]
    stok_data = stok_data.rename(columns={"Stok Kodu": "BARKOD"})
    stok_data = stok_data[stok_data["BARKOD"].isin(ticimax_data["BARKOD"])]
    stok_data_lst = stok_data.to_dict("records")
    stok_data_dict = process_stock_data(stok_data_lst)

    ticimax_data_lst = ticimax_data.to_dict("records")

    for ticimax_data in ticimax_data_lst:
        new_stok = stok_data_dict.get(ticimax_data["BARKOD"])
        if new_stok is None:
            ticimax_data["STOKADEDI"] = -1
            continue
        new_stok["Price"] = process_price_data(dolar_kuru, new_stok["Price"])
        if new_stok["Price"] == 0:
            ticimax_data["STOKADEDI"] = -1
            continue
        desi = math.ceil(ticimax_data["KARGOAGIRLIGI"])
        ticimax_data["SATISFIYATI"] = new_stok["Price"] * 1.15 * 1.20
        ticimax_data["UYETIPIFIYAT1"] = (
            new_stok["Price"] + kargo_data.loc[desi + 1]["N11"]
        ) * 1.20
        ticimax_data["UYETIPIFIYAT2"] = (
            new_stok["Price"] + kargo_data.loc[desi + 1]["Hepsiburada"]
        ) * 1.20
        ticimax_data["UYETIPIFIYAT3"] = (
            new_stok["Price"] + kargo_data.loc[desi + 1]["Trendyol"]
        ) * 1.20
        ticimax_data["UYETIPIFIYAT4"] = (
            new_stok["Price"] + kargo_data.loc[desi + 1]["PTTAvm"]
        ) * 1.20

    ticimax_data = pd.DataFrame(ticimax_data_lst)
    ticimax_data.to_excel(output, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stok", help="stock argument", default="stock_list.xlsx")
    parser.add_argument(
        "--kargo", help="cargo argument", default="kargo_bilgileri.xlsx"
    )
    parser.add_argument(
        "--ticimax", help="ticimax argument", default="TicimaxExport.xls"
    )
    parser.add_argument(
        "--dolar_kuru", help="ticimax argument", default=28.66, type=float
    )
    parser.add_argument(
        "--output", help="output argument", default="TicimaxExport_updated.xlsx"
    )
    args = parser.parse_args()
    main(args.stok, args.kargo, args.ticimax, args.dolar_kuru, args.output)
