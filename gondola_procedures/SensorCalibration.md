Evan C. Mayer

evanmayer@arizona.edu

Last Updated: 2024-08-18

# Purpose

This standard operating procedure (SOP) is intended to provide guidance on how to gather data to calibrate the Terahertz Intensity Mapper (TIM) gondola's pointing sensors during ground testing. Laboratory personnel should review this SOP, as well as the appropriate Safety Data Sheet(s) (SDSs), before calibrating the TIM gondola sensors. If you have questions concerning the requirements within this SOP, contact [Evan C. Mayer](evanmayer@arizona.edu) or [Ian Lowe](ianlowe@arizona.edu). This SOP is based on the [UArizona Laboratory Standard Operating Procedure Template](https://research.arizona.edu/compliance/RLSS/chemical-safety/forms-and-templates).

# Scope

This SOP applies during the process leading up to and during an operation where the TIM gondola will be moved by hand or motors to collect calibration data. It applies to all participants from the science team.

# Hazard Description

* Crushing: gondola contact points (support feet) may present crushing hazard if gondola were to fall or tilt during lift or motion
* Blunt force impact: gondola structure may present impact hazard if gondola motion were to become uncontrolled

# Process & Hazard Controls

## Elimination/Substitution

* Do not power any motor controllers not required for a test: each motor controller has a Safe Torque Off (STO) jumper that removes the ability to power the controller outputs if not installed.

## Engineering Controls

* Guide line affixed to TIM gondola outer frame on a rigid structural member
* Lock pin can prevent motion in elevation
* Ground station command `force_el_on` requires confirmation to move El axis despite pin being engaged, when issued via the `cow` interface

## Work Practices

* Required personnel:
    * 1 trained crane operator
    * 1 guide line operator
    * 1 spotter for surroundings
    * 2 ground station operators

* Always maintain a clean and clear work area around the ground station computer. Accidental keystrokes at the ground station can end the experiment. Always maintain line of sight between the ground station and inner frame; this may be fulfilled by a spotter if the inner frame is obscured by the sun shield.

## Personal Protective Equipment

* Hard hats
* Safety glasses
* High visibility vests
* Protective shoes

## Transportation and Storage

N/A

## Spills, Cleanup, and Disposal

N/A

## Prerequisite SOPs

* [Ground Station Startup](./GroundStationStartup.md): Required before beginning, in order to have ground software ready to issue commands before powering gondola on, and ready to view telemetry to interpret gondola and flight software behavior
* [Power-on Gondola](./PowerOnGondola.md): Required to safely check out and power on gondola in order to move using the flight software

# Procedure

> **NOTE:** This procedure can only augment onsite safety procedures; where both this procedure and onsite safety procedures are in effect, the more stringent of the two apply.

> **WARNING:** Sending commands, with few exceptions, is immediate. If you don't know what you're doing, or aren't paying attention, bad things can happen fast. Slow down. Always double check commands and parameters before sending; avoid mental errors such as sending an unintended command, and avoid typos.

## Background

### Do's and Don'ts

#### DO

* Move the gondola and inner frame by hand during this procedure
    * Moving TIM by software control without calibrated sensors is not recommended, so to bootstrap this, we may move TIM by hand to collect calibration data.

#### DON'T

* Spin the inner frame more than 360deg

## Sensors

Read the documentation for each sensor. Each outlines basic principles of operation, the calibration data collection procedure, and provides scripts for analyzing the data to update the flight software:

1. [Inclinometers](https://github.com/tim-balloon/TIM-software-primer/blob/main/sensor_calibration/inclinometer/inc.md)
2. [Gyroscopes](https://github.com/tim-balloon/TIM-software-primer/blob/main/sensor_calibration/gyroscope/gyro.md)
3. [Pinhole Sun Sensor Array](https://github.com/tim-balloon/TIM-software-primer/blob/main/sensor_calibration/pinhole_sun_sensor_array/pss.md)
4. [Star Cameras](https://github.com/tim-balloon/TIM-software-primer/blob/main/sensor_calibration/star_camera/sc.md)
5. [Magnetometers](https://github.com/tim-balloon/TIM-software-primer/blob/main/sensor_calibration/magnetometer/mag.md)
6. [GPS Compass](https://github.com/tim-balloon/TIM-software-primer/blob/main/sensor_calibration/differential_gps/dgps.md)

Commit any code changes to the development branch and file a pull request to `main` immediately.

# References
