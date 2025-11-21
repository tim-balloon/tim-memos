# Power-on Gondola

Evan C. Mayer

evanmayer@arizona.edu

Last Updated: 2024-07-23

# Purpose

This standard operating procedure (SOP) is intended to provide guidance on how to safely prepare the Terahertz Intensity Mapper (TIM) gondola for a power-on operation such as a flight software test, sensor test, attitude control test, or flight operation. Laboratory personnel should review this SOP, as well as the appropriate Safety Data Sheet(s) (SDSs) before preparing for a power-on operation. If you have questions concerning the requirements within this SOP, contact [Evan C. Mayer](evanmayer@arizona.edu) or [Ian Lowe](ianlowe@arizona.edu). This SOP is based on the [UArizona Laboratory Standard Operating Procedure Template](https://research.arizona.edu/compliance/RLSS/chemical-safety/forms-and-templates).

# Scope

This SOP applies during the process leading up to and during an operation where the TIM gondola is powered on. It applies to all participants from the science team.

# Hazard Description

* Shock hazard: gondola power system will be energized; lack of caution with tools could cause a short

# Process & Hazard Controls

## Elimination/Substitution

* Do not provide power if the operation does not require TIM electronics to be powered
* Disconnect power from devices that are not essential to the test or flight operation

## Engineering Controls

* When not performing a power-on operation with the intent to fly, the flight software service, `flight_software.service` shall be disabled on both flight computers, to disable flight software commands to motors and power controllers during the power-on process before ground station command and control is established
* Arm's reach access to a device that cuts gondola power - E-STOP switch or power cable

## Work Practices

* Required personnel:
    * 1 of: Evan Mayer, Justin Bracks, Ian Lowe, Shubh Agrawal

## Personal Protective Equipment

* Safety glasses

## Transportation and Storage

N/A

## Spills, Cleanup, and Disposal

N/A

## Prerequisite SOPs

[Ground Station Startup SOP](./GroundStationStartup.md), if connecting new devices.

# Procedure

> **NOTE:** This procedure can only augment onsite safety procedures; where both this procedure and onsite safety procedures are in effect, the more stringent of the two apply.

## Preparation

1. [ ] Kill switch (**motors** and flight computers) within arm's reach
    1. A power cable that removes power to motors and flight computers when disconnected may be used if an emergency stop switch is not present
2. [ ] Check grounding of power boxes to gondola
3. [ ] Check gondola power delivery - E-FUEL/batteries should be secured to gondola
4. [ ] Inspect harnessing for any pinched, broken, or dirty wires
    1. Replace any damaged harnessing
5. [ ] Check connector mating; wiggle all connections, secure loose connections

> **WARNING:** If connecting **any** power connectors (e.g. new device, new cable, or reconnecting a device that had been disconnected), refrain until after gondola power is applied, so that correct voltages can be verified at the power breakout box (PBoB) output and cable output before connecting.

## Connecting New Devices

> **NOTE:** Connecting new devices safely requires controlling the power breakout boxes (PBoBs) via the flight software. Refer to the [Ground Station Startup SOP](./GroundStationStartup.md).

If connecting new devices, reconnecting old devices, or connecting a new power cable:

1. [ ] Check device spec sheet to verify voltage tolerance
    1. [Datasheets](https://drive.google.com/drive/u/0/folders/1erbkUpVd5UW-Y4VRA8wPCMF6vXLMjCDW)
2. [ ] Cross-check command against PBoB output number:
    1. Open `TIMflight/mcp/commanding/commands.c`
    2. Check `SingleCommand()` switch case for command name
    3. Verify intended command's relay number matches number on outside of PBoB
3. [ ] Use flight software and `cow` or `blastcmd` to apply power to desired PBoB output - issue `<my_device>_on`
4. [ ] Use multimeter to verify voltage at power breakout box (PBoB)
5. [ ] Power off PBoB output - issue `<my_command>_off`
6. [ ] Plug in power cable
7. [ ] Power on PBoB output
8. [ ] Use multimeter to verify voltage at cable end
9. [ ] Power off PBoB
10. [ ] Connect cable to device
11. [ ] Power on PBoB output

> **WARNING:** Capacitance inside the PBoB may cause voltage to decay slowly after switching output power off if no load is connected. Use a multimeter to ensure that voltage has reduced to a safe level before plugging in any device.

## Cross-Check Connected Devices

Check all connectors are installed in proper place - cross-check cable labels against box labels and the cabling spreadsheet.

1. [ ] Power connections

2. [ ] Ethernet connections

3. [ ] Serial connections

## Ensure Motionless Power-on

Ensure power-on state of gondola/software prohibits motion.

1. [ ] Disconnect motor controller STO jumpers
    1. See motor controller datasheet - [BEL-090-30](https://drive.google.com/file/d/1CYNVfCuR24eKc1PknuGnF2Ig2tq5M2RC/view?usp=drive_link)
    2. When STO jumper is removed, motor controller connector marked "SAFETY" will be empty

## Power-on Operation

1. [ ] Apply power to power breakouts
    1. Apply AC power to E-FUEL by turning switch to ON, set to 28 VDC
    2. Power is supplied to rest of gondola devices
2. [ ] Listen for flight computer bring-up - BIOS beeps

## Ensure Future Power-ons are Safe

When not preparing to fly, we apply an engineering control: inhibit the automatic startup of the flight software to prevent motion before command and control is established via the ground station. When the flight software is not running, it is impossible to issue new current commands to the motor controllers.

1. [ ] Ping both flight computers from a PC connected to the gondola LAN (ideally, the ground station)
    1. `ping 192.168.1.3`, wait for response
    2. `ping 192.168.1.4`, wait for response
2. [ ] `ssh` into `fc1`: `ssh fc1user@192.168.1.3`
3. [ ] Run `sudo systemctl disable flight_software.service`
    1. This prevents the service that starts GPS daemons, `blastcmd` daemon, and `mcp` from running immediately on boot
    2. <font color="red">This service must be re-enabled prior to flight</font>: `sudo systemctl enable flight_software.service`
4. [ ] `ssh` into `fc2`: `ssh fc1user@192.168.1.4`
    1. Repeat above for `fc2`

## Power-off Operation

1. [ ] `ssh fc1user@192.168.1.3`
2. [ ] `sudo systemctl stop flight_software.service`
3. [ ] `sudo shutdown now`

4. [ ] `ssh fc1user@192.168.1.4`
5. [ ] `sudo systemctl stop flight_software.service`
6. [ ] `sudo shutdown now`

7. [ ] Remove power from gondola by disconnecting power breakout from ground power; unplug cable from wall
8. [ ] Turn E-Fuel switch to OFF

# References


