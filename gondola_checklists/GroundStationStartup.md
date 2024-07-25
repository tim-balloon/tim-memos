# Ground Station Startup

Evan C. Mayer

evanmayer@arizona.edu

Last Updated: 2024-07-23

# Purpose

This standard operating procedure (SOP) is intended to provide guidance on how to safely prepare the Terahertz Intensity Mapper (TIM) ground station for a power-on operation such as a flight software test, sensor test, attitude control test, or flight operation. Laboratory personnel should review this SOP, as well as the appropriate Safety Data Sheet(s) (SDSs) before preparing for a ground station startup operation. If you have questions concerning the requirements within this SOP, contact [Evan C. Mayer](evanmayer@arizona.edu) or [Ian Lowe](ianlowe@arizona.edu). This SOP is based on the [UArizona Laboratory Standard Operating Procedure Template](https://research.arizona.edu/compliance/RLSS/chemical-safety/forms-and-templates).

# Scope

This SOP applies during the process leading up to and during an operation where the TIM gondola requires commanding or telemetry readout. It applies to all participants from the science team.

# Hazard Description

* N/A

# Process & Hazard Controls

## Elimination/Substitution

N/A

## Engineering Controls

N/A

## Work Practices

* Required personnel:
    * 1 of: Evan Mayer, Ian Lowe

## Personal Protective Equipment

N/A

## Transportation and Storage

N/A

## Spills, Cleanup, and Disposal

N/A

## Prerequisite SOPs

N/A

# Procedure

> **NOTE:** This procedure can only augment onsite safety procedures; where both this procedure and onsite safety procedures are in effect, the more stringent of the two apply.

## Work Area Preparation

1. [ ] Clear work area of food, drink, or other objects that could strike keyboard or mouse
2. [ ] Clear work area of trip hazards - boxes, bags, or loose cables

## Power and Data Connection Check

1. [ ] Check PC power supply unit (PSU) switch is in ON position
2. [ ] Check gondola local area network (LAN) cable connection
    1. Only applies during ground testing
    2. Should run from back of PC to a switch, then to gondola, or directly to a switch on gondola
3. [ ] Check Internet connection

## Power On

1. [ ] Press power button on top of ground station PC tower
2. [ ] Log in as `tim` user
    1. Consult Ian Lowe or Evan Mayer for password

## Update Ground Station Source Code

If the flight software or ground software has changed since the last build, it is required to update the source code on the ground station.

1. [ ] Open a Terminal window
2. [ ] `cd ~/git/TIMflight/`
3. [ ] `git checkout main`
4. [ ] `git pull`
    1. If not connected to the Internet, you may specify another valid `git` repo as the pull target, e.g. `git pull evanmayer@192.168.1.242:/home/evanmayer/github/TIMflight/`

## Update Ground Station Executables

If the flight software or ground software has changed since the last build, it is required to rebuild the executables on the ground station.

### Build `groundhog`

`groundhog` receives telemetry.

1. [ ] `cd ~/git/TIMflight/groundhog/`
2. [ ] `mkdir build; cd build && cmake .. && cmake --build .`

### Build `guaca`

`guaca` is a GUI for the `mole` telemetry client application, which provides telemetry data to other applications.

1. [ ] `cd ~/git/TIMflight/guaca/`
2. [ ] `./configure && make`

### Build `owl`

`owl` is a GUI that provides a live telemetry dashboard of current values.

1. [ ] `cd ~/git/TIMflight/owl/`
2. [ ] `./configure $$ make`

### Build `cow`

`cow` is the Command Operations Window, a GUI that allows sending commands to a flight computer.

1. [ ] `cd ~/git/TIMflight/cow/`
2. [ ] `./configure $$ make`

## Start Ground Station Software

These instructions are for the mode of operation most common in ground-based testing, where the ground station is able to ping the flight computers. Other command-line options may be necessary for other telemetry links or ground station configurations. Consult Ian Lowe or Evan Mayer for these situations.

Start each application in a separate terminal window.

1. [ ] `cd ~/git/TIMflight`
2. [ ] `./groundhog/build/groundhog -pilot_only`
    1. You will not see any output unless a FC is found and `mcp` is running.
3. [ ] `sudo ./guaca/guaca`
    1. In "Linklist Dir" window, select the dirfile corresponding to the telemetry
    2. Click "Start MOLE"
    3. The dancing avocado will be unhappy unless a dirfile is being updated by `groundhog`
4. [ ] `sudo ./cow/cow`
    1. In the pop-up window, enter the IP of the FC you want to command, typically `192.168.1.3`
    2. Click "Connect"
    3. This will hang unless a the FC is pingable and is running the `blastcmd` daemon
4. [ ] `./owl/owl owl-files/time/tim2024.owl &`
5. [ ] `./owl/owl owl-files/time/motor_controller_status.owl &`
6. [ ] `./owl/owl owl-files/time/pointing.owl &`
7. [ ] `kst2 ./kst/tim/<any_file_of_interest>.kst &`
    1. Repeat for any other `kst` files

The next scripts are optional.

8. [ ] `attitude_vis`: animated gondola model
    1. Activate `conda` environment with packages to display animated gondola model: `conda activate ecm`
    2. `cd ~/evanmayer/vis/`
    3. `./start_vis.sh`
9. [ ] `scan_rate_vis`: rotary displays of Az/El
    1. If not already done, activate `conda` environment with packages to display animated gondola model: `conda activate ecm`
    2. `cd ~/evanmayer/vis/`
    3. `python3 ./scan_rate_vis.py`

## Power Off

`sudo shutdown`

# References
