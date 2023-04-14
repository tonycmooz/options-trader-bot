import pandas as pd
import numpy as np
import requests
import logging
import robin_stocks as r  # Unofficial API, if using Robinhood

logging.basicConfig(level=logging.INFO)

"""
Authenticate with your broker
Example API Authentication with the popular Robinhood App
This Robinhood API is not officially supported. 
USE CAUTION WHEN PLACING REAL TRADES.
"""

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

def select_atm_strike_price(options):
    """
    This function selects the At-the-Money (ATM) strike price based on the 
    current price of the underlying asset. 

    This function takes a list of option contracts as input and calculates 
    the strike price that is closest to the current price of the underlying asset. 
    It returns the strike price that has the smallest absolute difference with 
    the underlying asset price. This strike price is considered the At-the-Money 
    strike price.

    (You might want to modify this function based on your specific requirements,
    such as choosing the nearest Out-of-the-Money or In-the-Money strike price.
    """
    underlying_price = float(r.stocks.get_latest_price(options[0]['chain_symbol'])[0])

    closest_strike_price = float(options[0]['strike_price'])
    min_difference = abs(underlying_price - closest_strike_price)

    for option in options[1:]:
        strike_price = float(option['strike_price'])
        difference = abs(underlying_price - strike_price)

        if difference < min_difference:
            min_difference = difference
            closest_strike_price = strike_price

    return closest_strike_price

def bullish_calendar_spread_calls(symbol, near_expiration_date, far_expiration_date):
    """
    A Calendar Spread strategy involves buying and selling options with 
    the same strike price but different expiration dates. This strategy 
    is typically used when an investor expects the underlying asset's price 
    to remain stable in the short term but move in the long term.
    """
    # Get call options for both expiration dates
    near_option_chain = get_option_chain(symbol, near_expiration_date)
    far_option_chain = get_option_chain(symbol, far_expiration_date)

    near_call_options = [option for option in near_option_chain if option['type'] == 'call']
    far_call_options = [option for option in far_option_chain if option['type'] == 'call']

    # Select the At-the-Money strike price
    strike_price = select_atm_strike_price(near_call_options)

    # Sell a near-term call option
    near_option_id = get_option_id(near_call_options, strike_price)
    sell_near_order = place_order(near_option_id, 'sell', 1)
    logging.info(f"Sell near-term call option with strike price ({strike_price}) on {symbol} - Order ID: {sell_near_order['id']}")

    # Buy a longer-term call option
    far_option_id = get_option_id(far_call_options, strike_price)
    buy_far_order = place_order(far_option_id, 'buy', 1)
    logging.info(f"Buy longer-term call option with strike price ({strike_price}) on {symbol} - Order ID: {buy_far_order['id']}")

def long_straddle(symbol, expiration_date):
    """
    A Straddle strategy involves buying a call option and a put option with 
    the same strike price and expiration date. This strategy is used when 
    an investor expects a significant price movement in the underlying asset 
    but is uncertain about the direction.
    """
    # Get call and put options
    option_chain = get_option_chain(symbol, expiration_date)
    call_options = [option for option in option_chain if option['type'] == 'call']
    put_options = [option for option in option_chain if option['type'] == 'put']

    # Select the At-the-Money strike price
    strike_price = select_atm_strike_price(call_options)

    # Buy a call option
    call_option_id = get_option_id(call_options, strike_price)
    buy_call_order = place_order(call_option_id, 'buy', 1)
    logging.info(f"Buy call option with strike price ({strike_price}) on {symbol} - Order ID: {buy_call_order['id']}")

    # Buy a put option
    put_option_id = get_option_id(put_options, strike_price)
    buy_put_order = place_order(put_option_id, 'buy', 1)
    logging.info(f"Buy put option with strike price ({strike_price}) on {symbol} - Order ID: {buy_put_order['id']}")

def exponential_moving_average(data, window):
    return data.ewm(span=window, adjust=False).mean()

def main(symbol, expiration_date, price_history_length=14):
    """
    The trading program executes by analyzing factors such as the underlying 
    asset's price movement, implied volatility, market sentiment, and technical indicators.

    The following approach chooses a strategy based on the exponential moving average (EMA)
    of the underlying asset's price.
    """
    # Get price history
    price_history = r.stocks.get_stock_historicals(symbol, interval='day', span=f'{price_history_length}d')

    # Calculate moving averages
    closing_prices = pd.Series([float(record['close_price']) for record in price_history])
    short_ema = exponential_moving_average(closing_prices, 5)
    long_ema = exponential_moving_average(closing_prices, 14)

    # Get option chain and ATM strike price
    option_chain = get_option_chain(symbol, expiration_date)
    call_options = [option for option in option_chain if option['type'] == 'call']
    atm_strike_price = select_atm_strike_price(call_options)

    # Calculate the average implied volatility of ATM options
    atm_call_option = [option for option in call_options if float(option['strike_price']) == atm_strike_price][0]
    atm_put_option = [option for option in option_chain if option['type'] == 'put' and float(option['strike_price']) == atm_strike_price][0]
    avg_implied_volatility = (float(atm_call_option['implied_volatility']) + float(atm_put_option['implied_volatility'])) / 2

    # Determine the trend based on EMA crossover
    trend = None
    if short_ema.iloc[-1] > long_ema.iloc[-1] and short_ema.iloc[-2] <= long_ema.iloc[-2]:
        trend = "bullish"
    elif short_ema.iloc[-1] < long_ema.iloc[-1] and short_ema.iloc[-2] >= long_ema.iloc[-2]:
        trend = "bearish"
    else:
        trend = "neutral"

    # Choose a strategy based on the trend and implied volatility
    if trend == "bullish":
        if avg_implied_volatility > 0.3:
            logging.info("Executing Long Call strategy.")
            long_call_strategy(symbol, expiration_date)
        else:
            logging.info("Executing Bull Call Spread strategy.")
            bull_call_spread(symbol, expiration_date)
    elif trend == "bearish":
        if avg_implied_volatility > 0.3:
            logging.info("Executing Long Put strategy.")
            long_put_strategy(symbol, expiration_date)
        else:
            logging.info("Executing Bear Put Spread strategy.")
            bear_put_spread(symbol, expiration_date)
    else:
        if avg_implied_volatility > 0.3:
            logging.info("Executing Long Straddle strategy.")
            long_straddle(symbol, expiration_date)
        else:
            logging.info("Executing Calendar Spread strategy.")
            bullish_calendar_spread_calls(symbol, expiration_date, expiration_date + timedelta(days=30))


# def main(symbol, expiration_date, price_history_length=14):
#     """
#     Uses SMA (Simple Moving Average Crossover)
#     """

#     # Get price history
#     price_history = r.stocks.get_stock_historicals(symbol, interval='day', span=f'{price_history_length}d')

#     # Calculate moving averages
#     closing_prices = [float(record['close_price']) for record in price_history]
#     short_moving_average = np.mean(closing_prices[-5:])
#     long_moving_average = np.mean(closing_prices)

#     # Get option chain and ATM strike price
#     option_chain = get_option_chain(symbol, expiration_date)
#     call_options = [option for option in option_chain if option['type'] == 'call']
#     atm_strike_price = select_atm_strike_price(call_options)

#     # Calculate the average implied volatility of ATM options
#     atm_call_option = [option for option in call_options if float(option['strike_price']) == atm_strike_price][0]
#     atm_put_option = [option for option in option_chain if option['type'] == 'put' and float(option['strike_price']) == atm_strike_price][0]
#     avg_implied_volatility = (float(atm_call_option['implied_volatility']) + float(atm_put_option['implied_volatility'])) / 2

#     # Choose a strategy based on moving averages and implied volatility
#     if short_moving_average > long_moving_average:
#         # Bullish trend
#         if avg_implied_volatility > 0.3:
#             # High implied volatility, choose Long Call strategy
#             logging.info("Executing Long Call strategy.")
#             long_call_strategy(symbol, expiration_date)
#         else:
#             # Low implied volatility, choose Bull Call Spread strategy
#             logging.info("Executing Bull Call Spread strategy.")
#             bull_call_spread(symbol, expiration_date)
#     elif short_moving_average < long_moving_average:
#         # Bearish trend
#         if avg_implied_volatility > 0.3:
#             # High implied volatility, choose Long Put strategy
#             logging.info("Executing Long Put strategy.")
#             long_put_strategy(symbol, expiration_date)
#         else:
#             # Low implied volatility, choose Bear Put Spread strategy
#             logging.info("Executing Bear Put Spread strategy.")
#             bear_put_spread(symbol, expiration_date)
#     else:
#         # Neutral trend, choose Straddle or Calendar Spread based on implied volatility
#         if avg_implied_volatility > 0.3:
#             logging.info("Executing Long Straddle strategy.")
#             long_straddle(symbol, expiration_date)
#         else:
#             logging.info("Executing Calendar Spread strategy.")
#             bullish_calendar_spread_calls(symbol, expiration_date, expiration_date + timedelta(days=30))


if __name__ == '__main__':
    main()