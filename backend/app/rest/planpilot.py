from flask import Blueprint, request, jsonify
from ..service.planpilot.planpilot_manager import PlanPilotManager

planpilot_bp = Blueprint("planpilot", __name__)
planpilot_manager = PlanPilotManager()


@planpilot_bp.route("/run-planpilot", methods=["POST"])
def run_planpilot():
    data = request.json
    page_id = data.get("pageId")
    sas_file = data.get("sasFile")
    horizon = data.get("horizon")
    encoding = data.get("encoding")
    abstract_time_steps = data.get("abstractTimeStep")

    if not page_id or not sas_file or not horizon or not encoding:
        return jsonify({"error": "pageId, sasFile, horizon, and encoding are required"}), 400

    try:
        # Get or create instance
        instance = planpilot_manager.get_or_create(page_id)
        # Start PlanPilot instance
        output = instance.start(sas_file, horizon, encoding, abstract_time_steps)
        return jsonify({"output": output}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@planpilot_bp.route("/activate-plan", methods=["POST"])
def activate_plan():
    data = request.json
    page_id = data.get("pageId")
    plan_file = data.get("planFile")

    if not page_id or not plan_file:
        return jsonify({"error": "pageId and planFile are required"}), 400

    try:
        instance = planpilot_manager.get_or_create(page_id)
        result = instance.activate_best_plan(plan_file)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@planpilot_bp.route("/update-plan", methods=["POST"])
def update_plan():
    data = request.json
    page_id = data.get("pageId")
    changed_timestep = data.get("changedTimestep")
    commands = data.get("commands")

    if not page_id or changed_timestep is None or commands is None:
        return jsonify({"error": "pageId, changedTimestep, and commands are required"}), 400

    try:
        instance = planpilot_manager.get_or_create(page_id)
        result = instance.update_plan_from_timestep(changed_timestep, commands)
        # Trigger background refresh
        planpilot_manager.start_background_refresh(instance)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@planpilot_bp.route("/refresh-timeline", methods=["GET"])
def refresh_timeline():
    page_id = request.args.get("pageId")
    if not page_id:
        return jsonify({"error": "Missing 'pageId' parameter"}), 400

    try:
        result = planpilot_manager.switch_to_background(page_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@planpilot_bp.route("/check-refresh-status", methods=["GET"])
def check_refresh_status():
    try:
        bg_instance = planpilot_manager.instances.get("background")
        if not bg_instance:
            return jsonify({"status": "none"}), 404

        with bg_instance.refresh_lock:
            if bg_instance.refresh_in_progress:
                return jsonify({"status": "in_progress"}), 202
            else:
                return jsonify({"status": "done"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@planpilot_bp.route("/refresh-optional-facet", methods=["GET"])
def refresh_optional_facet():
    page_id = request.args.get("pageId")
    timestep_param = request.args.get("timestep")

    if not page_id or timestep_param is None:
        return jsonify({"error": "pageId and timestep are required"}), 400

    try:
        try:
            timestep_number = int(timestep_param)
        except ValueError:
            return jsonify({"error": "'timestep' must be an integer"}), 400

        instance = planpilot_manager.get_or_create(page_id)
        refreshed_answer = instance.refresh_timestep_optional_facet(timestep_number)

        if not refreshed_answer:
            return jsonify({"error": "No optional facet found for this timestep"}), 404

        return jsonify(refreshed_answer), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@planpilot_bp.route("/send-planpilot-command", methods=["POST"])
def send_command():
    data = request.json
    page_id = data.get("pageId")
    command = data.get("command")

    if not page_id or not command:
        return jsonify({"error": "pageId and command are required"}), 400

    try:
        instance = planpilot_manager.get_or_create(page_id)
        output = instance.send_command(command)
        return jsonify({"output": output}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@planpilot_bp.route("/stop-planpilot", methods=["POST"])
def stop_planpilot():
    page_id = request.json.get("pageId")
    if not page_id:
        return jsonify({"error": "pageId is required"}), 400

    try:
        planpilot_manager.stop(page_id)
        return jsonify({"status": f"PlanPilot instance '{page_id}' stopped"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
