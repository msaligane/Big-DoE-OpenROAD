import re
import glob

PLATFORM = "sky130"
DESIGN = "gcd"

design_list = glob.glob("data_bu/*")

all_results = open("all_results", "w")

for design in design_list:
    log_f = design + "/logs"
    object_f = design + "/objects"
    reports_f = design + "/reports"
    results_f = design + "/results"


    with open(reports_f + "/" + PLATFORM + "/" + DESIGN + "/6_final_report.rpt", "r") as rf:
        filedata = rf.read()

    tns_group = re.search("tns (.*)", filedata)
    wns_group = re.search("wns (.*)", filedata)
    power_group = re.search("report_power(\n.*)*(Total .*)", filedata)
    instance_group = re.search("instance_count(\n.*)\n(\d+)", filedata)


    try:
        tns = tns_group.group(1)
        wns = wns_group.group(1)
        
        power_all = power_group.group(2).split()
        internal_poewr = power_all[1]
        switching_power = power_all[2]
        leakage_power = power_all[3]
        total_power = power_all[4]

        instance = instance_group.group(2)
    except:
        print("Cannot extract valid data from: " + design)

    all_results.write(design + "\n")
    all_results.write("tns: " + tns + "\n")
    all_results.write("wns: " + wns + "\n")
    all_results.write("internal_poewr: " + internal_poewr + "\n")
    all_results.write("switching_power: " + switching_power + "\n")
    all_results.write("leakage_power: " + leakage_power + "\n")
    all_results.write("total_power: " + total_power + "\n")
    all_results.write("instance count: " + instance + "\n")

    all_results.write("\n")

all_results.close()
