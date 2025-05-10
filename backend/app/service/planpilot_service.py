import os
import re
import time
from ..persistence.models import FastDownwardRequest
import subprocess
import threading
from typing import List, Dict

class PlanpilotService:
    def __init__(self):
        self.process = None
        self.lock = threading.Lock()
        self.output_buffer = []
        self.reader_thread = None
    
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
        #current_directory = os.path.join(current_directory, "backend")
        lp_file_path = os.path.join(current_directory, "temp", hash_value, "output.lp")
        os.makedirs(os.path.dirname(lp_file_path), exist_ok=True)

        print("run plasp")
        self.generate_lp_with_plasp(
            sas_or_pddl_path=sas_file_path,
            lp_output_path=lp_file_path,
            encoding_type=encoding,
            is_pddl_instance=False
        )
        
        print("run fasb")
        fasb_binary = os.path.join(current_directory, "lib", "planpilot", "bin", "fasb-x86_64-unknown-linux-gnu", "fasb")
        fasb_command = [
            "stdbuf", "-oL",  # Line-buffer stdout
            fasb_binary,
            lp_file_path,
            "-c", f"horizon={horizon}",
            "0"
        ]

        print("start process")
        with self.lock:
            self.process = subprocess.Popen(
                fasb_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            self.reader_thread = threading.Thread(target=self._read_stdout, daemon=True)
            self.reader_thread.start()

        # Wait for fasb to be ready before sending commands
        self.wait_for_fasb_ready()

        # Send initial command to list facets
        output = self.send_command("?")

        print(output)

        # Parse the output
        facets = self.parse_facet_output(output)

        return facets
    
    def _read_stdout(self):
        while self.process and self.process.stdout:
            line = self.process.stdout.readline()
            if not line:
                break
            cleaned = line.strip()
            print(f"[fasb] {cleaned}")
            self.output_buffer.append(cleaned)
    
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
    
    def generate_lp_with_plasp(self, sas_or_pddl_path: str, lp_output_path: str, encoding_type: str = "exact", is_pddl_instance: bool = False, domain_file: str = None, abstract_time_steps: bool = False):
        current_dir = os.getcwd()
        #current_dir = os.path.join(current_dir, "backend")
        plasp_binary = os.path.join(current_dir, "lib", "planpilot", "bin", "plasp")

        encoding_dir = os.path.join(current_dir, "lib", "planpilot", "encodings")
        encoding_file = os.path.join(encoding_dir, "exact-sequential-horizon.lp" if encoding_type == "exact" else "bounded-sequential-horizon.lp")
        time_file = os.path.join(encoding_dir, "abstract-time-steps.lp" if abstract_time_steps else "action-per-time-step.lp")

        command = [plasp_binary, "translate"]
        if is_pddl_instance:
            if not domain_file:
                raise ValueError("Domain file is required for PDDL input.")
            command.extend([domain_file, sas_or_pddl_path])
        else:
            command.append(sas_or_pddl_path)

        with open(lp_output_path, "w") as lp_file:
            with open(encoding_file, "r") as ef:
                lp_file.write(ef.read())
            with open(time_file, "r") as tf:
                lp_file.write(tf.read())

            result = subprocess.run(
                command,
                stdout=lp_file,
                stderr=subprocess.PIPE,
                text=True
            )

        if result.returncode != 0:
            raise RuntimeError(f"plasp failed:\n{result.stderr}")

    
    def wait_for_fasb_ready(self, timeout: float = 5.0) -> None:
        print("wait for fasb to be ready")
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.lock:
                for line in self.output_buffer:
                    if "fasb v" in line:
                        return
            time.sleep(0.1)
        raise TimeoutError("FASB did not become ready in time.")
    
    def send_command(self, command: str) -> str:
        print("send command to fasb")
        if not self.process:
            raise RuntimeError("FASB process not running")

        with self.lock:
            try:
                print("send command: " + command)
                self.process.stdin.write(command + '\n')
                self.process.stdin.flush()

                prev_len = len(self.output_buffer)
                timeout = 2.0
                start_time = time.time()

                while time.time() - start_time < timeout:
                    if len(self.output_buffer) > prev_len:
                        break
                    time.sleep(0.1)

                new_output = self.output_buffer[prev_len:]
                return "\n".join(new_output)

            except BrokenPipeError:
                raise RuntimeError("FASB process closed the pipe unexpectedly.")
            except Exception as e:
                raise RuntimeError(f"Unexpected error communicating with FASB: {e}")

    def stop_fasb(self):
        if self.process:
            self.process.terminate()
            self.process = None