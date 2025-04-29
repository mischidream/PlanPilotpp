from flask import Blueprint, request, jsonify
from ..service.fastdownward_service import run_fastdownward_service

fastdownward_bp = Blueprint('fastdownward', __name__)

@fastdownward_bp.route('/run', methods=['POST'])
def run_fastdownward():
    data = request.json
    domain_file = data.get('domainFile')
    problem_file = data.get('problemFile')

    if not domain_file or not problem_file:
        return jsonify({"error": "Both domainFile and problemFile are required"}), 400

    try:
        result = run_fastdownward_service(domain_file, problem_file)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
