# GoMLOps
Preparing ML repositories for Devops and MLOps

## Purpose
This repository contains the code for a framework that aimes to prepare ML repositories for MLops platforms in a semi-automatic way.
Its main objective is to:
1) msr4ml: Retrieve and classify missing links between ML artifacts, mainly dataset and the corresponding code where it is imported. Supported artefacts types: data, model and configuration
2) Automatically build pipeline configuration file by extracting relevant information from the code (through the argument parser). For now, only argparse is supported. Work in progress to support click, flags and getopt

## How to reproduce

1) Prepare the python environnement and install the dependencies using pip:
   ```
   pip install -r requirements.txt
   ```
2) Download the ML project you want to analyse
3) Run the msr4ml tool to retrieve artefacts links : 
   ```
   python . -p [dir_path of the project]
   ```
   Run ```python . -h ``` for help
   ```
    usage: msr4ml [-h] [-p PROJECT] [-n NAME]

    Retrieve which code imports which file in the project

    optional arguments:
    -h, --help            show this help message and exit
    -p PROJECT, --project PROJECT
                            Relative or absolute path of the project to analyse
    -n NAME, --name NAME  Set the name of the project. Defaults to the name of the directory to analyse
    ```
    The results will be saved in the directory \[dir_path of the project\]/msr4ml
4) To create the generic pipeline file, run:
     ```
    python arg2pipeline -p [path_to_project]
    ```
5) A demo code is available to automatically migrate to MLflow (create MLproject and MLflow environnement configuration files) from the generic pipeline
     ```
    python convert.py -mlf [path_generic_pipeline_file]
    ```
Work is in progress to support automatic migration to DVC and kubeflow


