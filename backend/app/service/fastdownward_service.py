import os
import subprocess
from ..persistence.db import db
from ..persistence.models import FastDownwardRequest
from ..utils.hashing import compute_hash_from_files


def run_fastdownward_service(domain_file, problem_file, abstract_domain_file=None,
    abstract_problem_file=None):
    # Read file content
    domain_bytes = domain_file.read()
    problem_bytes = problem_file.read()

    # Compute hash from file contents
    hash_value = compute_hash_from_files(domain_bytes, problem_bytes)

    # Define a base directory for storing this run
    current_directory = os.getcwd()
    base_dir = os.path.join(current_directory, "temp", hash_value)
    os.makedirs(base_dir, exist_ok=True)

    # File paths
    domain_file_path = os.path.join(base_dir, "domain.pddl")
    problem_file_path = os.path.join(base_dir, "problem.pddl")
    sas_file_path = os.path.join(base_dir, "output.sas")
    plan_file_path = os.path.join(base_dir, "sas_plan")

    # Save domain/problem files if they don’t exist yet
    if not os.path.exists(domain_file_path):
        with open(domain_file_path, "wb") as f:
            f.write(domain_bytes)
    if not os.path.exists(problem_file_path):
        with open(problem_file_path, "wb") as f:
            f.write(problem_bytes)

    # Check if result already exists
    existing_request = FastDownwardRequest.query.filter_by(
        hash_value=hash_value
    ).first()
    if existing_request:
        horizon = calculate_horizon(existing_request.plan_file_path)
        concrete_result = {
            "horizon": horizon,
            "sasFile": existing_request.sas_file_path,
            "planFile": existing_request.plan_file_path,
            "cached": True,
        }
    else:
        # Paths to necessary files and directories
        fast_downward_script = os.path.join(
            current_directory, "lib", "downward", "fast-downward.py"
        )

        # Command to execute fast-downward
        command = [
            "python3",
            fast_downward_script,
            "--plan-file",
            plan_file_path,
            "--sas-file",
            sas_file_path,
            "--keep-sas-file",
            domain_file_path,
            problem_file_path,
            "--search",
            "astar(lmcut())",
        ]

        # Execute the command
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Fast Downward execution failed: {result.stderr}")

        # Calculate horizon
        horizon = calculate_horizon(plan_file_path)

        # Save result to DB
        try:
            new_request = FastDownwardRequest(
                hash_value=hash_value,
                domain_file_path=domain_file_path,
                problem_file_path=problem_file_path,
                sas_file_path=sas_file_path,
                plan_file_path=plan_file_path,
            )
            db.session.add(new_request)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error saving to DB: {e}")

        concrete_result =  {
            "horizon": horizon,
            "sasFile": sas_file_path,
            "planFile": plan_file_path,
            "cached": False,
        }

    # optional: save abstract files
    abstract_result = None
    if abstract_domain_file and abstract_problem_file:

        # Separate hash for abstract files
        abstract_bytes_domain = abstract_domain_file.read()
        abstract_bytes_problem = abstract_problem_file.read()
        abstract_hash = compute_hash_from_files(abstract_bytes_domain, abstract_bytes_problem)

        abstract_dir = os.path.join(base_dir, "abstract")
        os.makedirs(abstract_dir, exist_ok=True)

        abstract_domain_path = os.path.join(abstract_dir, "domain.pddl")
        abstract_problem_path = os.path.join(abstract_dir, "problem.pddl")
        abstract_sas_file = os.path.join(abstract_dir, "output.sas")
        abstract_plan_file = os.path.join(abstract_dir, "sas_plan")

        with open(abstract_domain_path, "wb") as f:
            f.write(abstract_bytes_domain)
        with open(abstract_problem_path, "wb") as f:
            f.write(abstract_bytes_problem)
        
        # Check DB for abstract
        existing_abstract = FastDownwardRequest.query.filter_by(hash_value=abstract_hash).first()
        if existing_abstract:
            abstract_horizon = calculate_horizon(existing_abstract.plan_file_path)
            abstract_result = {
                "horizon": abstract_horizon,
                "sasFile": existing_abstract.sas_file_path,
                "planFile": existing_abstract.plan_file_path,
                "cached": True
            }
        else:
            # Run Fast Downward on abstract
            cmd = [
                "python3", fast_downward_script,
                "--plan-file", abstract_plan_file,
                "--sas-file", abstract_sas_file,
                "--keep-sas-file",
                abstract_domain_path,
                abstract_problem_path,
                "--search", "astar(lmcut())"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"Fast Downward (abstract) failed: {result.stderr}")

            abstract_horizon = calculate_horizon(abstract_plan_file)
            abstract_result = {
                "horizon": abstract_horizon,
                "sasFile": abstract_sas_file,
                "planFile": abstract_plan_file,
                "cached": False
            }

            # Save abstract result to DB
            try:
                new_abstract_request = FastDownwardRequest(
                    hash_value=abstract_hash,
                    domain_file_path=abstract_domain_path,
                    problem_file_path=abstract_problem_path,
                    sas_file_path=abstract_sas_file,
                    plan_file_path=abstract_plan_file,
                )
                db.session.add(new_abstract_request)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Error saving abstract to DB: {e}")

    return concrete_result, abstract_result

def calculate_horizon(plan_file_path):
    with open(plan_file_path, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    # If last line starts with a semicolon, it's a comment (like "; cost = ...")
    if lines and lines[-1].startswith(";"):
        return len(lines) - 1
    return len(lines)
