import json
from types import SimpleNamespace
import yaml
import os
import argparse
import subprocess
import sys
import os

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def load_data(file: str) -> object:
    assert file.endswith(".json") and os.path.isfile(file), "Please provide a valid path to the json pipeline file"
    try:
        with open(file) as f:
            data = json.load(f, object_hook=lambda d: SimpleNamespace(**d))
            return data
    except Exception as e:
        print(e)
        return None

class ToDVC:
    def __init__(self, input: object):
        assert input is not None, "The input data to parse from must not be empty"
        self.input = input
        self.name = self.input.name.split("/")[-1]
        self.entry_points_title = "stages"
        self.cmd_title = "cmd"
        self.parameters_title = "params"
        self.ins_title = "deps"
        self.main_title = "deps"
        self.outs_title = "outs"
        self.params = {}
        self.params_file = "params.yaml"

    def set_param(self, ep_name: None, arg: None, to_file: bool = False):
        if to_file:
            self.export(self.params, self.params_file)
            return True
        else:
            if not ep_name or not arg:
                raise ValueError("The parameter's and entry point's names must not be empty")
            self.params[ep_name][arg.dest] = arg.default
            return arg.dest


    def set_project(self, to_file: bool= False) -> dict:
        p = {
            self.entry_points_title: {}
        }
        if hasattr(self.input, "entries") and self.input.entries:
            i = 0
            for ep in self.input.entries:
                if hasattr(ep, "alternate"):
                    if ep.alternate:
                        continue
                ep_name = f"step{i}_"+"_".join(ep.steps)
                ep_name = ep_name.replace(" ", "-")
                p[self.entry_points_title][ep_name] = {}
                p[self.entry_points_title][ep_name][self.cmd_title] = ep.cmd
                p[self.entry_points_title][ep_name][self.parameters_title] = []
                p[self.entry_points_title][ep_name][self.ins_title] = []
                p[self.entry_points_title][ep_name][self.outs_title] = []
                self.params[ep_name] = {}
                for arg in ep.args:
                    if arg.dest:
                        if arg.input:
                            if arg.default is not None:
                                p[self.entry_points_title][ep_name][self.parameters_title].append(self.set_param(ep_name, arg))
                                # p[self.entry_points_title][ep_name][self.cmd_title] += f" {arg.names[0]} ${{{arg.dest}}}"
                        # elif arg.mandatory:
                            # p[self.entry_points_title][ep_name][self.cmd_title] += f" {arg.names[0]}"
                if not p[self.entry_points_title][ep_name][self.parameters_title]:
                    del p[self.entry_points_title][ep_name][self.parameters_title]
                if ep.main != "unknown":
                    p[self.entry_points_title][ep_name][self.ins_title].append(ep.main)
                for dep in ep.ins:
                    if dep.ex_in_repo:
                        p[self.entry_points_title][ep_name][self.ins_title].append(dep.location)
                #Fix for the dvc error "Ouput paths overlap"
                # outputs should be in separate tracked directories or tracked individually.
                paths = []
                to_write = []
                tmp = []
                for out in ep.outs:
                    tmp.append(out.location)
                    paths.append(out.location)
                    to_write.append(out.location)
                # TODO: Fix this because no out is generated. Also fix the params and change to step.param
                for path in paths:
                    to_add = True
                    for tm in tmp:
                        if os.path.abspath(path).startswith(os.path.abspath(tm)):
                            to_add = False
                            to_write.remove(path)
                        elif os.path.abspath(tm).startswith(os.path.abspath(path)):
                            to_add = False
                            to_write.remove(tm)
                        if not to_add:
                            break
                for tw in to_write:
                    p[self.entry_points_title][ep_name][self.outs_title].append(tw)
                if not p[self.entry_points_title][ep_name][self.ins_title]:
                    del p[self.entry_points_title][ep_name][self.ins_title]
                if not p[self.entry_points_title][ep_name][self.outs_title]:
                    del p[self.entry_points_title][ep_name][self.outs_title]
                if not self.params[ep_name]:
                    del self.params[ep_name]
                i += 1
        if to_file:
            self.export(p, "dvc.yaml")          
        return p                    
    
    def set_all(self, to_file: bool = True) -> tuple:
        return  self.set_project(to_file), self.set_param(None, None, to_file)

    def export(self, data: object, file: str):
        with open(file, 'w') as f:
            print(f"Exporting the results to file {file}")
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

class ToMlflow:
    def __init__(self, input: object):
        assert input is not None, "The input data to parse from must not be empty"
        self.input = input
        self.name = self.input.name
        self.conda_env = f"conda_{self.name}.yaml"
        self.entry_points_title = "entry_points"
        self.cmd_title = "command"
        self.parameters_title = "parameters"
        self.multistep_filename = "ex_mlflow_multistep_main.py"


    def set_project(self, to_file: bool= False) -> dict:
        p = {
            "name": self.input.name,
            "conda_env": self.conda_env,
            self.entry_points_title: {}
        }
        if hasattr(self.input, "workflow") and self.input.workflow:
            i = 0
            for ep in self.input.workflow:
                if ep.main is None:
                    print("Found unknown command, creating bash file")
                    ep.steps.append("custom")
                    with open(f"ex_custom_cmd_step{i}.sh", "w") as f:
                        f.write("#!/bin/bash\n")
                        f.write("# Auto-generated file during conversion. MLflow accepts only .py or .sh files\n")
                        f.write(ep.cmd)
                    ep.cmd = f"bash ex_custom_cmd_step{i}.sh"
                
                ep_name = f"step{i}_"+"_".join(ep.steps) if len(self.input.workflow) > 1 else "main"
                ep_name = ep_name.replace(" ", "-")
                p[self.entry_points_title][ep_name] = {}
                p[self.entry_points_title][ep_name][self.parameters_title] = {}
                p[self.entry_points_title][ep_name][self.cmd_title] = ep.cmd
                for arg in ep.args:
                    if arg.destination:
                        if arg.input:
                            if arg.default is not None:
                                p[self.entry_points_title][ep_name][self.parameters_title][arg.destination] = {
                                    "type": arg.type
                                }
                                p[self.entry_points_title][ep_name][self.parameters_title][arg.destination]["default"] = arg.default 
                                p[self.entry_points_title][ep_name][self.cmd_title] += f" {arg.option_strings[0]} {{{arg.destination}}}"
                        elif arg.required:
                            p[self.entry_points_title][ep_name][self.cmd_title] += f" {arg.option_strings[0]}"
                if not p[self.entry_points_title][ep_name][self.parameters_title]:
                    del p[self.entry_points_title][ep_name][self.parameters_title]
                i += 1
            if len(self.input.workflow) > 1:
                p[self.entry_points_title]["main"]={self.cmd_title: f"python {self.multistep_filename}"}
        if to_file:
            self.export(p, "MLproject")          
        return p                    

    def set_conda(self, to_file: bool = False) -> dict:
        c = {
            "name": self.name,
            "channels": self.input.channels if hasattr(self.input, "channels") else ["default"],
            "dependencies": []
        }
        if self.input.python_version:
            c["dependencies"].append(f"python={self.input.python_version}")
            c["dependencies"].append("pip")
        if self.input.requirements.py_reqs:
            c["dependencies"].append({"pip": []})
            with open(self.input.requirements.py_reqs) as f:
                for r in f.readlines():
                    c["dependencies"][-1]["pip"].append(r.rstrip('\r\n'))
        if to_file:
            self.export(c, self.conda_env) 
        return c
    
    def set_all(self, to_file: bool = True) -> tuple:
        return  self.set_conda(to_file), self.set_project(to_file)

    def export(self, data: object, file: str):
        with open(file, 'w') as f:
            print(f"Exporting the results to file {file}")
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-dvc', action='store_true', help='If set, migrate to dvc')
    parser.add_argument('-mlf', action='store_true', help='If set, migrate to MLflow')
    parser.add_argument('filename', help="Name of the file for which you want to create documentation")
    args = parser.parse_args()
    if args.dvc:
        pr = ToDVC(load_data(args.filename))
        pr.set_all()
    elif args.mlf:
        pr = ToMlflow(load_data(args.filename))
        pr.set_all()
    else:
        raise ValueError("At least one argument should be provided: either -dvc or -mlf")


