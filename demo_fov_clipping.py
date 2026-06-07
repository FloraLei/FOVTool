"""
Demonstration of FOV clipping feature
Shows how to use the new clip_by_vehicle and clip_range parameters
"""
import sys
sys.path.insert(0, r'c:\Fuyue_WorkSpace\FOVTools')

from fov_tools import SensorConfig, VehicleConfig, SceneConfig

def demo_fov_clipping():
    """Demonstrate FOV clipping configuration"""
    
    print("=" * 70)
    print("FOV CLIPPING BY VEHICLE - FEATURE DEMONSTRATION")
    print("=" * 70)
    
    # Setup: Create a vehicle with trailer
    print("\n[1] CREATE VEHICLE WITH TRAILER")
    print("-" * 70)
    vehicle = VehicleConfig(
        length=2.5,           # 2.5m vehicle body
        width=2.0,
        height=1.5,
        trailer_length=3.0,   # 3.0m trailer
        trailer_width=2.0,
        name="Truck + Trailer"
    )
    print(f"✓ Vehicle created:")
    print(f"  - Body length: {vehicle.length}m")
    print(f"  - Trailer length: {vehicle.trailer_length}m")
    print(f"  - Total extent: {vehicle.total_length}m backward")
    
    # Demo 1: Automatic clipping (default)
    print("\n[2] DEMO: AUTOMATIC CLIPPING (DEFAULT)")
    print("-" * 70)
    rear_cam_auto = SensorConfig(
        id="rear_auto",
        name="Rear Camera (Auto)",
        sensor_type="camera",
        x=0.0, y=-1.0, z=1.0,
        mount_angle=180.0,  # Facing backward
        hfov=120.0, vfov=60.0, range=10.0,
        opacity=0.8,
        enabled=True,
        clip_by_vehicle=True,   # ← Enable clipping
        clip_range=0.0          # ← Auto-compute (0 = automatic)
    )
    print(f"✓ Sensor configured:")
    print(f"  - Name: {rear_cam_auto.name}")
    print(f"  - Position: Y={rear_cam_auto.y}m (behind vehicle front)")
    print(f"  - Mount angle: {rear_cam_auto.mount_angle}°")
    print(f"  - Clipping: ENABLED (auto-compute)")
    print(f"  - Clip plane will be at: Y={-vehicle.total_length}m")
    print(f"  - Result: FOV cut by vehicle/trailer body")
    
    # Demo 2: Manual clipping with custom distance
    print("\n[3] DEMO: MANUAL CLIPPING WITH CUSTOM DISTANCE")
    print("-" * 70)
    rear_cam_manual = SensorConfig(
        id="rear_manual",
        name="Rear Camera (Manual 50m)",
        sensor_type="camera",
        x=0.0, y=-1.0, z=1.0,
        mount_angle=180.0,
        hfov=120.0, vfov=60.0, range=10.0,
        opacity=0.8,
        enabled=True,
        clip_by_vehicle=True,   # ← Enable clipping
        clip_range=50.0         # ← Manual: cut at 50m distance
    )
    print(f"✓ Sensor configured:")
    print(f"  - Name: {rear_cam_manual.name}")
    print(f"  - Mount angle: {rear_cam_manual.mount_angle}°")
    print(f"  - Clipping: ENABLED (manual)")
    print(f"  - Clip plane will be at: Y={-rear_cam_manual.clip_range}m")
    print(f"  - Result: FOV cut at exactly 50m distance")
    
    # Demo 3: Clipping disabled (full FOV)
    print("\n[4] DEMO: CLIPPING DISABLED (FULL FOV)")
    print("-" * 70)
    rear_cam_full = SensorConfig(
        id="rear_full",
        name="Rear Camera (Full FOV)",
        sensor_type="camera",
        x=0.0, y=-1.0, z=1.0,
        mount_angle=180.0,
        hfov=120.0, vfov=60.0, range=10.0,
        opacity=0.8,
        enabled=True,
        clip_by_vehicle=False,  # ← Disable clipping
        clip_range=0.0
    )
    print(f"✓ Sensor configured:")
    print(f"  - Name: {rear_cam_full.name}")
    print(f"  - Clipping: DISABLED")
    print(f"  - Result: Full FOV pyramid visible (no occlusion)")
    
    # Demo 4: Side-facing sensor with clipping
    print("\n[5] DEMO: SIDE-FACING SENSOR WITH CLIPPING")
    print("-" * 70)
    side_cam = SensorConfig(
        id="side",
        name="Side Camera (Right)",
        sensor_type="camera",
        x=1.0, y=0.0, z=1.5,
        mount_angle=90.0,  # Facing right (lateral)
        hfov=100.0, vfov=80.0, range=15.0,
        opacity=0.7,
        enabled=True,
        clip_by_vehicle=True,   # Also works for side sensors
        clip_range=0.0
    )
    print(f"✓ Sensor configured:")
    print(f"  - Name: {side_cam.name}")
    print(f"  - Mount angle: {side_cam.mount_angle}° (lateral)")
    print(f"  - Clipping: ENABLED (auto)")
    print(f"  - Result: FOV clipped at vehicle edge")
    
    # Serialization test
    print("\n[6] SERIALIZATION & PERSISTENCE")
    print("-" * 70)
    
    # Save to dict
    sensor_dict = rear_cam_auto.to_dict()
    print(f"✓ Serialized sensor parameters:")
    print(f"  - clip_by_vehicle: {sensor_dict.get('clip_by_vehicle')}")
    print(f"  - clip_range: {sensor_dict.get('clip_range')} m")
    
    # Restore from dict
    restored = SensorConfig.from_dict(sensor_dict)
    print(f"✓ Restored from dict:")
    print(f"  - clip_by_vehicle: {restored.clip_by_vehicle}")
    print(f"  - clip_range: {restored.clip_range} m")
    print(f"  - Verification: {'✅ PASS' if restored.clip_by_vehicle == rear_cam_auto.clip_by_vehicle else '❌ FAIL'}")
    
    # UI Control Summary
    print("\n[7] UI CONTROL MAPPING IN SENSOR PROPERTIES PANEL")
    print("-" * 70)
    print("Right panel shows two new controls:")
    print("")
    print("  ┌─────────────────────────────────────────────┐")
    print("  │ ✓ 被车体遮挡时切割FOV                        │")
    print("  │   (Enable FOV clipping when vehicle occludes)│")
    print("  │                                             │")
    print("  │ 手动切割距离: [   0    ] m                   │")
    print("  │ (Manual cut distance: 0=auto, >0=manual)    │")
    print("  └─────────────────────────────────────────────┘")
    print("")
    print("When you change these values:")
    print("  - Canvas3D re-renders immediately")
    print("  - Settings persist in JSON config file")
    print("  - Each sensor can have independent settings")
    
    # Technical summary
    print("\n[8] TECHNICAL SUMMARY")
    print("-" * 70)
    print("Algorithm: Plane-based clipping")
    print("  Input:  FOV cone (24×6 faces from ray-casting)")
    print("  Method: Filter faces where Y > clip_plane_Y")
    print("  Output: Clipped face list for 3D rendering")
    print("")
    print("Performance: O(n_faces) per frame")
    print("  - ~160 faces per sensor (24 azimuth × 6 elevation + fans)")
    print("  - Filter operation is fast (simple Y comparison)")
    print("  - GPU rendering via Poly3DCollection (matplotlib)")
    print("")
    print("Data Flow:")
    print("  SensorConfig (clip_by_vehicle, clip_range)")
    print("      ↓")
    print("  Canvas3D._redraw_impl() calls _clip_fov_by_vehicle()")
    print("      ↓")
    print("  Matplotlib Poly3DCollection renders clipped faces")
    
    print("\n" + "=" * 70)
    print("✅ FEATURE DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Run the application: python fov_tools.py")
    print("2. Load or create a vehicle with sensors")
    print("3. Select a rear-facing sensor in the sensor list")
    print("4. In the right properties panel, adjust:")
    print("   - ✓ 被车体遮挡时切割FOV (checkbox)")
    print("   - 手动切割距离 (spinbox: 0-200m)")
    print("5. Switch to 3D view and observe the FOV changes")

if __name__ == "__main__":
    demo_fov_clipping()
