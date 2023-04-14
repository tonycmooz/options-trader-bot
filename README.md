# Automated Options Trading System
Automatically trades popular options strategies

## System Overview

After calculating the short-term (5-day) and long-term (14-day) exponential moving averages (EMA) of the underlying asset's price, the system finds a trend based on the relationship between the EMAs:

* If the short-term EMA crosses above the long-term EMA, it indicates a BULLISH trend
* If the short-term EMA crosses below the long-term EMA, it indicates a BEARISH trend
* If there is no crossover, it indicates a NEUTRAL trend

The chosen strategy is based on the determined trend and the average implied volatility of the At-the-Money options.

* If the trend is bullish:
  - If the average implied volatility is high (greater than 0.3 in this example), the system selects a Long Call strategy
  - If the average implied volatility is low, the system selects a Bull Call Spread strategy
* If the trend is bearish:
  - If the average implied volatility is high (greater than 0.3 in this example), the function selects a Long Put strategy
  - If the average implied volatility is low, the system selects a Bear Put Spread strategy
* If the trend is neutral:
  - If the average implied volatility is high (greater than 0.3 in this example), the system selects a Long Straddle strategy
  - If the average implied volatility is low, the system selects a Calendar Spread strategy

Currently, the system's approach combines both trend-following (EMA crossover) and a volatility-based (implied volatility) decision-making process to choose the most appropriate options trading strategy.

## Goals of the Trading System (In development)
An automated options trading system and strategy that aims to maximize profit and minimize risk by incorporating the following techniques:

### Diversification

Allocate capital across various options strategies to diversify risk, including both directional and non-directional strategies. This can be achieved by trading different types of options (e.g., calls, puts, European, American), different underlying assets (e.g., stocks, ETFs, indexes), and various expiration dates.

### Technical Analysis

Utilize technical analysis tools such as moving averages, support and resistance levels, and oscillators to identify trends, reversals, and momentum shifts in the market. This can help with timing entry and exit points for trades.

### Fundamental Analysis

Analyze the underlying assets by assessing financial statements, market news, and macroeconomic indicators. This can help identify options with attractive risk/reward profiles.

### Volatility Analysis

Monitor implied volatility (IV) and historical volatility (HV) to determine optimal entry and exit points for options trades. This can be done by using tools such as the Volatility Index (VIX) and the Implied Volatility Rank (IVR). Look for opportunities to sell options when IV is high and buy options when IV is low.

### Risk Management

Establish a predetermined risk/reward ratio for each trade and adjust position sizes accordingly. Implement stop losses and profit targets to minimize losses and lock in gains. Regularly review and adjust open positions to maintain the desired risk level.

### Time Decay Management

Be aware of the impact of time decay (theta) on options prices. Favor strategies that benefit from time decay, such as selling options or using spreads to offset theta risk.

### Trade Adjustment

Continuously monitor open positions and be prepared to adjust trades as market conditions change. This may involve rolling options to different strike prices or expiration dates, closing a position early, or adding new positions to hedge existing ones.

### Backtesting and Optimization

Test the strategy using historical data to evaluate its performance and optimize parameters. Continuously review and update the strategy as market conditions evolve.

### Discipline and Consistency

Follow the rules of the trading system and maintain consistency in execution. Avoid overtrading, and always adhere to risk management principles.

### Performance Tracking and Evaluation

Regularly track and analyze the performance of the trading strategy, identifying areas for improvement and adjusting as necessary.
