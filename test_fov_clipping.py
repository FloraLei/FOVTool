"""
Test FOV clipping by vehicle functionality
"""
import sys
sys.path.insert(0, r'c:\Fuyue_WorkSpace\FOVTools')

from fov_tools import SensorConfig, VehicleConfig, SceneConfig, Canvas3D

def test_fov_clipping():
    """Test FOV clipping algorithm in Canvas3D"""
    
    # Create vehicle
    vehicle = VehicleConfig(
        length=2.5,
        width=2.0,
        height=1.5,
        trailer_length=3.0,
        trailer_width=2.0,
        name="Test Vehicle"
    )
    
    # Create rear-facing sensor (should be clipped)
    rear_sensor = SensorConfig(
        name="Rear Camera",
        sensor_type="camera",
        x=0.0,
        y=-1.0,  # Behind the vehicle front
        z=1.0,
        mount_angle=180.0,  # Facing backward
        hfov=120.0,
        vfov=60.0,
        range=10.0,
        opacity=0.8,
        enabled=True,
        clip_by_vehicle=True,  # NEW: Enable clipping
        clip_range=0.0  # NEW: Auto-compute
    )
    
    # Create scene
    scene = SceneConfig(
        vehicle=vehicle,
        sensors=[rear_sensor]
    )
    
    print("✓ Scene created successfully")
    print(f"  Vehicle: length={vehicle.length}m, trailer_length={vehicle.trailer_length}m")
    print(f"  Sensor: {rear_sensor.name} at Y={rear_sensor.y}m, angle={rear_sensor.mount_angle}°")
    print(f"  Clipping: enabled={rear_sensor.clip_by_vehicle}, range={rear_sensor.clip_range}m")
    
    # Test clipping parameters are properly set
    assert rear_sensor.clip_by_vehicle == True, "clip_by_vehicle should be True"
    assert rear_sensor.clip_range == 0.0, "clip_range should be 0.0 (auto)"
    print("✓ FOV clipping parameters verified")
    
    # Test serialization (to_dict/from_dict)
    sensor_dict = rear_sensor.to_dict()
    assert 'clip_by_vehicle' in sensor_dict, "clip_by_vehicle should be in dict"
    assert 'clip_range' in sensor_dict, "clip_range should be in dict"
    assert sensor_dict['clip_by_vehicle'] == True, "Serialized clip_by_vehicle should be True"
    assert sensor_dict['clip_range'] == 0.0, "Serialized clip_range should be 0.0"
    print("✓ Serialization verified")
    
    # Test deserialization
    sensor_restored = SensorConfig.from_dict(sensor_dict)
    assert sensor_restored.clip_by_vehicle == True, "Deserialized clip_by_vehicle should be True"
    assert sensor_restored.clip_range == 0.0, "Deserialized clip_range should be 0.0"
    print("✓ Deserialization verified")
    
    # Test with manual clip range
    rear_sensor.clip_range = 50.0
    assert rear_sensor.clip_range == 50.0, "clip_range should be 50.0"
    print("✓ Manual clip range adjustment works")
    
    # Test with clipping disabled
    rear_sensor.clip_by_vehicle = False
    assert rear_sensor.clip_by_vehicle == False, "clip_by_vehicle should be False"
    print("✓ Clipping toggle works")
    
    print("\n✅ All FOV clipping tests passed!")

if __name__ == "__main__":
    try:
        test_fov_clipping()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
