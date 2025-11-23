# =============================================================================
# sample_analytics_logic.py
#
# This file provides a sanitized, conceptual sample of the core analytics logic
# for object tracking and event counting.
# It omits actual ML model calls to focus purely on the implemented logic.
# =============================================================================
import time

class DBMock:
    """A mock object simulating the database connection."""
    def log_event(self, source_id, direction):
        print(f"[DB LOG] Source {source_id}: Logged event, direction: {direction}")

class StreamAnalytics:
    """Manages the analytics for a single video stream."""
    def __init__(self, source_id, line_coordinates, db_connection):
        self.source_id = source_id
        self.line = line_coordinates
        self.db = db_connection
        # State-tracking dictionaries are crucial for accurate counting
        self.tracked_objects = {}  # Stores last position: { 'id': (x, y) }
        self.cooldown_manager = {} # Prevents re-counting: { 'id': timestamp }
        self.cooldown_period_seconds = 3.0

    def is_crossing_line(self, prev_pos, current_pos):
        """A placeholder for the geometric calculation to check for a line cross."""
        line_x = self.line[0] # Assuming a vertical line for simplicity
        if prev_pos[0] < line_x and current_pos[0] >= line_x:
            return "forward"
        if prev_pos[0] > line_x and current_pos[0] <= line_x:
            return "backward"
        return None

    def process_frame_detections(self, detected_objects):
        """
        This is the core method called for every new set of detections from a frame.
        'detected_objects' would be a list like: [{'id': 101, 'position': (x, y)}]
        """
        current_object_ids = {obj['id'] for obj in detected_objects}

        for obj in detected_objects:
            obj_id = obj['id']
            current_pos = obj['position']

            if obj_id in self.tracked_objects:
                # Check if the object is in a cooldown period
                if obj_id in self.cooldown_manager:
                    if time.time() - self.cooldown_manager[obj_id] > self.cooldown_period_seconds:
                        self.cooldown_manager.pop(obj_id) # Cooldown expired
                    else:
                        continue # Still in cooldown, skip

                # Apply the line-crossing logic
                direction = self.is_crossing_line(self.tracked_objects[obj_id], current_pos)
                if direction:
                    print(f"[ANALYTICS] Source {self.source_id}: Object {obj_id} crossed the line! Direction: {direction}")
                    # Log the event and place the object in cooldown
                    self.db.log_event(self.source_id, direction)
                    self.cooldown_manager[obj_id] = time.time()

            # Update the object's last known position for the next frame
            self.tracked_objects[obj_id] = current_pos

        # Clean up state for objects that have disappeared from the frame
        disappeared_ids = set(self.tracked_objects.keys()) - current_object_ids
        for obj_id in disappeared_ids:
            self.tracked_objects.pop(obj_id)
            self.cooldown_manager.pop(obj_id, None)

# Example Usage (how this class would be used in a processing thread)
db_connection = DBMock()
analytics_processor = StreamAnalytics(source_id=1, line_coordinates=(150,0,150,480), db_connection=db_connection)

# Simulate detections from the model for Frame 1
detections_frame_1 = [{'id': 101, 'position': (140, 200)}]
analytics_processor.process_frame_detections(detections_frame_1)

# Simulate detections from the model for Frame 2 (object crossed the line)
detections_frame_2 = [{'id': 101, 'position': (160, 205)}]
analytics_processor.process_frame_detections(detections_frame_2)