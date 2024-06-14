# 1. Setup virtual environment

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

# 2. Setup CI/CD node

1. Navigate to cicd-node folder

```
cd cicd-node/
```

2. Enable GitLab node exporter
3. Change `10.186.2.11` to the host IP in `/prometheus/prometheus.yml`
4. Start containers

```shell
docker compose up -d
```

# 3. Setup monitoring node

1. Navigate to monitoring-node folder

```
cd monitoring-node/
```

## 3.1 Setup Grafana & PostgreSQL

2. Modify sections `[POSTGRES]` and `[GRAFANA]` in file _.env_
3. Configure Grafana datasources in `grafana/datasource.yml`
4. Start containers

```shell
docker compose up -d
```

5. Import database schema

```shell
docker exec -i <CONTAINER> psql -U <DB_USER> -d <DB_NAME> < db.sql
```

_Note: replace necessary values_

## 3.2 Setup Flask API

6. Modify section `[API]` in file _.env_
7. Navigate to API folder

```shell
cd api/
```

8. Start API in the background

```shell
nohup python app.py > output.log &
```

## 3.3 Connect GitLab instance

9. In GitLab, select the project to be monitored
10. Go to `Settings > Webhooks` and create a new webhook
    - **URL**: `http://<API_HOST>:<API_PORT>/webhook`
    - **Secret token:** `GITLAB_TOKEN` from _.env_ file
    - **Trigger:** select `Pipeline events`
    - **SSL verification:** disable if not using SSL, keep otherwise
11. Press `Add webhook`
