# Big-DoE-OpenROAD

The run_design.py script executes the following steps: 
1. Modify the deisgn and platform config files to set different core utilization, clock period, place density, etc.
2. Create NUM_PROCESS different Makefiles.
3. Start NUM_PROCESS jobs.
4. Collect results/logs/reports/objects/designs folders, the pdn.cfg and the config.mk files in a data folder.

Currently, the run_design.py script can sweep the following parameters, the script can also generate random data points using LHS method

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

The genMetrics_bigDoE.py script extracts tns/wns/power values from designs' reports swept by run_design.py.

A clean_doe taget is added at the end of the Makefile to delete files/folders from the previous runs
```
clean_doe:
	rm -rf  ./data 
	rm -rf ./designs/*/*parallel*
	rm -rf ./*/process*
	rm -f Makefile_process*
	rm -rf ./doe_reports
```

