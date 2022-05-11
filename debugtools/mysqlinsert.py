import mysql.connector

mydb = mysql.connector.connect(
    host="localhost",
    port="3306",
    user="root",
    password="password",
    database="grafana",
)
mycursor = mydb.cursor()

queries = [
"""\
INSERT INTO wordsOverTime (word, count) VALUES('hello', 4)\
""",
"""\
INSERT INTO wordsOverTime (word, count) VALUES('test', 10)\
""",
"""\
INSERT INTO wordsOverTime (word, count) VALUES('diskriminierung', 2)\
""",
]

for q in queries:
    mycursor.execute(q,)

mycursor.close()

mydb.commit()

print("Done")
