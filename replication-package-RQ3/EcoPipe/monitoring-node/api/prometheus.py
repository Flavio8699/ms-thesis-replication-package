from prometheus_api_client import PrometheusConnect

def get_prometheus(host):
    prometheus_url = f'http://{host}:9595'
    return PrometheusConnect(url=prometheus_url, disable_ssl=True)

def query(host, query):
    return get_prometheus(host).custom_query(query)
    
def get_consumption_rate_microjoules(host, date):
    result = query(host, f'rate(scaph_host_energy_microjoules[20s]@{date.timestamp()})')
    consumption = float(result[0]['value'][1])
    return consumption

def get_consumption_microjoules(host, date, duration):
    result = query(host, f'increase(scaph_host_energy_microjoules[{duration}s]@{date.timestamp()})')
    consumption = float(result[0]['value'][1])
    return consumption
