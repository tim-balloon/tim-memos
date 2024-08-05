# 7/25/2024 [TIM] Mass Model Filling (Yum!)

Evan C. Mayer

## Strategy:

* Bottom layer of concrete ensures the mass model errs bottom-heavy, since test flight hardware adds mass to top.
* Middle layer of aggregate + sand obviates mixing & curing time for pouring a large volume of concrete
* Top layer of concrete acts as a "cap," curing in place to keep aggregate layer from shifting, and helps bring mean density up
* Materials should be buyable near Ft. Sumner (e.g.) Roswell during rental car pickup, to avoid hauling excess material and keep mass model mass down for safe transport via box truck.

## Relevant Constants

* ID: 23.5 in
* Interior height: 36 in
* Crosstube diameter: 21 in / $\pi$
* Body internal area: 433.7 in^2 = 3.012 ft^2
* Body vol: 9.036 ft^3
* Crosstube vol: 0.477 ft^3 (about 5%)
* Net vol: 8.56 ft^3
* Est. Req. filler weight: 1180 lb

## Layer 1

Quikrete concrete mix: 3 bags

* https://www.homedepot.com/p/Quikrete-60-lb-Concrete-Mix-110160/100318478
    * per bag: 60 lb / 0.45 ft^3
        * = 133.3 lb / ft^3
    * final cure: 140 lb / ft^3
    * 3 bags: 1.35 ft^3
        * slab height = 1.35 ft^3 / 3.012 ft^2 = 0.448 ft = 5.38 in
        * final weight = 140 * 1.35 = 189 lb

## Layer 3

Quikrete concrete mix: 2 bags

* 3 bags: 0.9 ft^3
    * slab height = 0.9 ft^3 / 3.012 ft^2 = 0.299 ft = 3.59 in
    * final weight = 140 * 0.9 = 126 lb

## Layer 2

Solve for the amount of aggregate and sand required to fill the volume not occupied by concrete floor & cap.

Alternate layers of pea gravel & sand to ensure voids in gravel are filled.

Weight to fill: 1180 - 189 - 126 = 865 lb
Volume remaining: 8.56 - 1.35 - 0.9 = 6.31 ft^3

Pea gravel:
* https://www.homedepot.com/p/Vigoro-0-5-cu-ft-Bagged-Pea-Gravel-Pebble-Landscape-Rock-54255/202523000
    * Similar size range to #57 gravel, for which [we may assume a void ratio of .40 unoccupied volume / occupied volume](https://www.eng-tips.com/viewthread.cfm?qid=32317)
    * per bag: 48 lb / 0.5 ft^3
        * = 96 lb / ft^3
    * Fill all remaining volume with pea gravel: 96 lb / ft^3 * 6.31 ft^3 = 605.8 lb
        * Required bags: 605.8 lb / 48 lb = 12.6 bags => 13
        * Remaining void volume: 6.31 ft^3 * 0.4 ft^3 / ft^3 = 2.52 ft^3

All purpose sand:
* https://www.homedepot.com/p/Quikrete-Coarse-50-lbs-Bag-All-Purpose-Sand-for-Potting-Soil-and-Concrete-Mix-All-Purpose-Sand/328271855
    * per bag: 50 lb / 0.8 ft^3
        * = 62.5 lb / ft^3
    * Fill void volume with sand (alternating layers of pea gravel and sand): 62.5 lb / ft^3 * 2.52 ft^3 = 157.5 lb
        * Required bags: 157.5 lb / 50 lb = 3.15 => 4 bags

Total weight:
* 189 + 605.8 + 157.5 + 126 = 1078.3
* short ~100 lb, within margin of error, can be made up with counterweights 

# Addendum 8/5/2024

Pouring of the mass model is complete. The final contents are:

* 3x: 60 lb bags Quikrete
* 10-3/8" thickness: mixture of Quikrete washed gravel and Quikrete sand
* 3x" 80 lb bags Quikrete
* 2.5x + 1.25x: mixture of Quikrete washed gravel + Quikrete sand
* 1.5x: 80 lb bags Quikrete

We called an audible and poured concrete in the middle to help transmit load from the upper fill to the el axis, which it was unclear if the looser gravel would do.