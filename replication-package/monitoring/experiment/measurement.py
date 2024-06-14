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

argparser = argparse.ArgumentParser(description='Run experiment')

argparser.add_argument('--sample', type=int, help='Sample size', metavar='S', required=True)
argparser.add_argument('--type', type=str, choices=['control', 'experimental'], help='Control or experimental', metavar='T', required=True)

args = argparser.parse_args()

SAMPLE_SIZE = args.sample
TYPE = args.type

def trigger_pipeline():
    logging.info(f"Triggering pipeline...")
    try:
        response = requests.post(
            f"{config['CICD-SERVER']['GITLAB_API_URL']}/trigger/pipeline?token={config['CICD-SERVER']['GITLAB_PIPELINE_TRIGGER_TOKEN']}&ref=master")
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
            f"{config['CICD-SERVER']['GITLAB_API_URL']}/pipelines/{id}?private_token={config['CICD-SERVER']['GITLAB_PERSONAL_ACCESS_TOKEN']}")
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
        response = requests.get(config['CICD-SERVER']['PROMETHEUS_API_URL'], params={
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


def get_avg_watts_between(api_url, start, end, delta):
    duration = end - start
    # Convert duration to ms
    duration *= 1000
    # Add delta in ms
    duration += int(delta * 1000)
    try:
        logging.info(f"Getting average Watts consumption...")
        response = requests.get(api_url, params={"query": f"avg_over_time(scaph_host_power_microwatts[{duration}ms]@{end})"})
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to query Prometheus: {str(e)}")
        return None
    else:
        result = response.json()["data"]["result"]
        avg_watts_consumption = float(result[0]["value"][1])/10**6 if result else "None"
        logging.info(f"Average Watts consumption = {avg_watts_consumption} W")
        return avg_watts_consumption


def collect_data(id):
    logging.info(f"(id: {id}) Collecting data...")
    return extract_data(*retrieve_data(id))


def retrieve_data(id):
    logging.info(f"(id: {id}) Retrieving data from GitLab...")
    try:
        pipeline = requests.get(
            f"{config['CICD-SERVER']['GITLAB_API_URL']}/pipelines/{id}?private_token={config['CICD-SERVER']['GITLAB_PERSONAL_ACCESS_TOKEN']}")
        pipeline.raise_for_status()
        jobs = requests.get(
            f"{config['CICD-SERVER']['GITLAB_API_URL']}/pipelines/{id}/jobs?private_token={config['CICD-SERVER']['GITLAB_PERSONAL_ACCESS_TOKEN']}")
        jobs.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to query GitLab: {str(e)}")
        return None
    else:
        return pipeline.json(), jobs.json()


def extract_data(pipeline_json, jobs_json):
    logging.info(f"(id: {pipeline_json['id']}) Extracting data...")
    time.sleep(5)
    results = {}
    results['project_id'] = pipeline_json['project_id']
    results['pipeline_id'] = pipeline_json['id']
    pipeline_start, pipeline_finish = [round(parser.parse(pipeline_json[var]).timestamp()) for var in ["started_at", "finished_at"]]
    results['pipeline_start'] = pipeline_start
    results['pipeline_finish'] = pipeline_finish
    results['pipeline_duration'] = pipeline_finish - pipeline_start
    results['cicd_server_avg_watts_consumption'] = get_avg_watts_between(config['CICD-SERVER']['PROMETHEUS_API_URL'], pipeline_start, pipeline_finish, 0)
    results['monitoring_pc_avg_watts_consumption'] = get_avg_watts_between(config['MONITORING-PC']['PROMETHEUS_API_URL'], pipeline_start, pipeline_finish, 1.385)
    return results


def is_ci_cd_prometheus_up():
    logging.info("Checking CI/CD Server Prometheus status...")
    try:
        response = requests.get(config['CICD-SERVER']['PROMETHEUS_API_URL'], params={"query":"up"})
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to query CI/CD Server Prometheus: {str(e)}")
        logging.info("CI/CD Server Prometheus is down")
        return False
    else:
        logging.info("CI/CD Server Prometheus is up")
        return response.json()["status"] == "success"


def is_monitoring_prometheus_up():
    logging.info("Checking Monitoring Computer Prometheus status...")
    try:
        response = requests.get(config['MONITORING-PC']['PROMETHEUS_API_URL'], params={"query":"up"})
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to query Monitoring Computer Prometheus: {str(e)}")
        logging.info("Monitoring Computer Prometheus is down")
        return False
    else:
        logging.info("Monitoring Computer Prometheus is up")
        return response.json()["status"] == "success"


def format_degrees(degrees):
    return "".join([str(x) for x in degrees])


def create_dataset_file_name(start_time):
    return f"dataset_{start_time}_{SAMPLE_SIZE}x_{str(config['CICD-SERVER']['AUTO_COOLDOWN_TEMP']) + 'C'}_6-conc"


def create_csv(file_name):
    file_dir = f"{DIR}/datasets/{TYPE}"
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
            f"{config['CICD-SERVER']['GITLAB_API_URL']}/pipelines?per_page={amount}&private_token={config['CICD-SERVER']['GITLAB_PERSONAL_ACCESS_TOKEN']}")
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to query GitLab: {str(e)}")
        return None
    else:
        return [p['id'] for p in response.json()]


def set_gitlab_concurrency(degree):
    logging.info(f"Setting concurrency to {degree}")
    connection = Connection(config['CICD-SERVER']['IP'], user=config['CICD-SERVER']['USER'], connect_kwargs={'password': config['CICD-SERVER']['PASSWORD']})
    sudopass = Responder(pattern=f"\[sudo\] password for {config['CICD-SERVER']['USER']}:", response=f"{config['CICD-SERVER']['PASSWORD']}\n")
    connection.run(f"sudo sed -i 's/concurrent =.*/concurrent = {degree}/' /etc/gitlab-runner/config.toml", pty=True, watchers=[sudopass])
    connection.run(f"sudo cat /etc/gitlab-runner/config.toml", pty=True, watchers=[sudopass])
    connection.run(f"sudo gitlab-runner restart", pty=True, watchers=[sudopass])
    time.sleep(10)


def run_experiment(start_time):
    logging.info("Starting experiment")
    logging.info(f"Project ID: {config['CICD-SERVER']['GITLAB_PROJECT_ID']}")
    logging.info(f"Number of runs: {SAMPLE_SIZE}")
    logging.info(f"Auto cooldown until {config['CICD-SERVER']['AUTO_COOLDOWN_TEMP']} C")
    if not is_ci_cd_prometheus_up():
        logging.error("Aborting experiment")
        return False
    if not is_monitoring_prometheus_up():
        logging.error("Aborting experiment")
        return False
    csv_file_path = create_csv(create_dataset_file_name(start_time))
    if csv_file_path is None:
        logging.error("Aborting experiment")
        return False
    cooldown_until_below(config['CICD-SERVER']['AUTO_COOLDOWN_TEMP'])
    set_gitlab_concurrency(6)
    for j in range(SAMPLE_SIZE):
        logging.info(f"Running experiment ({j+1}/{SAMPLE_SIZE})")
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
        data = collect_data(pipeline_id)
        if not data:
            logging.error("Aborting experiment")
            return False
        append_csv_line(data, csv_file_path, init=(j==0))
        cooldown_until_below(config['CICD-SERVER']['AUTO_COOLDOWN_TEMP'])
    return True


def init_logging(start_time):
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(
                f"{DIR}/logs/{TYPE}/log_{start_time}_{SAMPLE_SIZE}x_{str(config['CICD-SERVER']['AUTO_COOLDOWN_TEMP']) + 'C'}_6-conc.log", mode='w', encoding='utf-8'),
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