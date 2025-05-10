from flask import Blueprint, request, jsonify
from ..service.planpilot_service import PlanpilotService

planpilot_bp = Blueprint('planpilot', __name__)
planpilot_service = PlanpilotService()

@planpilot_bp.route('/run-planpilot', methods=['POST'])
def run_planpilot():
    data = request.json
    sas_file = data.get('sasFile')
    horizon = data.get('horizon')
    encoding = data.get('encoding')

    if not sas_file or not horizon or not encoding:
        return jsonify({"error": "sasFile, horizon, and encoding are required"}), 400

    try:
        # Run PlanPilot service and get the facets
        facets = planpilot_service.run_planpilot_service(sas_file, horizon, encoding)
        return jsonify({"facets": facets}), 200
    except Exception as e:
        print(e.__traceback__)
        return jsonify({"error": str(e)}), 500

@planpilot_bp.route('/send-planpilot-command', methods=['POST'])
def send_command():
    data = request.json
    command = data.get("command")
    if not command:
        return jsonify({"error": "No command provided"}), 400
    try:
        output = planpilot_service.send_command(command)
        return jsonify({"output": output}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@planpilot_bp.route('/stop-planpilot', methods=['POST'])
def stop_planpilot():
    try:
        planpilot_service.stop_fasb()
        return jsonify({"status": "FASB stopped"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
