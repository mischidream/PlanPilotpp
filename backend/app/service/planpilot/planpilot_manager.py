import copy
import threading
from .planpilot_instance import PlanPilotInstance


class PlanPilotManager:
    def __init__(self):
        self.instances: dict[str, PlanPilotInstance] = {}

    def get_or_create(self, page_id: str) -> PlanPilotInstance:
        if page_id not in self.instances:
            self.instances[page_id] = PlanPilotInstance(page_id, manager=self)
        return self.instances[page_id]

    def start_background_refresh(self, main_instance: PlanPilotInstance):
        bg_id = "background"

        # Stop old background instance
        if bg_id in self.instances:
            self.instances[bg_id].stop()
            del self.instances[bg_id]

        # Create new instance using main instance parameters
        bg_instance = PlanPilotInstance(
            page_id=bg_id,
            manager=self,
            sas_file_path=main_instance.sas_file_path,
            horizon=main_instance.horizon,
            encoding=main_instance.encoding,
            hash_value=main_instance.hash_value,
            abstract_timestep=main_instance.abstract_timestep,
        )

        # Give it a copy of the timeline
        bg_instance.timeline = copy.deepcopy(main_instance.timeline)

        # Mark as in progress immediately
        bg_instance.refresh_in_progress = True

        # Save in manager
        self.instances[bg_id] = bg_instance

        # Start refresh thread
        def background_task():
            with bg_instance.refresh_lock:
                try:
                    bg_instance.start_background_refresh_process()
                    bg_instance.refresh_result = {
                        "timeline": bg_instance.timeline,
                        "errors": bg_instance.errors,
                        "facetCount": bg_instance.facet_count,
                    }
                finally:
                    bg_instance.refresh_in_progress = False

        threading.Thread(target=background_task, daemon=True).start()

    def switch_to_background(self, page_id: str) -> dict:
        bg_id = "background"

        # Get background instance
        bg_instance = self.instances.get(bg_id)
        if not bg_instance:
            raise RuntimeError("No background instance available")

        # Stop old main instance
        if page_id in self.instances:
            old_instance = self.instances[page_id]
            old_instance.stop()
            del self.instances[page_id]

        # Move background to main
        self.instances[page_id] = bg_instance
        del self.instances[bg_id]

        return {
            "timeline": bg_instance.timeline,
            "errors": getattr(bg_instance, "errors", None),
            "facetCount": getattr(bg_instance, "facet_count", None),
        }

    def stop(self, page_id: str):
        if page_id in self.instances:
            self.instances[page_id].stop()
            del self.instances[page_id]

    def stop_all(self):
        for instance in self.instances.values():
            instance.stop()
        self.instances.clear()
