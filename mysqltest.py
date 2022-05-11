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
DROP TABLE wordsOverTime;\
""",
"""\
CREATE TABLE wordsOverTime (
     word VARCHAR(30) NOT NULL,
     count INT NOT NULL,
     ts DATETIME DEFAULT CURRENT_TIMESTAMP,
     PRIMARY KEY (word, ts)
);\
""",
"""\
DROP USER IF EXISTS 'grafanaReader'@'localhost';\
""",
"""\
CREATE USER 'grafanaReader'@'localhost' IDENTIFIED BY 'password';\
""",
"""\
GRANT SELECT ON grafana.* TO 'grafanaReader'@'localhost';\
"""
]

for q in queries:
    mycursor.execute(q,)

mycursor.close()

mydb.commit()

print("Done")
