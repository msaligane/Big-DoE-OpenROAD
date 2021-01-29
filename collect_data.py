import re
import glob
import json
import csv
import os

PLATFORM = "sky130"
DESIGN = "gcd"

design_list = glob.glob("data/*")

_2_init_all_results_csv = []
_3_pre_resize_all_results_csv = []
_3_post_resize_all_results_csv = []
_6_final_report_all_results_csv = []
all_results_json = {}

_2_init_csv_columns = ["name", "tns", "wns"]
_3_resize_csv_columns = ["name", "tns", "wns"]
_6_final_report_csv_columns = ["name", "tns", "wns", "internal_power", "switching_power", "leakage_power", "total_power", "instance_count"]

failed_designs = []

for design in design_list:
    log_f = design + "/logs"
    object_f = design + "/objects"
    reports_f = design + "/reports"
    results_f = design + "/results"

    design_name = design.split("/")[-1]
    
    all_results_json[design_name] = {}
    
    if os.path.isfile(reports_f + "/" + PLATFORM + "/" + DESIGN + "/2_init.rpt"):
        with open(reports_f + "/" + PLATFORM + "/" + DESIGN + "/2_init.rpt", "r") as rf:
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

            all_results_json[design_name]["2_init"] = results 
            _2_init_all_results_csv.append(results)
        except:
            print("Cannot extract 2_init.rpt from: " + design)


    if os.path.isfile(reports_f + "/" + PLATFORM + "/" + DESIGN + "/3_pre_resize.rpt"):
        with open(reports_f + "/" + PLATFORM + "/" + DESIGN + "/3_pre_resize.rpt", "r") as rf:
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

            all_results_json[design_name]["3_pre_resize"] = results 
            _3_pre_resize_all_results_csv.append(results)
        except:
            print("Cannot extract 3_pre_resize.rpt from: " + design)
    

    if os.path.isfile(reports_f + "/" + PLATFORM + "/" + DESIGN + "/3_post_resize.rpt"):
        with open(reports_f + "/" + PLATFORM + "/" + DESIGN + "/3_post_resize.rpt", "r") as rf:
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

            all_results_json[design_name]["3_post_resize"] = results 
            _3_post_resize_all_results_csv.append(results)
        except:
            print("Cannot extract 3_post_resize.rpt from: " + design)

    if os.path.isfile(reports_f + "/" + PLATFORM + "/" + DESIGN + "/6_final_report.rpt"):
        with open(reports_f + "/" + PLATFORM + "/" + DESIGN + "/6_final_report.rpt", "r") as rf:
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
    
            all_results_json[design_name]["6_final_report"] = results 
            _6_final_report_all_results_csv.append(results)
        except:
            print("Cannot extract 6_final_report.rpt from: " + design)
    else:    
        failed_designs.append(design_name)

    
os.mkdir("doe_reports")

with open("doe_reports/data_stream.json", "w") as wf:
    wf.write(json.dumps(all_results_json))

with open("doe_reports/2_init_all.csv", "w") as wf:
    writer = csv.DictWriter(wf, fieldnames=_2_init_csv_columns)
    writer.writeheader()
    for data in _2_init_all_results_csv:
        writer.writerow(data)

with open("doe_reports/3_pre_resize_all.csv", "w") as wf:
    writer = csv.DictWriter(wf, fieldnames=_3_resize_csv_columns)
    writer.writeheader()
    for data in _3_pre_resize_all_results_csv:
        writer.writerow(data)

with open("doe_reports/3_post_resize_all.csv", "w") as wf:
    writer = csv.DictWriter(wf, fieldnames=_3_resize_csv_columns)
    writer.writeheader()
    for data in _3_post_resize_all_results_csv:
        writer.writerow(data)

with open("doe_reports/6_final_reports_all.csv", "w") as wf:
    writer = csv.DictWriter(wf, fieldnames=_6_final_report_csv_columns)
    writer.writeheader()
    for data in _6_final_report_all_results_csv:
        writer.writerow(data)

with open("doe_reports/failed_designs.txt", "w") as wf:
    for design in failed_designs:
        wf.write(design + "\n")
