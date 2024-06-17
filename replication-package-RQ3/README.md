# Introduction

This is the replication package of the paper:
"EcoPipe: an energy monitoring framework for
deployment pipelines"

**License**:
The content of this replication package is licensed under the MIT license.

# Content

The replication package contains the following folders/files:

## 1. EcoPipe

This folder contains the **EcoPipe** framework source code files. It consists mainly of:

- _cicd-node_: configuration to include in the processing node hosting the CI/CD service
- _monitoring-node_: configuration to include in the processing node hosting the monitoring framework
- _README.md_: guidelines to setup the EcoPipe framework on both processing nodes
- _requirements.txt_: dependencies to be installed in a Python virtual environment

## 2. Efficiency

This folder contains the data files and analysis related to the efficiency experiment of the EcoPipe framework. The objective is to assess the introduced energy overhead by the framework to both processing nodes. It contains:

- _datasets_: the data files as a result of executing the experiment
- _logs_: associated logs produced by the experiment script
- _experiment_: folder containing the source files to reproduce the experiment
- _README.md_: guidelines to use the produced data and redo the experiment
- _efficiency-analysis.ipynb_: Jupyter Notebook containing the analysis of the produced data files

## 3. Timing

This folder contains the data files and analysis related to the timing experiment. The objective is to assess the time delay between a pipeline finishing and the associated energy consumption data being available in Grafana. It contains:

- _timing.csv_: the data file as a result of executing the experiment
- _timing-analysis.ipynb_: Jupyter Notebook containing the analysis of the produced data file

_Note:_ The code used to run the experiment is commented out in file `EcoPipe/monitoring-node/api/app.py`.
