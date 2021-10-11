from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from gate import *
from annealing import *


gate_machines_arn= { "riggeti_aspen8":"arn:aws:braket:::device/qpu/rigetti/Aspen-8",
                "riggeti_aspen9":"arn:aws:braket:::device/qpu/rigetti/Aspen-9",
                "ionq":"arn:aws:braket:::device/qpu/ionq/ionQdevice",
                "sv1":"arn:aws:braket:::device/quantum-simulator/amazon/sv1",
                "tn1":"arn:aws:braket:::device/quantum-simulator/amazon/tn1",
                "local":"local"}

adiabatic_machines_arn= { "dwave_advantage":"arn:aws:braket:::device/qpu/d-wave/Advantage_system1",
                "dwave_dw2000":"arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6"}


s3_folder = ("amazon-braket-7c2f2fa45286", "api")  # Use the S3 bucket you created during onboarding


app = Flask(__name__)
CORS(app)


# #OPTION 1: Create a session in AWS in the API
# session = boto3.Session(
#     aws_access_key_id=YOUR_ACCESS_KEY_ID,
#     aws_secret_access_key=YOUR_SECRET_ACCESS_JKEY,
#     aws_session_token=SESSION_TOKEN,
#     region_name="us-east-1"
# )
# aws_session = AwsSession(session)

# #OPTION 2 (the one choosed): Configure credentials and region in the files ~/.aws/credentials and ~/.aws/config, respectively



@app.route('/execute/adiabatic', methods=["get"])
def execute_adiabatic_quantum_tsp():
    machine = request.args.get('device')

    if machine not in adiabatic_machines_arn:
        return "Not machine", 400

    if 'file' not in request.files:
        return "Not file", 400
    file = request.files['file']
    if file.filename == '':
        return "Not file", 400

    filename = "graph.txt"
    file.save(filename)

    data, G, weights = def_graph(filename)

    best_route, best_distance = TSP(data, G, weights,
                                    s3_folder,
                                    adiabatic_machines_arn[machine])

    response = {
        "best_route":best_route,
        "best_distance":best_distance
    }
    return jsonify(response)




@app.route('/execute/gate', methods=["get"])
def execute_gate_based_quantum_tsp():

    machine = request.args.get('device')

    if machine not in gate_machines_arn:
        return "Not machine", 400

    eigenstates = ["11000110", "10001101", "11100001"]
    results = {}
    for e in eigenstates:
        counts = QPE(e, s3_folder, gate_machines_arn[machine])
        measure = list(counts.keys())[0]
        eigenstate = measure[n_ancilla:]
        phase = measure[:n_ancilla]
        results[eigenstate] = phase

    hamiltonian_cycle = get_minor_route_by_phase(results)

    response = {
        "best_route":hamiltonian_cycle
    }
    return jsonify(response)



if __name__ == '__main__':
    app.run(host="localhost", port=33888)
