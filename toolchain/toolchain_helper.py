import os

import yaml

from typing import List, Dict


def get_list_of_yaml_files(yaml_folder: str) -> List[str]:
    """
    Returns a list of all yaml files found in given folder. Files are returned as absolute paths.

    :param yaml_folder: the path to yaml folder
    :type yaml_folder: str
    :return all found yaml files as list of absolute paths
    :rtype List[str]
    """
    all_yaml_files = list()
    for file in os.listdir(yaml_folder):
        abs_file_path = os.path.join(yaml_folder, file)
        if abs_file_path.endswith("/data-types/address.yaml") or \
                abs_file_path.endswith("/data-types/agent.yaml") or \
                abs_file_path.endswith("/data-types/foaf-agent.yaml"):
            continue
        if os.path.isfile(abs_file_path):
            if not abs_file_path.endswith(".yaml"):
                # exclude non-yaml files
                continue
            all_yaml_files.append(abs_file_path)
        if os.path.isdir(abs_file_path):
            if abs_file_path.endswith("/validation") or abs_file_path.endswith("/to-be-integrated"):
                # exclude validation folder
                continue
            all_yaml_files = all_yaml_files + get_list_of_yaml_files(abs_file_path)

    return all_yaml_files


def load_yaml_definition_of_classes(all_yaml_files: List[str]) -> Dict[str, Dict]:
    """
    Returns for each yaml file in the given the yaml representation as dict. Return

    :param all_yaml_files: list of yam files whose yaml representation is to be loaded
    :type all_yaml_files: List[str]
    :return a dictionary of dictionaries with yaml representations. Keys of first dict are full class names.
    E.g. all_yaml_files = [gax-trust-framework/gax-participant/legal-person.yaml,
    gax-trust-framework/gax-participant/natural-person.yaml] will return:
    { 'gax-trust-framework:LegalPerson': { yaml dict of legal person},
       'gax-trust-framework:NaturalPerson': { yaml dict of natural person}
    }
    """
    print("########################################################")
    print("# Load yaml definition")
    print("########################################################")
    all_yaml_file_definitions = dict()
    for yaml_file in all_yaml_files:
        with open(yaml_file, 'r') as stream:
            print(" ...." + yaml_file)
            yaml_definition = yaml.safe_load(stream)
            class_name = list(yaml_definition.keys())[0]
            class_prefix = yaml_definition[class_name]['prefix']
            all_yaml_file_definitions[class_prefix + ":" + class_name] = yaml_definition

    return all_yaml_file_definitions
