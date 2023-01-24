# Bot-trade-on-Binance-
Bot trade Binance using API, with EMA cross-up strategy 

This project working by check between 2 EMA (EMA fast and slow) which is inspire by [CDC action zone V3 2020 by piriya33] on Trading views.

Requirement
  - Your API on Binance , need to turn on spot function.

Project ability
  - Buy or Sell when the condition is trigger.
  - Auto create limit order for stoploss at your desire stoploss percent when buy and sell condition is trigger.
  - Create graph from mpf.plot which contain EMA indicator , buy or sell price , stop loss price , uptrend or downtrend signal sign (default = candle stick)
  - Graph picture will return to folder graph_pic by default.
  - Find the coin that able to dust into BNB and sell it.
  - Auto collect data and append to excel file (default = data.xlsx).
  
 Warnning 
  - I reccommend to use this project on timeframe '1DAY' only.
  - Bot trade is not a Holy-grail that will genarate unlimited income for you, it just a labor-saving tools.
  - I will not responsible for any lose that happend to you
