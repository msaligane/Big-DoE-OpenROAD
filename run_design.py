import glob
import re
import os
import numpy as np
import shutil
import subprocess as sp
import multiprocessing
import sys
import math
import time
from itertools import product
from pyDOE import *
from scipy.stats.distributions import norm, uniform, truncnorm

################################
# Sweeping attributes
################################

SWEEPING_ATTRS = ["CLK_PERIOD", "CORE_UTILIZATION", "ASPECT_RATIO", "GP_PAD", "DP_PAD", \
                  "LAYER_ADJUST", "PLACE_DENSITY", "FLATTEN", "ABC_CLOCK_PERIOD", \
                  "PINS_DISTANCE", "CTS_CLUSTER_SIZE", "CTS_CLUSTER_DIAMETER", "GR_OVERFLOW"]

# The CLK_PERIOD is in ns for sky130, while the ABC_CLOCK_PERIOD is in ps
VALUE_TYPE = {
    "CLK_PERIOD": "float 4",
    "CORE_UTILIZATION": "int",
    "ASPECT_RATIO": "float 3",
    "GP_PAD": "int",
    "DP_PAD": "int",
    "LAYER_ADJUST": "float 1",
    "PLACE_DENSITY": "float 2",
    "FLATTEN": "int",
    "ABC_CLOCK_PERIOD": "float 1",
    "PINS_DISTANCE": "int",
    "CTS_CLUSTER_SIZE": "int",
    "CTS_CLUSTER_DIAMETER": "int",
    "GR_OVERFLOW": "int"
}
# PLACE_DENSITY is automatically added later

################################
# LHS setting
################################

AVAILABLE_DISTRIBUTIONS = ['uniform', 'norm', 'truncnorm']

# Run LHS?
_use_lhs = True

# arguments defined in LHS_ATTRS: a, b, c, d
# uniform: X ~ U(a, b)
# norm: X ~ N(loc=a, scale=b)
# truncnorm: X ~ TN(a, b, loc=c, scale=b), meaning a norm dist with only values between (a,b)
LHS_ATTRS = {
    "CLK_PERIOD":           ['truncnorm', 5, 8, 6, 1],
    "CORE_UTILIZATION":     ['truncnorm', 25, 50, 30, 3],
    "ASPECT_RATIO":         ['uniform', 0.7, 1],
    "GP_PAD":               ['uniform', 0, 4],
    "DP_PAD":               ['uniform', 0, 4],
    "LAYER_ADJUST":         ['uniform', 0.1, 0.7],
    "PLACE_DENSITY":        ['uniform', 0.1, 1.0],
    "FLATTEN":              ['uniform', 0, 1],
    "ABC_CLOCK_PERIOD":     ['uniform', 5000, 5000],
    "PINS_DISTANCE":        ['uniform', 1, 3],
    "CTS_CLUSTER_SIZE":     ['uniform', 10, 40],
    "CTS_CLUSTER_DIAMETER": ['uniform', 80, 120],
    "GR_OVERFLOW":          ['uniform', 1, 1]
}
LHS_SAMPLES = 5000

################################
# Design platform
################################

DESIGN = "ibex"
PLATFORM = "sky130hs"
PLATFORM_CONFIG = "config.mk"
PLATFORM_DIR = "./platforms/" + PLATFORM

NUM_PROCESS = 96

TIME_OUT = 2*60*60 # in seconds

################################
# Clock period
################################

# clock perio
CLK_PERIOD_USE_VALUES = True #invalid if it is an lhs attribute
CLK_PERIOD = 50
CLK_PERIOD_VALUES = [CLK_PERIOD * 0.8, CLK_PERIOD, CLK_PERIOD * 1.2]

CLK_PERIOD_START = 0
CLK_PERIOD_END = 100
CLK_PERIOD_STEP = 10

################################
# Floorplan
################################

# utilization
CORE_UTILIZATION_USE_VALUES = False #invalid if it is an lhs attribute
CORE_UTILIZATION_VALUES = [20, 45] 

CORE_UTILIZATION_START = 15
CORE_UTILIZATION_END = 45
CORE_UTILIZATION_STEP = 5

# aspect ratio
ASPECT_RATIO_USE_VALUES = True #invalid if it is an lhs attribute
ASPECT_RATIO_VALUES = [1] #[0.7, 0.85, 1]

ASPECT_RATIO_START = 0.7
ASPECT_RATIO_END = 1.0
ASPECT_RATIO_STEP = 0.1

# core/dire area
CORE_DIE_MARGIN = 10

# ################################
# # Powerplan
# ################################
# 
# # metal layers used in pdn.cfg
# METALS = ["met1", "met4", "met5"]
# 
# # [start, end, step], order is the same as in METALS var
# METAL_WIDTH = [[0.48, 0.48, 0.01], \
#                [0.95, 0.95, 0.01], \
#                [0.92, 0.92, 0.01]]
# 
# # [start, end, step], order is the same as METALS var
# METAL_PITCH = [[6.5, 6.5, 0.1], \
#                [56.5, 56.5, 0.1], \
#                [40.5, 40.5, 0.1]]


################################
# Placement
################################

# Global placement padding
GP_PAD_USE_VALUES = True #invalid if it is an lhs attribute
GP_PAD_VALUES = [2]

GP_PAD_START = 0
GP_PAD_END = 4
GP_PAD_STEP = 2

# Detail placement padding
DP_PAD_USE_VALUES = True #invalid if it is an lhs attribute
DP_PAD_VALUES = [2]

DP_PAD_START = 0
DP_PAD_END = 4
DP_PAD_STEP = 2


################################
# Cts
################################




################################
# Fastroute
################################

LAYER_ADJUST_USE_VALUES = True #invalid if using LHS
LAYER_ADJUST_VALUES = [0.2, 0.6]

LAYER_ADJUST_START = 0.1
LAYER_ADJUST_END = 1.0
LAYER_ADJUST_STEP = 0.1

################################
# Folder check
################################

try:
    os.mkdir("./data")
except:
    print("Cannot create the data folder, please delete the current data folder")
    sys.exit(1)

try:
    os.mkdir("./designs/" + PLATFORM + "/" + DESIGN + "_parallel/")
except:
    print("Cannot create the design parallel folder")
    sys.exit(1)


################################
# Sample preparation
################################

print("Running " + DESIGN + " deisgn in " + PLATFORM,  file=open("doe.log", "w"))

# Create LHS samples
lhs_knobs = []
if _use_lhs:
    lhd = lhs(len(LHS_ATTRS), samples=LHS_SAMPLES)
    lhs_knobs = np.copy(lhd)
    for idx, lhs_attr in enumerate(LHS_ATTRS.keys()):
        if LHS_ATTRS[lhs_attr][0] == 'uniform':
          # lhs_knobs[:, idx] = uniform(loc=LHS_ATTRS[lhs_attr][1], scale=LHS_ATTRS[lhs_attr][2] - LHS_ATTRS[lhs_attr][1]).ppf(lhd[:, idx])
          lhs_knobs[:, idx] = LHS_ATTRS[lhs_attr][1] + (LHS_ATTRS[lhs_attr][2] - LHS_ATTRS[lhs_attr][1]) * lhd[:, idx]
        elif LHS_ATTRS[lhs_attr][0] == 'truncnorm':
          left_shift = (LHS_ATTRS[lhs_attr][1] - LHS_ATTRS[lhs_attr][3]) / LHS_ATTRS[lhs_attr][4]
          right_shift = (LHS_ATTRS[lhs_attr][2] - LHS_ATTRS[lhs_attr][3]) /LHS_ATTRS[lhs_attr][4]
          lhs_knobs[:, idx] = truncnorm.ppf(lhd[:, idx], a=left_shift, b=right_shift, loc=LHS_ATTRS[lhs_attr][3], scale=LHS_ATTRS[lhs_attr][4])
        elif LHS_ATTRS[lhs_attr][0] == 'norm':
          lhs_knobs[:, idx] = norm(loc=LHS_ATTRS[lhs_attr][1], scale=LHS_ATTRS[lhs_attr][2]).ppf(lhd[:, idx])
        
        value_type = VALUE_TYPE[lhs_attr].split()
        precision = 0
        if value_type[0] == "int":
            precision = 0
        elif value_type[0] == "float":
            precision = int(value_type[1])
        lhs_knobs[:, idx] = np.around(lhs_knobs[:, idx], decimals = precision)
            
# Create non-LHS samples
std_knobs = []
std_attrs_names = []

for idx, attr in enumerate(SWEEPING_ATTRS):
    if _use_lhs and attr in LHS_ATTRS:
        continue
    else:
        std_attrs_names.append(attr)
        if attr+"_USE_VALUES" in globals() and vars()[attr+"_USE_VALUES"]:
            if attr+"_VALUES" not in globals():
                print (attr + "_VALUES variable is not defined but is required")
                sys.exit(0)
            std_knobs.append(np.array(vars()[attr+"_VALUES"]))

            print(attr + " values are defined in " + attr + "_VALUES", file=open("doe.log", "a"))
        elif attr+"_START" in globals() and attr+"_END" in globals() and attr+"_STEP" in globals():
            start       = vars()[attr+"_START"]
            end         = vars()[attr+"_END"]
            step        = vars()[attr+"_STEP"]
            vars()[attr.lower()] = np.arange(start, end + 0.1*step, step), 
            
            value_type = VALUE_TYPE[attr].split()
            precision = 0
            if value_type[0] == "int":
                precision = 0
            elif value_type[0] == "float":
                precision = int(value_type[1])
            std_knobs.append(*np.around(vars()[attr.lower()], decimals = precision))

            print(attr + " values are generated using np.arange", file=open("doe.log", "a"))
        elif attr in globals():
            std_knobs.append(np.array(vars()[attr])) 
            print(attr + " values are defined in " + attr, file=open("doe.log", "a"))
        else:
            print(attr + " variable is not well defined")
            sys.exit(0)


# Create design samples
if _use_lhs and len(LHS_ATTRS) > 0:
    knobs_list_temp = list(product(lhs_knobs, *std_knobs))
    knobs_list_temp = [[*knob[0], *knob[1:]] for knob in knobs_list_temp]
else:
    knobs_list_temp = list(product(*std_knobs))


if _use_lhs:
    attrs_names = [*LHS_ATTRS, *std_attrs_names]
else:
    attrs_names = std_attrs_names

if "PLACE_DENSITY" not in LHS_ATTRS.keys() or not _use_lhs:
    PLACE_DENSITY_VALUES = []
    knobs_list = []
    for knobs in knobs_list_temp:
        core_utilization = knobs[attrs_names.index("CORE_UTILIZATION")]
        gp_pad = knobs[attrs_names.index("GP_PAD")]
    
        if DESIGN == "ibex":
            LB = (core_utilization/100) + (gp_pad * (0.4*(core_utilization/100)-0.01))+0.01
        elif DESIGN == "aes":
            LB = (core_utilization/100) + (gp_pad * (0.5*(core_utilization/100)-0.005))+0.01
        else:
            LB = (core_utilization/100) + (gp_pad * (0.4*(core_utilization/100)-0.01))+0.01
    
        PLACE_DENSITY_VALUES = [LB, LB + 0.1, LB + 0.2]
        for pdv in PLACE_DENSITY_VALUES:
            knobs_list.append([*knobs, round(pdv, 2)])
    
    attrs_names.append("PLACE_DENSITY")
else:
    knobs_list = knobs_list_temp

print("{:d} runs will be executed".format(len(knobs_list)), file=open("doe.log", "a"))

# print("knobs num: clk-{:d}, core_utilization-{:d}, aspect_ratio-{:d}, cell_pad_in_sites_global_placement-{:d}, cell_pad_in_sites_detail_placement-{:d}, place_density-{:d}, layer_adjustment-{:d}".format(len(CLK_VALUES), len(core_utilization), len(aspect_ratio), len(cell_pad_in_sites_global_placement), len(cell_pad_in_sites_detail_placement), len(PLACE_DENSITY_VALUES), len(layer_adjust)))

print(attrs_names, file=open("doe.log", "a"))
for knob in knobs_list:
    print(knob, file=open("doe.log", "a"))
# with open("./scripts/cts.tcl", "r") as rf:
#     filedata = rf.read()
# filedata = re.sub("\n(.*repair_timing -hold.*)", "\n\g<0>\nrepair_timing -setup -max_utilization [expr $::env(PLACE_DENSITY_MAX_POST_HOLD) * 100]", filedata)
# with open("./scripts/cts_doe.tcl", "w") as wf:
#     wf.write(filedata)


# process function
def run_make_design(target):
    p = sp.call(["make", "-f", target], shell=False)

################################
# Sweep designs
################################
# start = time.perf_counter()

knob_iter = 0
while knob_iter < len(knobs_list):
    processes = []
    current_process_num = 0

    for process in range(NUM_PROCESS):
       
        if knob_iter + process >= len(knobs_list):
            break

        knobs = knobs_list[knob_iter + process]
        clock = knobs[attrs_names.index("CLK_PERIOD")]
        core_utilization = knobs[attrs_names.index("CORE_UTILIZATION")]
        core_aspect_ratio = knobs[attrs_names.index("ASPECT_RATIO")]
        cell_pad_in_sites_global_placement = knobs[attrs_names.index("GP_PAD")]
        cell_pad_in_sites_detail_placement = knobs[attrs_names.index("DP_PAD")]
        place_density = knobs[attrs_names.index("PLACE_DENSITY")]
        layer_adjustment = knobs[attrs_names.index("LAYER_ADJUST")]
        flatten = knobs[attrs_names.index("FLATTEN")]
        abc_clock_period_in_ps = knobs[attrs_names.index("ABC_CLOCK_PERIOD")]
        pins_distance = knobs[attrs_names.index("PINS_DISTANCE")]
        cts_cluster_size = knobs[attrs_names.index("CTS_CLUSTER_SIZE")]
        cts_cluster_diameter = knobs[attrs_names.index("CTS_CLUSTER_DIAMETER")]
        gr_overflow = knobs[attrs_names.index("GR_OVERFLOW")]

        core_margin = CORE_DIE_MARGIN

        # Create parallel fastroute scripts
        _platform_fastroute = False
        if os.path.isfile("./platforms/" + PLATFORM + "/fastroute.tcl"):
          _platform_fastroute = True
          with open("./platforms/" + PLATFORM + "/fastroute.tcl", "r") as rf:
            filedata = rf.read()
          filedata = re.sub("(set_global_routing_layer_adjustment .* )[0-9\.]+", "\g<1>{:.1f}".format(layer_adjustment), filedata)
          if int(gr_overflow) == 1:
              filedata = re.sub("(global_route(\s+.*\n)*.*)", "\g<1>  -allow_overflow", filedata)
          with open("./platforms/" + PLATFORM + "/fastroute_{:.1f}_allow_overflow_{:.0f}.tcl".format(layer_adjustment, gr_overflow), "w") as wf:
            wf.write(filedata)

        # Config.mk in platforms
        with open("./platforms/" + PLATFORM + "/" + PLATFORM_CONFIG, "r") as rf:
            filedata = rf.read()
        filedata = re.sub("\n(export CELL_PAD_IN_SITES_GLOBAL_PLACEMENT = ).*", "\n\g<1>{:.0f}".format(cell_pad_in_sites_global_placement), filedata)
        filedata = re.sub("\n(export CELL_PAD_IN_SITES_DETAIL_PLACEMENT = ).*", "\n\g<1>{:.0f}".format(cell_pad_in_sites_detail_placement), filedata)
        filedata = re.sub("\n(export FASTROUTE_TCL .*fastroute).*", "\n\g<1>_{:.1f}_allow_overflow_{:.0f}.tcl".format(layer_adjustment, gr_overflow), filedata)
        with open("./platforms/" + PLATFORM + "/" + PLATFORM_CONFIG[0:-3] + "_gppad_{:.0f}_dppad_{:.0f}_FR_{:.1f}_ALLOW_OVERFLOW_{:.0f}.mk".format(cell_pad_in_sites_global_placement, cell_pad_in_sites_detail_placement, layer_adjustment, gr_overflow), "w") as wf:
            wf.write(filedata)

        # design folder 
        os.mkdir("./designs/" + PLATFORM + "/" + DESIGN + "_parallel/process" + str(process))
        if os.path.isfile("./designs/" + PLATFORM + "/" + DESIGN + "/rules.json"): 
            shutil.copyfile("./designs/" + PLATFORM + "/" + DESIGN + "/rules.json", "./designs/" + PLATFORM + "/" + DESIGN + "_parallel/process" + str(process) + "/rules.json")
        
        with open("./designs/" + PLATFORM + "/" + DESIGN + "/constraint.sdc", "r") as rf:
            filedata = rf.read()
        filedata = re.sub("-period [0-9\.]+", "-period " + str(clock), filedata)
        filedata = re.sub("-waveform [{}\s0-9\.]+\n", "\n", filedata)
        with open("./designs/" + PLATFORM + "/" + DESIGN + "_parallel/process" + str(process) + "/constraint.sdc", "w") as wf:
            wf.write(filedata)
   
        with open("./designs/" + PLATFORM + "/" + DESIGN + "/config.mk", "r") as rf:
            filedata = rf.read()
        filedata = re.sub("\/constraint\.sdc", "_parallel/process" + str(process) + "/constraint.sdc", filedata)
        filedata = re.sub("\n(export FASTROUTE_TCL .*fastroute).*", "\n\g<1>_{:.1f}_allow_overflow_{:.0f}.tcl".format(layer_adjustment, gr_overflow), filedata)
        filedata = re.sub("\n(export DIE_AREA\s+= .*)", "\n#\g<1>", filedata)
        filedata = re.sub("\n(export CORE_AREA\s+= .*)", "\n#\g<1>", filedata)
        filedata = filedata + "\nexport CORE_UTILIZATION = {:.0f}".format(core_utilization)
        filedata = filedata + "\nexport CORE_ASPECT_RATIO = {:.2f}".format(core_aspect_ratio)
        filedata = filedata + "\nexport CORE_MARGIN = {:.0f}".format(core_margin)
        filedata = filedata + "\nexport PLACE_DENSITY = {:.2f}".format(place_density)
        filedata = filedata + "\nexport ABC_CLOCK_PERIOD_IN_PS = {:.1f}".format(abc_clock_period_in_ps)
        with open("./designs/" + PLATFORM + "/" + DESIGN + "_parallel/process" + str(process) + "/config.mk", "w") as wf:
            wf.write(filedata)


        # scripts files:
        with open("./scripts/synth.tcl", "r") as rf:
            filedata = rf.read()
        if int(flatten) == 0:
            filedata = re.sub(" -flatten", "", filedata)
        with open("./scripts/synth_{:.0f}.tcl".format(flatten), "w") as wf:
            wf.write(filedata)

        with open("./scripts/io_placement.tcl", "r") as rf:
            filedata = rf.read()
        filedata = re.sub("(io_placer.*\n(\s+).*\n)", "\g<1>\g<2>-min_distance {:.0f}\n".format(pins_distance), filedata)
        with open("./scripts/io_placement_{:.0f}.tcl".format(pins_distance), "w") as wf:
            wf.write(filedata)

        
        with open("./scripts/cts.tcl", "r") as rf:
            filedata = rf.read()
        filedata = re.sub("(set cluster_size)\s+\d+", "\g<1> {:.0f}".format(cts_cluster_size), filedata)
        filedata = re.sub("(set cluster_diameter)\s+\d+", "\g<1> {:.0f}".format(cts_cluster_diameter), filedata)
        with open("./scripts/cts_size_{:.0f}_diameter_{:.0f}.tcl".format(cts_cluster_size, cts_cluster_diameter), "w") as wf:
            wf.write(filedata)


        if PLATFORM_CONFIG != "config.mk":
          with open(PLATFORM_DIR + "/config.mk", "r") as rf:
              filedata = rf.read()
          filedata = re.sub("include\s+(.*)\.mk", "include \g<1>_gppad_{:.0f}_dppad_{:.0f}_FR_{:.1f}.mk".format(cell_pad_in_sites_global_placement, cell_pad_in_sites_detail_placement, layer_adjustment), filedata)
          with open(PLATFORM_DIR + "/config_gppad_{:.0f}_dppad_{:.0f}_FR_{:.1f}.mk".format(cell_pad_in_sites_global_placement, cell_pad_in_sites_detail_placement, layer_adjustment), "w") as wf:
              wf.write(filedata)

        # create parallel Makefiles
        with open("Makefile", "r") as rf:
            filedata = rf.read()
        filedata = re.sub("results", "results/process" + str(process), filedata)
        filedata = re.sub("logs", "logs/process" + str(process), filedata)
        filedata = re.sub("objects", "objects/process" + str(process), filedata)
        filedata = re.sub("reports", "reports/process" + str(process), filedata)
        filedata = re.sub("include \$\(PLATFORM_DIR\)\/config.*", "include $(PLATFORM_DIR)/config_gppad_{:.0f}_dppad_{:.0f}_FR_{:.1f}_ALLOW_OVERFLOW_{:.0f}.mk".format(cell_pad_in_sites_global_placement, cell_pad_in_sites_detail_placement, layer_adjustment, gr_overflow), filedata)
        filedata = re.sub("\ndefault: finish", "\nDESIGN_CONFIG = ./designs/" + PLATFORM + "/" + DESIGN + "_parallel/process" + str(process) + "/config.mk\ndefault: finish", filedata)
        filedata = re.sub("synth\.tcl", "synth_{:.0f}.tcl".format(flatten), filedata)
        filedata = re.sub("io_placement\.tcl", "io_placement_{:.0f}.tcl".format(pins_distance), filedata)
        filedata = re.sub("cts\.tcl", "cts_size_{:.0f}_diameter_{:.0f}.tcl".format(cts_cluster_size, cts_cluster_diameter), filedata)
        with open("Makefile_process" + str(process), "w") as wf:
            wf.write(filedata)

        p = multiprocessing.Process(target=run_make_design, args=["Makefile_process" + str(process)])
        p.start()
        processes.append(p)
        current_process_num += 1
   
    start = time.time()
    timeout_flag = True
    while time.time() - start <= TIME_OUT:
        if not any(p.is_alive() for p in processes):
            timeout_flag = False
            break
        time.sleep(.1)
    
    if timeout_flag:
        print("time out, killing all unended processes", file=open("doe.log", "a"))
        for p in processes:
            p.terminate()
            p.join()
    else:
        for p in processes:
          p.join()
    
    
    for process in range(current_process_num):
        knobs = knobs_list[knob_iter + process]
        clock = knobs[attrs_names.index("CLK_PERIOD")]
        core_utilization = knobs[attrs_names.index("CORE_UTILIZATION")]
        core_aspect_ratio = knobs[attrs_names.index("ASPECT_RATIO")]
        cell_pad_in_sites_global_placement = knobs[attrs_names.index("GP_PAD")]
        cell_pad_in_sites_detail_placement = knobs[attrs_names.index("DP_PAD")]
        place_density = knobs[attrs_names.index("PLACE_DENSITY")]
        layer_adjustment = knobs[attrs_names.index("LAYER_ADJUST")]
        flatten = knobs[attrs_names.index("FLATTEN")]
        abc_clock_period_in_ps = knobs[attrs_names.index("ABC_CLOCK_PERIOD")]
        pins_distance = knobs[attrs_names.index("PINS_DISTANCE")]
        cts_cluster_size = knobs[attrs_names.index("CTS_CLUSTER_SIZE")]
        cts_cluster_diameter = knobs[attrs_names.index("CTS_CLUSTER_DIAMETER")]
        gr_overflow = knobs[attrs_names.index("GR_OVERFLOW")]
        
        target_folder = "data/" + DESIGN + "_CORE_UTILIZATION_{:.2f}_CLOCK_{:.4f}_ASRATIO_{:.2f}_GPPAD_{:.0f}_DPPAD_{:.0f}_PLACE_DENSITY_{:.2f}_LAYER_ADJUST_{:.1f}_FLATTEN_{:.0f}_ABC_CLOCK_{:.1f}_PINS_DISTANCE_{:.0f}_CTS_SIZE_{:.0f}_CTS_DIAMETER_{:.0f}_ALLOW_OVERFLOW_{:.0f}".format(core_utilization, clock, core_aspect_ratio, cell_pad_in_sites_global_placement, cell_pad_in_sites_detail_placement, place_density, layer_adjustment, flatten, abc_clock_period_in_ps, pins_distance, cts_cluster_size, cts_cluster_diameter, gr_overflow)

        os.mkdir(target_folder)
        
        for data_folder in ["results", "logs", "reports", "objects"]:
            try:
                shutil.move(data_folder + "/process" + str(process), target_folder + "/" + data_folder)
            except:
                print("no " + data_folder + "/process" + str(process) + " is found for current run")
        
        shutil.move("./designs/" + PLATFORM + "/" + DESIGN + "_parallel/process" + str(process), target_folder + "/design")
        shutil.move("Makefile_process" + str(process), target_folder + "/Makefile")

        shutil.copyfile("./platforms/" + PLATFORM + "/" + PLATFORM_CONFIG[0:-3] + "_gppad_{:.0f}_dppad_{:.0f}_FR_{:.1f}_ALLOW_OVERFLOW_{:.0f}.mk".format(cell_pad_in_sites_global_placement, cell_pad_in_sites_detail_placement, layer_adjustment, gr_overflow), target_folder + "/" + PLATFORM_CONFIG[0:-3] + "_gppad_{:.0f}_dppad_{:.0f}_FR_{:.1f}_ALLOW_OVERFLOW_{:.0f}.mk".format(cell_pad_in_sites_global_placement, cell_pad_in_sites_detail_placement, layer_adjustment, gr_overflow))
        shutil.copyfile("./platforms/" + PLATFORM + "/" + "config_gppad_{:.0f}_dppad_{:.0f}_FR_{:.1f}_ALLOW_OVERFLOW_{:.0f}.mk".format(cell_pad_in_sites_global_placement, cell_pad_in_sites_detail_placement, layer_adjustment, gr_overflow), target_folder + "/config_gppad_{:.0f}_dppad_{:.0f}_FR_{:.1f}_ALLOW_OVERFLOW_{:.0f}.mk".format(cell_pad_in_sites_global_placement, cell_pad_in_sites_detail_placement, layer_adjustment, gr_overflow))
    
    knob_iter += current_process_num
