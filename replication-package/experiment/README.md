# 2. Conduct experiment
1. Navigate to experiment folder
```
cd experiment/
```

## 2.1 Setup Scaphandre & Prometheus
2. Enable GitLab node exporter
3. Change `10.186.2.11` to the host IP in `/prometheus/prometheus.yml`
4. Start containers
```shell
docker compose up -d
```

## 2.2 Configure & execute experiment
5. Modify _config.ini_
6. Execute experiment
```shell
python measurement.py --concurrency C --sample S
```