#!/usr/bin/env python
import requests
from xml.etree import ElementTree as ET
import csv
import time
import concurrent.futures


# Set the URL of the API endpoint
# Set the username and password for basic authentication
username = "gvn"
password = "KFAKsgjxseLV57"
step_size = 1000
last_product = 330000
thread_count = 50


def get_list_price(details):
    price = details["ListPriceWoVAT"]
    currency_type = details["ListPriceCurrency"]

    if currency_type == "USD":
        currency = "$"
    elif currency_type == "TLY":
        # currency = "\u20BA"
        currency = "₺"
    return f"{price} {currency}"


def fetch_products(start, end):
    session = requests.Session()
    session.auth = (username, password)
    url = f"http://denoto.sistemyazilim.com:4033/XmlService/GetAllProductsByParts/{start}/{end}"
    print(f"Fetching products from {start} to {end}")
    response = session.get(url)
    if response.status_code != 200:
        print("Error:", response.status_code)
        return []
    xml_str = response.content.decode("utf-8-sig")
    root = ET.fromstring(xml_str)
    products = root.findall(".//Product")
    product_list = []
    row_names = set()
    for product in products:
        product_details = {}
        for child in product:
            if child.tag in ["Pricing", "Stocks"]:
                continue
            result = child.text
            if child.text is not None:
                result = child.text.strip()
            else:
                result = ""
            product_details[child.tag] = result
        for child in product.find("Pricing"):
            product_details[child.tag] = child.text.strip()
        stock_list = []
        stocks = product.find("Stocks")
        for stock in stocks:
            attr = stock.attrib["WarehouseID"]
            product_details[f"stock_{attr}"] = int(stock.text.strip())
            stock_list.append(product_details[f"stock_{attr}"])
            product_details["Miktar"] = max(stock_list)
        product_details["L.Fiy. 1"] = get_list_price(product_details)
        product_details["L.Fiy. 3"] = get_list_price(product_details)
        product_details.update(product.attrib)
        product_details["Stok Kodu"] = str(product_details["ProductCode"])
        product_list.append(product_details)
        row_names = row_names.union(product_details.keys())
    return product_list, row_names


def main():
    start_time = time.time()
    # Create a session with basic authentication

    product_list = []
    futures = []
    row_names = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
        # Submit the fetch_products function for each iteration
        for i in range(0, last_product, step_size):
            future = executor.submit(fetch_products, i, i + step_size)
            futures.append(future)

    # Wait for all futures to complete and get the results
    product_list = []
    for future in concurrent.futures.as_completed(futures):
        result, row_names = future.result()
        product_list.extend(result)

        # Sort the product list

    row_names = row_names - set(
        [
            "Discount1",
            "Discount6",
            "New",
            "Category",
            "MinOrderAmount",
            "RivalNrs",
            "Unit",
            "Discount3",
            "InDiscount",
            "Discount4",
            "CurrencyRate",
            "Barcodes",
            "OeNrs",
            "Discount5",
            "CompatibleVehicleModels",
            "ProductNames",
            "Discount2",
            "ProductImages",
            "stock_1",
            "stock_2",
            "LocalListPriceWVat",
            "BrandID",
            "LocalNetPriceWoVat",
            "LocalNetPriceWVat",
            "BaseOeNr",
            "PiecesInBox",
            "ListPriceCurrency",
            "LocalCurrency",
            "ListPriceWoVAT",
            "LocalListPriceWoVat",
        ]
    )
    product_list = sorted(product_list, key=lambda x: x["Miktar"], reverse=True)
    result_product_list = []
    for product in product_list:
        result_product = {}
        for key in row_names:
            if key not in product:
                product[key] = ""
            result_product[key] = product[key]
        result_product_list.append(result_product)

    with open(
        "product_list.csv",
        "w",
        newline="",
        encoding="utf-8",
    ) as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=row_names,
            delimiter=";",
        )
        writer.writeheader()
        writer.writerows(result_product_list)

    end_time = time.time()
    # Calculate the duration
    duration = end_time - start_time

    print(f"The script took {duration} seconds to run.")


if __name__ == "__main__":
    main()
