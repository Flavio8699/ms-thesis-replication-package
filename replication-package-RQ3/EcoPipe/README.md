# Introduction

EcoPipe is a software-based framework for continuous energy consumption monitoring of deployment pipelines in a in-house infrastructure. It allows DevOps engineers to analyse the energy consumption of their pipelines and gain awareness of the associated environmental impact.

# Pre-requisites

The following software has to be installed on both the CI/CD node and monitoring node:

| **Software**   | **Version** |
| -------------- | ----------- |
| Docker         | 24.0.5      |
| Docker Compose | 2.24.7      |

The following software has also to be installed on the CI/CD node:

| **Software**  | **Version** |
| ------------- | ----------- |
| GitLab        | 15.10.3-ee  |
| GitLab Runner | 16.2.1      |

# Setup

This section contains the detailed guidelines on how to setup the CI/CD node (processing node containing the CI/CD service) and monitoring node (processing node which will host the framework). In a small environment, 1 processing node can host both the CI/CD service & the EcoPipe framework.

## 1. Setup CI/CD node

1. Navigate to cicd-node folder

```
cd cicd-node/
```

2. Enable GitLab node exporter ([help](https://docs.gitlab.com/ee/administration/monitoring/prometheus/gitlab_exporter.html))
3. Change `10.186.2.11` to the host IP in `/prometheus/prometheus.yml`
4. Start containers

```shell
docker compose up -d
```

### 1.1 Setup case study repository

5. Create a project on GitLab
6. Clone https://gitlab.com/fdroid/fdroidclient
7. Switch to commit hash **429eae6f9ed209c6d830f5e6213f4bf70c78c94e** from 11/04/2024
8. In file `HttpManagerInstrumentationTest.kt` comment the following failing tests:
   - checkTls12Support
   - checkTlsSupport
   - testNoTls10
   - testNoTls11
9. Push the code to GitLab
10. Repository is ready

### 1.2 Enable virtualisation

11. Enable virtualisation in the BIOS
12. In the file `/etc/gitlab-runner/config.toml`, for each runner under `[runners.docker]` add the following line:

- `devices = ["/dev/kvm"]`

## 2. Setup monitoring node

1. Navigate to monitoring-node folder

```
cd monitoring-node/
```

### 2.1 Setup virtual environment

2. Install virtualenv

```shell
sudo apt-get install python3-venv
```

3. Create and activate virtual environment

```shell
python3 -m venv env
source env/bin/activate
```

4. Install requirements

```shell
pip install -r requirements.txt
```

### 2.2 Setup Grafana & PostgreSQL

5. Modify sections `[POSTGRES]` and `[GRAFANA]` in file _.env_
6. Configure Grafana datasources in `grafana/datasource.yml`
7. Start containers

```shell
docker compose up -d
```

8. Import database schema

```shell
docker exec -i <CONTAINER> psql -U <DB_USER> -d <DB_NAME> < db.sql
```

_Note: replace necessary values_

### 2.3 Setup Flask API

9. Modify section `[API]` in file _.env_
10. Navigate to API folder

```shell
cd api/
```

11. Start API in the background

```shell
nohup python app.py > output.log &
```

### 2.4 Connect GitLab instance

12. In GitLab, select the project to be monitored
13. Go to `Settings > Webhooks` and create a new webhook
    - **URL**: `http://<API_HOST>:<API_PORT>/webhook`
    - **Secret token:** `GITLAB_TOKEN` from _.env_ file
    - **Trigger:** select `Pipeline events`
    - **SSL verification:** disable if not using SSL, keep otherwise
14. Press `Add webhook`
