import os
import subprocess

def run_fastdownward_service(domain_file, problem_file):
    # Paths to necessary files and directories
    current_directory = os.getcwd()
    fast_downward_script = os.path.join(current_directory, "backend", "lib", "downward", "fast-downward.py")
    sas_file_dir = os.path.join(current_directory, "backend", "sas_files")
    
    # Construct file paths
    domain_file_path = os.path.join(current_directory, "backend", "lib", "planpilot", "benchmarks", "blocks", domain_file)
    problem_file_path = os.path.join(current_directory, "backend", "lib", "planpilot", "benchmarks", "blocks", problem_file)

    # Check if files exist
    if not os.path.exists(domain_file_path) or not os.path.exists(problem_file_path):
        raise FileNotFoundError("One or more files do not exist.")

    # Paths to save the SAS file and plan file
    sas_file_path = os.path.join(sas_file_dir, "output.sas")
    plan_file_path = os.path.join(sas_file_dir, "sas_plan")

    # Command to execute fast-downward
    command = [
        "python3", fast_downward_script,
        "--plan-file", plan_file_path,
        "--sas-file", sas_file_path,
        "--keep-sas-file",
        domain_file_path,
        problem_file_path,
        "--search", "astar(lmcut())"
    ]

    # Execute the command
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Fast Downward execution failed: {result.stderr}")

    # For simplicity, returning a placeholder horizon (this could be parsed from the output)
    return {
        "horizon": 10,  # Replace with actual logic to extract horizon from Fast Downward output if needed
        "sasFile": sas_file_path
    }
