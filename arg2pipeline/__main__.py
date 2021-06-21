import argparse
import os
import extract


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=' Retrieve argparse information to build the pipeline',
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument(
        'project_dir', 
        help="Name of the project to extract the ML pipeline")

    parser.add_argument(
        '-t', '--target', 
        help="Name of the target json file to store pipeline data, defaults to [project_dir]/arg2pipeline/pipeline.json",
        default="",
        metavar="")
    
    parser.add_argument(
        '-n', '--name', 
        help="Name of project. Defaults to the project's folder name",
        default="",
        metavar="")

    args = parser.parse_args()
    target = args.target if args.target != '' else os.path.join(args.project_dir, 'arg2pipeline/pipeline.json')
    project_name = args.name if args.name != '' else os.path.basename(os.path.normpath(args.project_dir))

    assert args.project_dir is not None, "The path of the ML project must be specified"

    extract.run(args.project_dir, project_name, target)
