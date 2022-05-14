from attr import mutable
import yfinance as yf
from yahoo_fin import stock_info as si
from yahoo_fin.stock_info import *
import pandas as pd
import numpy as np
from datetime import date
import streamlit as st 



st.title("Options Stocks Screener")
#@st.cache(ttl=600,allow_output_mutation=True)
def get_data(custom,tk):
    if custom == "Custom Data":
        today = date.today()
        d1 = today.strftime("%Y-%m-%d")
        date1 = (pd.to_datetime(d1) + pd.Timedelta("1 day")).strftime("%Y-%m-%d")
        data = yf.download(list(tk),d1,date1, auto_adjust=True,interval="1d")
        print(data)
        return data
        
        

    if custom == "Screener":
        today = date.today()
        d1 = today.strftime("%Y-%m-%d")
        date1 = (pd.to_datetime(d1) + pd.Timedelta("1 day")).strftime("%Y-%m-%d")
        df1 = pd.DataFrame( si.tickers_sp500(),columns = ["tickers"] )
        sp500 = df1.tickers.values 
    
        data = yf.download(list(sp500)[:10],d1,date1, auto_adjust=True,interval="1d")
        return data
        
        
#@st.cache(ttl=600, allow_output_mutation=True)
def option_info(ticker):
    msft = yf.Ticker(ticker)
    opt = msft.option_chain(msft.options[0])[0]
    stock_price = get_live_price(ticker)
    closestStrike = opt.strike[(np.abs(opt.strike - stock_price)).argmin()]
    return opt[opt.strike == closestStrike]

def stock_screener(close_price):
    df_options = []
    for i in (range(len(close_price.tickers.values))):
        st.progress(i)
        try:
            aa = option_info(close_price.tickers.values[i])
            df_options.append(pd.concat([(close_price[close_price.tickers == close_price.tickers.values[i]]).reset_index(drop = True),aa.reset_index(drop = True)],axis = 1))
        
        except: 
            st.write("No data for ticker",close_price.tickers.values[i])      
    return pd.concat(df_options)

def convert_df(dfs):
    return dfs.to_csv().encode('utf-8')


genre = st.sidebar.radio(
     "Upload Custom Data or Use the Screener",
     ('Custom Data', 'Screener'))

pwd = "0"

pwd = st.sidebar.text_input('Input Password')
if pwd == "1":
    st.write("Success !")
else: 
    st.write("Wrong Password")

if genre == 'Custom Data' and pwd == "1":
    #st.write('Upload your excel file')
    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        #st.write(uploaded_file.name)
        tickers_excel = pd.read_excel(uploaded_file,engine='openpyxl')
        st.write(list(tickers_excel.Symbol.values))
        tickers = tickers_excel.Symbol.dropna().values
        tickers = tickers[tickers != "Cash"]
        tickers = tickers[:-1]
        data = get_data(genre,tickers)
        maximumPrice = pd.DataFrame(data.Close.T.iloc[:,-1:].values).max()[0]
        minimumPrice = pd.DataFrame(data.Close.T.iloc[:,-1:].values).min()[0]
        maximumVolume = pd.DataFrame(data.Volume.T.iloc[:,-1:].values).dropna().max()[0]
        minimumVolume = pd.DataFrame(data.Volume.T.iloc[:,-1:].values).dropna().min()[0]
       

if genre == 'Screener' and pwd == "1" :
    data = get_data(genre,1)
    maximumPrice = pd.DataFrame(data.Close.T.iloc[:,-1:].values).max()[0]
    minimumPrice = pd.DataFrame(data.Close.T.iloc[:,-1:].values).min()[0]
    maximumVolume = pd.DataFrame(data.Volume.T.iloc[:,-1:].values).dropna().max()[0]
    minimumVolume = pd.DataFrame(data.Volume.T.iloc[:,-1:].values).dropna().min()[0]


minValue = st.sidebar.text_input('Min Stock Price')
maxValue = st.sidebar.text_input('Max Stock Price')

try:
    
    
    close_price = pd.concat([pd.DataFrame(data.Close.T.iloc[:,:1].index),pd.DataFrame(data.Close.T.iloc[:,-1:].values)],axis =1)
    volume_price = pd.concat([pd.DataFrame(data.Volume.T.iloc[:,:1].index),pd.DataFrame(data.Volume.T.iloc[:,-1:].values)],axis =1)
    close_price.columns = ["ticker","close"]
    volume_price.columns = ["tickers","volumes"]
    df = pd.concat([close_price,volume_price],axis =1)
    df = df.drop("ticker",axis =1)
    

    cpmax = df[df.close > int(minValue)]
    cpmin = cpmax[cpmax.close < int(maxValue)]
    cpmin = cpmin.set_index("tickers").reset_index()
    
    if len(cpmin) > 0:

        with st.spinner(f"Downloading prices for {len(cpmin)} stocks "):
            dff = stock_screener(cpmin.reset_index(drop = True)).drop(["contractSize","currency","inTheMoney"],axis = 1)
            dff["mid"] = round(((dff["ask"] - dff["bid"])/ 2) + dff["bid"],2)
            dff["spreadPercent"] = round(((dff["ask"] - dff["bid"])) / dff["ask"],2)

        st.success('Stocks Options downloaded!')
        #print(dff)
        st.dataframe(dff.fillna(0))
        dff = dff.fillna(0)
        csv = convert_df(dff)
        
        st.download_button(
            label="Download file data ",
            data=csv,
            file_name='optionPrices.xlsx',
            mime="text/csv")
        
    else:
        st.write("No Data with those filters")
except:
    pass
