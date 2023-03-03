import ccxt
import pandas as pd
import pandas_ta as ta
import time
from binance.client import Client 
import mplfinance as mpf
import numpy as np

class Setup_condition :
    '''
    Base for APIkey and Secretkey, use for get the data from binance such as our balance, price data, amount of coin we have, etc.
    This setup will able for you to send a command and order to Binance to do your action according to your trading strategy.
    This Class is use for trade on spot not in future option, if you want to trade on future you will need to change the 
    Binance order command For future trade, it will require significant change, i reccommend to write a new version for Future option.
    
    '''
    # setup Client and exchange
    def __init__(self, apikey , secret , money_trade , timeframe , limit ,pair, ema_fast , ema_slow ,
     trade_volume , stop_loss_percent  ):
        self.apikey = apikey
        self.secret = secret
        self.my_account = Client(apikey, secret)
        self.exchange = ccxt.binance({'apiKey': apikey, 'secret': secret, 'enableRateLimit': True})
        self.balance = self.my_account.get_asset_balance(asset=money_trade)['free']
        self.trade_volume = trade_volume
        self.limit = limit
        df_ohlcv = self.exchange.fetch_ohlcv(pair, timeframe = timeframe , limit = limit)                  
        #ดึงมาเรียงในแบบ columns (ตาราง)
        data_price = pd.DataFrame(df_ohlcv, columns=['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'])   
        
        #เปลี่ยนรูปแบบวันที่ให้คนอ่านได้
        data_price['Datetime'] = pd.to_datetime(data_price['Datetime'], unit='ms')  
        data_price.set_index('Datetime', inplace=True)                                                     
        
        #เพิ่ม pair ต่อท้ายข้อมูล
        data_price['Pair'] = pair
        self.dataprice = data_price
        
        ema_fast_data = round(data_price.ta.ema(ema_fast),6)
        ema_slow_data = round(data_price.ta.ema(ema_slow),6)
        ema = pd.concat([data_price, ema_fast_data, ema_slow_data], axis=1)                 #รับ EMA มาต่อท้ายข้อมูล
                                                                   
        ema_back = len(ema)
        # Ema เร็ว ย้อนหลัง 3 วัน  (ที่ไม่ใช้ของวันนี้เพราะเทรดบน tf day)
        ema_fast_1 = ema['EMA_12'][ema_back - 2]
        ema_fast_2 = ema['EMA_12'][ema_back - 3]
        ema_fast_3 = ema['EMA_12'][ema_back - 4]
        # Ema ช้า ย้อนหลัง 3 วัน (ที่ไม่ใช้ของวันนี้เพราะเทรดบน tf day)
        ema_slow_1 = ema['EMA_26'][ema_back - 2]
        ema_slow_2 = ema['EMA_26'][ema_back - 3]
        ema_slow_3 = ema['EMA_26'][ema_back - 4]

        self.ema_fast_1 = ema_fast_1
        self.ema_fast_2 = ema_fast_2
        self.ema_fast_3 = ema_fast_3
        self.ema_slow_1 = ema_slow_1
        self.ema_slow_2 = ema_slow_2
        self.ema_slow_3 = ema_slow_3
        self.dataprice_with_ema = ema
    
        marketprice = self.my_account.get_symbol_ticker(symbol = pair) 
        marketprice = float(marketprice[ 'price' ])
        stop_loss_percent = (100 - stop_loss_percent) /100
        stop_loss_percent = round(stop_loss_percent,2)
        sl_price =  float(marketprice)
        # stoploss relate to your desire stoploss percent
        sl_price =  sl_price * stop_loss_percent 
        self.stop_loss_percent = stop_loss_percent
        self.marketprice = marketprice
        

        amount_sell_decimal = None
        sell_price_decimal = None
        # round เพื่อส่งคำสั่งซื้อขายแล้วไม่เกิด Error + ทำให้ไม่ขาดทุนในบางครั้ง
        if sl_price > 1000 :
            sell_price_decimal = None
            amount_sell_decimal = 5
        elif sl_price > 100 :
            sell_price_decimal = 1
            amount_sell_decimal = 3
        elif sl_price > 10 :
            sell_price_decimal = 2
            amount_sell_decimal = 2
        elif sl_price > 0 :
            sell_price_decimal = 3
            amount_sell_decimal = 2
        elif sl_price < 0 :
            sell_price_decimal = 3
            amount_sell_decimal = None
        
        self.amount_sell_decimal = amount_sell_decimal
        self.sell_price_decimal = sell_price_decimal
        self.sl_price = round(sl_price,sell_price_decimal)
        

    def check_signal(self,data_to_excel,pair) :
        '''
        Check signal happen from down trend turn into up trend, This won't trade yet just a prepare signal for you.
        '''
        signal = False
        ema_fast_1 = self.ema_fast_1
        ema_fast_2 = self.ema_fast_2  
        ema_fast_3 = self.ema_fast_3  
        ema_slow_1 = self.ema_slow_1  
        ema_slow_2 = self.ema_slow_2 
        ema_slow_3 = self.ema_slow_3
        
        if ema_fast_1 > ema_slow_1 and ema_fast_2 < ema_slow_2 :   
            check_signal_result = f"Check {pair} for buy signal next bar.\n"
            print(check_signal_result)
            
            data_to_excel['Check signal'].append(check_signal_result)
            
            signal = True
        
        else :
            print(f"Check signal {pair} = {signal}")
        
        return signal
    
    def buy_signal(self,data_to_excel,pair,each_coin):
        '''
        Buy signal trigger if yesterday [Check signal] happened and [EMA fast] for Today is higher than yesterday, This consider as buy signal.
        And it will check : Is your account balance (money trade) more than your trade volume or not , If more trade will happen.
        return True or False
        '''
        signal = False
        ema_fast_1 = self.ema_fast_1
        ema_fast_2 = self.ema_fast_2  
        ema_fast_3 = self.ema_fast_3    
        ema_slow_2 = self.ema_slow_2 
        ema_slow_3 = self.ema_slow_3
        marketprice = self.marketprice
        trade_volume = self.trade_volume
        stoploss_price = self.sl_price
        
        
        if ema_fast_1 > ema_fast_2 > ema_slow_2 and ema_fast_3 < ema_slow_3 :
            balance = self.balance
            balance = int(float(balance))
            
            if balance > trade_volume :
                self.my_account.create_order(                                                                
                    symbol = pair,
                    side = Client.SIDE_BUY,
                    type = Client.ORDER_TYPE_MARKET,
                    quoteOrderQty = trade_volume
                    )
                buy_result = f"Buy signal of {pair} at price {marketprice}$."
                print(buy_result)
                
                time.sleep(2)
                
                coin_balance = self.my_account.get_asset_balance(asset= each_coin)['free']
                coin_balance = float(coin_balance)
                coin_balance = coin_balance / 1.005
                coin_balance = round(coin_balance,self.amount_sell_decimal)
                print(coin_balance)
                print(stoploss_price)
                self.my_account.create_order(                                                                           
                    symbol = pair,
                    side = Client.SIDE_SELL,
                    type = Client.ORDER_TYPE_STOP_LOSS_LIMIT,
                    timeInForce = "GTC",
                    price = stoploss_price,
                    quantity = coin_balance,
                    stopPrice = stoploss_price
                    )
                sl_result = (f" , amount of {each_coin} = {coin_balance} coin, Stop loss price at {stoploss_price}.\n")
                print(sl_result)
                signal = True

                data_to_excel['Buy signal'].append(buy_result+sl_result)
    
            else :
                buy_but_no_money_result = f"Buy signal for {each_coin}, But your account balance have {balance}$. \n not enough for your trading volume\n"
                print(buy_but_no_money_result)
                signal = "no_money"
                data_to_excel['Buy signal'].append(buy_but_no_money_result)
        else :
            print(f"Buy signal {pair} = {signal}")
        
        return signal

        
    def sell_signal(self , data_to_excel , pair ,each_coin):
        '''
        if sell_signal happen (ema_fast cross down ema_slow), we will check for limit order and cancel it if you have,
        Then check the value of coin you have, If value is more than 10$ The sell will happen.
        return True or False
        '''
        signal = False
        ema_fast_1 = self.ema_fast_1
        ema_fast_2 = self.ema_fast_2  
        ema_slow_1 = self.ema_slow_1  
        ema_slow_2 = self.ema_slow_2 
        
        
        if ema_fast_1 < ema_slow_1 and ema_fast_2 > ema_slow_2 :
        # รับ Id order
            signal = True
            get_limit_order = self.my_account.get_open_orders(symbol= pair)
            
            for order in get_limit_order:
                order_id = order['orderId']
                # ยกเลิก Limit order ถ้ามี limit order อยู่
                if order['orderId'] == order_id and order['symbol'] == pair and order['side'] == 'SELL' and order['status'] == 'NEW':
                    self.my_account.cancel_order(symbol = pair , orderId = order_id)
                    
                    cancel_litmit_result = f"Cancel limit order {pair}.\n"
                    
                    data_to_excel['Cancel litmit order'].append(cancel_litmit_result)
                    print(cancel_litmit_result)
            
                #ถ้าไม่มี limit order = ผ่าน
                else :
                    pass
            
            time.sleep(2)
            coin_balance = self.my_account.get_asset_balance(asset= each_coin)['free']
            coin_balance = float(coin_balance)
            coin_balance = coin_balance / 1.005
            coin_balance = round(coin_balance,self.amount_sell_decimal)
            sell_value = self.marketprice * coin_balance
            
            if sell_value > 10 :
                # ส่งคำสั่งขาย
                self.my_account.create_order(                                                                
                    symbol = pair,
                    side = Client.SIDE_SELL,
                    type = Client.ORDER_TYPE_MARKET,
                    quantity= coin_balance
                    )
                sell_result = f"sell {pair} for {sell_value} $.\n"
                print(sell_result)
                
                data_to_excel['Sell signal'].append(sell_result)
                data_to_excel['Sell value'].append(f"{pair} = {sell_value}$.")

            else : 
                signal = 'no_coin'
                sell_but_no_coin_result = f"{pair} is down trend but your {pair} value < 10$ can't sell.\n"
                print(sell_but_no_coin_result)
                data_to_excel['Sell signal'].append(sell_but_no_coin_result)

        else :
            print(f"Sell signal {pair} = {signal}")        
        
        return signal 
    
    def check_limit_order(self,data_to_excel, pair):
        '''
        Check daily for limit order that you have and save to excel file.
        '''
        
        check_order= self.my_account.get_open_orders(symbol= pair)
        for order in check_order:
            order_id = order['orderId']
            
            # Check limit order (daily)
            if order['orderId'] == order_id and order['symbol'] == pair and order['side'] == 'SELL' and order['status'] == 'NEW':
                
                price = float(order['price']) 
                amount = float(order['origQty'])

                value_calculation = round(price * amount , 2)
                check_order_result = f"limit order {pair} at price {price}$ value at limit = {value_calculation}$.\n"
                print(check_order_result)
                data_to_excel['Limit order'].append(check_order_result)
        
    def Dust_an_asset_to_BNB(self,data_to_excel):
        '''
        Check for small asset that able to dust in BNB to maximize the profit
        '''
        check_asset = self.my_account.get_dust_assets()
        asset_that_able_to_dust = []
        
        for asset in check_asset['details']:
            print(asset)
            result = f"{asset['asset']}  can convert into {asset['toBNB']} BNB.\n"
            print(result)
            asset_that_able_to_dust.append(asset['asset'])
            data_to_excel['Dust asset'].append(result)
        
        print(asset_that_able_to_dust)

        # if we have more than 1 coin to dust
        if len(asset_that_able_to_dust) >= 1 :
            transfer_dust = self.my_account.transfer_dust(asset = ", ".join(asset_that_able_to_dust))
        
            transfer_dust_result = transfer_dust['totalTransfered']
            print(transfer_dust_result)
            data_to_excel['Dust to BNB'].append(transfer_dust_result)
        

    def sell_BNB(self,data_to_excel,money_trade) :
        '''
        This will sell BNB from dust method if your BNB value is over 10$
        '''
        BNB_price = self.my_account.get_symbol_ticker(symbol = f'BNB{money_trade}')
        BNB_price = float(BNB_price['price'])
        BNB_amount = self.my_account.get_asset_balance(asset= 'BNB')['free']
        BNB_amount = float(BNB_amount) / 1.001
        BNB_value = round(BNB_price * BNB_amount , 1)
        print(f'BNB value = {BNB_value}$.')
        
        if BNB_value > 10 :
                # ส่งคำสั่งขาย
            self.my_account.create_order(                                                                
                symbol = f'BNB{money_trade}',
                side = Client.SIDE_SELL,
                type = Client.ORDER_TYPE_MARKET,
                quantity= round(BNB_amount,3)
                )
            sell_result = f"Sell BNB for {BNB_value}$.\n"
            print(sell_result)
            data_to_excel['Sell value'].append(sell_result)
    
    def Graph_for_check_signal(self , pair , signal):
        '''
        If check signal happend this function will create the graph with ema_fast and ema_slow, 
        The uptrend will fill with green and downtrend will fill with red.
        Green marker mean buy signal.
        Red  marker mean sell signal.
        Yellow marker mean false signal (check signal happened but didn't turn into buy signal).
        This will save to graph_pic folder by default.
        Make sure you have the graph_pic folder before you run the code.
        '''
        if signal == True :
            data_for_graph = self.dataprice_with_ema
            marketprice = self.marketprice
            limit = self.limit
            add_ema_data_12 = data_for_graph['EMA_12']
            add_ema_data_26 = data_for_graph['EMA_26']
            x_position_for_text = round(limit *0.75)
            add_fill_between_up = dict(y1=add_ema_data_12.values , y2=add_ema_data_26.values , where = add_ema_data_12 > add_ema_data_26 , color="#93c47d" , alpha=0.3 , interpolate=True)
            add_fill_between_down = dict(y1=add_ema_data_12.values , y2=add_ema_data_26.values , where = add_ema_data_12 < add_ema_data_26 , color="#e06666" , alpha=0.3 , interpolate=True)
            
            fill_between = [add_fill_between_up , add_fill_between_down]
            
            up_trend_sign = [np.nan,np.nan]
            for day in range(len(data_for_graph)-2):
                if  data_for_graph['EMA_26'][day] > data_for_graph['EMA_12'][day] and data_for_graph['EMA_12'][day+2] >data_for_graph['EMA_12'][day+1] > data_for_graph['EMA_26'][day+1] :
                    up_trend_sign.append(add_ema_data_26[day+1]*0.95)
                else:
                    up_trend_sign.append(np.nan)
            
            down_trend_sign = [np.nan]
            for i in range (len(data_for_graph)-1) :
                if data_for_graph['EMA_26'][i+1] > data_for_graph['EMA_12'][i+1] and data_for_graph['EMA_12'][i] > data_for_graph['EMA_26'][i] :
                    down_trend_sign.append(add_ema_data_26[i+1]*1.05)
                else :
                    down_trend_sign.append(np.nan)

            add_all_data = [mpf.make_addplot(add_ema_data_12 , color = 'lime'),
                            mpf.make_addplot(add_ema_data_26 , color = 'r'),
                            mpf.make_addplot(up_trend_sign ,type='scatter',markersize=200,marker='^',color="lime"),
                            mpf.make_addplot(down_trend_sign ,type='scatter',markersize=200,marker='v',color="r"),
                           
                        ]
            
            hline = dict( hlines = [marketprice] , colors=['g'] , linestyle = '-.' ,)
            # create graph
            fig,axlist = mpf.plot(data_for_graph ,hlines = hline , title = f"{data_for_graph.index[-1]} \n {pair}." ,volume = True , addplot = add_all_data , type='candle' , figscale=2 , figsize=(20,10),
                style = 'binance' , tight_layout=True , fill_between = fill_between ,returnfig = True )
            
            axlist[0].text(x_position_for_text, marketprice*1.03 , f"Check buy signal Tomorrow (7.00 AM).", fontweight='bold' ,color = 'g')
            # folder เก็บภาพ
            path = "graph_pic"

            # แปลงชื่อ file ให้อ่านง่าย + save
            filename = f'{pair}{str(data_for_graph.index[-1]).replace(":","")}.png'
            filename = filename.replace("000000","") 
            fig.savefig(f"{path}/{filename}")
    
    
    
    
    def Graph_for_buy_signal(self,pair,signal):
        '''
        If buy signal happend this function will create the graph with ema_fast and ema_slow, 
        The uptrend will fill with green and downtrend will fill with red.
        Green marker mean buy signal.
        Red  marker mean sell signal.
        Yellow marker mean false signal (check signal happened but didn't turn into buy signal).
        This will save to graph_pic folder by default.
        Make sure you have the graph_pic folder before you run the code.
        '''
        if signal == True or signal == "no_money" :
            data_for_graph = self.dataprice_with_ema
            marketprice = self.marketprice
            limit = self.limit
            sl_price = self.sl_price
            
            x_position_for_text = round(limit *0.75)
            
            add_ema_data_12 = data_for_graph['EMA_12']
            add_ema_data_26 = data_for_graph['EMA_26']
            add_fill_between_up = dict(y1=add_ema_data_12.values , y2=add_ema_data_26.values , where = add_ema_data_12 > add_ema_data_26 , color="#93c47d" , alpha=0.3 , interpolate=True)
            add_fill_between_down = dict(y1=add_ema_data_12.values , y2=add_ema_data_26.values , where = add_ema_data_12 < add_ema_data_26 , color="#e06666" , alpha=0.3 , interpolate=True)
            
            fill_between = [add_fill_between_up , add_fill_between_down]
            
            up_trend_sign = [np.nan,np.nan]
            for day in range(len(data_for_graph)-2):
                if  data_for_graph['EMA_26'][day] > data_for_graph['EMA_12'][day] and data_for_graph['EMA_12'][day+2] > data_for_graph['EMA_12'][day+1] > data_for_graph['EMA_26'][day+1] :
                    up_trend_sign.append(add_ema_data_26[day+1]*0.95)
                else:
                    up_trend_sign.append(np.nan)
            
            down_trend_sign = [np.nan]
            for i in range (len(data_for_graph)-1) :
                if data_for_graph['EMA_26'][i+1] > data_for_graph['EMA_12'][i+1] and data_for_graph['EMA_12'][i] > data_for_graph['EMA_26'][i] :
                    down_trend_sign.append(add_ema_data_26[i+1]*1.05)
                else :
                    down_trend_sign.append(np.nan)
            
            add_all_data = [mpf.make_addplot(add_ema_data_12 , color = 'lime'),
                            mpf.make_addplot(add_ema_data_26 , color = 'r'),
                            mpf.make_addplot(up_trend_sign ,type='scatter',markersize=200,marker='^',color="lime"),
                            mpf.make_addplot(down_trend_sign ,type='scatter',markersize=200,marker='v',color="r"),
                            
                        ]
            if signal == True :
                hline = dict( hlines = [sl_price , marketprice] , colors=['r', 'g'] , linestyle = '-.' ,)
            
            elif signal == "no_money" :
                hline = dict( hlines = [sl_price , marketprice] , colors=['#e8e046', '#e8e046'] , linestyle = '-.' ,)
            
            fig,axlist = mpf.plot(data_for_graph ,hlines = hline , title = f"{data_for_graph.index[-1]} \n {pair}." ,volume = True , addplot = add_all_data , type='candle' , figscale=2 , figsize=(20,10),
                style = 'binance' , tight_layout=True , fill_between = fill_between ,returnfig = True )
            
            
            loss_calculation = self.trade_volume - (self.trade_volume * self.stop_loss_percent)
            
            if signal == True :
                axlist[0].text(x_position_for_text, sl_price*1.03 , f"Stop loss at {round(sl_price,self.sell_price_decimal) }$ \n Loss if Stop loss = {loss_calculation}$.", fontweight='bold' ,color = 'r')
                axlist[0].text(x_position_for_text, marketprice*1.03 , f"Buy '{pair}' at {marketprice}$ for {self.trade_volume}.", fontweight='bold' ,color = 'g')
            elif signal == "no_money" :
                axlist[0].text(x_position_for_text, sl_price*1.03 , f"if buy Stop loss at {round(sl_price,self.sell_price_decimal) }$ \n Loss if Stop loss = {loss_calculation}$.", fontweight='bold' ,color = '#e8e046')
                axlist[0].text(x_position_for_text, marketprice*1.03 , f"Buy signal for '{pair}' at {marketprice}$ \n But your balance is less than trade volume.", fontweight='bold' ,color = '#e8e046')
        
            # folder เก็บภาพ
            path = "graph_pic"

            # แปลงชื่อ file ให้อ่านง่าย + save
            filename = f'{pair}{str(data_for_graph.index[-1]).replace(":","")}.png'
            filename = filename.replace("000000","") 
            fig.savefig(f"{path}/{filename}")
    
    def Graph_for_sell_signal(self,pair,each_coin,signal,balance_check):
        '''
        If sell signal happend this function will create the graph with ema_fast and ema_slow, 
        The uptrend will fill with green and downtrend will fill with red.
        Green marker mean buy signal.
        Red  marker mean sell signal.
        Yellow marker mean false signal (check signal happened but didn't turn into buy signal)
        This will save to graph_pic folder by default.
        Make sure you have the graph_pic folder before you run the code.
        '''
        if signal == True or signal == "no_coin" :
            data_for_graph = self.dataprice_with_ema
            marketprice = self.marketprice
            limit = self.limit
            data_for_graph = data_for_graph.dropna()
            print(data_for_graph)
            
            x_position_for_text = round(limit *0.75)
            
            add_ema_data_12 = data_for_graph['EMA_12']
            add_ema_data_26 = data_for_graph['EMA_26']
            add_fill_between_up = dict(y1=add_ema_data_12.values , y2=add_ema_data_26.values , where = add_ema_data_12 > add_ema_data_26 , color="#93c47d" , alpha=0.3 , interpolate=True)
            add_fill_between_down = dict(y1=add_ema_data_12.values , y2=add_ema_data_26.values , where = add_ema_data_12 < add_ema_data_26 , color="#e06666" , alpha=0.3 , interpolate=True)
            
            fill_between = [add_fill_between_up , add_fill_between_down]
            
            up_trend_sign = [np.nan,np.nan]
            for day in range(len(data_for_graph)-2):
                if  data_for_graph['EMA_26'][day] > data_for_graph['EMA_12'][day] and data_for_graph['EMA_12'][day+2] > data_for_graph['EMA_12'][day+1] > data_for_graph['EMA_26'][day+1] :
                    up_trend_sign.append(add_ema_data_26[day+1]*0.95)
                else:
                    up_trend_sign.append(np.nan)
            
            down_trend_sign = [np.nan]
            for i in range (len(data_for_graph)-1) :
                if data_for_graph['EMA_26'][i+1] > data_for_graph['EMA_12'][i+1] and data_for_graph['EMA_12'][i] > data_for_graph['EMA_26'][i] :
                    down_trend_sign.append(add_ema_data_26[i+1]*1.05)
                else :
                    down_trend_sign.append(np.nan)
            
            
            add_all_data = [mpf.make_addplot(add_ema_data_12 , color = 'lime'),
                            mpf.make_addplot(add_ema_data_26 , color = 'r'),
                            mpf.make_addplot(up_trend_sign ,type='scatter',markersize=200,marker='^',color="lime"),
                            mpf.make_addplot(down_trend_sign ,type='scatter',markersize=200,marker='v',color="r"),
                        ]
           
            if signal == True :
                hline = dict( hlines = [marketprice] , colors=['r'] , linestyle = '-.' ,)
            
            elif signal == "no_coin" :
                hline = dict( hlines = [marketprice] , colors=['r'] , linestyle = '-.' ,)            
            
            fig,axlist = mpf.plot(data_for_graph ,hlines = hline , title = f"{data_for_graph.index[-1]} \n {pair}." ,volume = True , addplot = add_all_data , type='candle' , figscale=2 , figsize=(20,10),
                style = 'binance' , tight_layout=True , fill_between = fill_between ,returnfig = True )
            
            sell_value = int(float(self.balance)) - balance_check
            
            if signal == True :
                axlist[0].text(x_position_for_text, marketprice*0.93 , f"sell signal for '{pair}' at {marketprice}$ \n Your sell value is {sell_value}$.", fontweight='bold' ,color = 'r')
        
            elif signal == "no_coin" :
                axlist[0].text(x_position_for_text, marketprice*0.93 , f"sell signal for '{pair}' at {marketprice}$ \n But your {each_coin} value is less than 10$.", fontweight='bold' ,color = 'r')
        
            # folder เก็บภาพ
            path = "graph_pic"

            # แปลงชื่อ file ให้อ่านง่าย + save
            filename = f'{pair} {str(data_for_graph.index[-1]).replace(":","")}.png'
            filename = filename.replace("000000","") 
            fig.savefig(f"{path}/{filename}")
        
        
    def Balance_check(self):
        '''
        Check balance during a trade for check sell value(how much you get from this sell) if sell signal happen.
        '''
        balance_check = self.balance
        balance_check = int(float(balance_check))
        return balance_check


def balance_before_trade(apikey,secret,money_trade):
    '''
    check balance before trade for save to excel.
    '''
    before_trade_balance_check = Client(apikey, secret)
    before_trade_balance_check = before_trade_balance_check.get_asset_balance(asset=money_trade)['free']
    before_trade_balance_check = int(float(before_trade_balance_check))
    return before_trade_balance_check
