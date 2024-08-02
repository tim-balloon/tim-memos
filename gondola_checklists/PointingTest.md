Evan C. Mayer

evanmayer@arizona.edu

Last Updated: 2024-08-01

# Purpose

This standard operating procedure (SOP) is intended to provide guidance on how to safely point the Terahertz Intensity Mapper (TIM) gondola during ground testing. Laboratory personnel should review this SOP, as well as the appropriate Safety Data Sheet(s) (SDSs), before pointing the TIM gondola. If you have questions concerning the requirements within this SOP, contact [Evan C. Mayer](evanmayer@arizona.edu) or [Ian Lowe](ianlowe@arizona.edu). This SOP is based on the [UArizona Laboratory Standard Operating Procedure Template](https://research.arizona.edu/compliance/RLSS/chemical-safety/forms-and-templates).

# Scope

This SOP applies during the process leading up to and during an operation where the TIM gondola motion will be powered and controlled via the flight software. It applies to all participants from the science team.

# Hazard Description

* Crushing: gondola contact points (support feet) may present crushing hazard if gondola were to fall or tilt during lift or motion
* Blunt force impact: gondola structure may present impact hazard if gondola motion were to become uncontrolled

# Process & Hazard Controls

## Elimination/Substitution

* Do not lift the gondola if the test does not require motion in azimuth
* Do not power any motor controllers not required for a test: each motor controller has a Safe Torque Off (STO) jumper that removes the ability to power the controller outputs if not installed.

## Engineering Controls

* Guide line affixed to TIM gondola outer frame on a rigid structural member
* Lock pin prevents motion in elevation
* Ground station command `force_el_on` requires confirmation to move El axis despite pin being engaged, when issued via the `cow` interface

## Work Practices

* Required personnel:
    * 1 trained crane operator
    * 1 guide line operator
    * 1 spotter for surroundings
    * 2 ground station operators

* Always maintain a clean and clear work area around the ground station computer. Accidental keystrokes at the ground station can end the experiment.

## Personal Protective Equipment

* Hard hats
* Safety glasses
* High visibility vests
* Gloves
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

#### DON'T

* Push, pull, or kick the gondola
    * Control loops are tuned for smooth scanning and pointing, NOT for impulse rejection.
    * Impulses may exceed the controller bandwidth and may cause oscillations
    * Pushing on any part of the gondola is an external force; the control algorithm PID loops accumulate errors in pointing or scanning for the duration of any push; "integral wind-up" is software-limited, but a prolonged push may still cause an overcorrection and possible oscillations
    * Undamped oscillations can be extremely hazardous, especially early in the control loop tuning process

### Commanding Architecture

The TIM gondola is controlled primarily via the Command Operations Window, `cow`, which is a GUI frontend for the `blastcmd` program. `cow` queries a `blastcmd` daemon on the flight computer being commanded, and the flight computer responds with available commands and acceptable values. Commands are sent to the gondola via one of several selectable telemetry links. On the ground, we will use either (Iridium) Pilot faked via Ethernet, or Ethernet via Telemetry (EVTM) links.

Commands are organized into groups. Groups are selectable in the main window. Commands are selectable from the left sidebar. Once selected, if a command takes parameters, they will appear in the main window. Sending a command is done via clicking the button in the lower right or pressing `Shift + F12`. The equivalent `blastcmd` invocation is echoed in the status window at the bottom. Invalid commands are called out here.

### Hard Stops

### Software Limits

TIM's behavior is governed in software by various limits, which we can change with good rationale.

> **NOTE:** File line numbers are given as a guide since code changes may make them out of date.

#### El

El position limits are enforced by commanding a correcting velocity in the direction that returns the inner frame to the limits (~`motors.c:191`).

* Min Value: **19 deg**
    * ~`motors.h:33`
* Max Value: **55 deg**
    * ~`motors.h:35`
* Max Rate: **0.5 deg/s**
    * ~`motors.h:40`
* Max Accel.: **0.5 deg/s/s**
    * ~`motors.h:69`

#### Az

* Min Value: **N/A**
* Max Value: **N/A**
* Max Rate: **2.0 deg/s**
    * ~`motors.h:38`
* Max Scan Accel: **0.1 deg/s/s**
    * ~`motors.c:89`

### Critical Basic Commands

* `Pointing Motors`>`el_off`: <font color='red'>disables the El axis in software</font>
    * Sends 0 amp command to the El axis motor controller and inhibits further motion, regardless of pointing mode
    * Does not engage electronic brake
* `Pointing Motors`>`az_off`: <font color='red'>disables the Az axis in software</font>
    * Sends 0 amp command and inhibits further motion of reaction wheel and pivot motors, regardless of pointing mode
    * Does not engage electronic brake
* `Pointing Modes`>`stop`: <font color='red'>commands full stop</font>
    * Commands attitude control algorithm to stop, using gyro angular rates to achieve 0 deg/s in each axis
* `Pointing Modes`>`cur_mode`: <font color='red'>sends N amps to each axis</font>
    * With 0 amps to each axis, forces 0 current to all axes.

> **WARNING:** If `cur_mode 0 0 0` is sent, gondola will continue moving if already moving, and el axis may fall if unbalanced and not locked.

> **WARNING:** If the instrument is scheduled to observe particular targets (check `/data/blast/*.sch` on the flight computers), the pointing mode may change on its own! This may take you out of `stop` or `cur_mode`!

### Lock Pin Positions

* 0 deg
* 45 deg
* 90 deg

### Required Sensors

* Gyro
    * Control loops are closed around velocity, so at least one of two gyros is required to operate at all
* Elevation Encoder
    * The relative position of the outer + inner frames is required to operate the lock pin

TIM can slew and scan in Az without a true Az reference sensor, but the Az solution will not be valid.

#### Auxiliary Sensors

* Star Cameras
    * Sky must be dark
    * Provides absolute pointing via plate solving
* Inclinometers
    * Provides absolute El tilt relative to acceleration (usually gravity) vector
* Pinhole sun sensors
    * Sun must be out
    * Provides absolute Az relative to Sun, given location and time
* Magnetometers
    * Not reliable in the presence of ferromagnetic metals and magnetic fields that are not co-moving in the magnetometer frame of reference
    * Provides absolute Az relative to Earth magnetic field
* GPS compass
    * Provides absolute Az from dual-input GPS receiver (CSBF-provided)

## Procedure

### Resume Software Control

When performing ground testing, the flight software services are disabled; `blastcmd`, `mcp` , `gpsd`, and `chrony` will not start running upon boot, to ensure safe turn-on of the gondola while people may be present. When the flight software is not running, it is impossible to issue new current commands to the motor controllers.

> **NOTE:** *Before flight, it is crucial to re-enable the flight software service on each PC: `sudo systemctl enable flight_software.service`*. Disable with `sudo systemctl disable flight_software.service`. Single-time starts and stops can be done with `start` and `stop` instead of `enable` and `disable`.

When all personnel present are aware, and `cow` or `blastcmd` are ready to issue `el_off` and/or `az_off` if required, start the flight software on each FC:

1. [ ] `ssh fc1user@192.168.1.3`
2. [ ] `sudo systemctl start flight_software.service`

<hr> 

**IF AND ONLY IF THE WATCHDOG IS CONNECTED TO BOTH FCs**:

If this warning is not obeyed, it is possible based on their shutdown state that both FCs may assume they are in charge and issue conflicting commands.

1. [ ] `ssh fc1user@192.168.1.4`
2. [ ] `sudo systemctl start flight_software.service`

<hr>

3. **Immediately** issue `cow` or `blastcmd` commands:
	1. Pointing Modes > `cur_mode 0 0 0`
		1. Manually sets all motor current outputs to 0
	2. Pointing Motors > `az_off`
		1. Disables azimuth control algorithm outputs
	3. Pointing Motors > `el_off`
		1. Disables elevation control algorithm output
4. Verify good telemetry reception via `groundhog`, `kst`, and `owl` windows

### Pointing Test

Goals of pointing test may vary depending on flight readiness/sensor availability.

#### Ensure Sensors Are Trimmed

"Trimming" a sensor means manually setting an offset so that it is forced to agree with some external truth. This is typically another sensor or a reference external to the gondola. Commands also exist to trim one poor sensor to agree with a better one.

* `Pointing Sensors`>`az_el_trim`: manually set the pointing solution Az/El; trimmable sensors will have their trim offset changed (change rate limited) to agree with this.
* 

##### Procedure

1. [ ] Lock gondola to 0 deg using the lock pin:
2. [ ] Check available El sensors: are they consistent with 0 deg? Trim to enforce consistency.
3. [ ] Check available Az sensors: are their readings consistent with TIM boresight alignment to a compass or other reference surface (building foundation, landmark, etc.)? Trim to enforce consistency.

#### Az/El Goto

#### El Scan

#### Az Scan

#### RA/Dec Goto

# References