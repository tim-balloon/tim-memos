Evan C. Mayer

evanmayer@arizona.edu

Last Updated: 2024-08-18

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

* Always maintain a clean and clear work area around the ground station computer. Accidental keystrokes at the ground station can end the experiment. Always maintain line of sight between the ground station and inner frame; this may be fulfilled by a spotter if the inner frame is obscured by the sun shield.

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
* [Sensor Calibration](./SensorCalibration.md): Required to accurately control pointing and operate lock pin

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

For the TIM test flight, there are NO HARD STOPS. Cable wrapping is mitigated somewhat by the starboard cable feedthrough, but is still a concern. Do not flip TIM.

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

> **CAUTION:** If `cur_mode 0 0 0` is sent, gondola will continue moving if already moving, and el axis may fall if unbalanced and not locked.

> **CAUTION:** If the instrument is scheduled to observe particular targets (check `/data/etc/blast/*.sch` on the flight computers), the pointing mode may change on its own! This may take you out of `stop` or `cur_mode`!

### Lock Pin Positions

* 0 deg
* 22.5
* 45 deg
* 67.5
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

<font color='red'>**IF AND ONLY IF THE WATCHDOG IS CONNECTED TO BOTH FCs**:</font>

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

#### Engage Lock Pin

1. [ ] Manually move the inner frame to align the lock pin with the 45 degree lock pin hole to within the lock pin tolerance: `actuators.h:LOCK_THRESHOLD_DEG`
2. [ ] Engage the lock pin: `Lock Motor`>`lock 45`

#### Ensure Sensors Are Trimmed

"Trimming" a sensor means manually setting an offset so that it is forced to agree with some external truth at some point in time. This is typically another sensor or a reference external to the gondola. Commands also exist to trim one poor sensor to agree with a better one.

* `Pointing Sensor Trims`>`reset_trims`: Set all trim values to 0

##### Procedure

If star camera solutions are available:

1. [ ] `Pointing Sensor Trims`>`xsc_offset 0 <cross-el trim> <el trim>`
    1. Input the values which, when added to the star camera 0 Az/El, force it to agree with the actual Az/El of the inner frame, measured by an external reference.
2. [ ] `Pointing Sensor Trims`>`trim_xsc1_to_xsc0`
    1. Adjust star camera 1 offsets to agree with star camera 0
3. [ ] `Pointing Sensor Trims`>`trim_to_xsc0`
    1. Adjust sensor trims to agree with star camera 0
4. [ ] `Pointing Sensor Trims`>`autotrim_to_sc`
    1. Once commanded, begin updating sensor trims each time a star camera solution is obtained; take star camera Az/El solutions as truth

If no star camera solutions are available:

1. [ ] `Pointing Sensor Trims`>`az_el_trim <true Az> <true El>`
    1. Manually set the pointing solution Az/El; trimmable sensors will have their trim offset changed (though change is rate limited) to agree with this.
    2. List of sensor trims changed:
        * Inclinometer 1 El
        * Inclinometer 2 El
        * Motor Encoder El
        * Magnetometer 1 Az
        * Magnetometer 2 Az
        * Pinhole sun sensor array Az (only if good data is recent)
        * CSBF GPS compass

#### El Only

1. [ ] Ensure El motor controller STO jumper is installed. Set down the gondola before inserting jumpers. If a new STO jumper is installed after power-on, clear the latched STO fault by commanding to clear the fault (`reset_latched_el 18`) or power cycling the controller.
2. [ ] Enter stop mode to prepare for enablement: `Pointing Modes`>`stop`
3. [ ] Enable motor: `Pointing Motors`>`el_on`
4. [ ] Retract lock pin: `Lock Motor`>`unlock`

The El motor should engage when the lock pin has retracted, catching the inner frame. Motion should be arrested.

##### Az/El Goto

1. [ ] Static: `Pointing Modes`>`az_el_goto <current Az> <current El>`: fields populated with current estimated Az/El, do not change for now
    1. Enters goto mode without attempting to move.
2. [ ] Move: `Pointing Modes`>`az_el_goto <current Az> <MIN_EL>`: Az field populated with current estimated Az, do not change for now. Look up `motors.h:MIN_EL` to attempt to go to the minimum software-allowed El.

1. [ ] Az/El Goto: move: `Pointing Modes`>`az_el_goto <current Az> <MAX_EL>`: Az field populated with current estimated Az, do not change for now. Look up `motors.h:MAX_EL` to attempt to go to the maximum software-allowed El.

##### El Scan

1. [ ] `Pointing Modes`>`el_scan <current Az> 45 10 0.1`:
    * Centered on current Az
    * Centered on 45 deg El
    * Total scan height 10 deg El
    * Scan speed 0.1 deg/s

##### Lock El

1. [ ] `Lock Motor`>`lock45`
2. [ ] `Pointing Modes`>`stop`
3. [ ] `Pointing Motors`>`el_off`
3. [ ] Remove El axis STO jumper if desired

#### Az Only

1. [ ] Ensure reaction wheel (RW) and pivot (Piv) motor controller STO jumpers are installed. Set down the gondola before inserting jumpers. If a new STO jumper is installed after power-on, clear the latched STO fault by commanding to clear the fault (`reset_latched_rw 18`, `reset_latched_piv 18`) or power cycling the controller.
2. [ ] Enter `cur_mode` with 0 current to prepare for enablement: `Pointing Modes`>`cur_mode 0 0 0`
    * piv current 0
    * RW current 0
    * El current 0
3. [ ] Prepare team for gondola Az motion: when the RW is halted and then turned on, it must spin up to its setpoint - some transient outer frame motion is expected while the spin-up angular momentum is dumped through the pivot and the control system reaches steady-state.
4. [ ] Enable Az motors: `Pointing Motors`>`az_on`

##### Az/El Goto

We have written 0 Az here as the first move, assuming that it is practical given the space available. You can offset the Az moves by any amount that works for you.

1. [ ] Static: `Pointing Modes`>`az_el_goto <current Az> <current El>`: fields populated with current estimated Az/El, do not change for now
    1. Enters goto mode without attempting to move.
2. [ ] Move: `Pointing Modes`>`az_el_goto 0 <current El>`: Slew to 0 Az, or another value that makes sense given the current Az and the surroundings. El field populated with current estimated El, do not change for now.
3. [ ] Az/El Goto: move: `Pointing Modes`>`az_el_goto 5 <current El>`: A small move in positive Az (clockwise as seen from above; Az is defined as a positive rotation east of north)
4. [ ] Az/El Goto: move: `Pointing Modes`>`az_el_goto 45 <current El>`: A larger move in positive Az
5. [ ] Az/El Goto: move: `Pointing Modes`>`az_el_goto 0 <current El>`: Back to 0
5. [ ] Az/El Goto: move: `Pointing Modes`>`az_el_goto 90 <current El>`: A larger move

##### Az Scan

1. [ ] `Pointing Modes`>`az_scan 0 <current El> 0.1 0.05`:
    * Centered on 0 Az
    * Centered on current El
    * Total scan width 0.1 deg Az
    * Scan speed 0.05 deg/s
2. [ ] `Pointing Modes`>`az_scan 0 <current El> 5 0.1`:
    * Centered on 0 Az
    * Centered on current El
    * Total scan width 5 deg Az
    * Scan speed 0.1 deg/s
3. [ ] `Pointing Modes`>`stop`
4. [ ] `Pointing Motors`>`az_off`

Be prepared to catch the gondola - as the RW spins down, the gondola will begin to spin

#### Both Axes

1. [ ] Ensure El axis, reaction wheel (RW), and pivot (Piv) motor controller STO jumpers are installed. If required for access, set down the gondola or bring down the pivot before inserting jumpers. If a new STO jumper is installed after power-on, clear the latched STO fault by commanding to clear the fault (`reset_latched_rw 18`, `reset_latched_piv 18`, `reset_latched_el 18`) or power cycling the controller.
2. [ ] Enter stop mode to prepare for enablement: `Pointing Modes`>`stop`
3. [ ] Enable El motor: `Pointing Motors`>`el_on`
4. [ ] Retract lock pin: `Lock Motor`>`unlock`

The El motor should engage when the lock pin has retracted, catching the inner frame. Motion should be arrested.

5. [ ] Prepare team for gondola Az motion: when the RW is halted and then turned on, it must spin up to its setpoint - some transient outer frame motion is expected while the spin-up angular momentum is dumped through the pivot and the control system reaches steady-state.
6. [ ] Enable Az motors: `Pointing Motors`>`az_on`

##### Az/El Goto

We have written 0 Az here as the first move, assuming that it is practical given the space available. You can offset the Az moves by any amount that works for you.

1. [ ] Static: `Pointing Modes`>`az_el_goto <current Az> <current El>`: fields populated with current estimated Az/El, do not change for now
    1. Enters goto mode without attempting to move.
2. [ ] Move: `Pointing Modes`>`az_el_goto 0 20`: Slew to 0 Az, or another value that makes sense given the current Az and the surroundings. 20 El, near the lower software limit.
3. [ ] Az/El Goto: move: `Pointing Modes`>`az_el_goto 5 25`: A small move in positive Az (clockwise as seen from above; Az is defined as a positive rotation east of north), small move in positive El
4. [ ] Az/El Goto: move: `Pointing Modes`>`az_el_goto 45 45`
5. [ ] Az/El Goto: move: `Pointing Modes`>`az_el_goto 0 55`
6. [ ] Az/El Goto: move: `Pointing Modes`>`az_el_goto 90 20`
7. [ ] Az/El Goto: move: `Pointing Modes`>`az_el_goto 0 45`

##### RA/Dec Goto

1. [ ] Track: `Pointing Modes`>`ra_dec_goto <current RA> <current Dec>`: fields populated with current estimated RA/Dec track this RA/Dec
2. [ ] Observe the Ra/Dec tracking

#### Parking the scope

1. [ ] `Pointing Modes`>`stop`
2. [ ] `Lock Motor`>`lock45`
3. [ ] `Pointing Motors`>`el_off`
4. [ ] `Pointing Motors`>`az_off`

Be prepared to catch the gondola - as the RW spins down, the gondola will begin to spin.

# References
