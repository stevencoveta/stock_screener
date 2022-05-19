from attr import mutable
import yfinance as yf
from yahoo_fin import stock_info as si
from yahoo_fin.stock_info import *
import pandas as pd
import numpy as np
from datetime import date
import streamlit as st 


#@st.cache(ttl=600)
def option_info(ticker,date):
    try:
        msft = yf.Ticker(ticker,date)
        if date == False:
            strike_date = msft.options[0]
            opt = msft.option_chain(strike_date)[0]
        else: 
            strike_date = date
            opt = msft.option_chain(strike_date)[0]

        option_chain = pd.DataFrame(opt[opt.inTheMoney == False].iloc[0]).T.reset_index(drop = True)
        df = pd.concat([ pd.DataFrame({"Ticker":ticker,"StrikeDate":strike_date,"StockPrice": get_live_price(ticker)},index=[0]),option_chain], axis = 1)
        df["spread%"] = ((df["ask"] - df["bid"]) / df["bid"]).values[0]
        df["mid"] = ((df["ask"] - df["bid"]) /2 + df["bid"]).values
        df = df[["Ticker","StrikeDate","StockPrice","contractSymbol","strike","lastPrice","bid","ask","spread%","mid","change","percentChange","volume","openInterest","impliedVolatility"]]
        return df
    except:
        st.write(f"No ticker found or strike date incorrect for {ticker}")
    

def convert_df(dfs):
    return dfs.to_csv().encode('utf-8')


st.title("Options Stocks Screener")



genre = st.sidebar.radio(
     "Upload Custom Data or Use the Screener",
     ('Custom Data', 'Screener'))


pwd = "0001"

pwd = st.sidebar.text_input('Input Password')


if genre == 'Custom Data' and pwd == "0001":
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
            tickers = tickers
            dates = tickers_excel["Strike Date"].dropna().values
            dt = [pd.to_datetime(dates[i]).strftime("%Y-%m-%d") for i in range(len(dates))]
            dt = dt
            st.write(f"Downloading {len(tickers)} stocks from custom file with dates provided ")
            #my_bar = st.progress(0)
            for i in range(len(tickers)):
                st.progress(i/len(tickers))
                lst.append(option_info(tickers[i],dt[i]))
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
            tickers = tickers
            st.write(f"Downloading {len(tickers)} stocks from custom file ")
            for i in range(len(tickers)):
                st.progress(i/len(tickers))
                lst.append(option_info(tickers[i],False))
                
            main_df = pd.concat(lst).drop_duplicates()
            st.write(main_df)
            csv = convert_df(main_df)
            st.download_button(
                    label="Download file data ",
                    data=csv,
                    file_name='optionPrices.csv',
                    mime="text/csv")

elif genre == 'Screener' and pwd == "0001":
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
            st.progress(i/len(df1))
            lst.append(option_info(df1.values[i][0]))
        main_df = pd.concat(lst).drop_duplicates()
        st.write(main_df)
        csv = convert_df(main_df)
        st.download_button(
                    label="Download file data ",
                    data=csv,
                    file_name=f'optionPrices{option}.csv',
                    mime="text/csv")
    
    elif option == "SP500":
        df2 = pd.DataFrame( si.tickers_sp500() )
        st.write(f"Downloading {len(df2)} stocks from {option} ")
        for i in range(len(df2)):
            st.progress(i/len(df2))
            lst.append(option_info(df2.values[i][0]))
        main_df = pd.concat(lst).drop_duplicates()
        st.write(main_df)
        csv = convert_df(main_df)
        st.download_button(
                    label="Download file data ",
                    data=csv,
                    file_name=f'optionPrices{option}.csv',
                    mime="text/csv")
        
    
