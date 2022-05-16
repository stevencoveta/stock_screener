from attr import mutable
import yfinance as yf
from yahoo_fin import stock_info as si
from yahoo_fin.stock_info import *
import pandas as pd
import numpy as np
from datetime import date
import streamlit as st 


#@st.cache(ttl=600)
def option_info(ticker):
    try:
        msft = yf.Ticker(ticker)
        opt = msft.option_chain(msft.options[0])[0]
        stock_price = get_live_price(ticker)
        closestStrike = opt.strike[(np.abs(opt.strike - stock_price)).argmin()]
        option_chain = opt[opt.strike == closestStrike].reset_index(drop = True)
        df = pd.concat([ pd.DataFrame({"StockPrice": get_live_price(ticker)},index=[0]),option_chain], axis = 1)
        df["spread%"] = ((df["ask"] - df["bid"]) / df["bid"]).values[0]
        df["mid"] = (round(((df["ask"] - df["bid"]) /2),2) + df["bid"]).values[0]
        df = df[["StockPrice","contractSymbol","strike","lastPrice","bid","ask","spread%","mid","change","percentChange","volume","openInterest","impliedVolatility"]]
        lst.append(df)
        return df
    except:
        st.write(f"No ticker found for {ticker}")

def option_info_strike(ticker,date):
    try:
        msft = yf.Ticker(ticker)
        opt = msft.option_chain(date)[0]
        stock_price = get_live_price(ticker)
        closestStrike = opt.strike[(np.abs(opt.strike - stock_price)).argmin()]
        option_chain = opt[opt.strike == closestStrike].reset_index(drop = True)
        df = pd.concat([ pd.DataFrame({"StockPrice": get_live_price(ticker)},index=[0]),option_chain], axis = 1)
        df["spread"] = ((df["ask"] - df["bid"]) / df["bid"]).values[0]
        df["mid"] = ((df["ask"] - df["bid"]) + df["bid"]).values[0]
        df = df[["StockPrice","contractSymbol","strike","lastPrice","bid","ask","spread","mid","change","percentChange","volume","openInterest","impliedVolatility"]]
        lst.append(df)
        return df
    except:
        st.write(f"No ticker found or strike date incorrect for {ticker}")
             

def convert_df(dfs):
    return dfs.to_csv().encode('utf-8')


st.title("Options Stocks Screener")



genre = st.sidebar.radio(
     "Upload Custom Data or Use the Screener",
     ('Custom Data', 'Screener'))



if genre == 'Custom Data':
    agree = st.checkbox('Use custom strike dates')
    bt = st.button('Run')
    uploaded_file = st.file_uploader("Choose a file")

    if uploaded_file is not None:
        tickers_excel = pd.read_excel(uploaded_file,engine='openpyxl')
        if agree and bt:
            st.write('Great!')
            
            lst = []
            tickers = tickers_excel.Symbol.dropna().values
            tickers = tickers[tickers != "Cash"]
            tickers = tickers[:101]
            dates = tickers_excel["Date Added"].dropna().values
            dt = [pd.to_datetime(dates[i]).strftime("%Y-%m-%d") for i in range(len(dates))]
            dt = dt[:101]
            st.write(f"Downloading {len(tickers)} stocks from custom file with dates provided ")
            for i in range(len(tickers)):
                st.progress(i)
                lst.append(option_info_strike(tickers[i],dt[i]))
            main_df = pd.concat(lst).drop_duplicates()
            st.write(main_df)
            csv = convert_df(main_df)
            st.download_button(
                    label="Download file data ",
                    data=csv,
                    file_name='optionPrices.csv',
                    mime="text/csv")

        if not agree and bt:
            lst = []
            tickers = tickers_excel.Symbol.dropna().values
            tickers = tickers[tickers != "Cash"]
            tickers = tickers[:-101]
            st.write(f"Downloading {len(tickers)} stocks from custom file ")
            for i in range(len(tickers)):
                st.progress(i)
                lst.append(option_info(tickers[i]))
                
            main_df = pd.concat(lst).drop_duplicates()
            st.write(main_df)
            csv = convert_df(main_df)
            st.download_button(
                    label="Download file data ",
                    data=csv,
                    file_name='optionPrices.csv',
                    mime="text/csv")

elif genre == 'Screener':
    option = st.selectbox(
    'What data would you like to use',
    ('None','Dow', 'SP500'))
    lst = []
    if option == "None":
        pass
    if option == "Dow":
        df1 = pd.DataFrame( si.tickers_dow() )
        st.write(f"Downloading {len(df1)} stocks from {option} ")
        for i in range(len(df1)):
            st.progress(i)
            lst.append(option_info(df1.values[i][0]))
        main_df = pd.concat(lst).drop_duplicates()
        st.write(main_df)
        csv = convert_df(main_df)
        st.download_button(
                    label="Download file data ",
                    data=csv,
                    file_name='optionPrices.csv',
                    mime="text/csv")
    
    elif option == "SP500":
        df2 = pd.DataFrame( si.tickers_sp500() )
        st.write(f"Downloading {len(df2)} stocks from {option} ")
        for i in range(len(df2)):
            st.progress(i)
            lst.append(option_info(df2.values[i][0]))
        main_df = pd.concat(lst).drop_duplicates()
        st.write(main_df)
        csv = convert_df(main_df)
        st.download_button(
                    label="Download file data ",
                    data=csv,
                    file_name='optionPrices.csv',
                    mime="text/csv")
        
    
