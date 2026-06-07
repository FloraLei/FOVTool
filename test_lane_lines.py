#!/usr/bin/env python3
"""Test lane line functionality"""

import sys
from fov_tools import SceneConfig, LaneLineConfig

def test_lane_creation():
    """Test creating lane line configs"""
    # Create different types of lane lines
    straight_lane = LaneLineConfig(
        name="直线车道",
        line_type="straight",
        x_start=-1.0,
        y_start=-50.0,
        y_end=50.0,
        color="#FFFFFF"
    )
    
    curved_lane = LaneLineConfig(
        name="曲线车道",
        line_type="curved",
        x_start=0.0,
        y_start=-50.0,
        y_end=50.0,
        curvature=0.01,
        color="#FFFF00"
    )
    
    merge_in_lane = LaneLineConfig(
        name="汇入车道",
        line_type="merge_in",
        x_start=2.0,
        y_start=-50.0,
        y_end=50.0,
        curvature=0.5,
        color="#FF00FF"
    )
    
    merge_out_lane = LaneLineConfig(
        name="汇出车道",
        line_type="merge_out",
        x_start=-2.0,
        y_start=-50.0,
        y_end=50.0,
        curvature=0.5,
        color="#00FFFF"
    )
    
    print("✓ 直线车道线创建成功")
    print(f"  {straight_lane}")
    print("\n✓ 曲线车道线创建成功")
    print(f"  {curved_lane}")
    print("\n✓ 汇入车道线创建成功")
    print(f"  {merge_in_lane}")
    print("\n✓ 汇出车道线创建成功")
    print(f"  {merge_out_lane}")
    
    # Test serialization
    scene = SceneConfig()
    scene.lane_lines.append(straight_lane)
    scene.lane_lines.append(curved_lane)
    scene.lane_lines.append(merge_in_lane)
    scene.lane_lines.append(merge_out_lane)
    
    # Test to_dict and from_dict
    scene_dict = scene.to_dict()
    print(f"\n✓ 场景序列化成功，包含 {len(scene_dict['lane_lines'])} 条车道线")
    
    # Recreate from dict
    scene2 = SceneConfig.from_dict(scene_dict)
    print(f"✓ 场景反序列化成功，恢复 {len(scene2.lane_lines)} 条车道线")
    
    # Verify all lanes are preserved
    assert len(scene2.lane_lines) == 4, "Lane count mismatch"
    assert scene2.lane_lines[0].line_type == "straight", "Lane type mismatch"
    assert scene2.lane_lines[1].line_type == "curved", "Lane type mismatch"
    assert scene2.lane_lines[2].line_type == "merge_in", "Lane type mismatch"
    assert scene2.lane_lines[3].line_type == "merge_out", "Lane type mismatch"
    
    print("\n✓ 所有测试通过！")

if __name__ == "__main__":
    test_lane_creation()
