import sqlite3
import yfinance as yf
from yahoo_fin import stock_info as si
import pandas as pd
import numpy as np
from datetime import date
import streamlit as st

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Create table if not exists
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    role TEXT
)
''')
conn.commit()

# Function to authenticate user
def authenticate(username, password):
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    if user:
        return user[2]  # Return role (user[2] is the role)
    return None

# Function to create a new user
def create_new_user(username, password, role="user"):
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone() is None:  # If the user doesn't exist
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        st.success(f"User {username} created successfully!")
    else:
        st.error(f"User {username} already exists!")

# Function to delete a user
def delete_user(username):
    cursor.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    st.success(f"User {username} deleted successfully!")

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
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.username = None  # Initialize username in session state

# Check if the admin user exists, if not, create it
def create_admin_if_not_exists():
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if cursor.fetchone() is None:  # Admin doesn't exist
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("admin", "admin123", "admin"))
        conn.commit()
        st.success("Admin user created successfully!")

# Run the function to create admin if not exists
create_admin_if_not_exists()

if not st.session_state.authenticated:
    st.sidebar.header("Login")
    st.session_state.username = st.sidebar.text_input("Username")  # Store username in session state
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        role = authenticate(st.session_state.username, password)  # Use username from session state
        if role:
            st.session_state.authenticated = True
            st.session_state.role = role
            st.sidebar.success(f"Logged in as {st.session_state.username} ({role})")
        else:
            st.sidebar.error("Invalid username or password")
else:
    st.sidebar.success(f"Logged in as {st.session_state.username} ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.username = None  # Reset username
        st.experimental_rerun()

# Admin Panel
if st.session_state.role == "admin":
    st.header("Admin Panel: Manage Users")
    admin_action = st.radio("Choose an action", ["Create User", "Delete User"])

    if admin_action == "Create User":
        new_user = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        role = st.selectbox("Role", ["user", "admin"])
        if st.button("Create User"):
            create_new_user(new_user, new_password, role)

    elif admin_action == "Delete User":
        user_to_delete = st.selectbox("Select User to Delete", [user[0] for user in cursor.execute("SELECT username FROM users").fetchall()])
        if st.button("Delete User"):
            delete_user(user_to_delete)

# Main App Content (e.g., your screener logic here)
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

    # Add your Screener functionality here as needed...

    elif genre == "Screener":
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
