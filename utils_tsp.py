# imports
import numpy as np
import networkx as nx
import dimod
import dwave_networkx as dnx


# helper function to compute distance from route
def get_distance(route, data):
    """
    find distance for given route = [0, 4, 3, 1, 2] and original data
    """
    # get the total distance without return
    total_dist = 0
    for idx, node in enumerate(route[:-1]):
        dist = data[route[idx+1]][route[idx]]
        total_dist += dist

    print('Total distance (without return):', total_dist)

    # add distance between start and end point to complete cycle
    return_distance = data[route[0]][route[-1]]
    # print('Distance between start and end:', return_distance)

    # get distance for full cyle
    distance_with_return = total_dist + return_distance
    print('Total distance (including return):', distance_with_return)

    return total_dist, distance_with_return


# helper function for solving TSP with D-Wave adapted from Ocean
# including some heuristical filling if not all contraints have been met
def traveling_salesperson(G, sampler=None, lagrange=None, weight='weight',
                          start=None, **sampler_args):
    # get lists with all cities
    list_cities = list(G.nodes())

    # Get a QUBO representation of the problem
    Q = dnx.traveling_salesperson_qubo(G, lagrange, weight)

    # use the sampler to find low energy states
    response = sampler.sample_qubo(Q, **sampler_args)
    sample = response.first.sample

    # fill route with None values
    route = [None]*len(G)
    # get cities from sample
    # NOTE: Prevent duplicate city entries by enforcing only one occurrence per city along route
    for (city, time), val in sample.items():
        if val and (city not in route):
            route[time] = city

    # run heuristic replacing None values
    if None in route:
        # get not assigned cities
        cities_unassigned = [city for city in list_cities if city not in route]
        cities_unassigned = list(np.random.permutation(cities_unassigned))
        for idx, city in enumerate(route):
            if city == None:
                route[idx] = cities_unassigned[0]
                cities_unassigned.remove(route[idx])

    # cycle solution to start at provided start location
    if start is not None and route[0] != start:
        # rotate to put the start in front
        idx = route.index(start)
        route = route[idx:] + route[:idx]

    return route


# def traveling_salesperson(G, sampler=None, lagrange=None,
#                           weight='weight', start=None,
#                           **sampler_args):
#     list_cities = list(G.nodes())
#
#     Q = dnx.traveling_salesperson_qubo(G, lagrange, weight)
#
#     response = sampler.sample_qubo(Q, **sampler_args)
#     sample = response.first.sample
#
#     route = [None] * len(G)
#
#     for (city, time), val in sample.items():
#         if val and (city not in route):
#             route[time] = city
#
#     if None in route:
#         cities_unassigned = \
#             [city for city in list_cities if city not in route]
#         cities_unassigned = \
#             list(np.random.permutation(cities_unassigned))
#         for idx, city in enumerate(route):
#             if city == None:
#                 route[idx] = cities_unassigned[0]
#                 cities_unassigned.remove(route[idx])
#
#     if start is not None and route[0] != start:
#         idx = route.index(start)
#         route = route[idx:] + route[:idx]
#
#     return route
