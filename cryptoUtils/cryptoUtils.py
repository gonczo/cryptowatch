#!/usr/bin/env python
# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2017 Alex Epstein
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json
from datetime import datetime
from sys import platform
from os import system

try:
    import requests
except ImportError:
    raise ImportError("Error: no requests module found, install it with pip")
try:
    from terminaltables import AsciiTable
except ImportError:
    raise ImportError("Error: no terminaltables module found, install it with pip")

import cryptoUtils.cwconfig as cfg

config = cfg.config()

"""
Parameter url: url to request
Output: JSON ready response from the server
Logic:
    - Request the url
    - Check for successful status code from server
    - Return the JSON response
"""
def request(url):
    response = requests.get(url)
    if response.status_code != 200 and response.status_code != 500 and response.status_code != 404:
        raise Exception('Error: requesting the api resulted in status code %s' %
                        response.status_code)
    return response.text


"""
Output: Clears the terminal
Logic:
    - We just want to know how to clear the terminal
    - Check the platform type
    - Clear the terminal in the right way
"""
def clear():
    if platform == "linux" or platform == "linux2" or platform == "darwin":
        system("clear")
    elif platform == "win32":
        system("cls")
    else:
        print("Uh-oh you are using an unsported system :/")


"""
Output: Total crypto across all addresses in the config class
Parameters:
    - Cointype: Which coin do you want the total crypto for
Logic:
    - Start with 0 total crypto
    - For every address
        - Request respective api for balance
        - Add this balance to the total crypto
    - Return the total crypto
"""
def getTotalCrypto(coinType):
    totalCrypto = 0.0
    if coinType is "bitcoin":
        for address in config.bitcoinAddress:
            url =  url = "https://blockchain.info/rawaddr/" + address
            response = json.loads(request(url))
            totalCrypto += float(response['final_balance']) / pow(10, 8)
    elif coinType is "ethereum":
        etherscanAPIKey = "V8ENE44FM98SCDPIXGGHQDFD2KCRSKJ8BJ"
        for address in config.etherAddress:
            url = "http://api.etherscan.io/api?module=account&action=balance&address=" + \
            address + "&tag=latest&apikey=" + etherscanAPIKey
            response = json.loads(request(url))
            totalCrypto += float(response['result']) / pow(10, 18)
    elif coinType is "litecoin":
        for address in config.litecoinAddress:
            url = url = "https://chain.so/api/v2/get_address_balance/LTC/" + address
            response = json.loads(request(url))
            totalCrypto += float(response['data']['confirmed_balance'])
    return totalCrypto



"""
Output: Array of metrics related to the respective coin type
Parameters
    - Cointype: query coinmarketcap about this specified cointype
Logic:
    - Request info from coinmarket cap
    - Ready the response for JSON parsing
    - Parse the response and append each peice of info to the metrics array
    - Return the metrics array
"""
def getCryptoInfo(coinType):
    metrics = []
    coinTypes = ["bitcoin", "ethereum", "litecoin"]
    if coinType not in coinTypes:
        raise ValueError("Invalid coinType")
    url = "https://api.coinmarketcap.com/v1/ticker/" + coinType + "/?convert=" + config.fiatCurrency
    response = json.loads(request(url))
    metrics.append(response[0]['price_' + config.fiatCurrency.lower()])
    metrics.append(response[0]['24h_volume_' + config.fiatCurrency.lower()])
    metrics.append(response[0]['percent_change_7d'])
    metrics.append(response[0]['percent_change_24h'])
    metrics.append(response[0]['percent_change_1h'])
    totalCrypto = getTotalCrypto(coinType)
    metrics.append(totalCrypto)
    metrics.append(totalCrypto*float(response[0]['price_' + config.fiatCurrency.lower()]))
    return metrics


"""
Output: Returns an ascii table for all cryptocurrencies and their data
Parameters:
    - clearConsole: Do we want to clear the console before returning this data (we do want to do this when running in monitor mode)
Logic:
    - Create header
    - Get metrics on each legal currency and insert into their own array
    - Get the total fiat by adding the last index of each metrics array together
    - Insert cointypes into the respective array
    - Combine the header and the crypoto metrics into one big metrics array
    - Create the ascii table from this data
    -
"""
def getCryptoData(clearConsole=False):
    header = ["Coin Type","Price " + config.fiatCurrency, "24h Volume", "7d % Change", "24h % Change", "1h % Change", "Total Crypto Balance", "Total " + config.fiatCurrency]
    #coinTypes = ["Bitcoin", "Ethereum", "Litecoin"]
    metrics = []
    bitcoinMetrics = getCryptoInfo("bitcoin")
    ethereumMetrics = getCryptoInfo("ethereum")
    litecoinMetrics = getCryptoInfo("litecoin")
    totalFiat = bitcoinMetrics[-1] + ethereumMetrics[-1] + litecoinMetrics[-1]
    bitcoinMetrics.insert(0, "Bitcoin")
    ethereumMetrics.insert(0, "Ethereum")
    litecoinMetrics.insert(0, "Litecoin")
    metrics.append(header)
    metrics.append(bitcoinMetrics)
    metrics.append(ethereumMetrics)
    metrics.append(litecoinMetrics)
    table = AsciiTable(metrics)
    footer = "Last Updated: %s \t\t\t\t\t\t\t\tTotal %s: %.2f" % (str(datetime.now()), config.fiatCurrency, totalFiat)
    if clearConsole:
        clear()
    return table.table + "\n" + footer
