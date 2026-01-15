from flask import Blueprint, request, jsonify
import os

from .fastdownward import run_fastdownward_service
from ..utils.plasp_utils import generate_lp_with_plasp

planner_bp = Blueprint("planner", __name__)

@planner_bp.route("/compute-concrete-from-abstract", methods=["POST"])
def compute_concrete_from_abstract():

    abstract_problem = request.files.get("abstractProblem")
    abstract_domain = request.files.get("abstractDomain")
    concrete_problem = request.files.get("concreteProblem")
    concrete_domain = request.files.get("concreteDomain")

    if not all([abstract_problem, abstract_domain, concrete_problem, concrete_domain]):
        return jsonify({"error": "Missing one or more PDDL files"}), 400

    horizon = int(request.form.get("horizon", 1))
    encoding = request.form.get("encoding", "exact")
    time_step = request.form.get("timeStep", "false").lower() == "true"

    concrete_result, abstract_result = run_fastdownward_service(
            domain_file=concrete_domain,
            problem_file=concrete_problem,
            abstract_domain_file=abstract_domain,
            abstract_problem_file=abstract_problem
        )
    
    base_dir = os.path.dirname(concrete_result["sasFile"])
    output_c_lp = os.path.join(base_dir, "output_c.lp")
    output_a_lp = os.path.join(base_dir, "abstract", "output_a.lp")

    # Concrete LP
    generate_lp_with_plasp(
        sas_or_pddl_path=concrete_result["sasFile"],
        lp_output_path=output_c_lp,
        encoding_type=encoding,
        is_pddl_instance=False,
        abstract_time_steps=time_step
    )

    # Abstract LP
    generate_lp_with_plasp(
        sas_or_pddl_path=abstract_result["sasFile"],
        lp_output_path=output_a_lp,
        encoding_type=encoding,
        is_pddl_instance=False,
        abstract_time_steps=time_step
    )

    try:
        # For now, let's return a placeholder response
        result = {
            "sasFile": "concrete.sas",
            "planFile": "concrete.plan",
            "horizon": horizon
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
