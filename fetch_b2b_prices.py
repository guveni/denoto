#!/usr/bin/env python
import requests
from xml.etree import ElementTree as ET
import io


# Set the URL of the API endpoint
url = "http://denoto.sistemyazilim.com:4033/XmlService/GetAllProductsByParts/0/1000"

# Set the username and password for basic authentication
username = "gvn"
password = "KFAKsgjxseLV57"

# Create a session with basic authentication
session = requests.Session()
session.auth = (username, password)

# Make the GET request
response = session.get(url)

# Check the response status code
if response.status_code != 200:
    print("Error:", response.status_code)
    exit()

xml_str = response.content.decode("utf-8-sig")
# Process the data as XML
root = ET.fromstring(xml_str)

for product in root.iter("Product"):
    product_code = product.find(
        "ProductCode"
    ).text  # Replace 'ProductCode' with the actual tag name
    image_url = f"http://denoto.sistemyazilim.com:4033/XmlService/DownloadProductImage/ByCode/{product_code}"
    response = requests.get(image_url, stream=True)
    if response.status_code == 200:
        print(response)
