def clear_timeline_from_timestep(timeline, start_timestep):
    for t in range(start_timestep, len(timeline)):
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

def fetch_and_add_empty_facets(service, timeline, timestep):
    try:
        all_open = service.send_command("?")
        open_facets = [f for f in all_open if f.get("timestep") == timestep]
        if open_facets:
            add_facet_to_timestep(timeline, timestep, "empty", open_facets)
        return []
    except Exception as e:
        return [{"type": "open-fetch", "timestep": timestep, "error": str(e)}]

def fetch_and_add_implied_facets(service, timeline, global_implied_ids, activated_plan_ids, base_facet_id, horizon):
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
        return None  # no error
    except Exception as e:
        return {"type": "implied-fetch", "error": str(e)}

def fetch_and_insert_future_implied_facets(service, timeline, start_timestep, horizon, caused_by_command):
    try:
        implied_facets = service.send_command("|= %")
        for implied in implied_facets:
            implied_timestep = implied.get("timestep")
            if implied_timestep and start_timestep < implied_timestep <= horizon:
                implied_step = timeline[implied_timestep - 1]
                if any(f.get("type") in ("selected", "implied") for f in implied_step["facets"]):
                    continue
                implied_step["facets"].append({
                    "type": "implied",
                    "facets": [implied],
                    "causedBy": caused_by_command
                })
        return None
    except Exception as e:
        return {"type": "implied-fetch", "error": str(e)}
