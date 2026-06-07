"""直接测试 export_diagram_hq 函数"""
import sys
sys.path.insert(0, r"c:\Fuyue_WorkSpace\FOVTools")

from fov_tools import (
    SensorConfig, VehicleConfig, SceneConfig,
    export_diagram_hq, HW30_SENSORS,
)

# 构建场景：有挂车
v = VehicleConfig(length=4.8, width=2.0, height=1.5,
                  trailer_length=3.0, trailer_width=2.0)

sensors = [SensorConfig.from_dict(d) for d in HW30_SENSORS]
cfg = SceneConfig(vehicle=v, sensors=sensors)

out = r"c:\Fuyue_WorkSpace\FOVTools\test_export_output.png"
print(f"Exporting to: {out}")
export_diagram_hq(cfg, out, width_px=4000, bg='white',
                  show_legend=True, title='Test Export')
print("Done!")
