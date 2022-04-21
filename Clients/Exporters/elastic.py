import uuid
import datetime
import elasticsearch
from elasticsearch import helpers

from .exporter import Exporter


class ElasticExporter(Exporter):
    def __init__(self, ip, port) -> None:
        super().__init__()
        self.__ip = ip
        self.__port = port

    def __results_gen(self, results: list) -> dict:
        for result in results:
            scan_timestamp = datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()
            plugin_data = result['Plugin']
            plugin_type = result['Type']
            plugin_config = result['Config']
            for scan in result['Result']:
                yield {
                    '_index': f'plugin-{plugin_data.lower()}-{datetime.datetime.now().strftime("%m-%y")}',
                    '_type': 'document',
                    '_id': str(uuid.uuid4()),
                    'plugin': plugin_data,
                    'plugin_type': plugin_type,
                    'run_config': plugin_config,
                    '@timestamp': scan_timestamp,
                    **scan
                }

    def export(self, results: list) -> None:
        es = elasticsearch.Elasticsearch(hosts=self.__ip, port=self.__port)
        helpers.bulk(es, self.__results_gen(results))
