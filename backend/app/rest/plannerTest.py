from flask import Blueprint, request, jsonify
import os

from .fastdownward import run_fastdownward_service
from ..utils.plasp_utils import generate_lp_with_plasp
from ..utils.clingo_utils import *

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

    clingo_dir = os.path.join(base_dir, "clingo")
    os.makedirs(clingo_dir, exist_ok=True)

    occurs_abs_lp_path = os.path.join(clingo_dir, "occurs_abs.lp")
    map_lp_path = os.path.join(clingo_dir, "map.lp")

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

    # Solve abstract LP
    abstract_atoms = solve_abstract_lp(output_a_lp, horizon)

    # Create occurs_abs.lp
    write_occurs_abs_lp(abstract_atoms, occurs_abs_lp_path)

    # Read occurs_abs.lp back
    abs_atoms_for_map = read_occurs_abs_lp(occurs_abs_lp_path)

    # Create map.lp
    concrete_hangars = ["hangar1", "hangar2"]
    create_map_lp(
        atoms=abs_atoms_for_map,
        output_path=map_lp_path,
        concrete_hangars=concrete_hangars
    )

    # Solve concrete LP
    plans = solve_concrete_lp_with_mapping(
        output_c_lp=output_c_lp,
        occurs_abs_lp=occurs_abs_lp_path,
        map_lp=map_lp_path,
        horizon=horizon
    )
    for i, plan in enumerate(plans):
        print(f"--- PLAN {i+1} ---")
        for atom in sorted(plan, key=lambda a: a.arguments[-1].number):
            print(atom)

    
    plan_strings = []
    for plan in plans:
        sorted_plan = sorted(plan, key=lambda a: a.arguments[1].number)
        plan_strings.append([str(atom) for atom in sorted_plan])


    plan_strs1 = ["; ".join(str(a) for a in plan) for plan in plans]
    plan_strings2 = [
        [str(atom) for atom in model]
        for model in plans
    ]

    try:
        return jsonify({
            "horizon": horizon,
            "numPlans": len(plan_strings),
            "plans": plan_strings
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
