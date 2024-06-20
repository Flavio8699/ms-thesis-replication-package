# Introduction

intro missing

# Pre-requisites

The following software has to be installed on the processing node node:

| **Software**   | **Version** |
| -------------- | ----------- |
| GitLab         | 15.10.3-ee  |
| GitLab Runner  | 16.2.1      |
| Docker         | 24.0.5      |
| Docker Compose | 2.24.7      |

Furthermore, a repository with a project has to be set up on GitLab.

# Setup

This section contains the detailed guidelines on how to setup the processing node in order to execute the experiment.

## 1. Setup virtual environment

1. Install virtualenv

```shell
sudo apt-get install python3-venv
```

2. Create and activate virtual environment

```shell
python3 -m venv env
source env/bin/activate
```

3. Install requirements

```shell
pip install -r requirements.txt
```

## 2. Setup Scaphandre & Prometheus

1. Enable GitLab node exporter
2. Change `10.186.2.11` to the host IP in `/prometheus/prometheus.yml`
3. Start containers

```shell
docker compose up -d
```

# Configure & execute experiment

1. Modify _config.ini_
2. Execute experiment

```shell
python measurement.py --concurrency C --sample S
```

where:

- _C_: concurrency degree, i.e. number of jobs to run at the same time [Integer]
- _S_: number of samples to collect, i.e. pipeline executions to perform [Integer]
