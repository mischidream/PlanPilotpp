from ..utils.parsing import parse_facet_output


def clear_timeline_from_timestep(timeline, start_timestep):
    for t in range(start_timestep - 1, len(timeline)):
        timeline[t]["facets"] = []

def clear_all_but_implied_from_timestep(timeline, start_timestep):
    for t in range(start_timestep, len(timeline) + 1):
        step = timeline[t - 1]
        step["facets"] = [
            block for block in step.get("facets", [])
            if block.get("type") == "implied"
        ]

def add_facet_to_timestep(timeline, timestep, facet_type, facets, caused_by=None):
    entry = {"type": facet_type, "facets": facets}
    if caused_by:
        entry["causedBy"] = caused_by
    timeline[timestep - 1]["facets"].append(entry)

def fetch_and_add_optional_facets(service, timeline, timestep):
    try:
        optionals = service.send_command(f"? {timestep}")
        if optionals:
            add_facet_to_timestep(timeline, timestep, "optional", optionals)
        return []
    except Exception as e:
        return [{"type": "optional-fetch", "timestep": timestep, "error": str(e)}]

def fetch_and_add_empty_facets(service, timeline, timestep, used_facet_ids=None):
    try:
        all_open = service.send_command("?")
        open_facets = [f for f in all_open if f.get("timestep") == timestep]
        if used_facet_ids is not None:
            open_facets = [f for f in open_facets if f.get("id") not in used_facet_ids]
        if open_facets:
            add_facet_to_timestep(timeline, timestep, "empty", open_facets)
        return []
    except Exception as e:
        return [{"type": "open-fetch", "timestep": timestep, "error": str(e)}]
    
def fetch_and_replace_empty_facets(service, timeline, timestep):
    step = timeline[timestep - 1]

    if any(f.get("type") in ("plan", "implied", "selected") for f in step.get("facets", [])):
        return []

    try:
        empty_facets = service.send_command(f"? {timestep}")

        used_facet_ids = set()
        for f in step.get("facets", []):
            for facet in f.get("facets", []):
                if "id" in facet:
                    used_facet_ids.add(facet["id"])

        filtered_empty = [f for f in empty_facets if f.get("id") not in used_facet_ids]

        # Remove previous empty facets
        step["facets"] = [f for f in step.get("facets", []) if f.get("type") != "empty"]

        if filtered_empty:
            step["facets"].append({"type": "empty", "facets": filtered_empty})

        return []
    except Exception as e:
        return [{"type": "empty-fetch", "timestep": timestep, "error": str(e)}]

def fetch_and_add_implied_facets(service, timeline, global_implied_ids, base_facet_id, horizon):
    errors = []
    try:
        implied = service.send_command("|= %")
        for f in implied:
            implied_id = f["id"]
            ts = f.get("timestep")

            if ts is None or not (1 <= ts <= horizon):
                # Invalid timestep, skip
                continue

            # Check if facet already present at the timestep
            found = False
            for item in timeline[ts - 1]["facets"]:
                if item["type"] == "implied":
                    existing_ids = {facet["id"] for facet in item["facets"]}
                    if implied_id in existing_ids:
                        # Append to impliedBy if not already present
                        if base_facet_id not in item.get("impliedBy", []):
                            item.setdefault("impliedBy", []).append(base_facet_id)
                        found = True
                        break

            if not found:
                f["selectionState"] = "+"
                # Add a new implied facet entry
                timeline[ts - 1]["facets"].append({
                    "type": "implied",
                    "facets": [f],
                    "impliedBy": [base_facet_id]
                })

            # Track it globally regardless of duplication or activation
            global_implied_ids.add(implied_id)

    except Exception as e:
        errors.append({"type": "implied-fetch", "error": str(e)})

    return errors

def undo_facets(service, step_data, timeline):
    errors = []

    for step in step_data:
        for block in step.get("facets", []):
            if block.get("type") in ("selected", "plan"):
                for facet in block.get("facets", []):
                    facet_id = facet.get("id")
                    selection_state = facet.get("selectionState", "Not selected")
                    if facet_id and selection_state != "Not selected":
                        if selection_state == "+":
                            undo_cmd = f"- {facet_id}"
                        elif selection_state == "-":
                            undo_cmd = f"- ~{facet_id}"
                        else:
                            continue
                        try:
                            # Send command to undo the facet
                            service.send_command(undo_cmd, no_Output=True)

                            # Remove facet_id from all impliedBy lists in timeline
                            for timestep in timeline:
                                # We collect implied blocks to remove (with empty impliedBy) in a separate list
                                blocks_to_remove = []
                                for implied_block in timestep.get("facets", []):
                                    if implied_block.get("type") == "implied":
                                        if facet_id in implied_block.get("impliedBy", []):
                                            implied_block["impliedBy"].remove(facet_id)

                                            # If impliedBy is now empty, mark this block for removal
                                            if not implied_block["impliedBy"]:
                                                blocks_to_remove.append(implied_block)

                                # Now actually remove the marked blocks
                                for block_to_remove in blocks_to_remove:
                                    timestep["facets"].remove(block_to_remove)

                        except Exception as e:
                            errors.append({
                                "undo-error": f"- {facet_id}",
                                "error": str(e),
                                "timestep": step["timestep"]
                            })

    return errors


def getAllImpliedAndActivatedIds(timeline):
    global_implied_ids = set()
    activated_plan_ids = set()

    for step in timeline:
        for facet_group in step.get("facets", []):
            facet_type = facet_group.get("type")
            for facet in facet_group.get("facets", []):
                facet_id = facet.get("id")
                if facet_id is None:
                    continue
                if facet_type == "implied":
                    global_implied_ids.add(facet_id)
                elif facet_type == "plan":
                    activated_plan_ids.add(facet_id)
                elif facet_type == "selected":
                    activated_plan_ids.add(facet_id)
    return global_implied_ids, activated_plan_ids

def prepare_timeline_for_update(service, changed_timestep):
    # Save current facets for every step from the change point onward
    saved_steps = []
    for t in range(changed_timestep, service.horizon + 1):
        step = service.timeline[t - 1]
        saved_steps.append({
            "timestep": t,
            "facets": step.get("facets", [])
        })

    # Clear timeline steps
    clear_all_but_implied_from_timestep(service.timeline, changed_timestep)
    global_implied_ids, activated_plan_ids = getAllImpliedAndActivatedIds(service.timeline)
    # Undo all existing facet activations
    errors = undo_facets(service, reversed(saved_steps), service.timeline)
    return saved_steps, global_implied_ids, activated_plan_ids, errors


def apply_user_command(service, t, command, global_implied_ids):
    # TODO: If is negative add and on the timestep then is a positive one implied -> add it there -> how to show exactly??
    errors = []
    stripped = command.strip()
    is_remove = stripped.startswith("-")
    is_negative_add = stripped.startswith("+ ~")
    is_positive_add = stripped.startswith("+") and not is_negative_add
    clean_cmd = stripped.lstrip("+-~ ").strip()

    if is_remove:
        # Check if there are other facets remaining at this timestep
        current_facets = service.timeline[t]["facets"]
        non_removed_facets_exist = any(
            f.get("facets") for f in current_facets if f.get("facets")
        )

        # TODO: Now does later not fetch anymore the empty ones, need to fix this

        # Only fetch optionals if the timestep still has other facets
        if non_removed_facets_exist:
            try:
                errors.extend(fetch_and_add_optional_facets(service, service.timeline, t))
            except Exception as e:
                errors.append({"command-error": command, "error": str(e)})
    else:
        errors.extend(fetch_and_add_optional_facets(service, service.timeline, t))
        try:
            service.send_command(command, no_Output=True)
            parsed_facets = parse_facet_output(clean_cmd, command)
            for facet in parsed_facets:
                if is_negative_add:
                    facet["selectionState"] = "-"
                elif is_positive_add:
                    facet["selectionState"] = "+"
            add_facet_to_timestep(service.timeline, t, "selected", parsed_facets)

            errors.extend(fetch_and_add_implied_facets(
                            service,
                            service.timeline,
                            global_implied_ids,
                            clean_cmd,
                            service.horizon
                        ))
        except Exception as e:
            errors.append({"command-error": command, "error": str(e)})
    return errors

def reactivate_facets_from_step(self, t, step_data, optional_ids, global_implied_ids):
    errors = []
    reactivated_any = False

    for block in step_data.get("facets", []):
        if block.get("type") in ("selected", "plan"):  # Consider including "implied" if needed
            for facet in block.get("facets", []):
                facet_id = facet.get("id")
                selection_state = facet.get("selectionState", "Not selected")
                if facet_id and facet_id in optional_ids and selection_state != "Not selected":
                    if selection_state == "+":
                        cmd = f"+ {facet_id}"
                    elif selection_state == "-":
                        cmd = f"+ ~{facet_id}"
                    else:
                        continue
                    try:
                        self.send_command(cmd, no_Output=True)
                        reactivated_any = True

                        add_facet_to_timestep(self.timeline, t, block.get("type"), [facet])

                        # TODO: Maybe need to update all implied ones? Does not do it correctly right now
                        errors.extend(fetch_and_add_implied_facets(
                            self,
                            self.timeline,
                            global_implied_ids,
                            facet_id,
                            self.horizon
                        ))
                    except Exception as e:
                        errors.append({"reactivate-error": f"{facet_id}", "error": str(e)})

    return errors, reactivated_any

