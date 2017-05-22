
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pandas_datareader.data as web
import datetime as dt
import os
from   matplotlib.finance import candlestick_ohlc
import matplotlib.dates as mdates


start = '20100101'
end = '20170101'
#start = datetime.datetime(2010, 1, 1)
#end = datetime.datetime(2017, 1, 1)


def plot_candlestick(df, ax=None, fmt="%Y-%m-%d"):
    if ax is None:
        ax = plt.subplot(1, 1, 1)
    idx_name = df.index.name
    dat = df.reset_index()[[idx_name, "Open", "High", "Low", "Close"]]
    dat[df.index.name] = dat[df.index.name].map(mdates.date2num)
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter(fmt))
    ax.autoscale_view()
    plt.xticks(rotation=30)
    _ = candlestick_ohlc(ax, dat.values, width=.6, colorup='g', alpha = 0.75)
    ax.set_title("History price chart",fontsize=28)
    ax.set_xlabel(idx_name,fontsize=20)
    ax.set_ylabel("Price",fontsize=20)
    ax.set_ylim(df.Low.min()*0.9,df.High.max()*1.05)
    df.WeekResist.plot(linestyle='None',marker="_", markeredgecolor ='red', markersize=20)
    df.WeekSupport.plot(linestyle='None',marker="_", markeredgecolor ='blue', markersize=20)
    df.MonthResist.plot(linestyle='None',marker="_", markeredgecolor ='purple', markersize=20)
    df.MonthSupport.plot(linestyle='None',marker="_", markeredgecolor ='orange', markersize=20)
    df.TradeEntry.plot(linestyle='None',marker="^", markeredgecolor ='orange',markerfacecolor=None, markersize=20)
    ax.grid()
    plt.subplots_adjust(left=0.1, right=0.9, top=0.85, bottom=0.1)
    #plt.show()
    return ax


def loadData(symbol):
#    symbol ="F"
    filename = symbol + start+'_' + end+'.csv'
    loc = 'data\\'+ filename
    if not os.path.exists(loc):
        data  = web.DataReader(symbol, 'google', start, end)
        data.to_csv(loc)
    else:
        data =  pd.read_csv(loc,header=0, index_col='Date',parse_dates=['Date'])
    return data

def findSRs(data):
    
     #    WeeklySR
     #    MonthlySR
     #    YearlySR
     #    AllSR
     s = data.index.get_loc('20120101',"bfill")
     data['WeekResist'] = 0
     data['WeekSupport'] = 0
     data['MonthResist'] = 0
     data['MonthSupport'] = 0
     data['YearResist'] = 0
     data['YearSupport'] = 0
     data['HistoryResist'] = 0
     data['HistorySupport'] = 0
     
     for day in range(s,len(data)):
         idx = data.index[day-1]
         idx_week =  data.index[day] - pd.DateOffset(weeks=1)
         weekresist = data.ix[idx_week:idx,'High'].max()
         data.ix[day,'WeekResist'] = weekresist
         weeksupport = data.ix[idx_week:idx,'Low'].min()
         data.ix[day,'WeekSupport'] = weeksupport
         
         idx_month =  data.index[day] - pd.DateOffset(months=1)
         monthresist = data.ix[idx_month:idx,'High'].max()
         data.ix[day,'MonthResist'] = monthresist         
         monthsupport = data.ix[idx_month:idx,'Low'].min()
         data.ix[day,'MonthSupport'] = monthsupport         
         
         idx_year =  data.index[day] - pd.DateOffset(years=1)
         yearresist = data.ix[idx_year:idx,'High'].max()
         data.ix[day,'YearResist'] = yearresist        
         yearsupport = data.ix[idx_year:idx,'Low'].min()
         data.ix[day,'YearSupport'] = yearsupport        

         allresist = data.ix[:idx,'High'].max()
         data.ix[day,'HistoryResist'] = allresist
         allsupport = data.ix[:idx,'Low'].min()
         data.ix[day,'HistorySupport'] = allsupport
         
     return data

def tradeSRs(data):
     sdate = dt.datetime(2012, 1, 1)
     s = data.index.get_loc(sdate,"bfill")
     cond1 = data.index > sdate
     cond2 = data.Close > data.WeekResist
     cond3 = data.Close.shift(1) < data.WeekResist
     cond4 = data.MonthResist > data.WeekResist * 1.03
     all_conds = (cond1) & (cond2) & (cond3) & (cond4)
     data['TradeEntry'] = 0
     data.ix[all_conds, 'TradeEntry'] = data.ix[all_conds, 'Close'] 
     
     TakeProfit = 0.02
#     StopLoss = -0.02
     data['TradeExit'] = 0
     data['TradeExitDate'] = 0
     for day in range(s,len(data)):
#         idx = data.index[day]
         if data.ix[day, 'TradeEntry'] > 0:
             for daynext in range(day,day+5):
                 if daynext>= len(data):
                     break
                 profit_pct = data.ix[daynext, 'High'] / data.ix[day, 'TradeEntry'] -1
                 if profit_pct > TakeProfit:
                     data.ix[day, 'TradeExit'] = data.ix[day, 'TradeEntry'] * (1+TakeProfit)
                     data.ix[day, 'TradeExitDate'] = data.index[daynext]
                     break
             else:
                     data.ix[day, 'TradeExit'] = data.ix[daynext, 'Close']
                     data.ix[day, 'TradeExitDate'] = data.index[daynext]
     
     return data

def tradePerformance(data):
    totaltrades = len(data[data['TradeEntry']>0])
    wintrades = len(data[data['TradeExit'] - data['TradeEntry']>0])
    losetrades = len(data[data['TradeExit'] - data['TradeEntry']<0])
    winpct = float (wintrades / totaltrades)
    
    
    data['WinPct'] = 0
    t_ind = data['TradeExit']>0
    data.ix[t_ind, 'WinPct'] = data.ix[t_ind, 'TradeExit'] /  data.ix[t_ind, 'TradeEntry'] - 1
    finalblance =  data.ix[t_ind, 'WinPct'].sum() + 1
    
#    print("total number of trades: {}".format(totaltrades))
#    print("number of winning trades: {}".format(wintrades))
#    print("number of losing trades: {}".format(losetrades))
#    print("winning trade pencentage: {:.2f}%".format(winpct*100))
#    print("final balance: {:.2f}% (initial 100%)".format(finalblance*100))
    
    result =[totaltrades,wintrades,losetrades,winpct*100,finalblance*100]
    return (data,result)



    
if __name__ == "__main__":
    symbol_list = ["AAPL","IBM","YHOO", "STX", "MSFT", "GOOGL", "HP" , "FB"]
    symbol_list = ["ADM", "T", "AVY", "BAX", "BLK", "BA", "BSX", "COG"]
    symbol_list = ["CELG", "CF", "CI", "CSCO", "C", "KO", "DAL", "EFX"]
    symbol_list = ["EQR", "ACN", "EBAY", "AVGO", "MMM", "ADBE", "AIG", "AON"]
    TradeResults = pd.DataFrame(columns = ['Symbol','TotalTrades','Win','Lose','WinPnt(%)','Balance(%)'])
    for sym in symbol_list:
        data_sym = loadData(sym)
        data_sym = findSRs(data_sym)
        data_sym = tradeSRs(data_sym)
        data_sym, res = tradePerformance(data_sym)
        TradeResults = TradeResults.append({
              'Symbol':sym,
              'TotalTrades':res[0],
              'Win':res[1],
              'Lose':res[2],
              'WinPnt(%)':res[3],
              'Balance(%)':res[4]},ignore_index=True
              )
    TradeResults['TotalTrades'] =  TradeResults['TotalTrades'].astype(int)
    TradeResults['Win'] =  TradeResults['Win'].astype(int)
    TradeResults['Lose'] =  TradeResults['Lose'].astype(int)
    TradeResults['WinPnt(%)'] =  TradeResults['WinPnt(%)'].round(2)
    TradeResults['Balance(%)'] =  TradeResults['Balance(%)'].round(2)
    TradeResults = TradeResults.set_index(['Symbol'])
    print(TradeResults)
    #ax = plot_candlestick(AAPL)

