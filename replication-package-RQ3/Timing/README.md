# Introduction

This folder contains the data files and analysis related to the timing experiment. The objective is to assess the time delay between a pipeline finishing and the associated energy consumption data being available in Grafana.

# Reproduce experiment

1. Follow step `Setup virtual environment` of `EcoPipe/README.md`
2. Open `timing-analysis.ipynb` file
3. Press `Run All`

# Replicate experiment

## 1. Pre-requisites

The following software has to be installed on both the CI/CD node and monitoring node:

| **Software**   | **Version** |
| -------------- | ----------- |
| Docker         | 24.0.5      |
| Docker Compose | 2.24.7      |
| Prometheus     | 2.51.2      |
| Scaphandre     | 1.0.0       |

The following software has also to be installed on the CI/CD node:

| **Software**  | **Version** |
| ------------- | ----------- |
| GitLab        | 15.10.3-ee  |
| GitLab Runner | 16.2.1      |

_Note:_ the EcoPipe framework has to be configured and running on the monitoring node & be connected to the CI/CD service on the CI/CD node.

## 2. Setup & execution

1. In the monitoring node in file `api/app.py`, uncomment the following lines:

   - Line 7
   - Line 73-79

2. Execute the desired amount of pipelines

3. The file `api/timing.csv` is created with the results
