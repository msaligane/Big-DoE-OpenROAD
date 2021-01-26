import glob
import re
import os
import numpy as np
import shutil
import subprocess as sp
import sys
import math
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

NUM_THREAD = 10

################################
# Floorplan
################################

# utilization
UTIL_START = 0.6
UTIL_END = 0.8
UTIL_STEP = 0.01

# aspect ratio
ASPECT_RATIO_START = 0.8
ASPECT_RATIO_STOP = 1.5
ASPECT_RATIO_STEP = 0.1

# core/dire area
CORE_DIE_SPACING = 10
CORE_AREA = 40000 # in um^2 

# clock period
CLK_STEP = 0.001
CLK_START = 1 # in ns
CLK_END = 2 # in ns
# print("CLK_START:{:.3f}ns, CLK_STEP:{:.3f}ns, CLK_END:{:.3f}ns".format(CLK_START, CLK_STEP, CLK_END))

################################
# Powerplan
################################

# metal layers used in pdn.cfg
METALS = ["met1", "met4", "met5"]

# [start, end, step], order is the same as in METALS var
METAL_WIDTH = [[0.48, 0.50, 0.01], \
               [0.95, 0.97, 0.01], \
               [0.92, 0.94, 0.01]]

# [start, end, step], order is the same as METALS var
METAL_PITCH = [[6.5, 6.8, 0.1], \
               [56.5, 56.8, 0.1], \
               [40.5, 40.8, 0.1]]

################################
# Data preparation
################################

clk_iters = math.ceil((CLK_END - CLK_START) / (CLK_STEP * NUM_THREAD))

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
    for thread_folder in glob.glob("./designs/" + PLATFORM + "/*parallel*"):
        shutil.rmtree(thread_folder)
    for thread_folder in glob.glob("./*/thread*"):
        shutil.rmtree(thread_folder)
    for thread_file in glob.glob("./*thread*"):
        os.remove(thread_file)
except:
    print("Cannot remove thread folder" )
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

################################
# Sweep designs
################################
for aspect_ratio in np.arange(ASPECT_RATIO_START, ASPECT_RATIO_STOP, ASPECT_RATIO_STEP):
    core_x = (math.sqrt(CORE_AREA / aspect_ratio) // SITE_X ) * SITE_X
    core_y = (core_x * aspect_ratio // SITE_Y) * SITE_Y
    cd_x_dist = (CORE_DIE_SPACING // SITE_X ) * SITE_X
    cd_y_dist = (CORE_DIE_SPACING // SITE_Y ) * SITE_Y

        
    for UTIL in np.arange(UTIL_START, UTIL_END, UTIL_STEP):
    
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
                current_thread_num = 0
                for thread in range(1, NUM_THREAD + 1):
                    
                    # create multiple design folders
                    CLK_PERIOD = clk_iter * CLK_STEP * NUM_THREAD + thread * CLK_STEP + CLK_START

                    os.mkdir("./designs/" + PLATFORM + "/" + DESIGN + "_parallel/thread" + str(thread))
                    
                    shutil.copyfile("./designs/" + PLATFORM + "/" + DESIGN + "/rules.json", "./designs/" + PLATFORM + "/" + DESIGN + "_parallel/thread" + str(thread) + "/rules.json")
                    
                    with open("./designs/" + PLATFORM + "/" + DESIGN + "/constraint.sdc", "r") as rf:
                        filedata = rf.read()
                    filedata = re.sub("-period .*", "-period " + str(CLK_PERIOD), filedata)
                    with open("./designs/" + PLATFORM + "/" + DESIGN + "_parallel/thread" + str(thread) + "/constraint.sdc", "w") as wf:
                        wf.write(filedata)
        
                    with open("./designs/" + PLATFORM + "/" + DESIGN + "/config.mk", "r") as rf:
                        filedata = rf.read()
                    filedata = re.sub("\/constraint\.sdc", "_parallel/thread" + str(thread) + "/constraint.sdc", filedata)
                    filedata = re.sub("(DIE_AREA\s+= 0 0 ).* .*\n", "\g<1>{:.2f} {:.2f}\n".format(core_x + cd_x_dist, core_y + cd_y_dist), filedata)
                    filedata = re.sub("(CORE_AREA\s+=) .* .* .* .*\n", "\g<1> {:.2f} {:.2f} {:.2f} {:.2f}\n".format(cd_x_dist, cd_y_dist, core_x, core_y), filedata)
                    filedata 
                    with open("./designs/" + PLATFORM + "/" + DESIGN + "_parallel/thread" + str(thread) + "/config.mk", "w") as wf:
                        wf.write(filedata)

                    # create multiple Makefiles
                    with open("Makefile", "r") as rf:
                        filedata = rf.read()
                    filedata = re.sub("results", "results/thread" + str(thread), filedata)
                    filedata = re.sub("logs", "logs/thread" + str(thread), filedata)
                    filedata = re.sub("objects", "objects/thread" + str(thread), filedata)
                    filedata = re.sub("reports", "reports/thread" + str(thread), filedata)
                    filedata = re.sub("@1", "./designs/" + PLATFORM + "/" + DESIGN + "_parallel/thread" + str(thread) + "/config.mk", filedata)
                    with open("Makefile_thread" + str(thread), "w") as wf:
                        wf.write(filedata)
        
                    # Run parallel jobs

                    if CLK_PERIOD <= CLK_END:
                        p = sp.Popen(["make", "-f", "Makefile_thread" + str(thread)]) 
                        processes.append(p)
                        current_thread_num += 1
        
                for p in processes:
                    p.wait()
        
                for thread in range(1, current_thread_num + 1):
                    CLK_PERIOD = clk_iter * CLK_STEP * NUM_THREAD + thread * CLK_STEP + CLK_START
                    aspect_ratio = core_y / core_x
                    os.mkdir("data/" + DESIGN + "_UTIL_{:.2f}".format(UTIL) + "_CLK_PERIOD_{:.3f}".format(CLK_PERIOD) + "_ASRATIO_{:.4f}".format(aspect_ratio))
                    
                    shutil.move("results/thread" + str(thread), "data/" + DESIGN + "_UTIL_{:.2f}".format(UTIL) + "_CLK_PERIOD_{:.3f}".format(CLK_PERIOD) + "_ASRATIO_{:.4f}".format(aspect_ratio) + "/results")
                    shutil.move("logs/thread" + str(thread), "data/" + DESIGN + "_UTIL_{:.2f}".format(UTIL) + "_CLK_PERIOD_{:.3f}".format(CLK_PERIOD) + "_ASRATIO_{:.4f}".format(aspect_ratio) + "/logs")
                    shutil.move("reports/thread" + str(thread), "data/" + DESIGN + "_UTIL_{:.2f}".format(UTIL) + "_CLK_PERIOD_{:.3f}".format(CLK_PERIOD) + "_ASRATIO_{:.4f}".format(aspect_ratio) + "/reports")
                    shutil.move("objects/thread" + str(thread), "data/" + DESIGN + "_UTIL_{:.2f}".format(UTIL) + "_CLK_PERIOD_{:.3f}".format(CLK_PERIOD) + "_ASRATIO_{:.4f}".format(aspect_ratio) + "/objects")
                    shutil.move("./designs/" + PLATFORM + "/" + DESIGN + "_parallel/thread" + str(thread), "data/" + DESIGN + "_UTIL_{:.2f}".format(UTIL) + "_CLK_PERIOD_{:.3f}".format(CLK_PERIOD) + "_ASRATIO_{:.4f}".format(aspect_ratio) + "/design")
                    shutil.move("Makefile_thread" + str(thread), "data/" + DESIGN + "_UTIL_{:.2f}".format(UTIL) + "_CLK_PERIOD_{:.3f}".format(CLK_PERIOD) + "_ASRATIO_{:.4f}".format(aspect_ratio) + "/Makefile")

                    shutil.copyfile("./platforms/" + PLATFORM + "/" + PDN_CFG, "data/" + DESIGN + "_UTIL_{:.2f}".format(UTIL) + "_CLK_PERIOD_{:.3f}".format(CLK_PERIOD) + "_ASRATIO_{:.4f}".format(aspect_ratio) + "/" + PDN_CFG)
                    shutil.copyfile("./platforms/" + PLATFORM + "/" + PLATFORM_CONFIG, "data/" + DESIGN + "_UTIL_{:.2f}".format(UTIL) + "_CLK_PERIOD_{:.3f}".format(CLK_PERIOD) + "_ASRATIO_{:.4f}".format(aspect_ratio) + "/" + PLATFORM_CONFIG)

                sys.exit(0)
