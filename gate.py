import time
import math

# AWS imports: Import Braket SDK modules
import boto3
from braket.circuits import Circuit, Gate, Observable
from braket.devices import LocalSimulator
from braket.aws import AwsDevice


n_ancilla = 6
n_eigenvector = 8

def recover_task_result(task_load):
    # recover task
    sleep_times = 0
    while sleep_times < 100000:
        status = task_load.state()
        print('Status of (reconstructed) task:', status)
        print('\n')
        # wait for job to complete
        # terminal_states = ['COMPLETED', 'FAILED', 'CANCELLED']
        if status == 'COMPLETED':
            # get results
            return task_load.result()
        else:
            time.sleep(1)
            sleep_times = sleep_times + 1
    print("Quantum execution time exceded")
    return None

def execute(circuit, s3_folder, machine):

    if machine=="local":
        device = LocalSimulator()
        result = device.run(circuit, shots=100000).result()
        return result.measurement_counts

    device = AwsDevice(machine)

    if "sv1" not in machine and "tn1" not in machine:
        task = device.run(circuit, s3_folder, shots=1000, poll_timeout_seconds=5 * 24 * 60 * 60)
        return recover_task_result(task).measurement_counts
    else:
        task = device.run(circuit, s3_folder, shots=1000)
        return task.result().measurement_counts




def get_minor_route_by_phase(results):

    cycle_per_eigenstate = {"11000110": [0,1,2,3], "10001101":[0,3,1,2], "11100001":[0,1,3,2]}
    minor_eigenstate = None
    for e in results.keys():
        if minor_eigenstate == None or int(results[e],2)<int(results[minor_eigenstate],2):
            minor_eigenstate = e

    return cycle_per_eigenstate[minor_eigenstate]


def crz(circ, tetha, a, b):
    circ.rz(b, tetha/2)
    circ.cnot(a,b)
    circ.rz(b, -tetha/2)
    circ.cnot(a,b)


def controlled_U(circ,a,b,c,d,n,k):
    """this is corresponding to the C-U_j in equation (8) """
    crz(circ, c-a, n_ancilla-k, n_ancilla+n)
    circ.rz(n_ancilla-k, a)
    crz(circ, b-a, n_ancilla-k, n_ancilla+n+1)
    circ.ccnot(n_ancilla-k, n_ancilla+n, n_ancilla+n+1)
    circ.rz(n_ancilla+n+1, d+c-b-a)
    circ.ccnot(n_ancilla-k, n_ancilla+n, n_ancilla+n+1)


def qft_dagger(circ, n):
    """n-qubit QFTdagger on q in circ."""
    for j in range(n):
        k = (n-1) - j
        for m in range(k):
            crz(circ, -math.pi/float(2**(k-m)), k, m)
        circ.h(k)


def QPE(eigenstate, s3_folder, machine):
    # implementation limited to 8 qubits eigenstates
    if len(eigenstate) != n_eigenvector:
        return None

    qpe = Circuit()

    for i in range(0, n_eigenvector):
        if eigenstate[i] == "1":
            qpe.x(n_ancilla + i)

    for i in range(n_ancilla):
        qpe.h(i)

    controlled_U(qpe, 0, math.pi / 2, math.pi / 8, math.pi / 4, 0, 1)
    controlled_U(qpe, math.pi / 2, 0, math.pi / 4, math.pi / 4, 2, 1)
    controlled_U(qpe, math.pi / 8, math.pi / 4, 0, math.pi / 8, 4, 1)
    controlled_U(qpe, math.pi / 4, math.pi / 4, math.pi / 8, 0, 6, 1)
    for i in range(2):
        controlled_U(qpe, 0, math.pi / 2, math.pi / 8, math.pi / 4, 0, 2)
        controlled_U(qpe, math.pi / 2, 0, math.pi / 4, math.pi / 4, 2, 2)
        controlled_U(qpe, math.pi / 8, math.pi / 4, 0, math.pi / 8, 4, 2)
        controlled_U(qpe, math.pi / 4, math.pi / 4, math.pi / 8, 0, 6, 2)
    for i in range(4):
        controlled_U(qpe, 0, math.pi / 2, math.pi / 8, math.pi / 4, 0, 3)
        controlled_U(qpe, math.pi / 2, 0, math.pi / 4, math.pi / 4, 2, 3)
        controlled_U(qpe, math.pi / 8, math.pi / 4, 0, math.pi / 8, 4, 3)
        controlled_U(qpe, math.pi / 4, math.pi / 4, math.pi / 8, 0, 6, 3)
    for i in range(8):
        controlled_U(qpe, 0, math.pi / 2, math.pi / 8, math.pi / 4, 0, 4)
        controlled_U(qpe, math.pi / 2, 0, math.pi / 4, math.pi / 4, 2, 4)
        controlled_U(qpe, math.pi / 8, math.pi / 4, 0, math.pi / 8, 4, 4)
        controlled_U(qpe, math.pi / 4, math.pi / 4, math.pi / 8, 0, 6, 4)
    for i in range(16):
        controlled_U(qpe, 0, math.pi / 2, math.pi / 8, math.pi / 4, 0, 5)
        controlled_U(qpe, math.pi / 2, 0, math.pi / 4, math.pi / 4, 2, 5)
        controlled_U(qpe, math.pi / 8, math.pi / 4, 0, math.pi / 8, 4, 5)
        controlled_U(qpe, math.pi / 4, math.pi / 4, math.pi / 8, 0, 6, 5)
    for i in range(32):
        controlled_U(qpe, 0, math.pi / 2, math.pi / 8, math.pi / 4, 0, 6)
        controlled_U(qpe, math.pi / 2, 0, math.pi / 4, math.pi / 4, 2, 6)
        controlled_U(qpe, math.pi / 8, math.pi / 4, 0, math.pi / 8, 4, 6)
        controlled_U(qpe, math.pi / 4, math.pi / 4, math.pi / 8, 0, 6, 6)

    qft_dagger(qpe, 6)

    # for i in range(n_ancilla):
    #     qpe.measure(q[i],c[i])
    # print(qpe)


    results = execute(qpe, s3_folder, machine)

    return results