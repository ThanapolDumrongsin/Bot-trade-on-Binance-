from base import setup_condition , excel_file , date_to_excel_file
import time

# Stamp เวลา
time_stamp = time.ctime() 
date_to_excel_file(time_stamp)

# Your API
apikey = "Your apikey"
secret = "Your secret"
api = setup_condition(apikey,secret)


# Setting การดึงข้อมูล
timeframe = '1d'                    # Timeframe                   # your desire timeframe
limit = 200                         # ดึงข้อมูลย้อนหลัง 'limit' แท่ง   # how many data you would like to get
ema_fast =  12                      # EMA 12 วัน                   # you may change this to your trade strategy
ema_slow =  26                      # EMA 26 วัน                   # try not to change this more than 'limit' , Or you will get false calculation
money_trade = 'BUSD'                # ค่าเงินที่จะเทรดด้วย   
balance = api.balance(money_trade)  # เช็คเงินในบัญชี                 # check your balance (before trade)
balance_before = balance

# collect data then export to excel
check_limit_order_excel = []
check_signal_excel = []
buy_signal_excel = []
cancel_limit_excel = []
sell_signal_excel = []
sell_value_excel = []

trade_volume = 20                   # จำนวนเงินที่จะเทรด ($)        # how much you would like to trade 
stop_loss_percent = 10              # % stoploss จากจุดซื้อ        # calculate from entry price - your desire percent 

coin = ['BTC' , 'ETH' , 'BNB' , 'XRP' , 'ADA' , 'MATIC' ]   #คู่เหรียญที่ต้องการเทรด
coin_1 = ['SOL' , 'LTC' , 'DOT' , 'TRX' , 'AVAX' ,'LTC']
coin_2 = ['UNI' , 'ATOM' , 'LINK' , 'NEAR' , 'APE' , 'MANA']
coin_3 = ['SAND' , 'AAVE' , 'EOS' , 'FLOW' , ]
# 1,200 request weight per minute (keep in mind that this is not necessarily the same as 1,200 requests)

for each_coin in coin  + coin_1 + coin_2 + coin_3 :     # loop to check for signal (cross up)
    # สร้างคู่เทรด
    pair = (each_coin+money_trade)
    
    # พักเทรดเพื่อป้องกันการดึงข้อมูลมากเกินไป
    if each_coin == coin_1[0] :
        print("Cooldown for request\n")
        time.sleep(61)
    elif each_coin == coin_2[0] :
        print("Cooldown for request\n")
        time.sleep(61)
    elif each_coin == coin_3[0] :
        print("Cooldown for request\n")
        time.sleep(61)
   
    #ดึงข้อมูลจาก Exchange
    price_data = api.pricedata( pair , timeframe , limit)               # data chart from binance
    
    # เพิ่่มข้อมูล EMA ต่อท้าย
    price_chart_with_ema = setup_condition.EMA( price_data , ema_fast , ema_slow)       # add EMA to it 
    
    # EMA เร็วย้อนหลัง 3 วัน (ที่ไม่ใช้ของวันนี้เพราะเทรดบน tf day)                 # EMA fast back 3 days not including Today
    ema_fast_1 = price_chart_with_ema[1]
    ema_fast_2 = price_chart_with_ema[2]
    ema_fast_3 = price_chart_with_ema[3]
    # Ema ช้า ย้อนหลัง 3 วัน (ที่ไม่ใช้ของวันนี้เพราะเทรดบน tf day)                # EMA slow back 3 days not including Today
    ema_slow_1 = price_chart_with_ema[4]
    ema_slow_2 = price_chart_with_ema[5]
    ema_slow_3 = price_chart_with_ema[6]
    
    # ราคาตลาด
    marketprice = api.marketprice_and_sl(pair , stop_loss_percent)[0]       # market price 
    
    # จุด stoploss ถ้าหากเข้าซื้อ
    sl_price =   api.marketprice_and_sl(pair , stop_loss_percent)[1]        # stoploss price
    
    # ปริมาณการขาย
    sell_amount = api.sell_amount(each_coin)                                # check your coin balance
    
    # จุดทศนิยมสำหรับ ปริมาณ , ราคา ในการซื้อขาย
    amount_sell_decimal = setup_condition.round_sell_and_price(sl_price)[0]     # decimal point for amount
    sell_price_decimal = setup_condition.round_sell_and_price(sl_price)[1]      # decimal point for price

    # หาสัญญาณซื้อขายด้วย EMA 
    # มีสัญญาณเตรียมซื้อถ้าหาก  Ema_slow > Ema_fast แล้ววันถัดมา Ema_fast > Ema_slow
    # if Ema_slow > Ema_fast and then next day Ema_fast > Ema_slow
    check_signal = setup_condition.check_signal(pair , ema_fast_1 , ema_slow_1 , ema_fast_2 , ema_slow_2 , check_signal_excel)
    
    
    # ถ้าเกิด check signal แล้ววันต่อมา Ema_fast ยังคงนำ Ema_slow จะถือว่าเป็นสัญญาณซื้อ 
    # check signal trigger and the next day Ema_fast is still faster than Ema_slow
    buy_signal = api.buy_signal(pair , ema_fast_1 , ema_fast_2 , ema_fast_3 , ema_slow_2 , ema_slow_3 , balance , trade_volume , marketprice
                ,each_coin , amount_sell_decimal , sl_price , sell_price_decimal , buy_signal_excel )
    
    
    # ถ้าเกิดเป็นขาขึ้นอยู่ (Ema_fast > Ema_slow) แล้วเกิดการตัดลงของเส้นเร็ว (Ema_fast < Ema_slow) จะถือว่าเป็นสัญญาณขาย
    # if Ema_fast > Ema_slow and the next day Ema_slow > Ema_fast it mean sell signal
    # I will cancel limit order first otherwise you are unable to sell it
    cancel_limit = api.cancel_limit(pair , ema_fast_1 , ema_slow_1 , ema_fast_2 , ema_slow_2 , cancel_limit_excel)
    
    sell_signal = api.sell_signal( pair , each_coin , ema_fast_1 , ema_slow_1 , ema_fast_2 , ema_slow_2 , marketprice , 
                                sell_price_decimal , amount_sell_decimal , sell_signal_excel , sell_value_excel)
    
    
    # sell_signal[1] = sell value
    # สร้างกราฟถ้าหากมีสัญญาณจากการ check EMA                    # create graph if check_signal happen
    if check_signal == "check":
        graph_pic_for_check_signal = api.graph_pic(price_chart_with_ema , limit , pair , check_signal , sl_price , marketprice , each_coin , trade_volume , sell_signal[1] ,sell_price_decimal)
    
    # sell_signal[1] = sell value
    #กราฟฝั่งซื้อ
    if buy_signal == "buy_signal" :                          # create graph if buy_signal happen
        graph_pic_for_buy_signal = api.graph_pic(price_chart_with_ema , limit , pair , buy_signal , sl_price , marketprice , each_coin , trade_volume , sell_signal[1] , sell_price_decimal)
    elif buy_signal == "buy_signal_but_no_money" :
        graph_pic_for_buy_signal = api.graph_pic(price_chart_with_ema , limit , pair , buy_signal , sl_price , marketprice , each_coin , trade_volume , sell_signal[1] , sell_price_decimal)
    
    # sell_signal[1] = sell value
    #กราฟฝั่งขาย
    if sell_signal[0] == "sell_signal" :                     # create graph if sell_signal happen 
        graph_pic_for_sell_signal = api.graph_pic(price_chart_with_ema , limit , pair , sell_signal , sl_price , marketprice , each_coin , trade_volume , sell_signal[1] , sell_price_decimal)
    elif sell_signal[0] == "sell_signal_but_no_coin" :
        graph_pic_for_sell_signal = api.graph_pic(price_chart_with_ema , limit , pair , sell_signal , sl_price , marketprice , each_coin , trade_volume , sell_signal[1] , sell_price_decimal)
    
    # Check daily that we have limit order or not
    check_limit_order = api.check_order(pair , sell_price_decimal,check_limit_order_excel)


# Check for coin that able to convert into BNB (for maximise profit)  
asset_that_can_dust_excel = []
asset_that_can_dust = api.asset_that_can_dust(asset_that_can_dust_excel)

# dust it into BNB (if you have)
dust_to_BNB_excel = []
dust_to_BNB = api.dust_to_BNB(asset_that_can_dust , dust_to_BNB_excel)

# sell BNB and get your desire (money_trade)
sell_BNB = api.sell_bnb(sell_value_excel,money_trade)

# Check ยอดเงินหลังเทรด
balance = api.balance(money_trade)  
balance_after = balance
print(check_limit_order_excel)

# data list to apply to excel
all_data_to_excel = [ [balance_before] , [balance_after] , check_signal_excel , buy_signal_excel , sell_signal_excel , sell_value_excel , 
                       check_limit_order_excel , [stop_loss_percent] , [trade_volume] , [ema_fast] , [ema_slow] , [timeframe] , cancel_limit_excel, 
                       asset_that_can_dust_excel , dust_to_BNB_excel]

# append data to excel
excel_file(all_data_to_excel)

# อัพเดต daily
# Date	/ Balance (before trade) / Balance (after trade) / Check signal / Buy signal / Sell signal / Sell value	 / Limit order / Stop loss percent	
# Trade volume	/ EMA fast	/ EMA slow / Time frame / Cancel litmit order / Dust asset / Dust to BNB

