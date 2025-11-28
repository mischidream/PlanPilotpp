import os
import re
import subprocess
import threading
import time
from typing import Dict

from ...persistence.models import FastDownwardRequest
from ...utils.parsing import extract_plan_actions, parse_facet_output, parse_solution_output
from ...utils.plan_utils import *


class PlanPilotInstance:
    def __init__(
        self,
        page_id: str,
        manager,
        sas_file_path=None,
        horizon=None,
        encoding=None,
        hash_value=None,
        abstract_timestep=None,
    ):
        self.page_id = page_id
        self.manager = manager

        # Thread safety
        self.lock = threading.RLock()

        # Subprocess
        self.process: subprocess.Popen | None = None
        self.reader_thread: threading.Thread | None = None

        # Output buffering
        self.output_buffer = []
        self.running = False

        # Refresh status
        self.refresh_in_progress = False
        self.refresh_lock = threading.RLock()

        # Domain-specific data
        self.timeline = []
        self.facet_count = None
        self.errors = None
        self.best_plan = None
        self.horizon = horizon
        self.encoding = encoding
        self.sas_file_path = sas_file_path
        self.hash_value = hash_value
        self.abstract_timestep = abstract_timestep

    def start(self, sas_file=None, horizon=None, encoding=None, abstract_time_steps=None, from_existing=False):
        print("Run planpilot")
        
        if from_existing:
            horizon = self.horizon
            encoding = self.encoding
            abstract_time_steps = self.abstract_timestep
        else:
            # Reset horizon and timeline
            self.horizon = 0
            self.timeline = []
            self.facet_count = None
            self.errors = None
            # fetch from DB as usual
            request_data = FastDownwardRequest.query.filter_by(
                sas_file_path=sas_file
            ).first()
            if not request_data:
                raise ValueError("SAS file not found in the database.")

            # Retrieve file details
            self.sas_file_path = request_data.sas_file_path
            self.hash_value = request_data.hash_value

            self.encoding = encoding
            self.abstract_timestep = abstract_time_steps
            self.horizon = horizon

        # Prepare LP file path
        current_directory = os.getcwd()
        lp_file_path = os.path.join(current_directory, "temp", self.hash_value, "output.lp")
        os.makedirs(os.path.dirname(lp_file_path), exist_ok=True)

        # Generate LP using plasp
        self._generate_lp_with_plasp(
            sas_or_pddl_path=self.sas_file_path,
            lp_output_path=lp_file_path,
            encoding_type=encoding,
            abstract_time_steps=abstract_time_steps,
            is_pddl_instance=False,
        )

        # Kill old process if exists
        if self.process:
            self._terminate_process(self.process)
            self.process = None
            self.output_buffer = []

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
            self.running = True
            self.reader_thread = threading.Thread(target=self._read_stdout, daemon=True)
            self.reader_thread.start()

        self._wait_for_fasb_ready()
        output = self.send_command("?")
        return output

    def send_command(self, command: str, no_Output: bool = False) -> str:
        if not self.process:
            raise RuntimeError("FASB process not running")

        with self.lock:
            try:
                self.process.stdin.write(command + "\n")
                self.process.stdin.flush()

                if command.strip().startswith(("+", "-")):
                    print(command)
                    if no_Output:
                        return
                    return self.send_command("?")

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

                if command.startswith(("?", "#??", "#!!", "|= %", "|=")):
                    return parse_facet_output(output_str, command)

                if re.match(r"!\s*\d*$", command.strip()):
                    return parse_solution_output(output_str)

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
        facets_by_timestep = {}
        for facet in parsed_facets:
            ts = facet["timestep"]
            facets_by_timestep[ts] = facet

        errors, timeline = [], []
        timeline = [{"timestep": t, "facets": []} for t in range(1, self.horizon + 1)]
        global_implied_ids = set()
        activated_plan_ids = set()

        errors.append(
            fetch_and_add_implied_facets(
                self, timeline, global_implied_ids, "plan", self.horizon
            )
        )

        for t in range(1, self.horizon + 1):
            step = timeline[t - 1]["facets"]

            plan_facet = facets_by_timestep.get(t)

            if plan_facet:
                errors.extend(fetch_and_add_optional_facets(self, timeline, t))

                facet_id = plan_facet["id"]
                if facet_id not in global_implied_ids:
                    plan_facet["selectionState"] = "+"
                    step.append({"type": "plan", "facets": [plan_facet]})

                    try:
                        cmd_str = "+ " + facet_id
                        self.send_command(cmd_str, no_Output=True)
                        activated_plan_ids.add(facet_id)
                    except Exception as e:
                        errors.append({"action": cmd_str, "error": str(e)})

                errors.append(
                    fetch_and_add_implied_facets(
                        self, timeline, global_implied_ids, facet_id, self.horizon
                    )
                )

            if not any(f["type"] in ("plan", "implied") for f in step):
                errors.extend(fetch_and_add_empty_facets(self, timeline, t))

            # If the step contains only implied facets, add them again as optional (since fast_update_plan does not update it anymore)
            elif all(f["type"] == "implied" for f in step):
                try:
                    # collect all implied facet entries into a single list
                    implied_facets = []
                    for implied_block in step:
                        implied_facets.extend(implied_block.get("facets", []))

                    if implied_facets:
                        # re-add them as optional facets directly
                        add_facet_to_timestep(timeline, t, "optional", implied_facets)
                    else:
                        errors.extend(fetch_and_add_empty_facets(self, timeline, t))
                except Exception as e:
                    errors.append(
                        {
                            "type": "readd-implied-as-optional",
                            "timestep": t,
                            "error": str(e),
                        }
                    )

        self.timeline = timeline

        facetCount = self.send_command("#?")

        return {
            "errors": errors,
            "bestPlan": parsed_facets,
            "timeline": timeline,
            "facetCount": facetCount,
        }

    def update_plan_from_timestep(self, changed_timestep, commands):
        errors = []

        if not hasattr(self, "timeline") or not hasattr(self, "horizon"):
            raise RuntimeError("Timeline or horizon not initialized.")

        command = commands[0].strip()
        clean_id = command.lstrip("+-~ ").strip()
        t = changed_timestep

        # Apply user command
        fast_apply_user_command(self, command, t, errors)

        # Update timeline
        if not command.startswith("-"):
            # Fetch changes
            implied_facets = fetch_implied_facets(self, errors)
            removed_facets = fetch_removed_facets(self, errors)

            add_implied_facets(self, implied_facets, clean_id, errors)
            remove_facets_from_timeline(self, removed_facets, t, errors)

        # Get updated facet count
        facet_count = calculate_facet_count(self)

        # Launch background recompute
        if self.manager:
            self.manager.start_background_refresh(self)

        # Return result
        return {
            "timeline": self.timeline,
            "errors": errors,
            "facetCount": facet_count,
        }
    
    def start_background_refresh_process(self):
        self.start(from_existing=True)
        errors, facet_count = refresh_optionals_and_empties(self)
        self.facet_count = facet_count
        self.errors = errors

    def refresh_timestep_optional_facet(self, timestep_number: int):
        # Refreshes the 'optional' facet for the given timestep and updates it in the timeline.
        refreshed_facet = self._get_refreshed_optional_facet(timestep_number)
        if refreshed_facet is None:
            print(f"Failed to refresh optional facet for timestep {timestep_number}")
            return None

        with self.lock:
            if self.timeline is None:
                print("Timeline not initialized — cannot update optional facet.")
                return None

            timestep_facets = self.timeline[timestep_number - 1]

            # Remove old optional facet from the list of facets
            timestep_facets["facets"] = [
                f for f in timestep_facets["facets"] if f.get("type") != "optional"
            ]

            # Add new optional facet
            timestep_facets["facets"].append(refreshed_facet)
            self.timeline[timestep_number - 1] = timestep_facets

            # Calculate facet count
            facet_count = calculate_facet_count(self)

            refreshed_answer = {
                "refreshedFacet": refreshed_facet,
                "facetCount": facet_count,
            }

        return refreshed_answer
    
    def _get_refreshed_optional_facet(self, timestep_number: int):
        command = f"? {timestep_number}"  # query actions at this timestep
        try:
            facets = self.send_command(command)

            timeline_facet = {
                "type": "optional",
                "facets": facets,
                "causedBy": None,
            }

            return timeline_facet

        except Exception as e:
            print(
                f"Error refreshing optional facet for timestep {timestep_number}: {e}"
            )
            return None

    def stop(self):
        if self.process:
            self._terminate_process(self.process)
            self.process = None

        # cleanup helper state
        self.output_buffer = []
        self.reader_thread = None
        self.running = False
    
    def _terminate_process(self, proc: subprocess.Popen):
        if proc.poll() is None:  # process is still running
            try:
                proc.terminate()
                try:
                    proc.wait(timeout=5)  # wait for graceful exit
                except subprocess.TimeoutExpired:
                    proc.kill()  # force kill if it doesn’t exit
                    proc.wait()
            except Exception as e:
                print(f"Failed to terminate process: {e}")

    def _wait_for_fasb_ready(self, timeout: float = 5.0) -> None:
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.lock:
                for line in self.output_buffer:
                    if "fasb v" in line:
                        return
            time.sleep(0.1)
        raise TimeoutError("FASB did not become ready in time.")

    def _read_stdout(self):
        while self.process and self.process.stdout:
            line = self.process.stdout.readline()
            if not line:
                break
            self.output_buffer.append(line)
    
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
        plasp_binary = os.path.join(
            current_directory, "lib", "planpilot", "bin", "plasp"
        )

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
