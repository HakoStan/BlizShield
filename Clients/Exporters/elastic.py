import uuid
import datetime
import elasticsearch
from elasticsearch import helpers


def results_gen(results: list) -> dict:
    for result in results:
        plugin_data = result['Plugin']
        plugin_type = result['Type']
        plugin_config = result['Config']
        for scan in result['Result']:
            yield {
                '_index': f'{plugin_data.lower()}-{datetime.datetime.now().strftime("%m-%y")}',
                '_type': 'document',
                '_id': str(uuid.uuid4()),
                    'plugin': plugin_data,
                    'plugin_type': plugin_type,
                    'run_config': plugin_config,
                    'result': scan,
                    '@timestamp': datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()
            }


def export(results: list) -> None:
    # TODO: change hard codded variables to config values
    es = elasticsearch.Elasticsearch(hosts='127.0.0.1', port=9200)
    helpers.bulk(es, results_gen(results))
