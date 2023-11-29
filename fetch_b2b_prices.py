#!/usr/bin/env python
import requests
from xml.etree import ElementTree as ET
import csv
import time


def get_list_price(details):
    price = details["ListPriceWoVAT"]
    currency_type = details["ListPriceCurrency"]

    if currency_type == "USD":
        currency = "$"
    elif currency_type == "TLY":
        # currency = "\u20BA"
        currency = "₺"
    return f"{price} {currency}"


# Set the URL of the API endpoint
# Set the username and password for basic authentication
username = "gvn"
password = "KFAKsgjxseLV57"
step_size = 1000


start_time = time.time()
# Create a session with basic authentication
session = requests.Session()
session.auth = (username, password)

product_list = []
row_names = set()
for i in range(0, 350000, step_size):
    url = f"http://denoto.sistemyazilim.com:4033/XmlService/GetAllProductsByParts/{i}/{i+step_size}"
    # Make the GET request
    response = session.get(url)

    # Check the response status code
    if response.status_code != 200:
        print("Error:", response.status_code)
        exit()

    xml_str = response.content.decode("utf-8-sig")
    # Process the data as XML
    root = ET.fromstring(xml_str)

    products = root.findall(".//Product")
    # Extract the details of each product into a list

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
product_list = sorted(product_list, key=lambda x: x["Miktar"])
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
