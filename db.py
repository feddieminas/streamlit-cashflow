import sqlite3

"""
idea
https://github.com/bradtraversy/part_manager/blob/master/part_manager.py
do context manager
https://stackoverflow.com/questions/865115/how-do-i-correctly-clean-up-a-python-object
"""


class Database:

    def __init__(self, db):
        self.conn = sqlite3.connect(db, check_same_thread=False)
        self.cur = self.conn.cursor()
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS users \
                (id INTEGER PRIMARY KEY not null, \
                    name text, username text not null, passwd text not null)")
        self.conn.commit()

    def __enter__(self):
        return self

    def fetch(self):
        self.cur.execute("SELECT * FROM users")
        rows = self.cur.fetchall()
        return rows

    def fetchUser(self, username):
        self.cur.execute("SELECT * FROM users WHERE username=?", (username,))
        row = self.cur.fetchall()
        return row

    def insert(self, name, username, passwd):
        self.cur.execute("INSERT INTO users VALUES (NULL, ?, ?, ?)",
                         (name, username, passwd))
        self.conn.commit()

    def remove(self, id):
        self.cur.execute("DELETE FROM users WHERE id=?", (id,))
        self.conn.commit()

    def update(self, id, name, username, passwd):
        self.cur.execute(
            "UPDATE users SET name = ?, username = ?, passwd = ? WHERE id = ?",
                        (name, username, passwd, id))
        self.conn.commit()

    # function credentials here
    def user_credentials(self):
        users = []
        for row in self.fetch():
            users.append(row)

        usernames = [user[2] for user in users]
        names = [user[1] for user in users]
        passwords = [user[3] for user in users]

        credentials = {"usernames": {}}
        for un, name, pw in zip(usernames, names, passwords):
            user_dict = {"name": name, "password": pw}
            credentials["usernames"].update({un: user_dict})

        return credentials

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.close()
