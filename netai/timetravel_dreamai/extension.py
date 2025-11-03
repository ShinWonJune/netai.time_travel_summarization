# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary

import omni.ext
import omni.ui as ui
import omni.usd
from pxr import Usd, UsdGeom, Gf
import carb
import os
from pathlib import Path
from .window import TimeTravelWindow
from .core import TimeTravelCore

# Optional imports for overlay (with error handling)
try:
    from .view_overlay import TimeTravelViewportOverlay
    from .overlay_window import OverlayControlWindow
    OVERLAY_AVAILABLE = True
except Exception as e:
    carb.log_warn(f"[TimeTravel] Overlay components not available: {e}")
    OVERLAY_AVAILABLE = False


class NetAITimetravelDreamAI(omni.ext.IExt):
    """Time Travel Extension for visualizing object movements over time."""
    
    def on_startup(self, ext_id):
        """Initialize the extension."""
        print("[netai.timetravel_dreamai] Extension startup")
        
        # Print current working directory and extension path
        current_dir = os.getcwd()
        extension_file = Path(__file__).absolute()
        extension_dir = extension_file.parent
        
        # Initialize core logic
        self._core = TimeTravelCore() 
        
        # Load configuration
        config_path = extension_dir / "config.json"
        
        if self._core.load_config(str(config_path)):
            # Auto-generate astronauts if enabled
            if self._core._config.get('auto_generate', False):
                self._core._prim_map = self._core.auto_generate_astronauts()
            
            # Auto-generate astronauts if enabled
            if self._core._config.get('auto_generate', False):
                self._core._prim_map = self._core.auto_generate_astronauts()
            
            # Load data
            self._core.load_data()
        
        # Create main TimeTravel UI window (ALWAYS created)
        self._window = TimeTravelWindow(self._core)
        carb.log_info("[Extension] TimeTravel window created")
        
        # Try to create overlay components (OPTIONAL - won't break if it fails)
        self._overlay = None
        self._overlay_window = None
        
        if OVERLAY_AVAILABLE:
            try:
                # Create viewport overlay (VLM-friendly visualization)
                self._overlay = TimeTravelViewportOverlay(self._core)
                carb.log_info("[Extension] Viewport overlay created")
                
                # Create overlay control window
                self._overlay_window = OverlayControlWindow(self._overlay)
                carb.log_info("[Extension] Overlay Control window created")
            except Exception as e:
                carb.log_error(f"[Extension] Failed to create overlay components: {e}")
                carb.log_warn("[Extension] TimeTravel will continue without overlay features")
                self._overlay = None
                self._overlay_window = None
                self._overlay_window = None
        else:
            carb.log_info("[Extension] Overlay features disabled")
        
        # Start update loop (Events 2.0)
        import omni.kit.app
        self._update_sub = (
            omni.kit.app.get_app_interface()
            .get_update_event_stream()
            .create_subscription_to_pop(self._on_update)
        )
        
        # Set initial time to earliest timestamp
        if self._core.has_data():
            self._core.set_to_earliest_time()
    
    def _on_update(self, e):
        """Update loop for playback and UI updates."""
        dt = e.payload.get("dt", 0)
        
        # Update core logic (handles playback) - ALWAYS runs
        self._core.update(dt)
        
        # Update main TimeTravel UI - ALWAYS runs
        if self._window:
            self._window.update_ui()
        
        # Update overlay UI - OPTIONAL (only if available and created successfully)
        if self._overlay_window:
            try:
                self._overlay_window.update_ui()
            except Exception as e:
                carb.log_error(f"[Extension] Overlay window update error: {e}")
        
        # Update viewport overlay - OPTIONAL (only if available and created successfully)
        if self._overlay:
            try:
                self._overlay.update()
            except Exception as e:
                carb.log_error(f"[Extension] Viewport overlay update error: {e}")
    
    def on_shutdown(self):
        """Clean up the extension."""
        print("[netai.timetravel_dreamai] Extension shutdown")
        
        # Clean up subscription
        if hasattr(self, '_update_sub'):
            self._update_sub = None
        
        # Clean up main TimeTravel window (ALWAYS cleanup)
        if hasattr(self, '_window') and self._window:
            try:
                self._window.destroy()
            except Exception as e:
                carb.log_error(f"[Extension] Error destroying window: {e}")
            self._window = None
        
        # Clean up overlay window (OPTIONAL)
        if hasattr(self, '_overlay_window') and self._overlay_window:
            try:
                self._overlay_window.destroy()
            except Exception as e:
                carb.log_error(f"[Extension] Error destroying overlay window: {e}")
            self._overlay_window = None
        
        # Clean up overlay (OPTIONAL)
        if hasattr(self, '_overlay') and self._overlay:
            try:
                self._overlay.destroy()
            except Exception as e:
                carb.log_error(f"[Extension] Error destroying overlay: {e}")
            self._overlay = None
        
        # Clean up core
        if hasattr(self, '_core'):
            self._core = None
            self._core = None