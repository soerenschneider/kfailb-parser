#!/usr/bin/env python3

import logging
import configargparse

import redis
import backoff

from kfailb import IncidentParser
from kfailb import Incident
from kfailb import StreamEmitter

from prometheus_client import Counter


class KFailB:
    """
    Downloads website data, parses it and emits transformed data.
    """
    def __init__(self, args):
        self._parser = IncidentParser(args.metrics_prefix)

        logging.info("Trying to connect to redis at %s:%d...", args.redis_host, args.redis_port)
        self._client = self.init(host=args.redis_host, port=args.redis_port)
        self._emitter = StreamEmitter(self._client, stream_name=args.stream_sending)
        self._stream_name = args.stream_listening

        self._prom_consumed_messages = Counter(f'{args.metrics_prefix}_consumed_messages_total', 'Description of counter')
        self._prom_consumed_messages_err = Counter(f'{args.metrics_prefix}_consumed_messages_errors_total', 'Description of counter')

    @backoff.on_exception(backoff.expo,
                          redis.exceptions.ConnectionError,
                          max_time=300)
    def init(self, host="localhost", port=6379, db=0):
        client = redis.Redis(host=host, port=port, db=db, charset="utf-8", decode_responses=True)
        client.get("x")
        logging.info("Successfully connected to redis")
        return client

    @backoff.on_exception(backoff.expo,
                          redis.exceptions.ConnectionError,
                          max_time=3600)
    def read_stream(self, last_id='$'):
        streams = {self._stream_name: last_id}
        incidents = self._client.xread(streams, count=100, block=0)
        last_seen_id = None

        for incident in incidents:
            payload = incident[1][0]
            msg_id = payload[0]
            last_seen_id = msg_id
            try:
                line = payload[1]["line"]
                problem = payload[1]["problem"]

                logging.debug("Received message: Line %s, problem: %s", line, problem)
                text, stations = self._parser.parse_data(problem)
                parsed = Incident(line=line, what=text, stations=stations)
                self._prom_consumed_messages.inc()

                self._emitter.dispatch(parsed)
            except KeyError:
                logging.error("Missing 'line' and/or 'problem' in msg: %s", payload)
                self._prom_consumed_messages_err.inc()
        return last_seen_id

    def start(self):
        cont = True
        logging.info("Waiting for messages on stream")
        try:
            msg_id = "$"
            while cont:
                msg_id = self.read_stream(msg_id)
        except KeyboardInterrupt:
            cont = False


def parse_args():
    """
    Parses the arguments given to the program.
    :return: parsed Namespace with the arguments.
    """
    parser = configargparse.ArgumentParser(prog='k-fail-b')
    parser.add_argument('-d', '--debug', action="store_true", env_var="KFAILB_DEBUG",
                        default=False)
    parser.add_argument('--prometheus-port', type=int, dest="prometheus_port",
                        action="store", env_var="KFAILB_PROMPORT", default=8080)
    parser.add_argument('-p', '--redis-port', type=int, dest="redis_port",
                        action="store", env_var="KFAILB_PORT", default=6379)
    parser.add_argument('-r', '--redis-host', dest="redis_host", action="store",
                        env_var="KFAILB_REDIS", default="localhost")
    parser.add_argument('-m', '--metrics-prefix', dest='metrics_prefix', action='store',
                        env_var='KFAILB_METRICS_PREFIX', default='kfailb_parser')
    parser.add_argument('--listening-stream-name', dest='stream_listening', action='store',
                        env_var='KFAILB_STREAM_LISTEN', default='kfailb_scrape')
    parser.add_argument('--sending-stream-name', dest='stream_sending', action='store',
                        env_var='KFAILB_STREAM_SEND', default='kfailb_incidents')
    return parser.parse_args()


def setup_logging(args):
    """ Sets up the logging. """
    loglevel = logging.INFO
    if args.debug:
        loglevel = logging.DEBUG

    logging.basicConfig(level=loglevel, format='%(levelname)s\t %(asctime)s %(message)s')
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger('chardet.charsetprober').setLevel(logging.INFO)


if __name__ == '__main__':
    args = parse_args()
    setup_logging(args)
    KFailB(args).start()
