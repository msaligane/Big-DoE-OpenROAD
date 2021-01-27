# Big-DoE-OpenROAD

The run_design.py script executes the following steps: 
1. clear the files/folders from the previous run.
2. Modify the pdn.cfg, config.mk files (for power stripes and placement density sweeping).
3. Create NUM_PROCESS design folders, each with a different clock period and core/die areas.
4. Create NUM_PROCESS different Makefiles.
5. Start NUM_PROCESS jobs.
6. Collect results/logs/reports/objects/designs folders, the pdn.cfg and the config.mk files in a data folder.

The collect_data.py script extracts the tns/wns/power values from the data folder created by run_design.py

The run_design.py and collect_data.py should be placed inside the OpenROAD-flow/flow folder (no need to add `DESIGN_CONFIG=@1` in Makefile)

The run_design.py script has these parameters that can be modified:

```python
#Design that will be swept
DESIGN = "aes" 

PLATFORM = "sky130"

#Number of threads that will be used
NUM_THREAD = 8

#Path to the tech LEF file
TECH_LEF = "platforms/" + PLATFORM + "/lef/sky130_fd_sc_hd.tlef"

#SITE that will be used to determine the CORE_AREA and DIE_AREA
SITE_NAME = "unithd"

#Sweeping start point of aspect ratio (height/width)
ASPECT_RATIO_START = 0.8

#Sweeping endpoint of aspect ratio
ASPECT_RATIO_STOP = 1.5

#Sweeping step
ASPECT_RATIO_STEP = 0.1

#Distance between the CORE_AREA and DIE_AREA
CORE_DIE_SPACING = 10

#Core area, defined in um^2
CORE_AREA = 1000000

UTIL_START = 0.6
UTIL_END = 0.8
UTIL_STEP = 0.01

CLK_STEP = 0.1
CLK_START = 1 # in ns
CLK_END = 2 # in ns
CLK_VARIATIONS = 5 # for denoise

#Metal layers used in pdn.cfg
METALS = ["met1", "met4", "met5"]

# [start, end, step], order is the same as in METALS var
METAL_WIDTH = [[0.48, 0.50, 0.01], 
               [0.95, 0.97, 0.01], 
               [0.92, 0.94, 0.01]]

# [start, end, step], order is the same as METALS var
METAL_PITCH = [[6.5, 6.8, 0.1], 
               [56.5, 56.8, 0.1], 
               [40.5, 40.8, 0.1]] 
```



