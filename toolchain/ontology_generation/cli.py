import argparse

import csv
import sys
from pathlib import Path

from colorama import Fore, Style

import yaml2ttl

# Command Line Interface for the script check_yaml
if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='generates ontology files based single-source-of-truth')
    sub_parser = parser.add_subparsers(title="Output to be generated", dest="output")

    # Setup parser for sd-attribute command
    y2j_parser = sub_parser.add_parser("ontology-generation",
                                       help="Creates a turtle file for each prefix in the single source of truth, which defines the ontology")

    y2j_parser.add_argument('--srcFile', type=str, required=True,
                            help='Path to CSV file specifying where fo find specific files')
    y2j_parser.add_argument('--dstPath', type=str, required=True,
                            help='Path to file  file specifying where fo find specific files')
    y2j_parser.add_argument('-e', '--ecosystem', action='append', required=True,
                            help='Select ecosystem, if ecosystem depends on other ecosystem please specify as list e.g ( --ecosystem gax-core --ecosystem trusted-cloud')

    args = parser.parse_args()
    if args.output == "ontology-generation":

        src_path: str = args.srcFile
        ontology_target_folder = args.dstPath
        ecosystems: list = args.ecosystem

        with open(src_path, encoding='utf-8') as file:
            csvreader = csv.reader(file)
            dict_from_csv = {}
            for row in csvreader:
                dict_from_csv[row[0]] = row[1]

        # loading data
        root_path: str = dict_from_csv['SSOT_root_path']
        validation_path: str = dict_from_csv['SSOT_validation_path']

        print(root_path)
        # load all yaml files associated with specified ecosystem
        files = [path for path in yaml2ttl.load_yml_file_paths(Path(root_path), ecosystems=ecosystems)]
        # load all prefixes associated with ecosystem
        prefixes = [path for path in yaml2ttl.load_yml_file_paths(Path(validation_path), ecosystems=ecosystems) if
                    path.name == "prefixes.yaml"]
        prefixes_metadata = [path for path in yaml2ttl.load_yml_file_paths(Path(validation_path), ecosystems=ecosystems)
                             if path.name != "prefixes.yaml" and path.name != 'dataTypeAbbreviation.yaml']

        # sorting files per ecosystem
        files = yaml2ttl.sort_by_ecosystem(root=Path(root_path), files=files, ecosystems=ecosystems)
        prefixes = yaml2ttl.sort_by_ecosystem(root=Path(validation_path), files=prefixes, ecosystems=ecosystems)
        prefixes_metadata = yaml2ttl.sort_by_ecosystem(root=Path(validation_path), files=prefixes_metadata,
                                                       ecosystems=ecosystems)

        # finding files associated to defined prefix of ecosystem
        matches = {i: {} for i in ecosystems}
        for eco in ecosystems:
            assert len(prefixes[eco]) == 1
            prefix_dict = yaml2ttl.parseYAML(str(prefixes[eco][0]))
            found_matches = yaml2ttl.find_matches(files=files[eco], prefixes=prefix_dict, ecosystem=eco)
            matches[eco].update(found_matches)

        # preparing metadata files per prefix and ecosystem
        for k in prefixes_metadata.keys():
            prefixes_metadata[k] = {str(i.name).split('.')[0] : i for i in prefixes_metadata[k]}

        print("===========================================")
        print("Starting to generate ontology files (*.ttl)")
        print("===========================================")

        for eco in ecosystems:
            for prefix_name in matches[eco].keys():
                #print("generating ontology file for ecosystem" + str(Path(eco)) + " and associated prefix " + str(
                 #   prefix_name))

                # loading simple datatypes
                try:
                    simple_data_types = list(
                        yaml2ttl.parseYAML(str(Path(validation_path) / eco / 'dataTypeAbbreviation.yaml')).keys())
                except:
                    # catches exception if dataTypeAbbreviation.yaml is empty file => dict is None and has no keys
                    simple_data_types = []

                assert len(prefixes[eco]) == 1
                eco_prefix = yaml2ttl.parseYAML(str(prefixes[eco][0]))
                prefix_metadata = yaml2ttl.parseYAML(str(prefixes_metadata[eco][prefix_name]))

                yaml2ttl.generate_ontology_file(save_to=Path(ontology_target_folder), name=prefix_name,
                                       yaml_base_files=matches[eco][prefix_name],
                                       simple_data_types=simple_data_types, prefixes=eco_prefix,
                                       prefix_metadata_dic=prefix_metadata, ecosystems=ecosystems)
        print(Fore.GREEN + 'Successfully generated ontology' + Style.RESET_ALL)
