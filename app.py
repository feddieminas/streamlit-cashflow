import os
import numpy as np
import pandas as pd
import io
import plotly.express as px
import streamlit as st
import streamlit_authenticator as stauth
from db import Database
import streamlit.components.v1 as components

# Ideas coming from Coding is fun and J-Harris

st.set_page_config(page_title="YTD MTD CASH FLOWS",
                   page_icon="https://www.mytilineos.gr/favicon.ico",
                   layout="wide")


# we import the jwtsecret. insert it on a safe place as an env variable
if os.path.exists('env.py'):
    import env

pd.options.display.float_format = '{:.2f}'.format


def load_css_file(css_file_path):
    with open(css_file_path) as f:
        return st.markdown(
            f"<style>{f.read()}</style>", unsafe_allow_html=True)


def load_js_file(js_file_path):
    with open(js_file_path) as f:
        return f"<script>{f.read()}</script>"


credentials = None
with Database('store.db') as db:
    credentials = db.user_credentials()

# --- USER AUTHENTICATION --- streamlit-authenticator

# a. cash_flow below is the json web token cookie stored on clients
# and will re-authenticate the user when refresh page
# b. jwtSecret random key to hash the cookie signature
# c. cookie_expiry_days is the number of days the cookie can be used for.
# the less days the safer
authenticator = stauth.Authenticate(credentials, "cash_flow",
                                    os.environ.get("jwtSecret"),
                                    cookie_expiry_days=30)

# "Login" is the name of the login form
# "main" or "sidebar" where the Login Form should be located
name, authentication_status, username = authenticator.login("Login", "main")

# if user inserts it to false
if authentication_status is False:
    st.error("Username/password is incorrect")

# if user has not inserted anything
if authentication_status is None:
    st.warning("Please enter your username and password")

# --- MAIN APP ---
if authentication_status:
    @st.cache
    def get_data_from_excel():
        df = pd.read_excel(
                io="cashflow_data.xlsx",
                engine="openpyxl",
                sheet_name="Sheet1",
                skiprows=0,
                usecols="A:J",
                converters={'Date': pd.to_datetime})
        return df

    df = get_data_from_excel()

    # ---- DATE RANGE ----
    st.title(":bar_chart: Cash Flow")

    min_date = df["Date"].min()
    max_date = df["Date"].max()

    THIS_DIR = os.getcwd()
    CSS_FILE = os.path.join(THIS_DIR, "style.css")
    load_css_file(CSS_FILE)

    left_column, right_column = st.columns(2)
    with left_column:
        st.markdown("""
        <a class="btn btn-outline">Reload Page</a> """,
                    unsafe_allow_html=True)
    with right_column:
        table_width = st.checkbox('Widen Table', value=True)

    def searchFunc(search_term):
        mask = np.column_stack(
            [df[col].astype(str).str.contains(
                search_term, na=False, case=False) for col in df])
        df_submit = df.loc[mask.any(axis=1)]
        return df_submit

    left_column, right_column = st.columns((1, 2))
    with left_column:
        # returns an array
        a_date = st.date_input("Pick a date", (min_date, max_date))
    with right_column:
        with st.form(key='searchform'):
            search_term = st.text_input("Search *")
            st.session_state['key'] = search_term
            submit = st.form_submit_button(label='Search')

    st.text("")

    # ---- SIDEBAR ----

    # "Logout" is the button's name
    # "sidebar" is the button's position
    authenticator.logout("Logout", "sidebar")  # streamlit-authenticator
    st.sidebar.title(f"Welcome {name}")  # streamlit-authenticator

    st.sidebar.header("Please Filter Here:")

    # sector
    tomeas = st.sidebar.multiselect(
        "Select the ΤΟΜΕΑΣ:",
        options=df["ΤΟΜΕΑΣ"].unique(),
        default=df["ΤΟΜΕΑΣ"].unique(),
    )

    groupnewco = st.sidebar.multiselect(
        "Select the Group NewCo:",
        options=df["Group NewCo"].unique(),
        default=df["Group NewCo"].unique(),
    )

    ic = st.sidebar.multiselect(
        "Select the IC:",
        options=df["IC"].unique(),
        default=df["IC"].unique(),
    )

    df = searchFunc(st.session_state['key'])
    df_selection = df.query(
            "`Group NewCo` == @groupnewco & ΤΟΜΕΑΣ == @tomeas & IC == @ic"
    )

    if len(a_date) == 2:
        df_selection = df_selection.query(
            "((Date >= @a_date[0]) & (Date <= @a_date[1]))"
        )

    numRows = 20  # table number of rows
    # use_container_width=True will widen the table in the screen
    # use_container_width=False will do more of a column fit
    st.dataframe(
        df_selection, use_container_width=table_width,
        height=(numRows + 1) * 35 + 3)

    @st.cache  # Cache the conversion to prevent computation on every rerun
    def convert_df_to_csv(df):
        return df.to_csv().encode('utf-8-sig')  # utf-8-sig to be able to read english and greek language

    @st.cache(allow_output_mutation=True)
    def convert_df_to_xlsx(df):
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Sheet1')
            # writer.save()
        return buffer

    left_column, right_column = st.columns((1, 2))
    with left_column:
        csv = convert_df_to_csv(df_selection)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name='dfselection.csv',
            mime='text/csv',
        )
    with right_column:
        # https://discuss.streamlit.io/t/how-to-add-a-download-excel-csv-function-to-a-button/4474/16
        xlsx = convert_df_to_xlsx(df_selection)
        st.download_button(
            label=":white_check_mark: Download Excel",
            data=xlsx,
            file_name="dfselection.xlsx",
            mime="application/vnd.ms-excel"
        )

    st.markdown("""
    <hr style="height:0.313rem;max-width:15.5rem;margin:0.625rem auto;
    border:none;background-color:#779fc9;" /> """,
                unsafe_allow_html=True)

    # --- MAIN APP ---

    left_column, right_column = st.columns(2)

    df_by_tomeas = df_selection.groupby(
        by=["ΤΟΜΕΑΣ"]).sum(
        numeric_only=True)[["Amount"]].sort_values(by="Amount")

    fig_tomeas_amounts = px.bar(
        df_by_tomeas,
        x="Amount",
        y=df_by_tomeas.index,
        orientation="h",
        title="<b>Amounts by Tomeas</b>",
        color_discrete_sequence=["#0083B8"] * len(df_by_tomeas),
        template="plotly_white",
    )

    fig_tomeas_amounts.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=(dict(showgrid=False))
    )

    left_column.plotly_chart(fig_tomeas_amounts, use_container_width=True)

    df_by_group = (
        df_selection.assign(
                CREDIT_DEBT=np.select(
                    [df_selection.Amount >= 0,
                     df_selection.Amount < 0], ['+', "-"], "+"))
    )
    df_by_group.Amount = np.where(
        df_by_group.Amount >= 0, df_by_group.Amount, df_by_group.Amount * -1)
    df_by_group = df_by_group.groupby(
        by=["CREDIT_DEBT"]).sum(numeric_only=True)[["Amount"]]
    if '+' not in df_by_group.index:
        df_by_group.loc["+"] = pd.Series([], dtype=pd.StringDtype())
    if '-' not in df_by_group.index:
        df_by_group.loc["-"] = pd.Series([], dtype=pd.StringDtype())
    df_by_group = df_by_group.sort_index()
    fig_credit_debt = px.pie(
        df_by_group, values="Amount", names=df_by_group.index,
        title="<b>Net Cash</b>", hole=0.3,
        color=['green', '#b2182b'],
        color_discrete_sequence=['green', '#b2182b'],
        color_discrete_map={'+': 'green', '-': '#b2182b'})

    right_column.plotly_chart(fig_credit_debt, use_container_width=True)

    JS_FILE = os.path.join(THIS_DIR, "script.js")
    js_contents = load_js_file(JS_FILE)
    components.html(js_contents)


# CLI to run application
# streamlit run app.py
