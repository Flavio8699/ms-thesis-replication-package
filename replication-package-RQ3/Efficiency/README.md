# Introduction

This folder contains the data files and analysis related to the efficiency experiment of the EcoPipe framework. The objective is to assess the introduced energy overhead by the framework to both processing nodes.

# Reproduce experiment

1. Follow step `Setup virtual environment` of `EcoPipe/README.md`
2. Open `efficiency-analysis.ipynb` file
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

_Note:_ if the group to be collect is **experimental**, the EcoPipe framework has to be configured and running on the monitoring node & be connected to the CI/CD service on the CI/CD node.

## 2. Setup & execution

1. Follow step `Setup virtual environment` of `EcoPipe/README.md`
2. Navigate to experiment folder

```
cd experiment/
```

3. Modify _config.ini_
4. Execute experiment

```shell
python measurement.py --sample S --type [control|experimental]
```

where:

- _S_: number of samples to collect, i.e. pipeline executions to perform [Integer]
- _type_: either control or experimental group depending on current setup [String]
