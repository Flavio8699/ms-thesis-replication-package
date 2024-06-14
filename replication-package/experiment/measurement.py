#!/usr/bin/python3

import requests
import logging
from dateutil import parser
import time
from datetime import datetime
import csv
import os
from fabric import Connection
from invoke import Responder
import argparse
from configparser import ConfigParser, ExtendedInterpolation

DIR = os.path.dirname(os.path.realpath(__file__))

config = ConfigParser(interpolation=ExtendedInterpolation())
config.read(f'{DIR}/config.ini')

argparser = argparse.ArgumentParser(description='Run experiment for specific concurrency settings')

argparser.add_argument('--concurrency', type=int, help='Concurrency degree (combination of either 1 2 3 4 5 6)', metavar='C', nargs='+', choices=[1, 2, 3, 4, 5, 6], required=True)
argparser.add_argument('--sample', type=int, help='Sample size per concurrency', metavar='S', required=True)

args = argparser.parse_args()

SAMPLE_SIZE = args.sample
CONCURRENCY_DEGREES = args.concurrency

def trigger_pipeline():
    logging.info(f"Triggering pipeline...")
    try:
        response = requests.post(
            f"{config['GITLAB']['API_URL']}/trigger/pipeline?token={config['GITLAB']['PIPELINE_TRIGGER_TOKEN']}&ref=master")
        logging.info(f"Trigger response: {response.status_code}")
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Pipeline failed to trigger: {str(e)}")
        return None
    else:
        logging.info(
            f"(id: {response.json()['id']}) Pipeline successfully triggered")
        return response.json()['id']


def is_pipeline_finished(id):
    logging.info(f"(id: {id}) Checking pipeline status...")
    try:
        response = requests.get(
            f"{config['GITLAB']['API_URL']}/pipelines/{id}?private_token={config['GITLAB']['PERSONAL_ACCESS_TOKEN']}")
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Pipeline status could not be retrieved: {str(e)}")
        return False
    else:
        logging.info(
            f"(id: {id}) Pipeline status: {response.json()['status']}")
        if response.json()["finished_at"] is not None:
            return response.json()['status']
        else:
            return False


def wait_for_pipeline_completion(id):
    res = is_pipeline_finished(id)
    while not res:
        logging.info(f"(id: {id}) Waiting for pipeline to complete...")
        time.sleep(60)
        res = is_pipeline_finished(id)
    return res


def cooldown(duration):
    logging.info(f"Cooling down for {duration} seconds...")
    time.sleep(duration)


def is_temp_under(temp, average_period=5, average_unit="m"):
    logging.info(f"Checking average CPU temp in last {average_period}{average_unit}...")
    try:
        response = requests.get(config['PROMETHEUS']['API_URL'], params={
                                "query": f"avg_over_time(node_hwmon_temp_celsius{{chip='nvme_nvme0',sensor='temp1'}}[{average_period}{average_unit}])"})
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to query Prometheus: {str(e)}")
        return None
    else:
        curr_temp = float(response.json()["data"]["result"][0]["value"][1])
        logging.info(f"CPU temp: {curr_temp} C")
        return curr_temp < float(temp)


def cooldown_until_below(temp, wait_time=600):
    start_time = time.time()
    logging.info(f"Cooling down until average CPU temp is below {temp} C")
    while not is_temp_under(temp):
        logging.info(f"CPU too hot, waiting...")
        time.sleep(wait_time)
    logging.info(f"Total cooldown period: {time.time()-start_time}s")
    return True


def get_avg_watts_between(start, end):
    duration = end - start
    try:
        logging.info(f"Getting average Watts consumption...")
        response = requests.get(config['PROMETHEUS']['API_URL'], params={"query": f"avg_over_time(scaph_host_power_microwatts[{duration}s]@{end})"})
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to query Prometheus: {str(e)}")
        return None
    else:
        result = response.json()["data"]["result"]
        avg_watts_consumption = float(result[0]["value"][1])/10**6 if result else "None"
        logging.info(f"Average Watts consumption = {avg_watts_consumption} W")
        return avg_watts_consumption


def get_avg_ram_between(start, end):
    duration = end - start
    try:
        logging.info(f"Getting average RAM usage...")
        response = requests.get(config['PROMETHEUS']['API_URL'], params={"query": f"avg_over_time(scaph_host_memory_used_bytes[{duration}s]@{end})"})
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to query Prometheus: {str(e)}")
        return None
    else:
        result = response.json()["data"]["result"]
        avg_ram_usage = float(result[0]["value"][1])/10**6 if result else "None"
        logging.info(f"Average RAM usage = {avg_ram_usage} MB")
        return avg_ram_usage


def get_avg_disk_between(start, end):
    duration = end - start
    try:
        logging.info(f"Getting average disk usage...")
        response = requests.get(config['PROMETHEUS']['API_URL'], params={"query": f"avg_over_time(scaph_host_disk_used_bytes[{duration}s]@{end})"})
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to query Prometheus: {str(e)}")
        return None
    else:
        result = response.json()["data"]["result"]
        avg_disk_usage = float(result[0]["value"][1])/10**6 if result else "None"
        logging.info(f"Average disk space usage = {avg_disk_usage} MB")
        return avg_disk_usage

def get_avg_cpu_usage_between(start, end):
    duration = end - start
    try:
        logging.info(f"Getting average CPU usage...")
        response = requests.get(config['PROMETHEUS']['API_URL'], params={"query": f"avg_over_time(node_cpu_usage[{duration}s]@{end})"})
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to query Prometheus: {str(e)}")
        return None
    else:
        result = response.json()["data"]["result"]
        avg_cpu_usage = float(result[0]["value"][1]) if result else "None"
        logging.info(f"Average CPU usage = {avg_cpu_usage}%")
        return avg_cpu_usage

def get_max_cpu_usage_between(start, end):
    duration = end - start
    try:
        logging.info(f"Getting max CPU usage...")
        response = requests.get(config['PROMETHEUS']['API_URL'], params={"query": f"max_over_time(node_cpu_usage[{duration}s]@{end})"})
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to query Prometheus: {str(e)}")
        return None
    else:
        result = response.json()["data"]["result"]
        max_cpu_usage = float(result[0]["value"][1]) if result else "None"
        logging.info(f"Max CPU usage = {max_cpu_usage}%")
        return max_cpu_usage


def collect_data(concurrency_degree, id):
    logging.info(f"(id: {id}) Collecting data...")
    return extract_data(concurrency_degree, *retrieve_data(id))


def retrieve_data(id):
    logging.info(f"(id: {id}) Retrieving data from GitLab...")
    try:
        pipeline = requests.get(
            f"{config['GITLAB']['API_URL']}/pipelines/{id}?private_token={config['GITLAB']['PERSONAL_ACCESS_TOKEN']}")
        pipeline.raise_for_status()
        jobs = requests.get(
            f"{config['GITLAB']['API_URL']}/pipelines/{id}/jobs?private_token={config['GITLAB']['PERSONAL_ACCESS_TOKEN']}")
        jobs.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to query GitLab: {str(e)}")
        return None
    else:
        return pipeline.json(), jobs.json()


def extract_data(concurrency_degree, pipeline_json, jobs_json):
    logging.info(f"(id: {pipeline_json['id']}) Extracting data...")
    results = {}
    results['project_id'] = pipeline_json['project_id']
    results['concurrency_degree'] = concurrency_degree
    results['pipeline_id'] = pipeline_json['id']
    pipeline_start, pipeline_finish = [round(parser.parse(pipeline_json[var]).timestamp()) for var in ["started_at", "finished_at"]]
    results['pipeline_start'] = pipeline_start
    results['pipeline_finish'] = pipeline_finish
    results['pipeline_duration'] = pipeline_finish - pipeline_start
    results['pipeline_avg_watts_consumption'] = get_avg_watts_between(pipeline_start, pipeline_finish)
    results['pipeline_avg_ram_consumption'] = get_avg_ram_between(pipeline_start, pipeline_finish)
    results['pipeline_avg_disk_consumption'] = get_avg_disk_between(pipeline_start, pipeline_finish)
    results['pipeline_avg_cpu_usage'] = get_avg_cpu_usage_between(pipeline_start, pipeline_finish)
    results['pipeline_max_cpu_usage'] = get_max_cpu_usage_between(pipeline_start, pipeline_finish)
    jobs_json.sort(key=lambda x: x['id'])
    jobs_by_stage = {}
    curr_jobs = []
    for i, job in enumerate(jobs_json):
        if i == 0:
            currStage = job['stage']
        if job['stage'] != currStage:
            if currStage in jobs_by_stage:
                jobs_by_stage[currStage].extend(curr_jobs)
            else:
                jobs_by_stage[currStage] = curr_jobs
            curr_jobs = []
            currStage = job['stage']
        curr_jobs.append((job['id'], job['name'], job['started_at'], job['finished_at']))
    if currStage in jobs_by_stage:
        jobs_by_stage[currStage].extend(curr_jobs)
    else:
        jobs_by_stage[currStage] = curr_jobs
    job_index = 1
    for i, stage in enumerate(jobs_by_stage):
        results[f'stage{i+1}'] = stage
        stage_start  = min([round(parser.parse(js[2]).timestamp()) for js in jobs_by_stage[stage]])
        stage_finish = max([round(parser.parse(js[3]).timestamp()) for js in jobs_by_stage[stage]])
        print(stage_start, stage_finish)
        results[f'stage{i+1}_start'] = stage_start
        results[f'stage{i+1}_finish'] = stage_finish
        results[f'stage{i+1}_duration'] = stage_finish - stage_start
        results[f'stage{i+1}_avg_watts_consumption'] = get_avg_watts_between(stage_start, stage_finish)
        for job in jobs_by_stage[stage]:
            results[f'job{job_index}'] = job[1]
            results[f'job{job_index}_id'] = job[0]
            job_start, job_finish = [round(parser.parse(job[var]).timestamp()) for var in [2, 3]]
            results[f'job{job_index}_start'] = job_start
            results[f'job{job_index}_finish'] = job_finish
            results[f'job{job_index}_duration'] = job_finish - job_start
            job_index += 1
    return results


def is_prometheus_up():
    logging.info("Checking Prometheus status...")
    try:
        response = requests.get(config['PROMETHEUS']['API_URL'], params={"query":"up"})
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to query Prometheus: {str(e)}")
        logging.info("Prometheus is down")
        return False
    else:
        logging.info("Prometheus is up")
        return response.json()["status"] == "success"


def format_degrees(degrees):
    return "".join([str(x) for x in degrees])


def create_dataset_file_name(start_time):
    return f"dataset_{start_time}_{SAMPLE_SIZE}x_{str(config['EXPERIMENT']['AUTO_COOLDOWN_TEMP']) + 'C' if config['EXPERIMENT']['AUTO_COOLDOWN'] else str(config['EXPERIMENT']['COOLDOWN_DURATION']) + 's'}_{format_degrees(CONCURRENCY_DEGREES)}-conc"


def create_csv(file_name):
    file_dir = f"{DIR}/datasets/{config['HOST']['NAME']}"
    file_path = f"{file_dir}/{file_name}.csv"
    logging.info(f"Initialized dataset at {file_path}")
    return file_path


def append_csv_line(data, csv_file, init=False):
    logging.info(f"Adding data to dataset...")
    with open(csv_file, "a") as f:
        writer = csv.DictWriter(f, fieldnames=data)
        if init:
            writer.writeheader()
        writer.writerow(data)
    return True


def create_dataset_from_ids(pipeline_ids, file_name):
    csv_file_path = create_csv(file_name)
    for i, p_id in enumerate(pipeline_ids):
        data = collect_data(p_id)
        append_csv_line(data, csv_file_path, init=i==0)
    return True


def get_last_x_pipeline_ids(amount):
    if amount > 100:
        logging.error("Maximum amount is 100")
        return None
    try:
        response = requests.get(
            f"{config['GITLAB']['API_URL']}/pipelines?per_page={amount}&private_token={config['GITLAB']['PERSONAL_ACCESS_TOKEN']}")
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to query GitLab: {str(e)}")
        return None
    else:
        return [p['id'] for p in response.json()]


def set_gitlab_concurrency(degree):
    logging.info(f"Setting concurrency to {degree}")
    connection = Connection(config['HOST']['IP'], user=config['HOST']['USER'], connect_kwargs={'password': config['HOST']['PASSWORD']})
    sudopass = Responder(pattern=f"\[sudo\] password for {config['HOST']['USER']}:", response=f"{config['HOST']['PASSWORD']}\n")
    connection.run(f"sudo sed -i 's/concurrent =.*/concurrent = {degree}/' /etc/gitlab-runner/config.toml", pty=True, watchers=[sudopass])
    connection.run(f"sudo cat /etc/gitlab-runner/config.toml", pty=True, watchers=[sudopass])
    connection.run(f"sudo gitlab-runner restart", pty=True, watchers=[sudopass])
    time.sleep(10)


def run_experiment(start_time):
    logging.info("Starting experiment")
    logging.info(f"Project ID: {config['GITLAB']['PROJECT_ID']}")
    logging.info(f"Degrees of concurrency: {CONCURRENCY_DEGREES}")
    logging.info(f"Number of runs: {SAMPLE_SIZE}")
    if config['EXPERIMENT']['AUTO_COOLDOWN']:
        logging.info(f"Auto cooldown until {config['EXPERIMENT']['AUTO_COOLDOWN_TEMP']} C")
    else:
        logging.info(f"Cooldown duration: {config['EXPERIMENT']['COOLDOWN_DURATION']}s")
    if not is_prometheus_up():
        logging.error("Aborting experiment")
        return False
    csv_file_path = create_csv(create_dataset_file_name(start_time))
    if csv_file_path is None:
        logging.error("Aborting experiment")
        return False
    cooldown_until_below(config['EXPERIMENT']['AUTO_COOLDOWN_TEMP'])
    for i, concurrency_degree in enumerate(CONCURRENCY_DEGREES):
        logging.info(f"Running concurrency={concurrency_degree} treatment ({i+1}/{len(CONCURRENCY_DEGREES)})")
        set_gitlab_concurrency(concurrency_degree)
        for j in range(SAMPLE_SIZE):
            logging.info(f"(conc={concurrency_degree}) Running experiment ({j+1}/{SAMPLE_SIZE})")
            for k in range(5):
                pipeline_id = trigger_pipeline() 
                if pipeline_id is None:
                    logging.error("Aborting experiment")
                    return False
                res = wait_for_pipeline_completion(pipeline_id)
                if res == "success":
                    break
                elif k < 4:
                    logging.warning(f"(id: {pipeline_id}) Pipeline not successful, trying again...({k+2}/5)")
                else:
                    logging.error(f"Pipeline failed 5 times in a row")
                    logging.error("Aborting experiment")
                    return False
            data = collect_data(concurrency_degree, pipeline_id)
            if not data:
                logging.error("Aborting experiment")
                return False
            append_csv_line(data, csv_file_path, init=(i+j==0))
            if i+j < len(CONCURRENCY_DEGREES)+SAMPLE_SIZE-2:
                if config['EXPERIMENT']['AUTO_COOLDOWN']:
                    cooldown_until_below(config['EXPERIMENT']['AUTO_COOLDOWN_TEMP'])
                else:
                    cooldown(config['EXPERIMENT']['COOLDOWN_DURATION'])
    return True


def init_logging(start_time):
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(
                f"{DIR}/logs/{config['HOST']['NAME']}/log_{start_time}_{SAMPLE_SIZE}x_{str(config['EXPERIMENT']['AUTO_COOLDOWN_TEMP']) + 'C' if config['EXPERIMENT']['AUTO_COOLDOWN'] else str(config['EXPERIMENT']['COOLDOWN_DURATION']) + 's'}_{format_degrees(CONCURRENCY_DEGREES)}-conc.log", mode='w', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logging.info(
        f"Logging level set to {logging.getLevelName(logging.getLogger().getEffectiveLevel())}")


def main():
    start_time = datetime.now().strftime('%Y-%m-%d_%H-%M')
    init_logging(start_time)
    if run_experiment(start_time):
        logging.info("Experiment completed successfully")
    else:
        logging.error("Experiment failed")


if __name__ == "__main__":
    main()