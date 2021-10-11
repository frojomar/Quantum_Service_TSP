import boto3
from braket.aws import AwsDevice
from braket.ocean_plugin import BraketSampler, BraketDWaveSampler


import numpy as np
import networkx as nx
import dimod
import dwave_networkx as dnx
from dimod.binary_quadratic_model import BinaryQuadraticModel
from dwave.system.composites import EmbeddingComposite
import matplotlib.pyplot as plt
# magic word for producing visualizations in notebook
from collections import defaultdict
import itertools
import pandas as pd


# local imports
from utils_tsp import get_distance, traveling_salesperson



# fix random seed for reproducibility
seed = 1
np.random.seed(seed)



def def_graph(file):
    data = pd.read_csv(file, sep='\s+', header=None)

    # G = nx.from_pandas_dataframe(data)
    G = nx.from_pandas_adjacency(data)
    # pos = nx.random_layout(G)
    pos = nx.spring_layout(G, seed=seed)

    # get characteristics of graph
    nodes = G.nodes()
    edges = G.edges()
    weights = nx.get_edge_attributes(G, 'weight');

    return data, G, weights


def get_lagrange_list(G):
    # get QUBO for TSP
    tsp_qubo = dnx.algorithms.tsp.traveling_salesperson_qubo(G)

    # find default Langrange parameter for enforcing constraints

    # set parameters
    lagrange = None
    weight = 'weight'

    # get corresponding QUBO step by step
    N = G.number_of_nodes()

    if lagrange is None:
        # If no lagrange parameter provided, set to 'average' tour length.
        # Usually a good estimate for a lagrange parameter is between 75-150%
        # of the objective function value, so we come up with an estimate for
        # tour length and use that.
        if G.number_of_edges() > 0:
            lagrange = G.size(weight=weight) * G.number_of_nodes() / G.number_of_edges()
        else:
            lagrange = 2

    print('Default Lagrange parameter:', lagrange)

    # create list around default value for HPO
    lagrange_list = list(np.arange(int(0.8 * lagrange), int(1.1 * lagrange)))
    print('Lagrange parameter for HPO:', lagrange_list)
    return lagrange_list


def TSP(data, G, weights, s3_folder, machine):

    lagrange_list = get_lagrange_list(G)

    # run TSP with imported TSP routine
    sampler = BraketDWaveSampler(s3_folder,machine)
    sampler = EmbeddingComposite(sampler)

    # set parameters
    num_shots = 1000
    start_city = 0
    best_distance = sum(weights.values())
    best_route = [None]*len(G)

    # run HPO to find route
    for lagrange in lagrange_list:
        print('Running quantum annealing for TSP with Lagrange parameter=', lagrange)
        route = traveling_salesperson(G, sampler, lagrange=lagrange,
                                      start=start_city, num_reads=num_shots, answer_mode="histogram")


        # print distance
        total_dist, distance_with_return = get_distance(route, data)

        # update best values
        if distance_with_return < best_distance:
            best_distance = distance_with_return
            best_route = route

    return best_route, best_distance

