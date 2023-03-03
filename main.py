from Class import *
from To_excel import *
import time


apikey = "Insert your API here"
secret = "Insert your secret here"

money_trade =      "BUSD"           # recommend as $ for prevent volatility

timeframe =        '1d'             # Timeframe                   # your desire timeframe
limit =             200             # ดึงข้อมูลย้อนหลัง 'limit' แท่ง   # how many candle you would like to get
#                                   # limit amount should have at least double of your ema_slow
# EMA 12,26 วัน                      
ema_fast =          12              # you may change this to your trade strategy
ema_slow =          26              

trade_volume =      20              # จำนวนเงินที่จะเทรด ($)        # how much you would like to trade 
stop_loss_percent = 10              # % stoploss จากจุดซื้อ        # calculate from entry price - your desire percent 

data_to_excel = {                                                   'Balance (before trade)': [], 
                        'Balance (after trade)': [],                'Check signal' : [],
                        'Buy signal' : [] ,                         'Sell signal' : [],
                        'Sell value' : [] ,                         'Limit order' : [],
                        'Stop loss percent' : [stop_loss_percent] , 'Trade volume' : [trade_volume],
                        'EMA fast' : [ema_fast] ,                   'EMA slow' : [ema_slow] ,
                        'Time frame' : [timeframe] ,                'Cancel litmit order' : [],
                        'Dust asset' : [] ,                         'Dust to BNB' : [],
                        }

coin = ['BTC' , 'ETH' , 'BNB' , 'XRP' , 'ADA' , 'MATIC' ]   #คู่เหรียญที่ต้องการเทรด
coin_1 = ['SOL' , 'LTC' , 'DOT' , 'TRX' , 'AVAX' ,'LTC']    # Your desire coin
coin_2 = ['UNI' , 'ATOM' , 'LINK' , 'NEAR' , 'APE' , 'MANA']
coin_3 = ['SAND' , 'AAVE' , 'EOS' , 'FLOW' , ]



# append balance before trade 
check_balance = balance_before_trade(apikey,secret,money_trade)
data_to_excel['Balance (before trade)'].append(check_balance)

for each_coin in  coin + coin_1 + coin_2 + coin_3    :     # loop to check for signal (cross up or cross down)
    
    # create pair trade
    pair = (each_coin+money_trade)
    
    # cooldown because Binance limit 1200 data per minute.
    if  each_coin == coin_1[-1] or each_coin == coin_2[-1] or each_coin == coin_3[-1] :
        print("Cooldown for 60 second")
        time.sleep(60)
    
    # setup main condition.
    main_condition = Setup_condition(apikey , secret , money_trade , timeframe , limit , pair , ema_fast , 
    ema_slow , trade_volume , stop_loss_percent )
    # check for each signal.
    check_signal = main_condition.check_signal(data_to_excel,pair)
    buy_signal = main_condition.buy_signal(data_to_excel , pair , each_coin)
    sell_signal = main_condition.sell_signal(data_to_excel,pair,each_coin)
    
    # check balance for sell value if sell signal happen.
    balance_check = main_condition.Balance_check()
    # check if we have limit order or not..
    check_limit_order = main_condition.check_limit_order(data_to_excel,pair)
    
    # if signal happen we will create a graph.
    graph_for_check_signal = main_condition.Graph_for_check_signal(pair,check_signal) 
    graph_for_buy_signal = main_condition.Graph_for_buy_signal(pair,buy_signal)
    graph_for_sell_signal = main_condition.Graph_for_sell_signal(pair,each_coin,sell_signal,balance_check)


# check the balance after trade 
after_trade_balance_check = main_condition.Balance_check()

data_to_excel['Balance (after trade)'].append(after_trade_balance_check)

# find asset that can dust into BNB
dust_an_asset_to_BNB = main_condition.Dust_an_asset_to_BNB(data_to_excel)

# sell BNB for maximize profit
sell_BNB = main_condition.sell_BNB(data_to_excel , money_trade)

# append date to excel file 
date = time.ctime()
date_to_excel_file(date)
# append all information into excel file
excel_file(data_to_excel)

print(data_to_excel)