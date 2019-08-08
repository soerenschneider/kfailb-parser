
import dataclasses
import json

import redis
import backoff


class DataclassJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


class StreamEmitter:
    def __init__(self, client, stream_name="kfailb_incidents"):
        if client is None:
            raise ValueError("Client not initialized")

        self._cache = client
        self._stream_name = stream_name

    @backoff.on_exception(backoff.expo,
                          redis.exceptions.ConnectionError,
                          max_time=3600)
    def dispatch(self, incident):
        incident_json = json.dumps(incident, cls=DataclassJsonEncoder, ensure_ascii=False)
        incident_dict = { 'data': incident_json }
        self._cache.xadd(self._stream_name, incident_dict)
