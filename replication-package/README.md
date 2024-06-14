The software versions utilised are listed below.

| **Software**     | **Version**    |
|------------------|----------------|
| GitLab           | 15.10.3-ee     |
| GitLab Runner    | 16.2.1         |
| Docker           | 24.0.5         |
| Docker Compose   | 2.24.7         |
| Prometheus       | 2.51.2         |
| Scaphandre       | 1.0.0          |

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

# 2. Conduct experiment
Instructions [here](https://github.com/Flavio8699/ms-thesis/blob/main/replication-package/experiment/README.md).

# 3. Continuous monitoring
Instructions [here](https://github.com/Flavio8699/ms-thesis/blob/main/replication-package/monitoring/README.md).
