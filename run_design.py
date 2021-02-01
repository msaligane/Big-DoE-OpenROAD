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

################################
# Design platform
################################

DESIGN = "ibex"
PLATFORM = "sky130"
PLATFORM_CONFIG = "config_hd.mk"

TECH_LEF = "platforms/" + PLATFORM + "/lef/sky130_fd_sc_hd.tlef"
SITE_NAME = "unithd"
PDN_CFG = "pdn.cfg"

NUM_PROCESS = 8

################################
# Clock period
################################

# clock period
CLK_PERIOD = 9
CLK_VALUES = [CLK_PERIOD * 0.8, CLK_PERIOD, CLK_PERIOD * 1.2]

CLK_STEP = 0.1
CLK_START = 5 # in ns
CLK_END = 7 # in ns
CLK_VARIATIONS = 3 # step 1ps
# print("CLK_START:{:.3f}ns, CLK_STEP:{:.3f}ns, CLK_END:{:.3f}ns".format(CLK_START, CLK_STEP, CLK_END))


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

SETUP_FIX = [1]

################################
# Data preparation
################################


with open(TECH_LEF, "r") as rf:
    filedata = rf.read()
    site_group = re.search("SITE "+SITE_NAME+"\n(.*\n)*.+SIZE\s+(.+)\s+BY\s+(.+)\s+.+(.*\n)*END "+SITE_NAME+"\n", filedata)
    if site_group:
        SITE_X = float(site_group.group(2))
        SITE_Y = float(site_group.group(3))
        print("SITE found, SITE_X:{:.2f}, SIZE_Y:{:.2f}".format(SITE_X, SITE_Y))
    else:
        print("SITE information is not found")

# try:
#     for process_folder in glob.glob("./designs/" + PLATFORM + "/*parallel*"):
#         shutil.rmtree(process_folder)
#     for process_folder in glob.glob("./*/process*"):
#         shutil.rmtree(process_folder)
#     for process_file in glob.glob("./*process*"):
#         os.remove(process_file)
# 
#     if os.path.exists("./data"):
#         shutil.rmtree("./data")
# except:
#     print("Cannot remove process folder" )
#     sys.exit(1)

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

# generate clock groups, not used
clk_pool_temp = np.arange(CLK_START, CLK_END+0.1*CLK_STEP, CLK_STEP)
clk_pool = [np.arange(clk-0.001*(CLK_VARIATIONS//2), clk+0.001*(CLK_VARIATIONS//2) + 0.1*0.001, 0.001) for clk in clk_pool_temp]
clk_pool = np.concatenate(clk_pool, axis=0)

clk_iters = (len(clk_pool) // NUM_PROCESS) + 1
clk_final = len(clk_pool) % NUM_PROCESS

# # generate pdn design configs
# pdn_designs = []
# metal_width_ranges = []
# metal_pitch_ranges = []
# for idx, metal in enumerate(METALS):
#     metal_width_ranges.append(np.arange(METAL_WIDTH[idx][0], METAL_WIDTH[idx][1] + 0.1*METAL_WIDTH[idx][2], METAL_WIDTH[idx][2]))
#     metal_pitch_ranges.append(np.arange(METAL_PITCH[idx][0], METAL_PITCH[idx][1] + 0.1*METAL_PITCH[idx][2], METAL_PITCH[idx][2]))
#     
# metal_width_iters = list(product(*metal_width_ranges))
# metal_pitch_iters = list(product(*metal_pitch_ranges))
# 
# for width_iter in metal_width_iters:
#     for pitch_iter in metal_pitch_iters:
#         pdn_designs.append(list(width_iter) + list(pitch_iter))


core_utilization = np.arange(CORE_CORE_UTILIZATION_START, CORE_CORE_UTILIZATION_END + 0.1*CORE_CORE_UTILIZATION_STEP, CORE_CORE_UTILIZATION_STEP)

aspect_ratio = np.array(ASPECT_RATIO_VALUES)

cell_pad_in_sites_global_placement = np.arange(CELL_PAD_IN_SITES_GLOBAL_PLACEMENT_START, \
                                                CELL_PAD_IN_SITES_GLOBAL_PLACEMENT_END + 0.1*CELL_PAD_IN_SITES_GLOBAL_PLACEMENT_STEP, \
                                                CELL_PAD_IN_SITES_GLOBAL_PLACEMENT_STEP)
cell_pad_in_sites_detail_placement = np.arange(CELL_PAD_IN_SITES_DETAIL_PLACEMENT_START, \
                                                CELL_PAD_IN_SITES_DETAIL_PLACEMENT_END + 0.1*CELL_PAD_IN_SITES_DETAIL_PLACEMENT_STEP, \
                                                CELL_PAD_IN_SITES_DETAIL_PLACEMENT_STEP)


# place_density = np.arange(PLACE_DENSITY_START, \
#                             PLACE_DENSITY_END + 0.1*PLACE_DENSITY_STEP, \
#                             PLACE_DENSITY_STEP)

setup_fix = np.array(SETUP_FIX)

knobs = [CLK_VALUES, core_utilization, aspect_ratio, cell_pad_in_sites_global_placement, cell_pad_in_sites_detail_placement, setup_fix]
knobs_list_temp = list(product(*knobs))

PLACE_DENSITY_VALUES = []
knobs_list = []
for knobs in knobs_list_temp:
    util = knobs[1]
    gppad = knobs[3]

    if DESIGN == "ibex":
        LB = util + (gppad * (0.4*util-0.01))+0.01
    elif DESIGN == "aes":
        LB = util + (gppad * (0.5*util-0.005))+0.01
    
    PLACE_DENSITY_VALUES = [LB, LB + 0.1, LB + 0.2]
    for pdv in PLACE_DENSITY_VALUES:
        knobs_list.append([*knobs[0:-1], pdv, knobs[-1]])

print("{:d} runs will be executed".format(len(knobs_list)))

print("knobs num: clk-{:.0f}, core_utilization-{:.0f}, aspect_ratio-{:.0f}, cell_pad_in_sites_global_placement-{:.0f}, cell_pad_in_sites_detail_placement-{:.0f}, place_density-{:.0f}".format(len(CLK_VALUES), len(core_utilization), len(aspect_ratio), len(cell_pad_in_sites_global_placement), len(cell_pad_in_sites_detail_placement), len(PLACE_DENSITY_VALUES)))


with open("./scripts/cts.tcl", "r") as rf:
    filedata = rf.read()
filedata = re.sub("\n(.*repair_timing -hold.*)", "\n\g<0>\nrepair_timing -setup -max_utilization [expr $::env(PLACE_DENSITY_MAX_POST_HOLD) * 100]", filedata)
with open("./scripts/cts_doe.tcl", "w") as wf:
    wf.write(filedata)

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
        clock= knobs[0]
        core_utilization = knobs[1]
        core_aspect_ratio = knobs[2]
        cell_pad_in_sites_global_placement = knobs[3]
        cell_pad_in_sites_detail_placement = knobs[4]
        place_density = knobs[5]
        setup_fix = knobs[6]

        core_margin = CORE_DIE_MARGIN

        # Config.mk in platforms
        with open("./platforms/" + PLATFORM + "/" + PLATFORM_CONFIG, "r") as rf:
            filedata = rf.read()
        filedata = re.sub("\n(export CELL_PAD_IN_SITES_GLOBAL_PLACEMENT = ).*", "\n\g<1>{:.0f}".format(cell_pad_in_sites_global_placement), filedata)
        filedata = re.sub("\n(export CELL_PAD_IN_SITES_DETAIL_PLACEMENT = ).*", "\n\g<1>{:.0f}".format(cell_pad_in_sites_detail_placement), filedata)
        with open("./platforms/" + PLATFORM + "/" + PLATFORM_CONFIG[0:-3] + "_gppad_{:.0f}_dppad_{:.0f}.mk".format(cell_pad_in_sites_global_placement, cell_pad_in_sites_detail_placement), "w") as wf:
            wf.write(filedata)
        
        # design folder 
        os.mkdir("./designs/" + PLATFORM + "/" + DESIGN + "_parallel/process" + str(process))
        if os.path.isfile("./designs/" + PLATFORM + "/" + DESIGN + "/rules.json"): 
            shutil.copyfile("./designs/" + PLATFORM + "/" + DESIGN + "/rules.json", "./designs/" + PLATFORM + "/" + DESIGN + "_parallel/process" + str(process) + "/rules.json")
        
        with open("./designs/" + PLATFORM + "/" + DESIGN + "/constraint.sdc", "r") as rf:
            filedata = rf.read()
        filedata = re.sub("-period .*", "-period " + str(clock), filedata)
        with open("./designs/" + PLATFORM + "/" + DESIGN + "_parallel/process" + str(process) + "/constraint.sdc", "w") as wf:
            wf.write(filedata)
   
        with open("./designs/" + PLATFORM + "/" + DESIGN + "/config.mk", "r") as rf:
            filedata = rf.read()
        filedata = re.sub("\/constraint\.sdc", "_parallel/process" + str(process) + "/constraint.sdc", filedata)
        filedata = re.sub("\n(export DIE_AREA\s+= .*)", "\n#\g<0>", filedata)
        filedata = re.sub("\n(export CORE_AREA\s+= .*)", "\n#\g<0>", filedata)
        filedata = filedata + "\nexport CORE_UTILIZATION = {:.0f}".format(core_utilization)
        filedata = filedata + "\nexport CORE_ASPECT_RATIO = {:.2f}".format(core_aspect_ratio)
        filedata = filedata + "\nexport CORE_MARGIN = {:.0f}".format(core_margin)
        filedata = filedata + "\nexport PLACE_DENSITY = {:.2f}".format(place_density)
        with open("./designs/" + PLATFORM + "/" + DESIGN + "_parallel/process" + str(process) + "/config.mk", "w") as wf:
            wf.write(filedata)

        if re.search("(130|12)", PLATFORM):
            with open("./platforms/" + PLATFORM + "/config.mk", "r") as rf:
                filedata = rf.read()
            filedata = re.sub("include\s+(.*)\.mk", "include \g<1>_gppad_{:.0f}_dppad_{:.0f}.mk".format(cell_pad_in_sites_global_placement, cell_pad_in_sites_detail_placement), filedata)
            with open("./platforms/" + PLATFORM + "/config_gppad_{:.0f}_dppad_{:.0f}.mk".format(cell_pad_in_sites_global_placement, cell_pad_in_sites_detail_placement), "w") as wf:
                wf.write(filedata)

        # create multiple Makefiles
        with open("Makefile", "r") as rf:
            filedata = rf.read()
        filedata = re.sub("results", "results/process" + str(process), filedata)
        filedata = re.sub("logs", "logs/process" + str(process), filedata)
        filedata = re.sub("objects", "objects/process" + str(process), filedata)
        filedata = re.sub("reports", "reports/process" + str(process), filedata)
        filedata = re.sub("include \$\(PLATFORM_DIR\)\/config.*", "include $(PLATFORM_DIR)/config_gppad_{:.0f}_dppad_{:.0f}.mk".format(cell_pad_in_sites_global_placement, cell_pad_in_sites_detail_placement), filedata)
        filedata = re.sub("\ndefault: finish", "\nDESIGN_CONFIG = ./designs/" + PLATFORM + "/" + DESIGN + "_parallel/process" + str(process) + "/config.mk\ndefault: finish", filedata)
        if setup_fix == 1:
            filedata = re.sub("cts\.tcl", "cts_doe.tcl", filedata)
        with open("Makefile_process" + str(process), "w") as wf:
            wf.write(filedata)

        p = multiprocessing.Process(target=run_make_design, args=["Makefile_process" + str(process)])
        p.start()
        processes.append(p)
        current_process_num += 1
   
    
    for p in processes:
        p.join()
   

    for process in range(current_process_num):
        knobs = knobs_list[knob_iter + process]
        clock= knobs[0]
        core_utilization = knobs[1]
        core_aspect_ratio = knobs[2]
        cell_pad_in_sites_global_placement = knobs[3]
        cell_pad_in_sites_detail_placement = knobs[4]
        place_density = knobs[5]
        setup_fix = knobs[6]

        target_folder = "data/" + DESIGN + "_CORE_UTILIZATION_{:.2f}_CLOCK_{:.4f}_ASRATIO_{:.4f}_GPPAD_{:.0f}_DPPAD_{:.0f}_PLACE_DENSITY_{:.2f}_SETUPFIX_{:d}".format(core_utilization, clock, core_aspect_ratio, cell_pad_in_sites_global_placement, cell_pad_in_sites_detail_placement, place_density, setup_fix)

        os.mkdir(target_folder)
        
        for data_folder in ["results", "logs", "reports", "objects"]:
            try:
                shutil.move(data_folder + "/process" + str(process), target_folder + "/" + data_folder)
            except:
                print("no " + data_folder + "/process" + str(process) + " is found for current run")
        
        shutil.move("./designs/" + PLATFORM + "/" + DESIGN + "_parallel/process" + str(process), target_folder + "/design")
        shutil.move("Makefile_process" + str(process), target_folder + "/Makefile")

        shutil.copyfile("./platforms/" + PLATFORM + "/" + PLATFORM_CONFIG[0:-3] + "_gppad_{:.0f}_dppad_{:.0f}.mk".format(cell_pad_in_sites_global_placement, cell_pad_in_sites_detail_placement), target_folder + "/" + PLATFORM_CONFIG[0:-3] + "_gppad_{:.0f}_dppad_{:.0f}.mk".format(cell_pad_in_sites_global_placement, cell_pad_in_sites_detail_placement))
        shutil.copyfile("./platforms/" + PLATFORM + "/" + "config_gppad_{:.0f}_dppad_{:.0f}.mk".format(cell_pad_in_sites_global_placement, cell_pad_in_sites_detail_placement), target_folder + "/config_gppad_{:.0f}_dppad_{:.0f}.mk".format(cell_pad_in_sites_global_placement, cell_pad_in_sites_detail_placement))
    
    knob_iter += current_process_num
