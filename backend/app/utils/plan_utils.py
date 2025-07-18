def clear_timeline_from_timestep(timeline, start_timestep):
    for t in range(start_timestep - 1, len(timeline)):
        timeline[t]["facets"] = []

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


def fetch_and_add_implied_facets(service, timeline, global_implied_ids, activated_plan_ids, base_facet_id, horizon):
    errors = []
    try:
        implied = service.send_command("|= %")
        for f in implied:
            implied_id = f["id"]
            ts = f.get("timestep")

            if implied_id in global_implied_ids:
                # is this id already implied -> no need to add it twice
                continue
            if implied_id in activated_plan_ids:
                # is this a plan that was initially activated -> if yes this should not be implied so that the user
                # can change it
                continue
            if ts is None or not (1 <= ts <= horizon):
                # if the implied facet has no time step -> no need to add it
                # TODO: is this not an error case?
                continue
            if not (1 <= ts <= horizon):
                # ts needs to lie inside 1 and the horizon, so the valid planning range
                continue

            global_implied_ids.add(implied_id)
            timeline[ts - 1]["facets"].append({
                "type": "implied",
                "facets": [f],
                "causedBy": base_facet_id
            })
    except Exception as e:
        errors.append({"type": "implied-fetch", "error": str(e)})

    return errors

def undo_facets(service, step_data):
    errors = []
    for step in step_data:
        for block in step.get("facets", []):
            if block.get("type") in ("selected", "plan"):
                for facet in block.get("facets", []):
                    facet_id = facet.get("id")
                    if facet_id:
                        try:
                            service.send_command(f"- {facet_id}", no_Output=True)
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
