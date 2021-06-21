import os
import utils
import json
from sys import version_info

def save_to_json(template, target):
    #Create msr4ml dir in target project's path if not exists
    if not os.path.exists(os.path.dirname(target)):
        os.mkdir(os.path.dirname(target))

    with open(target, 'w') as f:
        json.dump(template, f, indent=4, sort_keys=False)


def run(project_path, project_name, target, py_files = None):
    print("+++ Starting pipeline reconstruction...")
    if py_files is None:
        py_files = utils.get_files(project_path, ".py")

    #Load pipeline template
    with open(os.path.join(os.path.dirname(__file__), "templates/pipeline.json")) as f:
        template = json.load(f)
    
    template["workflow"] = []
    
    # Get python version
    template["python_version"] = f"{version_info.major}.{version_info.minor}.{version_info.micro}"

    #Get requirements file
    try:
        template["requirements"]["py_reqs"] = utils.get_files(project_path, "requirements.txt")[0]
    except IndexError:
        template["requirements"]["py_reqs"] = "No requirements.txt found"

    #Get project name and path
    template["name"] = project_name
    template["path"] = project_path

    for file in py_files:
        is_step = False
        try:
            #Make temporary random file name
            tmp_file = utils.make_random_filename(20)

            # Retrieve argparse code from file
            code, parser_var_name = utils.get_argparse(file)
            if code is not None:
                # Save argparse code to temporary random file
                utils.save_to_module(parser_var_name, code, tmp_file)

                # Retrieve module name of temporary file
                _, tmp_file2 = os.path.split(tmp_file)
                module = tmp_file2.replace(".py", "")

                #Import the temporary module
                mod = utils.load_module(module)
                try:
                    parser_obj = mod.parser
                    description = parser_obj.description
                    parser_info = mod.INFO
                    is_step = True
                except Exception as e:
                    print(e)
                    is_step = False
            else:
                is_step = False
        finally:
            utils.delete_module(tmp_file)
        
        #Retrieve workflow:
        if is_step:
            print(f"Found step in {file}")
            step_name = []
            if "data" in file.lower():
                step_name.append("data-preprocess")
            if "train" in file.lower():
                step_name.append("train")
            if "test" in file.lower():
                step_name.append("test")
            step = {
                "cmd": f"python {file}",
                "main": file,
                "steps": step_name,
                "args_lib": "argparse",
                "description": description,
                "args": utils.get_args(parser_info),
                "ins": [],
                "outs": []
            }
            template["workflow"].append(step)
    save_to_json(template, target)
    print(f"     Finished... Results saved to {target}")
    return template
            


