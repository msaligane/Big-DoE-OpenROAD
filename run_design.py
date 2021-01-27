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

DESIGN = "gcd"
PLATFORM = "sky130"
PLATFORM_CONFIG = "config_hd.mk"

TECH_LEF = "platforms/" + PLATFORM + "/lef/sky130_fd_sc_hd.tlef"
SITE_NAME = "unithd"
PDN_CFG = "pdn.cfg"

NUM_PROCESS = 7

################################
# Floorplan
################################

# utilization
UTIL_START = 0.8
UTIL_END = 0.8
UTIL_STEP = 0.1

# aspect ratio
ASPECT_RATIO_START = 1.2
ASPECT_RATIO_STOP = 1.2
ASPECT_RATIO_STEP = 0.1

# core/dire area
CORE_DIE_SPACING = 10
CORE_AREA = 40000 # in um^2 

# clock period
CLK_STEP = 0.1
CLK_START = 1 # in ns
CLK_END = 2 # in ns
CLK_VARIATIONS = 5 # step 1ps
# print("CLK_START:{:.3f}ns, CLK_STEP:{:.3f}ns, CLK_END:{:.3f}ns".format(CLK_START, CLK_STEP, CLK_END))

################################
# Powerplan
################################

# metal layers used in pdn.cfg
METALS = ["met1", "met4", "met5"]

# [start, end, step], order is the same as in METALS var
METAL_WIDTH = [[0.48, 0.48, 0.01], \
               [0.95, 0.95, 0.01], \
               [0.92, 0.92, 0.01]]

# [start, end, step], order is the same as METALS var
METAL_PITCH = [[6.5, 6.5, 0.1], \
               [56.5, 56.5, 0.1], \
               [40.5, 40.5, 0.1]]

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

try:
    for process_folder in glob.glob("./designs/" + PLATFORM + "/*parallel*"):
        shutil.rmtree(process_folder)
    for process_folder in glob.glob("./*/process*"):
        shutil.rmtree(process_folder)
    for process_file in glob.glob("./*process*"):
        os.remove(process_file)

    if os.path.exists("./data"):
        shutil.rmtree("./data")
except:
    print("Cannot remove process folder" )
    sys.exit(1)

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

# generate clock groups

clk_pool_temp = np.arange(CLK_START, CLK_END+0.1*CLK_STEP, CLK_STEP)
clk_pool = [np.arange(clk-0.001*(CLK_VARIATIONS//2), clk+0.001*(CLK_VARIATIONS//2) + 0.1*0.001, 0.001) for clk in clk_pool_temp]
clk_pool = np.concatenate(clk_pool, axis=0)

clk_iters = (len(clk_pool) // NUM_PROCESS) + 1
clk_final = len(clk_pool) % NUM_PROCESS

# generate pdn design configs
pdn_designs = []
metal_width_ranges = []
metal_pitch_ranges = []
for idx, metal in enumerate(METALS):
    metal_width_ranges.append(np.arange(METAL_WIDTH[idx][0], METAL_WIDTH[idx][1] + 0.1*METAL_WIDTH[idx][2], METAL_WIDTH[idx][2]))
    metal_pitch_ranges.append(np.arange(METAL_PITCH[idx][0], METAL_PITCH[idx][1] + 0.1*METAL_PITCH[idx][2], METAL_PITCH[idx][2]))
    
metal_width_iters = list(product(*metal_width_ranges))
metal_pitch_iters = list(product(*metal_pitch_ranges))

for width_iter in metal_width_iters:
    for pitch_iter in metal_pitch_iters:
        pdn_designs.append(list(width_iter) + list(pitch_iter))

# process function
def run_make_design(target):
    p = sp.call(["make", "-f", target, "synth"], shell=False)

################################
# Sweep designs
################################
# start = time.perf_counter()

for aspect_ratio in np.arange(ASPECT_RATIO_START, ASPECT_RATIO_STOP + 0.1*ASPECT_RATIO_STEP, ASPECT_RATIO_STEP):
    core_x = (math.sqrt(CORE_AREA / aspect_ratio) // SITE_X ) * SITE_X
    core_y = (core_x * aspect_ratio // SITE_Y) * SITE_Y
    cd_x_dist = (CORE_DIE_SPACING // SITE_X ) * SITE_X
    cd_y_dist = (CORE_DIE_SPACING // SITE_Y ) * SITE_Y
        
    for UTIL in np.arange(UTIL_START, UTIL_END + 0.1*UTIL_STEP, UTIL_STEP):
    
        for pdn_design in pdn_designs:
            with open("./platforms/" + PLATFORM + "/" + PDN_CFG, "r") as rf:
                filedata = rf.read()
            for idx, metal in enumerate(METALS):
                filedata = re.sub(metal + "\s+{width\s+([0-9\.]+)\s+pitch\s+([0-9\.]+)\s+offset\s+([0-9\.]+)}", metal + " {{width {:.2f} pitch {:.2f} offset \g<3>}}".format(pdn_design[idx], pdn_design[len(METALS)+idx]), filedata)
            with open("./platforms/" + PLATFORM + "/" + PDN_CFG, "w") as wf:
                    wf.write(filedata)

            with open("./platforms/" + PLATFORM + "/" + PLATFORM_CONFIG, "r") as rf:
                filedata = rf.read()
            filedata = re.sub("\n(export PLACE_DENSITY \?= ).*", "\n\g<1>{:.2f}".format(UTIL), filedata)
            with open("./platforms/" + PLATFORM + "/" + PLATFORM_CONFIG, "w") as wf:
                wf.write(filedata)
    
            for clk_iter in range(clk_iters):
                processes = []
                current_process_num = 0
                for process in range(1, NUM_PROCESS + 1):
                    if clk_iter == clk_iters - 1 and process > clk_final:
                        break
                    # create multiple design folders
                    # CLK_PERIOD = clk_iter * CLK_STEP * NUM_PROCESS + process * CLK_STEP + CLK_START
                    CLK_PERIOD = clk_pool[clk_iter*NUM_PROCESS + process - 1]
                    print("@@@ Running CLK_PERIOD = {:.3f}".format(CLK_PERIOD))

                    os.mkdir("./designs/" + PLATFORM + "/" + DESIGN + "_parallel/process" + str(process))
                    
                    shutil.copyfile("./designs/" + PLATFORM + "/" + DESIGN + "/rules.json", "./designs/" + PLATFORM + "/" + DESIGN + "_parallel/process" + str(process) + "/rules.json")
                    
                    with open("./designs/" + PLATFORM + "/" + DESIGN + "/constraint.sdc", "r") as rf:
                        filedata = rf.read()
                    filedata = re.sub("-period .*", "-period " + str(CLK_PERIOD), filedata)
                    with open("./designs/" + PLATFORM + "/" + DESIGN + "_parallel/process" + str(process) + "/constraint.sdc", "w") as wf:
                        wf.write(filedata)
        
                    with open("./designs/" + PLATFORM + "/" + DESIGN + "/config.mk", "r") as rf:
                        filedata = rf.read()
                    filedata = re.sub("\/constraint\.sdc", "_parallel/process" + str(process) + "/constraint.sdc", filedata)
                    filedata = re.sub("(DIE_AREA\s+= 0 0 ).* .*\n", "\g<1>{:.2f} {:.2f}\n".format(core_x + cd_x_dist, core_y + cd_y_dist), filedata)
                    filedata = re.sub("(CORE_AREA\s+=) .* .* .* .*\n", "\g<1> {:.2f} {:.2f} {:.2f} {:.2f}\n".format(cd_x_dist, cd_y_dist, core_x, core_y), filedata)
                    filedata 
                    with open("./designs/" + PLATFORM + "/" + DESIGN + "_parallel/process" + str(process) + "/config.mk", "w") as wf:
                        wf.write(filedata)

                    # create multiple Makefiles
                    with open("Makefile", "r") as rf:
                        filedata = rf.read()
                    filedata = re.sub("results", "results/process" + str(process), filedata)
                    filedata = re.sub("logs", "logs/process" + str(process), filedata)
                    filedata = re.sub("objects", "objects/process" + str(process), filedata)
                    filedata = re.sub("reports", "reports/process" + str(process), filedata)
                    filedata = re.sub("@1", "./designs/" + PLATFORM + "/" + DESIGN + "_parallel/process" + str(process) + "/config.mk", filedata)
                    with open("Makefile_process" + str(process), "w") as wf:
                        wf.write(filedata)
        
                    # Run parallel jobs

                    p = multiprocessing.Process(target=run_make_design, args=["Makefile_process" + str(process)])
                    p.start()
                    processes.append(p)
                    current_process_num += 1
        
                for p in processes:
                    p.join()
        
                for process in range(1, current_process_num + 1):
                    CLK_PERIOD = clk_pool[clk_iter*NUM_PROCESS + process - 1]
                    aspect_ratio = core_y / core_x
                    pdn_info = "_".join(METALS) + "_" + "_".join(["{:.2f}".format(pdn_val) for pdn_val in pdn_design])

                    os.mkdir("data/" + DESIGN + "_UTIL_{:.2f}".format(UTIL) + "_CLK_PERIOD_{:.3f}".format(CLK_PERIOD) + "_ASRATIO_{:.4f}".format(aspect_ratio) + "_PDN_" + pdn_info)
                    
                    for data_folder in ["results", "logs", "reports", "objects"]:
                        shutil.move(data_folder + "/process" + str(process), "data/" + DESIGN + "_UTIL_{:.2f}".format(UTIL) + "_CLK_PERIOD_{:.3f}".format(CLK_PERIOD) + "_ASRATIO_{:.4f}".format(aspect_ratio) + "_PDN_" + pdn_info + "/" + data_folder)
                    
                    shutil.move("./designs/" + PLATFORM + "/" + DESIGN + "_parallel/process" + str(process), "data/" + DESIGN + "_UTIL_{:.2f}".format(UTIL) + "_CLK_PERIOD_{:.3f}".format(CLK_PERIOD) + "_ASRATIO_{:.4f}".format(aspect_ratio) + "_PDN_" + pdn_info + "/design")
                    shutil.move("Makefile_process" + str(process), "data/" + DESIGN + "_UTIL_{:.2f}".format(UTIL) + "_CLK_PERIOD_{:.3f}".format(CLK_PERIOD) + "_ASRATIO_{:.4f}".format(aspect_ratio) + "_PDN_" + pdn_info + "/Makefile")

                    shutil.copyfile("./platforms/" + PLATFORM + "/" + PDN_CFG, "data/" + DESIGN + "_UTIL_{:.2f}".format(UTIL) + "_CLK_PERIOD_{:.3f}".format(CLK_PERIOD) + "_ASRATIO_{:.4f}".format(aspect_ratio) + "_PDN_" + pdn_info + "/" + PDN_CFG)
                    shutil.copyfile("./platforms/" + PLATFORM + "/" + PLATFORM_CONFIG, "data/" + DESIGN + "_UTIL_{:.2f}".format(UTIL) + "_CLK_PERIOD_{:.3f}".format(CLK_PERIOD) + "_ASRATIO_{:.4f}".format(aspect_ratio) + "_PDN_" + pdn_info + "/" + PLATFORM_CONFIG)

                # finish = time.perf_counter()
                # print("Finished in {:.2f} seconds".format(finish-start))
                # sys.exit(0)
