from attr import mutable
import yfinance as yf
from yahoo_fin import stock_info as si
import pandas as pd
import numpy as np
from datetime import date
import streamlit as st


# In-memory user database (for demonstration)
user_db = {
    "admin": {"password": "admin123", "role": "admin"},
    "user1": {"password": "user123", "role": "user"}
}


# Authentication function
def authenticate(username, password):
    user = user_db.get(username)
    if user and user["password"] == password:
        return user["role"]
    return None


# Helper Function to Fetch Option Information
def option_info(ticker, strike_date):
    try:
        msft = yf.Ticker(ticker)
        if not strike_date:
            strike_date = msft.options[0]
        opt = msft.option_chain(strike_date).calls
        option_chain = pd.DataFrame(opt[opt["inTheMoney"] == False].iloc[0]).T.reset_index(drop=True)
        df = pd.concat([
            pd.DataFrame({"Ticker": ticker, "StrikeDate": strike_date, "StockPrice": msft.history(period="1d")["Close"].iloc[-1]}, index=[0]),
            option_chain
        ], axis=1)
        df["spread%"] = ((df["ask"] - df["bid"]) / df["bid"]).values[0]
        df["mid"] = ((df["ask"] - df["bid"]) / 2 + df["bid"]).values
        df = df[["Ticker", "StrikeDate", "StockPrice", "contractSymbol", "strike", "lastPrice", "bid", "ask", "spread%", "mid", "change", "percentChange", "volume", "openInterest", "impliedVolatility"]]
        return df
    except Exception as e:
        st.write(f"Error processing {ticker}: {e}")
        return pd.DataFrame()


# Convert DataFrame to CSV
def convert_df(dfs):
    return dfs.to_csv().encode("utf-8")


# App UI
st.title("Options Stocks Screener")

# User Authentication
# User Authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.username = None  # Add this line to store the username

if not st.session_state.authenticated:
    st.sidebar.header("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        role = authenticate(username, password)
        if role:
            st.session_state.authenticated = True
            st.session_state.role = role
            st.session_state.username = username  # Store the username in session state
            st.sidebar.success(f"Logged in as {username} ({role})")
        else:
            st.sidebar.error("Invalid username or password")
else:
    # Use the username from session state
    st.sidebar.success(f"Logged in as {st.session_state.username} ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.username = None  # Clear the username
        st.experimental_rerun()


# Main App Content
if st.session_state.authenticated and st.session_state.role:
    genre = st.sidebar.radio(
        "Upload Custom Data or Use the Screener",
        ("Custom Data", "Screener")
    )

    if genre == "Custom Data":
        agree = st.checkbox("Use custom strike dates")
        bt = st.button("Run")
        uploaded_file = st.file_uploader("Choose a file")
        if uploaded_file is not None:
            tickers_excel = pd.read_excel(uploaded_file, engine="openpyxl")
            if agree and bt:
                st.write("Great!")
                lst = []
                tickers = tickers_excel.Symbol.dropna().values
                dates = tickers_excel["Strike Date"].dropna().values
                dt = [pd.to_datetime(dates[i]).strftime("%Y-%m-%d") for i in range(len(dates))]
                st.write(f"Downloading {len(tickers)} stocks from custom file with dates provided")
                for i in range(len(tickers)):
                    st.progress(i / len(tickers))
                    lst.append(option_info(tickers[i], dt[i]))
                main_df = pd.concat(lst).drop_duplicates()
                st.write(main_df)
                csv = convert_df(main_df)
                st.download_button(
                    label="Download file data",
                    data=csv,
                    file_name="optionPrices.csv",
                    mime="text/csv"
                )

    elif genre == "Screener" :
        option = st.selectbox(
            "What data would you like to use",
            ("None", "Dow", "SP500")
        )
        lst = []
        if option == "Dow":
            df1 = pd.DataFrame(si.tickers_dow())
            st.write(f"Downloading {len(df1)} stocks from {option}")
            for i in range(len(df1)):
                st.progress(i / len(df1))
                lst.append(option_info(df1.values[i][0], None))
            main_df = pd.concat(lst).drop_duplicates()
            st.write(main_df)
            csv = convert_df(main_df)
            st.download_button(
                label="Download file data",
                data=csv,
                file_name=f"optionPrices{option}.csv",
                mime="text/csv"
            )
        
        elif option == "SP500":
            df2 = pd.DataFrame(si.tickers_sp500())
            st.write(f"Downloading {len(df2)} stocks from {option}")
            for i in range(len(df2)):
                st.progress(i / len(df2))
                lst.append(option_info(df2.values[i][0], None))
            main_df = pd.concat(lst).drop_duplicates()
            st.write(main_df)
            csv = convert_df(main_df)
            st.download_button(
                label="Download file data",
                data=csv,
                file_name=f"optionPrices{option}.csv",
                mime="text/csv"
            )
# Add your Screener functionality here as needed...
