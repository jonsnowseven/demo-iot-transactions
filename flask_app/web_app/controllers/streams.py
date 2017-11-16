import os
import signal
import sys
import time
import subprocess

from flask import Blueprint, current_app, request, url_for, jsonify, abort

from web_app.netcat.netcat import Netcat
from web_app.utils.decorators import parse_args
from web_app.utils.flask import RequestParser, Parameter

streams = Blueprint('stream', __name__)


@streams.route('/')
def index():
    return "<h1>Transactions Demo</h1>\n"


@streams.route('/stream/start/transactions', methods=['GET'])
@parse_args(RequestParser.withParameters(
    Parameter('speed', type=str, required=True),
    Parameter('transactions', type=str, required=True))
)
def start_stream_transactions(speed, transactions):
    """
    Start 'Transactions' streaming process
    ---
    tags:
      - streams
    parameters:
      - name: speed
        in: query
        description: Stream velocity
        required: true
        default: 1x
      - name: transactions
        in: query
        description: Transaction IDs (comma separated)
        required: true
    responses:
        200:
            description: Streaming operation done
    """
    frequency = 1.0 / float(speed.strip().replace('x', ''))

    journey_ids = [int(id_) for id_ in transactions.split(",")]

    print('Transactions: {} with speed: {} x'.format(str(journey_ids), str(frequency)))

    #  launch spark streaming app
    cmd = '/Users/joaoneves/Tools/spark-2.2.0-bin-hadoop2.7/bin/spark-submit spark_streaming_transactions_app.py'
    p_spark = subprocess.Popen(cmd.split(" "))
    print("Process ID of Spark Streaming subprocess %s" % p_spark.pid)

    time.sleep(5)

    script = '/Users/joaoneves/Documents/demo-iot-transactions/flask_app/web_app/scripts/transactions.py'
    p = subprocess.Popen(["python", script, str(frequency)] + [str(x) for x in journey_ids])
    print("Process ID of Source subprocess %s" % p.pid)

    current_app.PID_SPARK_STREAMING_TRANSACTIONS = p_spark.pid
    current_app.PID_TRANSACTIONS = p.pid

    return jsonify({"status": "streaming", "msg": "OK"})


@streams.route('/stream/stop/transactions', methods=['DELETE'])
def stop_stream_transactions():
    """
    Stop 'Transactions' streaming process
    ---
    tags:
      - streams
    responses:
        200:
            description: Streaming operation completed
    """
    os.kill(current_app.PID_TRANSACTIONS, signal.SIGTERM)
    os.kill(current_app.PID_SPARK_STREAMING_TRANSACTIONS, signal.SIGTERM)

    return jsonify({"status": "Streaming process stopped", "msg": "OK",
                    "pid": [current_app.PID_TRANSACTIONS, current_app.PID_SPARK_STREAMING_TRANSACTIONS]})
