# Introduction

This is the replication package of the paper: "The route towards sustainable DevOps"

**License**:
The content of this replication package is licensed under the MIT license.

# Content

The replication package contains the following folders/files:

## 1. Experiment

This folder contains the experiment source code files and results. It contains:

- _analysis.ipynb_: Jupyter Notebook containing the analysis of the results
- _datasets_: the data files as a result of executing the experiment
- _logs_: associated logs produced by the experiment script
- _prometheus_: files related to the Prometheus instance
- _config.ini.template_: configuration file template for the experiment
- _docker-compose.yaml_: docker compose file to set up Prometheus & Scaphandre
- _measurement.py_: experiment script
- _nrg_pc_205_page_tabular.tsv_: average EU kWh prices per year (from Eurostat)
- _README.md_: guidelines to setup the EcoPipe framework on both processing nodes
- _requirements.txt_: dependencies to be installed in a Python virtual environment

## 2. Temperature

This folder contains the data files and analysis related to the temperature experiment. The objective is to assess the temperature impact on the results obtained from the first experiment by comparing the same data executed under 22 and 24 degrees. It contains:

- _datasets_: the data files as a result of executing the experiment
- _logs_: associated logs produced by the experiment script
- _experiment_: folder containing the source files to reproduce the experiment
- _README.md_: guidelines to use the produced data and redo the experiment
- _analysis-debian.ipynb_: Jupyter Notebook containing the analysis of the produced data files for **processing node 1**
- _analysis-lamport.ipynb_: Jupyter Notebook containing the analysis of the produced data files for **processing node 2**
