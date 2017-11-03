from pyspark.streaming import StreamingContext
from pyspark.sql import SparkSession
from pyspark.sql import Row

from pyspark.ml.classification import LogisticRegressionModel
from pyspark.ml.feature import VectorAssembler
from plot.fraud_map import maps_stream
from plot.fraud_dashboard import upload_dashboard
from plot.colors.colors import get_color
from plotly.graph_objs import *

spark = SparkSession.builder.master("local[2]").appName("ScoringApp").getOrCreate()

sc = spark.sparkContext
sc.setLogLevel("ERROR")

batchIntervalSeconds = 2
hostname = 'localhost'
ip = 5900

columns = ['step', 'type', 'amount', 'nameOrig', 'oldbalanceOrg', 'newbalanceOrig', 'nameDest', 'oldbalanceDest',
           'newbalanceDest', 'isFraud', 'isFlaggedFraud', 'gps_latitude', 'gps_longitude', "id"]
float_columns = ['step', 'amount', 'oldbalanceOrg', 'newbalanceOrig', 'oldbalanceDest', 'newbalanceDest',
                 'gps_latitude', 'gps_longitude']
target_column = 'isFraud'

model = LogisticRegressionModel.load("data/models/pythonLogisticRegression")

vector_assembler = VectorAssembler(inputCols=float_columns, outputCol="features")

maps_stream.open()
upload_dashboard()


def parse_row(row):
    new_row = []
    for column in columns:
        if column in float_columns:
            new_row.append((column, float(row[column])))
        elif column == target_column:
            new_row.append((column, int(round(float(row[column])))))
        else:
            new_row.append((column, row[column]))
    return Row(**dict(new_row))


def create_features(df):
    return vector_assembler.transform(df)


def publish_journeys(rdd):
    for transaction in rdd.collect():
        lat, lon, prob = transaction["gps_latitude"], transaction["gps_longitude"], transaction["probability"][1]
        maps_stream.write(
            dict(lat=lat, lon=lon, type="Scattermapbox", marker=Marker(size=15, color=get_color(prob)),
                 text="{} {}\n\t{}\n\tAmount: {}\n\tType: {}".format(transaction["id"], transaction["prediction"], prob,
                                                                     transaction["amount"],
                                                                     transaction["type"])))


def transform_to_df(rdd):
    if rdd.isEmpty():
        return
    else:
        df = spark.createDataFrame(rdd.map(lambda line: line.split(",")), columns)
        new_df = spark.createDataFrame(df.rdd.map(parse_row))
        df_to_predict = create_features(new_df)
        df_with_prediction = model.transform(df_to_predict)
        # df_with_prediction.show()
        publish_journeys(df_with_prediction.rdd)
        return


def create_stream(batch_interval):
    ssc = StreamingContext(sc, batch_interval)

    dstream = ssc.socketTextStream(hostname, ip)

    dstream.foreachRDD(transform_to_df)

    return ssc


ssc = create_stream(batchIntervalSeconds)

ssc.start()
ssc.awaitTermination()
# maps_stream.close()
