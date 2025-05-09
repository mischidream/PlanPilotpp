import os
import re
import time
from ..persistence.models import FastDownwardRequest
import subprocess
import threading
from typing import List, Dict
from ...lib.planpilot.planpilot import run_plasp

class PlanpilotService:
    def __init__(self):
        self.process = None
        self.lock = threading.Lock()
    
    def run_planpilot_service(self, sas_file: str, horizon: int, encoding: str) -> List[Dict]:
        # Fetch SAS file from the database (assumed saved in your DB)
        request_data = FastDownwardRequest.query.filter_by(sas_file_path=sas_file).first()
        if not request_data:
            raise ValueError("SAS file not found in the database.")
        
        # Retrieve the necessary file path from the database
        hash_value = request_data.hash_value
        sas_file_path = request_data.sas_file_path

        # Now, we will create the LP file path, which should be stored in the database later
        current_directory = os.getcwd()
        lp_file_path = os.path.join(current_directory, "temp", hash_value, "output.lp")
        os.makedirs(os.path.dirname(lp_file_path), exist_ok=True)

        # Path to the PlanPilot script (no domain/problem file)
        planpilot_directory = os.path.join(current_directory, "lib", "planpilot")
        planpilot_script = os.path.join(planpilot_directory, "planpilot.py")

        # Prepare the command to execute the PlanPilot script
        command = [
            "python3", planpilot_script, 
            "--instance", sas_file_path,
            "--horizon", str(horizon),
            "--encoding", encoding,
            "--lp-name", lp_file_path
        ]

        try:
            result = subprocess.run(
                command,
                cwd=planpilot_directory,
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"PlanPilot failed with exit code {e.returncode}\n"
                f"Command: {' '.join(command)}\n"
                f"Stdout:\n{e.stdout}\n"
                f"Stderr:\n{e.stderr}"
            )
        
        fasb_binary = os.path.join(planpilot_directory, "bin", "fasb-x86_64-unknown-linux-gnu", "fasb")
        fasb_command = [
            fasb_binary,
            lp_file_path,
            "-c", f"horizon={horizon}",
            "0"
        ]

        with self.lock:
            self.process = subprocess.Popen(
                fasb_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

        # Wait for fasb to be ready before sending commands
        self._wait_for_fasb_ready()

        # Send initial command to list facets
        output = self.send_command("?")

        # Parse the output
        facets = self.parse_facet_output(output)

        return facets
    
    def parse_facet_output(self, output: str) -> List[Dict]:
        pattern = r'occurs\(action\(\(([^)]+)\)\),(\d+)\)'
        matches = re.findall(pattern, output)

        facets = []
        for idx, (action_part, timestep_str) in enumerate(matches):
            parts = [p.strip().strip('"') for p in action_part.split(",")]

            action_type = parts[0]
            constant1 = parts[1] if len(parts) > 1 else None
            constant2 = parts[2] if len(parts) > 2 else None

            facet = {
                "id": idx + 1,
                "action": action_type,
                "constant1": constant1,
                "constant2": constant2,
                "timestep": int(timestep_str),
                "reduction": None,
                "remaining": None,
                "selectionState": "NotSelected"
            }

            facets.append(facet)

        return facets
    
    def _wait_for_fasb_ready(self, timeout: float = 5.0) -> None:
        """Waits until fasb prints its ready prompt."""
        start_time = time.time()
        buffer = []

        while time.time() - start_time < timeout:
            if self.process.stdout.readable():
                line = self.process.stdout.readline()
                if line:
                    buffer.append(line.strip())
                    if "fasb v" in line:
                        return
            time.sleep(0.1)  # prevent CPU spin
        raise TimeoutError("FASB did not become ready in time.\nPartial output:\n" + "\n".join(buffer))
    
    def send_command(self, command: str) -> str:
        if not self.process:
            raise RuntimeError("FASB process not running")

        with self.lock:
            try:
                self.process.stdin.write(command + '\n')
                self.process.stdin.flush()

                output_lines = []
                while True:
                    line = self.process.stdout.readline()
                    if not line or line.strip() == "":
                        break
                    output_lines.append(line.strip())

                return "\n".join(output_lines)

            except BrokenPipeError:
                raise RuntimeError("FASB process closed the pipe unexpectedly.")
            except Exception as e:
                raise RuntimeError(f"Unexpected error communicating with FASB: {e}")

    def stop_fasb(self):
        if self.process:
            self.process.terminate()
            self.process = None