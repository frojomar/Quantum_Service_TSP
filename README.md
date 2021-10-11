
# Quantum Service for resolv Travelling Salesman Problem

## Description

This repository provides the code to deploy a hybrid quantum service that solves the TSP problem using AWS Braket quantum processors. Both for a gate-based and annealing approaches.

## Requirements

To run the gateway it is necessary to have the following software installed:

- Python 3
- pip3
- boto3 (with pip3)
- amazon-braket-sdk (with pip3)
- flask (with pip3)

Previously execute, you must configure credentials and region to access AWS using boto3 in the files ~/.aws/credentials and ~/.aws/config, respectively 

## Starting TSP API

Execute python3 main.py

## Operations
Two endpoints:

- GET /execute/adiabatic: Resolves TSP using adiabatic quantum computing. You must indicate the device where code is going to be executed (as "device" args param) and you must attach a file.txt with the weights of the paths between nodes (see attached four_d.txt file). This return 200 status and a JSON with best route and best distance if all have gone good.

- GET /execute/gate: Resolves TSP using gate-based quantum computing. You must indicate the device where code is going to be executed (as "device" args param). This return 200 status and a JSON with best route if all have gone good.
