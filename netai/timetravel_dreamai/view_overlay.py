# view_overlay.py - Viewport overlay for displaying object ID labels above prims

import omni.ui as ui
import omni.ui.scene as sc
import omni.usd
import omni.kit.app
import carb
from pxr import UsdGeom, Gf
from omni.kit.viewport.utility import get_active_viewport_window


# -----------------------------------------------------------------
#  1. View (Manipulator) Class - Simplified
# -----------------------------------------------------------------
class ObjectIDManipulator(sc.Manipulator):
    """
    Displays an object ID label at the prim's 3D position.
    Directly reads prim position without using a model.
    """
    def __init__(self, prim_path: str, label_text: str, **kwargs):
        super().__init__(**kwargs)
        self._prim_path = prim_path
        self._label_text = label_text
        self._stage = omni.usd.get_context().get_stage()
        self._prim = self._stage.GetPrimAtPath(self._prim_path)
        self._xformable = UsdGeom.Xformable(self._prim)
        self._label = None
        self._transform = None
        self._last_position = None

    def on_build(self):
        """Build the label UI at prim's current position."""
        if not self._prim or not self._prim.IsValid():
            return

        # Get world position
        xform_cache = UsdGeom.XformCache()
        world_transform = xform_cache.GetLocalToWorldTransform(self._prim)
        translation = world_transform.ExtractTranslation()
        
        # Store transform for updates
        self._transform = sc.Transform(transform=sc.Matrix44.get_translation_matrix(
            translation[0], translation[1] + 100, translation[2]
        ))
        
        # Create label at world position (offset 100 units above)
        with self._transform:
            # Draw label text
            self._label = sc.Label(
                self._label_text,
                color=0xFF000000,  # Black text
                size=24
            )
        
        # Store position for comparison
        self._last_position = (translation[0], translation[1], translation[2])
    
    def update_position(self):
        """Update label position only if prim has moved."""
        if not self._prim or not self._prim.IsValid() or not self._transform:
            return
        
        # Get current world position
        xform_cache = UsdGeom.XformCache()
        world_transform = xform_cache.GetLocalToWorldTransform(self._prim)
        translation = world_transform.ExtractTranslation()
        
        current_position = (translation[0], translation[1], translation[2])
        
        # Only update if position has changed
        if self._last_position != current_position:
            # Update transform matrix
            self._transform.transform = sc.Matrix44.get_translation_matrix(
                translation[0], translation[1] + 100, translation[2]
            )
            self._last_position = current_position

    def on_model_updated(self, item):
        """Called when model changes (not used in this simplified version)."""
        pass

# -----------------------------------------------------------------
#  2. Manager Class (Model removed - not needed)
# -----------------------------------------------------------------
class ViewOverlay:
    """
    Manages viewport overlay, creating and updating
    3D labels and 2D time display.
    """
    def __init__(self, viewport_window, ext_id, core):
        self._viewport_window = viewport_window
        self._ext_id = ext_id
        self._core = core  # TimeTravelCore for time data
        self._usd_context = omni.usd.get_context()
        self._scene_view = None
        self._manipulators = []
        self._stage_event_sub = None
        self._update_sub = None
        self._visible = True
        self._labels_visible = True  # 3D labels visibility
        self._time_visible = True    # Time display visibility
        
        # Time display UI elements
        self._time_frame = None
        self._date_label = None
        self._time_label = None

        # Subscribe to stage events
        self._stage_event_sub = self._usd_context.get_stage_event_stream().create_subscription_to_pop(
            self._on_stage_event, name="ViewOverlayStageEvent"
        )
        
        carb.log_info("[ViewOverlay] Initialized")
        
        # Create time display
        self._create_time_overlay()
        
        # If stage is already open, build UI immediately
        stage = self._usd_context.get_stage()
        if stage:
            carb.log_info("[ViewOverlay] Stage already open, building UI now...")
            self._build_scene_for_stage()
        else:
            carb.log_info("[ViewOverlay] No stage yet, waiting for OPENED event...")
    
    def _create_time_overlay(self):
        """Create time display overlay in bottom-right corner."""
        viewport_window = get_active_viewport_window()
        
        if not viewport_window:
            carb.log_warn("[ViewOverlay] No active viewport for time overlay")
            return
        
        try:
            with viewport_window.get_frame("timetravel_time_overlay"):
                self._time_frame = ui.Frame(separate_window=False)
                
                with self._time_frame:
                    # Bottom-right corner positioning
                    with ui.HStack():
                        ui.Spacer()
                        with ui.VStack(width=220):
                            ui.Spacer()
                            # Time display box
                            with ui.ZStack(width=200, height=80):
                                # Background rectangle
                                ui.Rectangle(
                                    style={
                                        "background_color": 0xFF1A1A1A,
                                        "border_color": 0xFF00FF00,
                                        "border_width": 2,
                                        "border_radius": 5
                                    }
                                )
                                
                                # Date and Time text
                                with ui.VStack(spacing=3):
                                    ui.Spacer(height=10)
                                    # Date label
                                    with ui.HStack():
                                        ui.Spacer(width=50)
                                        self._date_label = ui.Label(
                                            "2025-01-01",
                                            style={
                                                "font_size": 24,
                                                "color": 0xFFCCCCCC,
                                                "font_weight": "normal"
                                            }
                                        )
                                        ui.Spacer()
                                    # Time label
                                    with ui.HStack():
                                        ui.Spacer(width=50)
                                        self._time_label = ui.Label(
                                            "00:00:00",
                                            style={
                                                "font_size": 28,
                                                "color": 0xFFFFFFFF,
                                                "font_weight": "bold"
                                            }
                                        )
                                        ui.Spacer()
                                    ui.Spacer(height=10)
                            ui.Spacer(height=10)
                
                self._time_frame.visible = self._visible
                carb.log_info("[ViewOverlay] Time display created")
        except Exception as e:
            carb.log_error(f"[ViewOverlay] Failed to create time display: {e}")
            import traceback
            carb.log_error(traceback.format_exc())
    
    def set_visible(self, visible: bool):
        """Show or hide all labels and time display."""
        self._visible = visible
        self._labels_visible = visible
        self._time_visible = visible
        
        # Control 3D labels
        if self._scene_view:
            self._scene_view.visible = visible
        
        # Control time display
        if self._time_frame:
            self._time_frame.visible = visible
            
        carb.log_info(f"[ViewOverlay] All visibility set to: {visible}")
    
    def set_labels_visible(self, visible: bool):
        """Show or hide 3D object ID labels only."""
        self._labels_visible = visible
        if self._scene_view:
            self._scene_view.visible = visible
        carb.log_info(f"[ViewOverlay] Labels visibility set to: {visible}")
    
    def set_time_visible(self, visible: bool):
        """Show or hide time display only."""
        self._time_visible = visible
        if self._time_frame:
            self._time_frame.visible = visible
        carb.log_info(f"[ViewOverlay] Time visibility set to: {visible}")
    
    def is_visible(self) -> bool:
        """Get current visibility state."""
        return self._visible

    def shutdown(self):
        """Clean up all resources."""
        carb.log_info("[ViewOverlay] Shutting down...")
        
        self._stage_event_sub = None
        self._update_sub = None
        
        # Clean up 3D scene view
        if self._scene_view:
            self._viewport_window.viewport_api.remove_scene_view(self._scene_view)
        
        self._scene_view = None
        self._manipulators = []
        
        # Clean up time display
        if self._time_frame:
            self._time_frame.clear()
            self._time_frame = None
        
        self._date_label = None
        self._time_label = None
        
        carb.log_info("[ViewOverlay] Cleanup complete")

    def _on_stage_event(self, event):
        """Handle stage open/close events."""
        if event.type == int(omni.usd.StageEventType.OPENED):
            carb.log_info("[ViewOverlay] Stage opened. Building UI...")
            self._build_scene_for_stage()
        elif event.type == int(omni.usd.StageEventType.CLOSED):
            carb.log_info("[ViewOverlay] Stage closed. Cleaning up UI...")
            self._cleanup_scene()

    def _get_id_from_name(self, prim_name: str) -> str:
        """
        Extract ID from prim name's last 3 digits.
        Example: 'Astronaut001' -> '1'
        """
        if len(prim_name) < 3:
            return None
        
        last_three = prim_name[-3:]
        if not last_three.isdigit():
            return None
        
        # Convert to int to remove leading zeros, then back to string
        return str(int(last_three))

    def _cleanup_scene(self):
        """Clean up UI when stage is closed."""
        # Stop update subscription
        self._update_sub = None
        
        # Clear manipulators
        self._manipulators = []
        
        # Remove and clear scene view
        if self._scene_view:
            self._viewport_window.viewport_api.remove_scene_view(self._scene_view)
            self._scene_view = None
        
        carb.log_info("[ViewOverlay] Scene view cleaned up")

    def _build_scene_for_stage(self):
        """
        Build all Models and Manipulators when stage is ready.
        Creates labels for all prims under /World/TimeTravel_Objects.
        """
        if self._scene_view:
            carb.log_info("[ViewOverlay] Scene view already exists. Cleaning up...")
            self._cleanup_scene()

        stage = self._usd_context.get_stage()
        if not stage:
            carb.log_error("[ViewOverlay] Cannot get stage")
            return

        parent_prim_path = "/World/TimeTravel_Objects"
        parent_prim = stage.GetPrimAtPath(parent_prim_path)
        
        if not parent_prim.IsValid():
            carb.log_warn(f"[ViewOverlay] '{parent_prim_path}' prim not found")
            return

        # Create scene view
        with self._viewport_window.get_frame(self._ext_id):
            self._scene_view = sc.SceneView()
            
            with self._scene_view.scene:
                # Create manipulator for each child prim
                for prim in parent_prim.GetChildren():
                    prim_name = prim.GetName()
                    label_id = self._get_id_from_name(prim_name)

                    if not label_id:
                        carb.log_info(f"[ViewOverlay] Cannot extract ID from '{prim_name}', skipping")
                        continue

                    prim_path = str(prim.GetPath())
                    
                    carb.log_info(f"[ViewOverlay] Tracking '{prim_path}' (ID: {label_id})")
                    
                    # Create manipulator (reads prim position directly)
                    manipulator = ObjectIDManipulator(prim_path=prim_path, label_text=label_id)
                    self._manipulators.append(manipulator)

            # Add scene view to viewport
            self._viewport_window.viewport_api.add_scene_view(self._scene_view)

        # Subscribe to frame updates
        if not self._update_sub:
            self._update_sub = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(
                self._on_update, name="ViewOverlayFrameUpdate"
            )

    def _on_update(self, e):
        """Called every frame to update all manipulators and time display."""
        # Update 3D label positions (only if visible and changed - no flicker)
        if self._labels_visible and self._manipulators:
            for manipulator in self._manipulators:
                manipulator.update_position()
        
        # Update time display
        if self._time_visible and self._time_label and self._date_label:
            try:
                current_time = self._core.get_current_time()
                date_str = current_time.strftime("%Y-%m-%d")
                time_str = current_time.strftime("%H:%M:%S")
                self._date_label.text = date_str
                self._time_label.text = time_str
            except Exception as e:
                carb.log_error(f"[ViewOverlay] Error updating time: {e}")
