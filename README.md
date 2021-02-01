# Big-DoE-OpenROAD

The run_design.py script executes the following steps: 
1. Modify the pdn.cfg, config.mk files (for power stripes and placement density sweeping).
2. Create NUM_PROCESS design folders, each with a different clock period and core/die areas.
3. Create NUM_PROCESS different Makefiles.
4. Start NUM_PROCESS jobs.
5. Collect results/logs/reports/objects/designs folders, the pdn.cfg and the config.mk files in a data folder.

The collect_data.py script extracts the tns/wns/power values from the data folder created by run_design.py. These values are extracted from the OpenROAD reports:

```
2_1_floorplan.log => doe_reports/2_1_floorplan_all.csv
 - tns
 - wns

3_3_resizer.log => doe_reports/3_3_resizer_all.csv
 - tns
 - wns

4_1_cts.log => doe_reports/4_1_cts_all.csv
 - tns
 - wns

6_report.log => doe_reports/6_report_all.csv
 - tns
 - wns
 - internal power
 - switching power
 - leakage power
 - total power
 - instance count
```

All data is also stored in a json file called data_stream.json. Designs that cannot generate valid 6_report.log files are identified as failed desings and are recorded in the doe_reports/failed_designs.txt file.

The run_design.py and collect_data.py should be placed inside the OpenROAD-flow/flow folder (no need to add `DESIGN_CONFIG=@1` in Makefile)

The run_design.py script has these parameters that can be modified:

```python
#Design that will be swept
DESIGN = "gcd"

PLATFORM = "sky130"
PLATFORM_CONFIG = "config_hd.mk"

#Number of threads that will be used
NUM_PROCESS = 8

################################
# Clock period
################################

# clock period
CLK_STEP = 0.1
CLK_START = 5 # in ns
CLK_END = 7 # in ns
CLK_VARIATIONS = 3 # step 1ps

################################
# Floorplan
################################

# utilization
CORE_CORE_UTILIZATION_START = 15
CORE_CORE_UTILIZATION_END = 35
CORE_CORE_UTILIZATION_STEP = 5

# aspect ratio
ASPECT_RATIO_VALUES = [3/4, 1, 4/3]
ASPECT_RATIO_START = 0.8
ASPECT_RATIO_STOP = 1.2
ASPECT_RATIO_STEP = 0.1

# core/dire area
CORE_DIE_MARGIN = 10

################################
# Placement
################################

CELL_PAD_IN_SITES_GLOBAL_PLACEMENT_START = 0
CELL_PAD_IN_SITES_GLOBAL_PLACEMENT_END = 4
CELL_PAD_IN_SITES_GLOBAL_PLACEMENT_STEP = 2

PLACE_DENSITY_START = 0.4
PLACE_DENSITY_END = 0.8
PLACE_DENSITY_STEP = 0.2

CELL_PAD_IN_SITES_DETAIL_PLACEMENT_START = 0
CELL_PAD_IN_SITES_DETAIL_PLACEMENT_END = 4
CELL_PAD_IN_SITES_DETAIL_PLACEMENT_STEP = 2


################################
# Cts
################################

SETUP_FIX = [0, 1]

```

A clean_doe taget is added at the end of the Makefile to delete files/folders from the previous runs
```
clean_doe:
	rm -rf  ./data 
	rm -rf ./designs/*/*parallel*
	rm -rf ./*/process*
	rm -f Makefile_process*
	rm -rf ./doe_reports
```

