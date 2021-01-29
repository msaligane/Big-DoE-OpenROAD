import re
import glob
import json
import csv
import os

PLATFORM = "sky130"
DESIGN = "gcd"

design_list = glob.glob("data/*")

all_results_csv = []
all_results_json = {}
csv_columns = ["name", "tns", "wns", "internal_power", "switching_power", "leakage_power", "total_power", "instance_count"]

failed_designs = []

for design in design_list:
    log_f = design + "/logs"
    object_f = design + "/objects"
    reports_f = design + "/reports"
    results_f = design + "/results"

    if not os.path.isfile(reports_f + "/" + PLATFORM + "/" + DESIGN + "/6_final_report.rpt"):
        failed_designs.append(design.split("/")[-1])
        continue

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



    results = {}
    results["name"] = design.split("/")[-1]
    results["tns"] = tns
    results["wns"] = wns
    results["internal_power"] = internal_poewr
    results["switching_power"] = switching_power
    results["leakage_power"] = leakage_power
    results["total_power"] = total_power
    results["instance_count"] = instance

    all_results_json[design.split("/")[-1]] = results 

    all_results_csv.append(results)

with open("data_stream.json", "w") as wf:
    wf.write(json.dumps(all_results_json))

with open("data_stream.csv", "w") as wf:
    writer = csv.DictWriter(wf, fieldnames=csv_columns)
    writer.writeheader()
    for data in all_results_csv:
        writer.writerow(data)

with open("failed_designs.txt", "w") as wf:
    for design in failed_designs:
        wf.write(design + "\n")
