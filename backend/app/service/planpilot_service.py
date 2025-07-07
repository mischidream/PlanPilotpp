import os
import re
import time
import subprocess
import threading
from typing import List, Dict
from ..persistence.models import FastDownwardRequest
from ..utils.parsing import parse_facet_output, parse_solution_output, extract_plan_actions


class PlanpilotService:
    def __init__(self):
        self.process = None
        self.lock = threading.RLock()
        self.output_buffer = []
        self.reader_thread = None
        self.horizon = 0

    def run_planpilot_service(
        self, sas_file: str, horizon: int, encoding: str, abstract_time_steps: bool
    ) -> List[Dict]:
        print("Run planpilot")

        # Fetch SAS file from DB
        request_data = FastDownwardRequest.query.filter_by(
            sas_file_path=sas_file
        ).first()
        if not request_data:
            raise ValueError("SAS file not found in the database.")

        # Retrieve file details
        hash_value = request_data.hash_value
        sas_file_path = request_data.sas_file_path

        # Prepare LP file path
        current_directory = os.getcwd()
        lp_file_path = os.path.join(current_directory, "temp", hash_value, "output.lp")
        os.makedirs(os.path.dirname(lp_file_path), exist_ok=True)

        # Generate LP using plasp
        self._generate_lp_with_plasp(
            sas_or_pddl_path=sas_file_path,
            lp_output_path=lp_file_path,
            encoding_type=encoding,
            abstract_time_steps=abstract_time_steps,
            is_pddl_instance=False,
        )

        # Start FASB subprocess
        fasb_binary = os.path.join(
            current_directory,
            "lib",
            "planpilot",
            "bin",
            "fasb-x86_64-unknown-linux-gnu",
            "fasb",
        )
        fasb_command = [
            "stdbuf",
            "-oL",
            fasb_binary,
            lp_file_path,
            "-c",
            f"horizon={horizon}",
            "0",
        ]

        with self.lock:
            self.process = subprocess.Popen(
                fasb_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            self.reader_thread = threading.Thread(target=self._read_stdout, daemon=True)
            self.reader_thread.start()

        self.horizon = horizon

        self._wait_for_fasb_ready()
        output = self.send_command("?")
        return output

    def send_command(self, command: str) -> str:
        if not self.process:
            raise RuntimeError("FASB process not running")

        with self.lock:
            try:
                self.process.stdin.write(command + "\n")
                self.process.stdin.flush()

                prev_len = len(self.output_buffer)
                timeout = 2.0
                last_change_time = time.time()
                current_len = prev_len

                while time.time() - last_change_time < timeout:
                    new_len = len(self.output_buffer)
                    if new_len > current_len:
                        current_len = new_len
                        last_change_time = time.time()
                    time.sleep(0.1)

                new_output = self.output_buffer[prev_len:]
                output_str = "".join(new_output)

                if command.startswith(("?", "#??", "#!!", "|= %")):
                    return parse_facet_output(output_str, command)

                if re.match(r"!\s*\d*$", command.strip()):
                    return parse_solution_output(output_str)

                if command.strip().startswith(("+", "-")):
                    print("+ command")
                    return self.send_command("?")

                return "\n".join(new_output)

            except BrokenPipeError:
                raise RuntimeError("FASB process closed the pipe unexpectedly.")
            except Exception as e:
                raise RuntimeError(
                    f"Unexpected error communicating with FASB or parsing output: {e}"
                )
            
    def activate_best_plan(self, plan_file_path: str) -> Dict:
        # Resolve the request from DB
        request_data = FastDownwardRequest.query.filter_by(
            plan_file_path=plan_file_path
        ).first()
        if not request_data:
            raise ValueError("Plan file not found in the database.")
        
        hash_value = request_data.hash_value
        current_directory = os.getcwd()
        plan_file_path = os.path.join(current_directory, "temp", hash_value, "sas_plan")
        
        if not os.path.isfile(plan_file_path):
            raise FileNotFoundError("sas_plan file not found in expected location.")

        # Extract actions from plan
        parsed_facets = extract_plan_actions(plan_file_path)
        parsed_facets.sort(key=lambda x: x["timestep"])
        #print("parsed facets: ", parsed_facets)
        facets_by_time = {i: [] for i in range(1, self.horizon + 1)}
        activated, errors, timeline = [], [], []

        def group_facets_by_timestep(facets, horizon):
            grouped = {t: [] for t in range(1, horizon + 1)}
            for f in facets:
                t = f.get("timestep")
                if 1 <= t <= horizon:
                    grouped[t].append(f)
            return grouped

        try:
            all_optionals = self.send_command("#??")
            optional_by_time = group_facets_by_timestep(all_optionals, self.horizon)
        except Exception as e:
            optional_by_time = {t: [] for t in range(1, self.horizon + 1)}
            errors.append({"type": "optional-fetch", "error": str(e)})

        # Initialize timeline structure first
        timeline = [{"timestep": t, "facets": []} for t in range(1, self.horizon + 1)]
        global_implied_ids = set()

        for t in range(1, self.horizon + 1):
            step = timeline[t - 1]["facets"]

            # Plan facets for this timestep
            plan_facets = [f for f in parsed_facets if f["timestep"] == t]

            for facet in plan_facets:
                if facet["id"] in global_implied_ids:
                    continue

                step.append({"type": "plan", "facet": facet})

                try:
                    cmd_str = "+ " + facet["id"]
                    self.send_command(cmd_str)
                    activated.append(f"+ {facet['id']}")
                except Exception as e:
                    errors.append({"action": cmd_str, "error": str(e)})
                    continue

                try:
                    all_implied = self.send_command("|= %")
                    for implied_facet in all_implied:
                        implied_id = implied_facet["id"]
                        implied_ts = implied_facet.get("timestep")

                        if implied_id in global_implied_ids or implied_ts is None:
                            continue  # Skip if already added or malformed

                        global_implied_ids.add(implied_id)

                        # Add implied facet to correct future step
                        if 1 <= implied_ts <= self.horizon:
                            timeline[implied_ts - 1]["facets"].append({
                                "type": "implied",
                                "facet": implied_facet,
                                "causedBy": facet["id"]
                            })

                except Exception as e:
                    errors.append({"type": "implied-fetch", "error": str(e)})

            # If this step has no plan or implied facets, try to fetch open ones
            if not any(f["type"] in ("plan", "implied") for f in step):
                try:
                    all_open = self.send_command("?")
                    open_facets = [f for f in all_open if f.get("timestep") == t]
                except Exception as e:
                    open_facets = []
                    errors.append({"type": "open-fetch", "error": str(e)})

                step.append({"type": "empty", "facets": open_facets})


        final_output = self.send_command("!")

        return {
            "activated": activated,
            "errors": errors,
            "bestPlan": final_output[0] if final_output else None,
            "timeline": timeline
        }


    def stop_fasb(self):
        if self.process:
            self.process.terminate()
            self.process = None

    def _read_stdout(self):
        while self.process and self.process.stdout:
            line = self.process.stdout.readline()
            if not line:
                break
            self.output_buffer.append(line)

    def _wait_for_fasb_ready(self, timeout: float = 5.0) -> None:
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.lock:
                for line in self.output_buffer:
                    if "fasb v" in line:
                        return
            time.sleep(0.1)
        raise TimeoutError("FASB did not become ready in time.")

    def _generate_lp_with_plasp(
        self,
        sas_or_pddl_path: str,
        lp_output_path: str,
        encoding_type: str = "exact",
        is_pddl_instance: bool = False,
        domain_file: str = None,
        abstract_time_steps: bool = False,
    ):
        current_directory = os.getcwd()
        plasp_binary = os.path.join(current_directory, "lib", "planpilot", "bin", "plasp")

        encoding_dir = os.path.join(current_directory, "lib", "planpilot", "encodings")
        encoding_file = os.path.join(
            encoding_dir,
            (
                "exact-sequential-horizon.lp"
                if encoding_type == "exact"
                else "bounded-sequential-horizon.lp"
            ),
        )
        time_file = os.path.join(
            encoding_dir,
            (
                "abstract-time-steps.lp"
                if abstract_time_steps
                else "action-per-time-step.lp"
            ),
        )

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
                command, stdout=lp_file, stderr=subprocess.PIPE, text=True
            )

        if result.returncode != 0:
            raise RuntimeError(f"plasp failed:\n{result.stderr}")
