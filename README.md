# Big-DoE-OpenROAD

The run_design.py script executes the following steps: 
1. Modify the deisgn and platform config files to set different core utilization, clock period, place density, etc.
2. Create NUM_PROCESS different Makefiles.
3. Start NUM_PROCESS jobs.
4. Collect results/logs/reports/objects/designs folders, the pdn.cfg and the config.mk files in a data folder.

Currently, the run_design.py can use LHS method to generate random data points, and the following parameters can be swept using the script.

```
CLK_PERIOD  		- constraint.sdc in designs
CORE_UTILIZATION 	- config.mk in designs
ASPECT_RATIO 		- config.mk in designs
PLACE_DENSITY    	- config.mk in designs
GP_PAD			- config.mk in platforms
DP_PAD			- config.mk in platforms
FLATTEN 		- synth.tcl in scripts
ABC_CLOCK_PERIOD 	- synth.tcl in scripts
PINS_DISTANCE		- io_placement.tcl in scripts
CTS_CLUSTER_SIZE 	- cts.tcl in scripts
CTS_CLUSTER_DIAMETER 	- cts.tcl in scripts
LAYER_ADJUST 		- fastroute.tcl in platforms
GR_OVERFLOW 		- fastroute.tcl in platforms
```

Different adjustment values can be applied to separate layers in **LHS_ATTRS** in the following way:
```
"LAYER_ADJUST":         ['uniform', 0.1, 0.7],    - default range
"LAYER_ADJUST_met1":    ['uniform', 0.2, 0.4],    - range for met1 only
"LAYER_ADJUST_met2":    ['uniform', 0.5, 0.6],    - range for met2 only
```

The genMetrics_bigDoE.py script extracts tns/wns/power values from designs' reports swept by run_design.py. The Big-DOE-plots.ipynb is used to plot figures/distributions within Jupyter Notebook.

A clean_doe taget is added at the end of the Makefile to delete files/folders from the previous runs
```
clean_doe:
    rm -rf  ./data
    rm -rf ./designs/*/*parallel*
    rm -rf ./*/process*
    rm -f Makefile_process*
    rm -rf ./doe_reports
    rm -f ./platforms/sky130hd/config_*
    rm -f ./platforms/sky130hs/config_*
    rm -f ./platforms/sky130hs/fastroute_*
    rm -f ./platforms/sky130hd/fastroute_*
    rm -f $(SCRIPTS_DIR)/cts_*.tcl $(SCRIPTS_DIR)/synth_*.tcl $(SCRIPTS_DIR)/global_route_*.tcl
    rm -f doe.log
```

