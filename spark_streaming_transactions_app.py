from pyspark.streaming import StreamingContext
from pyspark.sql import SparkSession
from pyspark.sql import Row
import numpy as np
from plotly.graph_objs import *

from plot.transactions_map import maps_stream
from plot.transactions_pie import transactions_pie_stream
from plot.dashboard import upload_dashboard
from plot.color.color import convert_to_color

spark = SparkSession.builder.master("local[2]").appName("ScoringApp").getOrCreate()

sc = spark.sparkContext
sc.setLogLevel("ERROR")

batchIntervalSeconds = 5
hostname = 'localhost'
ip = 5900

columns = ['step', 'type', 'amount', 'nameOrig', 'oldbalanceOrg', 'newbalanceOrig', 'nameDest', 'oldbalanceDest',
           'newbalanceDest', 'isFraud', 'isFlaggedFraud', 'gps_latitude', 'gps_longitude', "location", "id",
           "entity_id"]
float_columns = ['step', 'amount', 'oldbalanceOrg', 'newbalanceOrig', 'oldbalanceDest', 'newbalanceDest',
                 'gps_latitude', 'gps_longitude']

transactions_pie_stream.open()
maps_stream.open()
upload_dashboard()


def parse_row(row):
    new_row = []
    for column in columns:
        if column in float_columns:
            new_row.append((column, float(row[columns.index(column)])))
        else:
            new_row.append((column, row[columns.index(column)]))
    return Row(**dict(new_row))


def publish_transactions_to_map(rdd):
    color = {}
    for transaction in rdd.collect():
        if transaction["entity_id"] not in color:
            color[transaction["entity_id"]] = convert_to_color(transaction["entity_id"])
        lat, lon = transaction["gps_latitude"], transaction["gps_longitude"]
        maps_stream.write(
            dict(lat=lat, lon=lon, type="Scattermapbox",
                 marker=Marker(size=15, color=color[transaction["entity_id"]]),
                 text="{}\n\tAmount: {}\n\tType: {}".format(transaction["id"] + "/" + transaction["entity_id"],
                                                            transaction["amount"],
                                                            transaction["type"])))


def publish_transactions_to_pie(rdd):
    if not rdd.isEmpty():
        array_data = np.transpose(np.array(rdd.collect())).tolist()
        transactions_pie_stream.write(dict(labels=array_data[0],
                                           values=array_data[1],
                                           type='pie'))


def parse_rdd(rdd):
    if not rdd.isEmpty():
        return rdd.map(lambda line: line.split(",")).map(parse_row)
    else:
        return sc.parallelize([])


def create_stream(batch_interval):
    ssc = StreamingContext(sc, batch_interval)

    dstream_input = ssc.socketTextStream(hostname, ip)

    dstream_parsed = dstream_input.transform(parse_rdd)

    dstream_parsed.foreachRDD(publish_transactions_to_map)

    dstream_total_by_location = dstream_parsed.map(lambda row: (row["location"], row["amount"])).reduceByKey(
        lambda a, b: a + b)

    # dstream_total_by_location.pprint()

    dstream_total_by_location.foreachRDD(publish_transactions_to_pie)

    return ssc


ssc = create_stream(batchIntervalSeconds)

ssc.start()
ssc.awaitTermination()
# maps_stream.close()
