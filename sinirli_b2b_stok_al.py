#!/usr/bin/env python
import requests
from xml.etree import ElementTree as ET
import csv
import time
import concurrent.futures
import logging

logging.basicConfig(level=logging.INFO)


# Set the URL of the API endpoint
# Set the username and password for basic authentication
username = "botsinirli"
password = "KFAKsgjxseLV57"
step_size = 100000
last_product = 340000
first_product = 0
thread_count = 1
timeout = 60
retry_count = 3
sleep_time = 10


def get_list_price(details):
    price = details["ListPriceWoVAT"]
    currency_type = details["ListPriceCurrency"]

    if currency_type == "USD":
        currency = "$"
    elif currency_type == "TLY":
        # currency = "\u20BA"
        currency = "₺"
    elif currency_type == "EUR":
        currency = "€"
    return f"{price} {currency}"


def fetch_products(start, end):
    def _fetch_products(start, end):
        session = requests.Session()
        session.auth = (username, password)
        url = f"http://denoto.sistemyazilim.com:4033/XmlService/GetAllProductsByParts/{start}/{end}"
        logging.info("Fetching products from %s to %s", start, end)
        response = session.get(url, timeout=timeout)
        if response.status_code != 200:
            raise Exception(f"Error : {response.status_code}")
        xml_str = response.content.decode("utf-8-sig")
        root = ET.fromstring(xml_str)
        products = root.findall(".//Product")
        session.close()
        product_map = {}
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

            product_map[product_details["ID"]] = product_details

            row_names = row_names.union(product_details.keys())
        return product_map, row_names

    for i in range(retry_count):
        try:
            return _fetch_products(start, end)
        except Exception as e:
            logging.debug(f"Error {start} - {end}: {e}")
            time.sleep(sleep_time * i)
            continue
    logging.warning(f"No data for {start} - {end}")
    return dict(), set()


def main():
    start_time = time.time()
    # Create a session with basic authentication

    futures = []
    row_names = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
        # Submit the fetch_products function for each iteration
        for i in range(first_product, last_product, step_size):
            next_step = i + step_size
            if next_step > last_product:
                next_step = last_product
            future = executor.submit(fetch_products, i, next_step)
            futures.append(future)

    # Wait for all futures to complete and get the results
    product_dict = {}
    for future in concurrent.futures.as_completed(futures):
        result_dict, row_names = future.result()
        product_dict.update(result_dict)

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
    product_list = sorted(
        product_dict.values(), key=lambda x: x["Miktar"], reverse=True
    )
    result_product_list = []
    for product in product_list:
        result_product = {}
        for key in row_names:
            if key not in product:
                product[key] = ""
            result_product[key] = product[key]
        result_product_list.append(result_product)

    with open(
        "tum_stoklar.csv",
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
