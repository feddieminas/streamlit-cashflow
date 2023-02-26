import pandas as pd
import streamlit_authenticator as stauth
from db import Database

df = pd.read_excel(
    io="credentials.xlsx",
    engine="openpyxl",
    sheet_name="Sheet1",
    skiprows=0,
    usecols="A:C"
)

names = [item for sublist in df.iloc[:, [0]].values for item in sublist]
usernames = [item for sublist in df.iloc[:, [1]].values for item in sublist]
passwords = [item for sublist in df.iloc[:, [2]].values for item in sublist]
# uses bcrypt for password hashing
hashed_passwords = stauth.Hasher(passwords).generate()

# use sql to store the users
with Database('store.db') as db:
    for i in range(0, len(usernames)):
        recExist = db.fetchUser(usernames[i])
        if not recExist:
            db.insert(names[i], usernames[i], hashed_passwords[i])