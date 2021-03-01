from flask import Flask, Response
import  requests


from pymemcache.client.hash import HashClient
from cassandra.cluster import Cluster
from cassandra.query import dict_factory
import json
import time
import re
import sys

client = HashClient([
    'memcached1',
    'memcached2',
    'memcached3',
])


app = Flask(__name__)

@app.route("/")
def root():
    resp = requests.get("http://web-client/")
    return (resp.text, resp.status_code, resp.headers.items())

@app.route("/1")
def _1_():
    #data = select("701111", "0000")
    data = select("702212", "0000")

    #data = select("701111", "0000", "M11", 1999)
    return Response(response=json.dumps(data))

@app.route("/2")
def _2_():
    cluster= Cluster(["cassandra"])
    session = cluster.connect(keyspace="bls_ap")
    session.row_factory = dict_factory

    #TODO need to change this be resolved
    us_average_area_code = "0000"
    query = "SELECT * From series where area_code='{}' ALLOW FILTERING;".format(us_average_area_code)
    result = session.execute(query)

    table_data = {}
    for row in result.all():
        table_data[row["item_code"]] = select(row["item_code"], "0000")

    return Response(response=json.dumps(table_data))

def select(item, area, start_month=None, start_year=None, end_month=None, end_year=None):
    cluster= Cluster(["cassandra"])
    session = cluster.connect(keyspace="bls_ap")
    session.row_factory = dict_factory

    session.execute("CREATE INDEX IF NOT EXISTS ON series(item_code);")
    query = "SELECT * FROM series where item_code='{}' ALLOW FILTERING;".format(item)
    result = session.execute(query)
    series = None
    for row in result.all():
        if row["area_code"] == area:
            series = row

    if series is None:
        raise Exception

    log(series["series_id"])

    if (start_month and start_year) or (end_month and end_year):
        assert int(series["begin_year"]) <= start_year and end_year <= int(series["end_year"])
        #assert client.get("period.{}".format(series.begin_period)) <= month <= client.get("period.{}".format(series.end_period))
        assert int(series["begin_period"].replace("M", "")) <= int(start_month.replace("M", "")) and \
                int(end_month.replace("M", ""))  <= int(series["end_period"].replace("M", ""))

        query = "SELECT * FROM data where series_id='{}' and period='{}' and year='{}'".format(series["series_id"], start_month, start_year)
    else:
        query = "SELECT * FROM data where series_id='{}'".format(series["series_id"])

    result = session.execute(query)
    cluster.shutdown()
    data = result.all()

    table_data = []
    for index in range(len(data)):
        #log("{} {}".format(data[index]["year"], data[index]["period"]))
        del(data[index]["series_id"])
        del(data[index]["footnote_codes"])
        data[index]["period"] = int(data[index]["period"].replace("M", ""))

        try:
            data[index]["price"] = float(data[index]["value"])
        except Exception as ex:
            # there are instances of "   -" values, indicating no surveyed value
            data[index]["price"] = float(data[index - 1]["price"])

        # change in price from index 0
        data[index]["value"] = float(data[index]["price"]) / float(data[0]["price"]) * 100

        # change of ratio between price and amount purchased by minimum wage
        data[index]["ratio"] = (data[index]["price"] / mw(data[index]["year"])) / (data[0]["price"] / mw(data[0]["year"])) * 100
        data[index]["minimum"] = mw(data[index]["year"])


        table_data.append([data[index]["year"], data[index]["period"], data[index]["price"], data[index]["value"], data[index]["ratio"] ])


    return table_data

def mw(year):
    a = {
            "1967": 1.4,
            "1968": 1.6,
            "1969": 1.6,
            "1970": 1.6,
            "1971": 1.6,
            "1972": 1.6,
            "1973": 1.6,
            "1974": 2.0,
            "1975": 2.1,
            "1976": 2.3,
            "1977": 1.6,
            "1978": 2.6,
            "1979": 2.9,
            "1980": 3.1,
            "1981": 3.35,
            "1982": 3.35,
            "1983": 3.35,
            "1984": 3.35,
            "1985": 3.35,
            "1986": 3.35,
            "1987": 3.35,
            "1988": 3.35,
            "1989": 3.35,
            "1990": 3.8 ,
            "1991": 4.25,
            "1992": 4.25,
            "1993": 4.25,
            "1994": 4.25,
            "1995": 4.25,
            "1996": 4.75,
            "1997": 5.15,
            "1998": 5.15,
            "1999": 5.15,
            "2000": 5.15,
            "2001": 5.15,
            "2002": 5.15,
            "2003": 5.15,
            "2004": 5.15,
            "2005": 5.15,
            "2006": 5.15,
            "2007": 5.85,
            "2008": 6.55,
            "2009": 7.25,
            "2010": 7.25,
            "2011": 7.25,
            "2012": 7.25,
            "2013": 7.25,
            "2014": 7.25,
            "2015": 7.25,
            "2016": 7.25,
            "2017": 7.25,
            "2018": 7.25,
            "2019": 7.25,
            "2020": 7.25
            #"2020": 9.57
            }
    return a[year]

def log(message):
    print(message, file=sys.stderr)


if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host='0.0.0.0', debug=True, port=12345)
