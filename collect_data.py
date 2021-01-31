import re
import glob
import json
import csv
import os

PLATFORM = "SKY130HS"
DESIGN = "jpeg"

design_list = glob.glob("data/*")

_2_1_floorplan_all_results_csv = []
_3_3_resizer_all_results_csv = []
_4_1_cts_all_results_csv = []
_6_report_all_results_csv = []
all_results_json = {}

_2_1_floorplan_csv_columns = ["name", "tns", "wns"]
_3_3_resizer_csv_columns = ["name", "tns", "wns"]
_4_1_cts_csv_columns = ["name", "tns", "wns"]
_6_report_csv_columns = ["name", "tns", "wns", "internal_power", "switching_power", "leakage_power", "total_power", "instance_count"]

failed_designs = []

for design in design_list:
    logs_f = design + "/logs"
    objects_f = design + "/objects"
    reports_f = design + "/reports"
    results_f = design + "/results"

    design_name = design.split("/")[-1]
    
    all_results_json[design_name] = {}
    
    if os.path.isfile(logs_f + "/" + PLATFORM + "/" + DESIGN + "/2_1_floorplan.log"):
        with open(logs_f + "/" + PLATFORM + "/" + DESIGN + "/2_1_floorplan.log", "r") as rf:
            filedata = rf.read()
        tns_group = re.search("tns (.*)", filedata)
        wns_group = re.search("wns (.*)", filedata)
        
        results = {}
        results["name"] = design_name
        
        try:
            tns = tns_group.group(1)
            wns = wns_group.group(1)
            
            results["tns"] = tns
            results["wns"] = wns

            all_results_json[design_name]["2_1_floorplan"] = results 
            _2_1_floorplan_all_results_csv.append(results)
        except:
            print("Cannot extract 2_1_floorplan.log from: " + design)


    if os.path.isfile(logs_f + "/" + PLATFORM + "/" + DESIGN + "/3_3_resizer.log"):
        with open(logs_f + "/" + PLATFORM + "/" + DESIGN + "/3_3_resizer.log", "r") as rf:
            filedata = rf.read()

        tns_group = re.search("tns (.*)", filedata)
        wns_group = re.search("wns (.*)", filedata)
        
        results = {}
        results["name"] = design_name
        
        try:
            tns = tns_group.group(1)
            wns = wns_group.group(1)
            
            results["tns"] = tns
            results["wns"] = wns

            all_results_json[design_name]["3_3_resizer"] = results 
            _3_3_resizer_all_results_csv.append(results)
        except:
            print("Cannot extract 3_3_resizer.log from: " + design)
    

    if os.path.isfile(logs_f + "/" + PLATFORM + "/" + DESIGN + "/4_1_cts.log"):
        with open(logs_f + "/" + PLATFORM + "/" + DESIGN + "/4_1_cts.log", "r") as rf:
            filedata = rf.read()

        tns_group = re.search("tns (.*)", filedata)
        wns_group = re.search("wns (.*)", filedata)
        
        results = {}
        results["name"] = design_name
        
        try:
            tns = tns_group.group(1)
            wns = wns_group.group(1)
            
            results["tns"] = tns
            results["wns"] = wns

            all_results_json[design_name]["4_1_cts"] = results 
            _4_1_cts_all_results_csv.append(results)
        except:
            print("Cannot extract 4_1_cts.log from: " + design)

    if os.path.isfile(logs_f + "/" + PLATFORM + "/" + DESIGN + "/6_report.log"):
        with open(logs_f + "/" + PLATFORM + "/" + DESIGN + "/6_report.log", "r") as rf:
            filedata = rf.read()

        tns_group = re.search("tns (.*)", filedata)
        wns_group = re.search("wns (.*)", filedata)
        power_group = re.search("report_power(\n.*)*(Total .*)", filedata)
        instance_group = re.search("instance_count(\n.*)\n(\d+)", filedata)

        results = {}
        results["name"] = design_name
        
        try:
            tns = tns_group.group(1)
            wns = wns_group.group(1)
            
            power_all = power_group.group(2).split()
            internal_poewr = power_all[1]
            switching_power = power_all[2]
            leakage_power = power_all[3]
            total_power = power_all[4]

            instance = instance_group.group(2)
            
            results["tns"] = tns
            results["wns"] = wns
            results["internal_power"] = internal_poewr
            results["switching_power"] = switching_power
            results["leakage_power"] = leakage_power
            results["total_power"] = total_power
            results["instance_count"] = instance
    
            all_results_json[design_name]["6_report"] = results 
            _6_report_all_results_csv.append(results)
        except:
            print("Cannot extract 6_report.log from: " + design)
    else:    
        failed_designs.append(design_name)

if not os.path.isdir("doe_reports"):
    os.mkdir("doe_reports")

with open("doe_reports/data_stream.json", "w") as wf:
    wf.write(json.dumps(all_results_json))

with open("doe_reports/2_1_floorplan_all.csv", "w") as wf:
    writer = csv.DictWriter(wf, fieldnames=_2_1_floorplan_csv_columns)
    writer.writeheader()
    for data in _2_1_floorplan_all_results_csv:
        writer.writerow(data)

with open("doe_reports/3_3_resizer_all.csv", "w") as wf:
    writer = csv.DictWriter(wf, fieldnames=_3_3_resizer_csv_columns)
    writer.writeheader()
    for data in _3_3_resizer_all_results_csv:
        writer.writerow(data)

with open("doe_reports/4_1_cts_all.csv", "w") as wf:
    writer = csv.DictWriter(wf, fieldnames=_4_1_cts_csv_columns)
    writer.writeheader()
    for data in _4_1_cts_all_results_csv:
        writer.writerow(data)

with open("doe_reports/6_report_all.csv", "w") as wf:
    writer = csv.DictWriter(wf, fieldnames=_6_report_csv_columns)
    writer.writeheader()
    for data in _6_report_all_results_csv:
        writer.writerow(data)

with open("doe_reports/failed_designs.txt", "w") as wf:
    for design in failed_designs:
        wf.write(design + "\n")

print("Extraction done, data is stored in the doe_reports folder")
