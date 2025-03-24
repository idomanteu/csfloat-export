"""
csfloat trades exporter

this script fetches trade data from csfloat api and exports it to csv files.
it creates two csv files:
- csfloat_purchases.csv: contains purchases (buyer role)
- csfloat_sales.csv: contains sales (seller role)

each csv contains the following columns:
- item name
- price
- float
- type
- date bought/sold
- csfloat transaction id

created by @loz.tf (Discord))
"""

import csv
import os
import time
import asyncio
import aiohttp
from datetime import datetime
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

load_dotenv()

# constants
STEAM_ID = os.getenv('STEAM_ID')
API_KEY = os.getenv('API_KEY')
RATE_LIMIT = 120  # wait 2 minutes between api requests :)


def safe_float(value, default=None) -> Optional[float]:
    """float conversion"""
    try:
        if value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def format_price(price_in_cents: int, is_sale: bool = False) -> float:
    """
    convert price from cents to dollars
    
    args:
    - price_in_cents: price in cents
    - is_sale: if true, applies csfloat 2% fee to the price
    """
    try:
        if price_in_cents is None:
            return 0.0
        # convert cents to dollars
        price = round(price_in_cents / 100, 2)
        # apply 2% fee reduction for sales
        if is_sale:
            price = round(price * 0.98, 2)  # csfloat takes 2% fee
        return price
    except (ValueError, TypeError):
        return 0.0


async def fetch_csfloat_trades(api_key: str, role: str = "buyer") -> List[Dict]:
    """
    fetch all trades from csfloat api
    
    args:
    - api_key: csfloat api key
    - role: 'buyer' or 'seller'
        
    returns:
    - list of trade objects
    """
    page = 0
    all_trades = []
    last_request_time = 0
    
    async with aiohttp.ClientSession() as session:
        while True:
            # don't want to make too many requests; still a reasonable run time
            current_time = time.time()
            time_since_last_request = current_time - last_request_time
            
            if time_since_last_request < RATE_LIMIT:
                wait_time = RATE_LIMIT - time_since_last_request
                print(f"waiting {wait_time:.2f} seconds before next api request")
                await asyncio.sleep(wait_time)
            
            last_request_time = time.time()
            
            try:
                print(f"fetching {role} trades page {page}")
                async with session.get(
                    f'https://csfloat.com/api/v1/me/trades?role={role}&state=verified&limit=500&page={page}',
                    headers={'Authorization': api_key}
                ) as response:
                    if response.status != 200:
                        print(f"api request failed with status code {response.status}: {await response.text()}")
                        break
                    
                    data = await response.json()
                    trades = data.get('trades', [])
                    
                    if not trades:
                        print(f"no more {role} trades found")
                        break
                    
                    all_trades.extend(trades)
                    
                    # stop if we've reached the end of the trades
                    if len(trades) < 500:
                        print(f"end of {role} trades")
                        break
                    
                    page += 1
                
            except Exception as e:
                print(f"error fetching {role} trades: {str(e)}")
                break
    
    return all_trades


def process_trades(trades: List[Dict], role: str) -> List[Dict]:
    """
    process trades into a simplified format for csv export
    
    args:
    - trades: list of trade objects from csfloat api
    - role: 'buyer' or 'seller'
        
    returns:
    - list of simplified trade objects
    """
    processed_trades = []
    
    for trade in trades:
        # check if this is a valid trade for our steam id
        if role == "buyer" and trade.get('buyer', {}).get('steam_id') != STEAM_ID:
            continue
        if role == "seller" and trade.get('seller', {}).get('steam_id') != STEAM_ID:
            continue
        
        # skip trades that aren't verified
        if trade.get('state') != "verified":
            continue
        
        # get contract data
        contract = trade.get('contract', {})
        item = contract.get('item', {})
        
        # get date (accepted_at or verified_at)
        date_str = trade.get('accepted_at')
        if not date_str:
            date_str = trade.get('verified_at')
        
        # skip if we can't find a date
        if not date_str:
            continue
        
        # parse the date and format as yyyy-mm-dd
        try:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            formatted_date = date.strftime('%Y-%m-%d')
        except ValueError:
            if 'T' in date_str:
                formatted_date = date_str.split('T')[0]
            else:
                formatted_date = date_str[:10]  # just take first 10 characters (yyyy-mm-dd)
        
        # get item type
        item_type = item.get('type_name', 'Unknown')
        
        # extract the data we want
        processed_trade = {
            'item_name': item.get('market_hash_name', 'Unknown'),
            'price': format_price(contract.get('price'), is_sale=(role == "seller")),  # Apply fee for sales
            'float': safe_float(item.get('float_value')),
            'type': item_type,
            'date': formatted_date,
            'id': trade.get('id', '')
        }
        
        processed_trades.append(processed_trade)
    
    # sort by date (ascending)
    processed_trades.sort(key=lambda x: x['date'])
    
    return processed_trades


def export_to_csv(trades: List[Dict], filename: str):
    """
    export trades to a csv file
    
    args:
    - trades: list of simplified trade objects
    - filename: output csv filename
    """
    # define csv fieldnames (column headers)
    fieldnames = ['item_name', 'price', 'float', 'type', 'date', 'id']
    
    # write to csv
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # write headers with nice formatting
        writer.writerow({
            'item_name': 'Item Name',
            'price': 'Price',
            'float': 'Float',
            'type': 'Type',
            'date': 'Date',
            'id': 'CSFloat Transaction ID'
        })
        
        # write data rows
        writer.writerows(trades)
    
    print(f"successfully exported {len(trades)} trades to {filename}")


async def async_main():
    """async main entry point"""
    # get api key from environment
    if not API_KEY:
        print("error: csfloat_api_key not found in environment variables")
        print("please create a .env file with your api key or set it as an environment variable")
        return
    
    # fetch purchases (buyer role)
    purchase_trades = await fetch_csfloat_trades(API_KEY, role="buyer")
    print(f"found {len(purchase_trades)} purchases")
    
    # process purchases
    processed_purchases = process_trades(purchase_trades, role="buyer")
    print(f"processed {len(processed_purchases)} valid purchases")
    
    # export purchases to csv
    export_to_csv(processed_purchases, "csfloat_purchases.csv")
    
    # Introduce a delay before fetching sales
    await asyncio.sleep(RATE_LIMIT)  # Wait for the rate limit duration
    
    # fetch sales (seller role)
    sale_trades = await fetch_csfloat_trades(API_KEY, role="seller")
    print(f"found {len(sale_trades)} sales")
    
    # process sales
    processed_sales = process_trades(sale_trades, role="seller")
    print(f"processed {len(processed_sales)} valid sales")
    
    # export sales to csv
    export_to_csv(processed_sales, "csfloat_sales.csv")
    
    print("done! :)")


if __name__ == "__main__":
    asyncio.run(async_main())
