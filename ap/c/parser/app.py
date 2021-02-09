from pymemcache.client.hash import HashClient
from cassandra.cluster import Cluster
import json
import time
import re

client = HashClient([
    'memcached1',
    'memcached2',
    'memcached3',
])


def read_file(file):
    with open("./data/ap.{}".format(file)) as f:
        for line in f:
            data = line.rstrip().replace('  ', '').split("\t")
            for i in range(len(data)):
                data[i] = re.sub("\s+$", "", data[i])
            yield data



def create_table(columns, table):

    query = "CREATE TABLE IF NOT EXISTS {} ({} text, PRIMARY KEY({}, {}, {}));".format(
        table,
        " text, ".join(columns),
        columns[0], columns[1], columns[2])

    session.execute(query)

def insert_record(file, columns, data):

    while len(data) != len(columns):
        data.append("")

    query = "INSERT INTO {} ({}) VALUES ('{}');".format(
        file,
        ", ".join(columns),
        "', '".join(data))

    session.execute(query)

def parse_store():

    data_files = ["series", "data.3.Food", "data.2.Gasoline", "data.1.HouseholdFuels", "data.0.Current"]

    for file in data_files:
        table = file.split(".")[0]
        lines = read_file(file)
        columns = next(lines)
        create_table(columns, table)
        while True:
            try:
                insert_record(table, columns, next(lines))
            except StopIteration as ex:
                break


    series_files = ["area", "seasonal", "period", "item"]
    for file in series_files:
        lines = read_file(file)
        columns = next(lines)
        while True:
            try:
                data = next(lines)

                while len(data) != len(columns):
                    data.append("")
                store_data = {}
                for index in range(len(columns)):
                    store_data[columns[index]] = data[index]

                client.set('{}.{}'.format(file, data[0]), json.dumps(store_data))
            except StopIteration as ex:
                break

    time.sleep(10)


def select(item, area, month=None, year=None):
    session.execute("CREATE INDEX IF NOT EXISTS ON series(item_code);")
    query = "SELECT * FROM series where item_code='{}' ALLOW FILTERING;".format(item)
    result = session.execute(query)
    series = None
    for row in result.all():
        if row.area_code == area:
            series = row

    if series is None:
        raise Exception

    print(series.begin_year)
    print(series.end_year)
    print(client.get("period.{}".format(series.begin_period)))
    assert int(series.begin_year) <= year <= int(series.end_year)
    #assert client.get("period.{}".format(series.begin_period)) <= month <= client.get("period.{}".format(series.end_period))
    assert int(series.begin_period.replace("M", "")) <= int(month.replace("M", "")) <= int(series.end_period.replace("M", ""))



    print(series.series_id)
    query = "SELECT * FROM data where series_id='{}' and period='{}' and year='{}'".format(series.series_id, month, year)
    result = session.execute(query)
    for i in result.all():
        print(i)

    print(len(result.all()))



cluster= Cluster(["cassandra"])
session = cluster.connect()
session.execute("CREATE KEYSPACE IF NOT EXISTS bls_ap WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 3 };")
session.set_keyspace("bls_ap")

#parse_store()
select("701111", "0000", "M11", 1999)

