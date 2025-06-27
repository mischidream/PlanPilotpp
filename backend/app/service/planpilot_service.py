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

                if command in ("?", "#??", "#!!") or command.startswith("|= %"):
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
        actions = extract_plan_actions(plan_file_path)
        print("actions: ", actions)
        activated = []
        errors = []

        for action in actions:
            try:
                self.send_command(action)
                activated.append(action)
                time.sleep(0.1)
            except Exception as e:
                errors.append({"action": action, "error": str(e)})

        final_output = self.send_command("!")
        print(final_output)
        
        return {
            "activated": activated,
            "errors": errors,
            "solution": final_output
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
        current_dir = os.getcwd()
        plasp_binary = os.path.join(current_dir, "lib", "planpilot", "bin", "plasp")

        encoding_dir = os.path.join(current_dir, "lib", "planpilot", "encodings")
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
