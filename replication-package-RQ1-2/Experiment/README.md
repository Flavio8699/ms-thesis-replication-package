# Introduction

This folder contains the data files and analysis related to the experiment conducted on the pipeline energy consumption. The objective is to assess the pipeline energy consumption and execution duration on both processing nodes.

# Reproduce experiment

1. Follow step `Setup virtual environment` below in the replication section
2. Open `analysis.ipynb` file
3. Press `Run All`

# Replicate experiment

## 1. Pre-requisites

The following software has to be installed on the processing node node:

| **Software**   | **Version** |
| -------------- | ----------- |
| GitLab         | 15.10.3-ee  |
| GitLab Runner  | 16.2.1      |
| Docker         | 24.0.5      |
| Docker Compose | 2.24.7      |

## 2. Setup

This section contains the detailed guidelines on how to setup the processing node in order to execute the experiment.

### Setup virtual environment

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

### Setup Scaphandre & Prometheus

1. Enable GitLab node exporter ([help](https://docs.gitlab.com/ee/administration/monitoring/prometheus/gitlab_exporter.html))
2. Change `10.186.2.11` to the host IP in `/prometheus/prometheus.yml`
3. Start containers

```shell
docker compose up -d
```

### Setup case study repository

1. Create a project on GitLab
2. Clone https://gitlab.com/fdroid/fdroidclient
3. Switch to commit hash **429eae6f9ed209c6d830f5e6213f4bf70c78c94e** from 11/04/2024
4. In file `HttpManagerInstrumentationTest.kt` comment the following failing tests:
   - checkTls12Support
   - checkTlsSupport
   - testNoTls10
   - testNoTls11
5. Push the code to GitLab
6. Repository is ready

## 3. Configure & execute experiment

1. Modify _config.ini_
2. Execute experiment

```shell
python measurement.py --concurrency C --sample S
```

where:

- _C_: concurrency degree, i.e. number of jobs to run at the same time [Integer]
- _S_: number of samples to collect, i.e. pipeline executions to perform [Integer]
