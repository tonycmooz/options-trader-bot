import pandas as pd
import numpy as np
import requests
import logging
import robin_stocks as r  # If using Robinhood

logging.basicConfig(level=logging.INFO)

# Authenticate with your broker
# Example API Authentication with the popular Robinhood App

username = 'your_username'
password = 'your_password'

r.authentication.login(username=username, password=password)


def get_historical_prices(symbol, interval, span):
    historical_data = r.get_stock_historicals(symbol, interval=interval, span=span)
    df = pd.DataFrame(historical_data)
    df['begins_at'] = pd.to_datetime(df['begins_at'])
    df.set_index('begins_at', inplace=True)
    df = df[['close_price', 'high_price', 'low_price', 'open_price', 'volume']]
    df = df.astype(float)
    return df

def get_option_chain(symbol, expiration_date=None):
    if expiration_date:
        return r.options.get_options_for_stock(symbol, expirationDate=expiration_date)
    else:
        return r.options.get_options_for_stock(symbol)

## TODO
def get_volatility_data(symbol):
    return r.options.get_stock_option_market_data(symbol)

def place_order(option_id, order_type, quantity, price=None):
    if order_type == 'limit':
        return r.options.place_limit_order(option_id, 'buy', quantity, price)
    elif order_type == 'market':
        return r.options.place_market_order(option_id, 'buy', quantity)

def modify_order(order_id, new_price):
    return r.options.modify_order(order_id, new_price)

def cancel_order(order_id):
    return r.options.cancel_order(order_id)


def select_higher_strike_price(options, distance=2):
    """
    This function finds strike prices that are a fixed distance away from the 
    current underlying asset price. You can adjust the distance parameter 
    to control how far away the selected strike prices should be.
    """
    underlying_price = float(r.stocks.get_latest_price(options[0]['chain_symbol'])[0])
    target_strike = underlying_price + distance

    for option in options:
        strike_price = float(option['strike_price'])
        if strike_price >= target_strike:
            return strike_price

    return float(options[-1]['strike_price'])


def select_lower_strike_price(options, distance=2):
    """
    This function finds strike prices that are a fixed distance away from the 
    current underlying asset price. You can adjust the distance parameter 
    to control how far away the selected strike prices should be.
    """
    underlying_price = float(r.stocks.get_latest_price(options[0]['chain_symbol'])[0])
    target_strike = underlying_price - distance

    for option in options[::-1]:  # Iterate in reverse order
        strike_price = float(option['strike_price'])
        if strike_price <= target_strike:
            return strike_price

    return float(options[0]['strike_price'])


def get_option_id(options, target_strike_price):
    """
    This function searches the provided list of option contracts and returns 
    the ID of the option with the target strike price. If no such option is 
    found, it returns None

    You may customize these functions based on your specific strategy 
    requirements, such as selecting strike prices based on delta, 
    implied volatility, or other criteria.
    """
    for option in options:
        strike_price = float(option['strike_price'])
        if strike_price == target_strike_price:
            return option['id']

    return None

def bull_call_spread(symbol, expiration_date):
    """
    This strategy involves simultaneously buying and selling call options with 
    the same expiration date but different strike prices. The purpose of this 
    strategy is to profit from a moderate increase in the price of the 
    underlying asset while limiting the risk and capital required.
    """
    # Get call options
    option_chain = get_option_chain(symbol, expiration_date)
    call_options = [option for option in option_chain if option['type'] == 'call']

    # Buy a call option with a lower strike price
    lower_strike_price = select_lower_strike_price(call_options)
    lower_option_id = get_option_id(call_options, lower_strike_price)
    buy_lower_order = place_order(lower_option_id, 'buy', 1)
    logging.info(f"Buy call option with a lower strike price ({lower_strike_price}) on {symbol} - Order ID: {buy_lower_order['id']}")

    # Sell a call option with a higher strike price
    higher_strike_price = select_higher_strike_price(call_options)
    higher_option_id = get_option_id(call_options, higher_strike_price)
    sell_higher_order = place_order(higher_option_id, 'sell', 1)
    logging.info(f"Sell call option with a higher strike price ({higher_strike_price}) on {symbol} - Order ID: {sell_higher_order['id']}")

def bear_put_spread(symbol, expiration_date):
    """
    This bear put spread strategy involves buying a put option with a 
    higher strike price and selling a put option with a lower strike price 
    on the same underlying asset with the same expiration date. 
    
    This strategy is suitable for a moderately bearish market outlook and profits from a 
    decline in the underlying asset's price.
    """
    # Get put options
    option_chain = get_option_chain(symbol, expiration_date)
    put_options = [option for option in option_chain if option['type'] == 'put']

    # Buy a put option with a higher strike price
    higher_strike_price = select_higher_strike_price(put_options)
    higher_option_id = get_option_id(put_options, higher_strike_price)
    buy_order = place_order(higher_option_id, 'buy', 1)
    logging.info(f"Buy put option with a higher strike price ({higher_strike_price}) on {symbol} - Order ID: {buy_order['id']}")

    # Sell a put option with a lower strike price
    lower_strike_price = select_lower_strike_price(put_options)
    lower_option_id = get_option_id(put_options, lower_strike_price)
    sell_order = place_order(lower_option_id, 'sell', 1)
    logging.info(f"Sell put option with a lower strike price ({lower_strike_price}) on {symbol} - Order ID: {sell_order['id']}")
