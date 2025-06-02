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
        self.lock = threading.RLock()
        self.output_buffer = []
        self.reader_thread = None
    
    def run_planpilot_service(self, sas_file: str, horizon: int, encoding: str, abstract_time_steps: bool) -> List[Dict]:
        print("Run planpilot")
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

        self._generate_lp_with_plasp(
            sas_or_pddl_path=sas_file_path,
            lp_output_path=lp_file_path,
            encoding_type=encoding,
            abstract_time_steps=abstract_time_steps,
            is_pddl_instance=False
        )

        fasb_binary = os.path.join(current_directory, "lib", "planpilot", "bin", "fasb-x86_64-unknown-linux-gnu", "fasb")
        fasb_command = [
            "stdbuf", "-oL",  # Line-buffer stdout
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
            self.reader_thread = threading.Thread(target=self._read_stdout, daemon=True)
            self.reader_thread.start()

        # Wait for fasb to be ready before sending commands
        self._wait_for_fasb_ready()

        # Send initial command to list facets
        output = self.send_command("?")

        return output
    
    def _read_stdout(self):
        while self.process and self.process.stdout:
            line = self.process.stdout.readline()
            if not line:
                break
            #cleaned = line.strip()
            self.output_buffer.append(line)

    def _parse_facet_output(self, output: str, command: str) -> List[Dict]:
        def make_facet(action_str, timestep, raw_id):
            parts = [p.strip().strip('"') for p in action_str.split(",")]
            return {
                "id": raw_id,
                "action": parts[0],
                "constant1": parts[1] if len(parts) > 1 else None,
                "constant2": parts[2] if len(parts) > 2 else None,
                "timestep": int(timestep),
                "reduction": {
                    "solution": {"positive": None, "negative": None},
                    "facets": {"positive": None, "negative": None}
                },
                "remaining": {
                    "solution": {"positive": None, "negative": None},
                    "facets": {"positive": None, "negative": None}
                },
                "selectionState": "Not selected"
            }

        if command == "?" or command.startswith("|= %"):
            facets = []
            pattern = r'(occurs(?:_sometime)?\(action\(\(([^)]+)\)\)(?:,(\d+))?\))'
            matches = re.findall(pattern, output)
            for full_match, action_str, timestep in matches:
                ts = int(timestep) if timestep else 0  # default to 0 for occurs_sometime
                facets.append(make_facet(action_str, ts, full_match))
            return facets

        elif command in ("#??", "#!!"):
            tokens = output.strip().split()
            facets = {}
            key_to_id = {}

            # Iterate in chunks of 3 (val1, val2, occurs...)
            for i in range(0, len(tokens) - 2, 3):
                val1_str = tokens[i]
                val2_str = tokens[i + 1]
                action_part = tokens[i + 2]
                match = re.search(r'(occurs(?:_sometime)?\(action\(\(([^)]+)\)\)(?:,(\d+))?\))', action_part)
                if not match:
                    continue

                full_match, action_str, timestep = match.groups()
                ts = int(timestep) if timestep else 0  # default to 0 for occurs_sometime
                key = (action_str, ts)

                if key not in facets:
                    key_to_id[key] = full_match
                    facets[key] = make_facet(action_str, ts, full_match)

                facet = facets[key]
                target = "solution" if command == "#!!" else "facets"
                sign = "negative" if '~' in action_part else "positive"

                facet["reduction"][target][sign] = float(val1_str)
                facet["remaining"][target][sign] = float(val2_str)

            return list(facets.values())

        return []
    
    def _parse_solution_output(self, output: str) -> List[Dict]:
        solutions = []
        action_id = 0

        # Split by each solution block
        solutions = re.split(r'solution (\d+):', output.strip())

        for i in range(1, len(solutions), 2):
            solution_number = solutions[i]
            actions_block = solutions[i + 1]

            current_actions = []

            # Find all occurs(...) within this block
            pattern = r'(occurs(?:_sometime)?\(action\(\(([^)]+)\)\)(?:,(\d+))?\))'
            action_matches = re.findall(pattern, actions_block)

            for full_match, action_str, timestep in action_matches:
                parts = [p.strip().strip('"') for p in action_str.split(",")]
                action_type = parts[0]
                const1 = parts[1] if len(parts) > 1 else None
                const2 = parts[2] if len(parts) > 2 else None

                ts = int(timestep) if timestep else 0  # Default timestep for occurs_sometime

                action_dict = {
                    "id": full_match,
                    "action": action_type,
                    "constant1": const1,
                    "constant2": const2,
                    "timestep": ts,
                    "reduction": None,
                    "remaining": None
                }
                current_actions.append(action_dict)
                action_id += 1

            solutions.append({
                "label": f"solution {solution_number}",
                "facets": current_actions
            })
        
        return solutions

    def _generate_lp_with_plasp(self, sas_or_pddl_path: str, lp_output_path: str, encoding_type: str = "exact", is_pddl_instance: bool = False, domain_file: str = None, abstract_time_steps: bool = False):
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

    
    def _wait_for_fasb_ready(self, timeout: float = 5.0) -> None:
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.lock:
                for line in self.output_buffer:
                    if "fasb v" in line:
                        return
            time.sleep(0.1)
        raise TimeoutError("FASB did not become ready in time.")
    
    def send_command(self, command: str) -> str:
        if not self.process:
            raise RuntimeError("FASB process not running")

        with self.lock:
            try:
                self.process.stdin.write(command + '\n')
                self.process.stdin.flush()

                prev_len = len(self.output_buffer)
                timeout = 2.0
                last_change_time = time.time()
                current_len = prev_len

                while time.time() - last_change_time < timeout:
                    new_len = len(self.output_buffer)
                    if new_len > current_len:
                        current_len = new_len
                        last_change_time = time.time() # reset timer on new data
                    time.sleep(0.1)

                # Get the new output after the previous length
                new_output = self.output_buffer[prev_len:]

                print("command: \"" + command + "\"")
                #print("output: ", new_output)

                # Normalize new_output to a string
                output_str = "".join(new_output)

                #print(output_str)

                # If the command is one of "?", "#??", or "#!!", parse the output
                if command in ("?", "#??", "#!!") or command.startswith("|= %"):
                    parsed_output = self._parse_facet_output(output_str, command)
                    return parsed_output
                
                if re.match(r"!\s*\d*$", command.strip()):
                    return self._parse_solution_output(output_str)
                
                if command.strip().startswith(('+', '-')):
                    print("+ command")
                    return self.send_command('?')
                
                # If it's not one of these commands, just return the raw output
                return "\n".join(new_output)

            except BrokenPipeError:
                raise RuntimeError("FASB process closed the pipe unexpectedly.")
            except Exception as e:
                raise RuntimeError(f"Unexpected error communicating with FASB or parsing output: {e}")

    def stop_fasb(self):
        if self.process:
            self.process.terminate()
            self.process = None