# Big-DoE-OpenROAD

The run_design.py script modifies the pdn.cfg, config.mk files inside the platform folder (for sweeping power stripe width/pitch, and utilization). The script creates NUM_THREAD different Makefiles/design folders, each Makefile is pointing to a different design folder. Each design folder has a different clock period and core/die areas according to the aspect ratio and area defined in the script. The script starts NUM_THREAD processes in parallel. After all processes are finished, the results/logs/reports/objects/designs folders and the modified pdn.cfg and config.mk files are moved into a new data folder for future extraction. The run_design.py script has these parameters can be modified.

```python
#Design that will be sweeped
DESIGN = "aes" 

PLATFORM = "sky130"

#Number of threads that will be used
NUM_THREAD = 8

#Path to the tech lef file
TECH_LEF = "platforms/" + PLATFORM + "/lef/sky130_fd_sc_hd.tlef"

#SITE that will be used to determine the CORE_AREA and DIE_AREA
SITE_NAME = "unithd"

#Sweeping start point of aspect ratio (hight/width)
ASPECT_RATIO_START = 0.8

#Sweeping end point of aspect ratio
ASPECT_RATIO_STOP = 1.5

#Sweeping step
ASPECT_RATIO_STEP = 0.1

#Distance between the CORE_AREA and DIE_AREA
CORE_DIE_SPACING = 10

Core area, defined in um^2

CORE_AREA = 1000000

UTIL_START = 0.6

UTIL_END = 0.8

UTIL_STEP = 0.01

CLK_STEP = 0.001

CLK_START = 1 # in ns

CLK_END = 2 # in ns

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



