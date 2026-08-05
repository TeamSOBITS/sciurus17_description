# Flexible Base Configuration for Sciurus17

## Overview

The Sciurus17 URDF supports two base configurations, selected with the
`use_kachaka_base` argument:

- **fixed base** (default) — the upper body is bolted to a static `world` frame.
- **Kachaka base** — the upper body is carried by a Kachaka mobile platform,
  turning the robot into a mobile manipulator.

The default configuration has no dependency on the Kachaka packages.

## Frame naming

The manipulator base frame is `body_base_link`.

This matters when the Kachaka base is enabled, because the Kachaka platform
brings its own link called `base_link`. The two are different frames:

| Frame | Meaning |
| --- | --- |
| `body_base_link` | Root of the Sciurus17 upper body (arms, neck, cameras) |
| `base_link` | Kachaka mobile platform body (only present with the Kachaka base) |

Always express manipulator goal poses in `body_base_link`.

## Configuration

### Fixed base (default)

No arguments needed.

```bash
ros2 launch sciurus17_description display.launch.py
ros2 launch sciurus17_gazebo sciurus17_with_table.launch.py
```

### With the Kachaka base

Pass `use_kachaka_base:=true`. The argument has to be given to the top-level
launch file, which forwards it to the description, MoveIt and the controllers.

```bash
# RViz display
ros2 launch sciurus17_description display.launch.py use_kachaka_base:=true

# Gazebo
ros2 launch sciurus17_gazebo sciurus17_with_table.launch.py use_kachaka_base:=true

# Real hardware
ros2 launch sciurus17_examples demo.launch.py use_kachaka_base:=true
```

## Kinematic structure

### Fixed base (`use_kachaka_base:=false`)

```
world
  └─ body_base_link
      ├─ body_link
      │   ├─ neck_yaw_link
      │   ├─ l_link1 (left arm)
      │   └─ r_link1 (right arm)
      └─ ...
```

`world -> body_base_link` is a fixed joint declared in the URDF, so
`robot_state_publisher` publishes it.

### Kachaka base (`use_kachaka_base:=true`)

```
odom
  └─ base_footprint
      └─ base_link (Kachaka platform)
          ├─ base_l_drive_wheel_link
          ├─ base_r_drive_wheel_link
          ├─ laser_frame, imu_link, tof_link, docking_link, camera_*_link
          └─ kachaka_base_link
              └─ sciurus17_vehicle_body_lower_front_link
                  ├─ sciurus17_vehicle_body_lower_back_link
                  └─ sciurus17_vehicle_body_upper_link
                      └─ body_base_link
                          ├─ body_link
                          │   ├─ neck_yaw_link
                          │   ├─ l_link1 (left arm)
                          │   └─ r_link1 (right arm)
                          └─ ...
```

There is no `world` link in this mode. `odom -> base_footprint` is published by
`wheel_controller` (a `diff_drive_controller`) from wheel odometry.

## Technical implementation

### Modified files

- `urdf/sciurus17.urdf.xacro` — argument, conditional includes and base structure
- `urdf/sciurus17.gazebo_ros2_control.xacro` — wheel joint interfaces
- `urdf/sciurus17_gazebo.xacro` — wheel friction and contact parameters
- `urdf/sciurus17_left_gripper.xacro`, `urdf/sciurus17_right_gripper.xacro` —
  mimic-fix dummy links reparented from `world` to `body_base_link`, since
  `world` does not exist with the Kachaka base
- `sciurus17_description/robot_description_loader.py` — passes the argument to xacro

### Conditional includes

The Kachaka xacro files are included inside `<xacro:if value="$(arg use_kachaka_base)">`,
so the default configuration parses without the Kachaka packages installed.

### Virtual joint

MoveIt needs the robot root anchored to a world-fixed frame, and the two modes
need different anchors. `sciurus17_moveit_config/config/sciurus17.srdf.xacro`
selects between them on the same argument:

- fixed base — `fixed` joint, `world -> body_base_link`
- Kachaka base — `planar` joint, `odom -> base_footprint`

The SRDF also disables collisions between the Kachaka links, which are rigidly
stacked and permanently in contact. Without those entries MoveIt rejects every
plan for a self-colliding start state.

## Package dependencies

The Kachaka mode additionally requires:

- `sciurus17_kachaka_description` — vehicle body and Kachaka mount meshes
- `kachaka_description` — the Kachaka mobile platform itself

Both are declared as `exec_depend` in `package.xml`, since they are only needed
when the URDF is built with `use_kachaka_base:=true`.

## Troubleshooting

### "Package 'kachaka_description' not found"

The Kachaka packages are only needed for `use_kachaka_base:=true`. Either install
them into the workspace, or leave the argument at its default.

### Planning fails with an invalid start state

Usually means the SRDF and URDF disagree about the base. Check that
`use_kachaka_base` was passed to the top-level launch file rather than to an
individual node, so the same value reaches the URDF, the SRDF and the controllers.

### TF lookups fail for `base_link` or `world`

`world` only exists in fixed-base mode, and `base_link` only with the Kachaka
base. Manipulator poses belong in `body_base_link`, which exists in both.
