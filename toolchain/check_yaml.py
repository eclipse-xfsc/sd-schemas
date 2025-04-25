#!/usr/bin/env python3
import sys
import yaml

from pathlib import Path
from os import walk

from typing import Dict, List
from colorama import Fore, Style

import collections
import os

def load_yaml_file(filepath: Path) -> Dict:
    with open(filepath, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(Fore.RED + "ERROR in file " + str(filepath)+ " -- " + " unable to load yaml file" + Style.RESET_ALL)
            print(exc)
            return {}


# get all yaml or yml files except those who contain example in their name
def load_yml_file_paths(yml_folder: Path) -> List:
    filenames = next(walk(yml_folder), (None, None, []))[2]
    filenames = [file for file in filenames if file.endswith(".yaml") or file.endswith(".yml")]
    filenames = [file for file in filenames if "example" not in file]

    return filenames


def load_data_type_list(data_type_abbreviation_path: Path) -> List:
    return list(load_yaml_file(data_type_abbreviation_path).keys())

def load_prefix_list(prefix_path: Path ) -> List:

    prefix_dic = load_yaml_file(prefix_path)
    lvl0 = list(prefix_dic.keys())[0]
    prefixes = [p['name'] for p in list(prefix_dic[lvl0])]
    return prefixes


# goes through all yaml files and checks if all DataTypes exist defines DataTypes
def discover_object_data_types(yml_root_path: Path, yml_files: List) -> (List, int):

    additional_datatypes = []
    error_count = 0
    for file in yml_files:
        yml_dic = load_yaml_file(filepath=yml_root_path / file)
        name = list(yml_dic.keys())[0]
        try:
            prefix = yml_dic[name]['prefix']
            dataType = str(prefix) + ":" + str(name)
            additional_datatypes.append(dataType)
        except KeyError:
            print(
                Fore.RED + "ERROR in file " + str(file)
                + " -- " + "datatype for class " + name + " ignored, because it is unclear. Please add a prefix." + Style.RESET_ALL)
            error_count += 1

    return additional_datatypes, error_count


def file_validation(yml_file_path: Path, dt_list: List, p_list: List, mandatorty_attributes: List) -> (str, int):
    err_count = 0

    yml_dic = load_yaml_file(filepath=yml_file_path)
    # check if yml file was loaded correctly
    if bool(yml_dic) is False:
        return "", 1

    cls_name = list(yml_dic.keys())[0]
    yml_dic = yml_dic[cls_name]
    print('validating file ' + yml_file_path.name + ' ...')

    # 1.Value of subClassOff must be a list.
    try:
        subclass_list = yml_dic['subClassOf']
        if isinstance(subclass_list, list):
            pass
        else:
            print(
                Fore.RED + "ERROR in file " + str(yml_file_path)
                + " -- " + "subClassOf not a list" + Style.RESET_ALL)
            err_count += 1

    except KeyError:
        print(
            Fore.RED + "ERROR in file " + str(yml_file_path)
            + " -- " + "missing mandatory specification subClassOf" + Style.RESET_ALL)
        err_count += 1

    try:
        attribute_list = yml_dic['attributes']
        title_list = []

        for attribute in attribute_list:

            attribute_list = list(attribute.keys())
            missing_attributes = [ma for ma in mandatorty_attributes if ma not in attribute_list]

            if len(missing_attributes) > 0:
                print(
                    Fore.RED + "ERROR in file " + str(yml_file_path)
                    + " -- " + "missing mandatory attributes : " + str(missing_attributes) + Style.RESET_ALL)
                err_count += 1

            for itm in attribute.keys():
                val = attribute[itm]
                if itm == "title":
                    if val[0].isupper():
                        print(
                            Fore.RED + "ERROR in file " + str(yml_file_path)
                            + " -- " + "attribute title starts with upper case : " + str(val) + Style.RESET_ALL)
                        err_count += 1
                    title_list.append(val)

                # Value of dataType must be an abbreviation listed in dataTypeAbbreviation.yaml.
                # Mapping of abbreviation in dataTypeAbbreviation.yaml must be a valid data type in Self-Description ontology.
                if itm == 'dataType':
                    if val not in dt_list:
                        print(
                            Fore.RED + "ERROR in file " + str(yml_file_path)
                            + " -- " + "dataType " + val + " not defined: "
                                                           "\n1. Either add the dataType to dataTypeAbbreviation.yaml, if it is a simple dataType (e.g xsd:dateTimeStamp)"
                                                           "\n2. Or add a new *.yaml file if it is a more complex dataType (e.g gax-core:*****)"
                                                           "\n" + Style.RESET_ALL)
                        err_count += 1

                if itm == 'prefix':
                    if val not in p_list:

                        print( Fore.RED + "ERROR in file " + str(yml_file_path)
                        + " -- " + "prefix " + val + " not defined in yaml/validation/prefixes.yaml " + Style.RESET_ALL)
                        err_count += 1
                # Element cardinality is optional. If its is missing, the attribute is considered to be optional.
                # Value of minCount and maxCount must be a positive integer
                if itm == 'cardinality':
                    try:
                        min_count = val["minCount"]
                        # max count is optional based on schema.json
                        max_count = 0
                        if "maxCount" in list(val.keys()):
                            max_count = val["maxCount"]

                        if isinstance(min_count, int) and isinstance(max_count, int):
                            if min_count >= 0 and max_count >= 0:
                                pass
                            else:
                                print(Fore.RED + "ERROR in file " + str(yml_file_path)
                                      + " -- " + itm + " minCount or maxCount not a positive integer" + Style.RESET_ALL)
                                err_count += 1
                        else:
                            print(Fore.RED + "ERROR in file " + str(yml_file_path)
                                  + " -- " + itm + " minCount or maxCount not a number" + Style.RESET_ALL)
                            err_count += 1
                    except KeyError:
                        print(Fore.RED + "ERROR in file " + str(yml_file_path)
                              + " -- " + "missing mandatory specification minCount" + Style.RESET_ALL)
                        err_count += 1

                # Value of description  must be a at least one human readable sentence.
                if itm == "description":
                    if not isinstance(val, str):
                        print(Fore.RED + "ERROR in file " + str(yml_file_path)
                              + " -- " + itm + " is not a human readable sentence" + Style.RESET_ALL)
                        err_count += 1

                # Value of exampleValues must be a list. There must be at least one list item.
                if itm == 'exampleValues':
                    if isinstance(val, list):
                        if len(val) < 1:
                            print(Fore.RED + "ERROR in file " + str(yml_file_path)
                                  + " -- " + itm + " must contain at least one list item" + Style.RESET_ALL)
                            err_count += 1
                    else:
                        print(Fore.RED + "ERROR in file " + str(yml_file_path)
                              + " -- " + itm + " must be a list" + Style.RESET_ALL)
                        err_count += 1

        # Value of title must be unique within a file as it is used as ID of a Self-Description attribute
        duplicates = [item for item, count in collections.Counter(title_list).items() if count > 1]
        if len(duplicates) > 0:
            print(
                Fore.RED + "ERROR in file " + str(yml_file_path)
                + " -- " + "title must be unique! duplicates found: " + str(duplicates) + Style.RESET_ALL)
            err_count += 1

    # file has to contain attributes
    except KeyError:
        print(
            Fore.RED + "ERROR in file " + str(yml_file_path)
            + " -- " + "missing mandatory specification attributes" + Style.RESET_ALL)
        err_count += 1

    # print out green
    if err_count == 0:
        print(
            Fore.GREEN + " File " + str(yml_file_path) + " checked" + Style.RESET_ALL)

    return cls_name, err_count


# python check_yaml1.py '../single-point-of-truth/yaml' '../single-point-of-truth/yaml/dataTypeAbbreviation.yaml
if __name__ == "__main__":

    print("Starting semantic validation of yaml files")
    report_errors: Dict = {}
    data_type_list = []
    p_list = []

    # List of files
    yml_files = []
    add_yaml_files = []
    error_count = 0

    # list of discovered classes in all files
    defined_classes = []

    try:
        YML_DIR_PATH: Path = Path(sys.argv[1])
        ADD_YAML_FILES: Path = Path(sys.argv[2])
        PREFIX_FILE = "prefixes.yaml"
        DATA_TYPE_ABBREVIATION_FILE = "dataTypeAbbreviation.yaml"
        # hardcoded list of mandatorty attributes
        MANDATORY_ATTRIBUTES = ['title', 'prefix', 'dataType', 'description', 'exampleValues']

        # loading all available data types

        yml_files: List = load_yml_file_paths(YML_DIR_PATH)
        add_yaml_files: List = load_yml_file_paths(ADD_YAML_FILES)


        data_type_list = load_data_type_list(ADD_YAML_FILES / DATA_TYPE_ABBREVIATION_FILE)
        p_list: List = load_prefix_list(ADD_YAML_FILES / PREFIX_FILE)


        # remove DATA_TYPE_ABBREVIATION_FILE from files to validate
        yml_files = [yml_file for yml_file in yml_files if str(yml_file) != DATA_TYPE_ABBREVIATION_FILE]
        yml_files = [yml_file for yml_file in yml_files if str(yml_file) != PREFIX_FILE]

        # additional yaml files
        add_yaml_files = [yml_file for yml_file in add_yaml_files if str(yml_file) != DATA_TYPE_ABBREVIATION_FILE]
        add_yaml_files = [yml_file for yml_file in add_yaml_files if str(yml_file) != PREFIX_FILE]

    except Exception as e:
        print(Fore.RED + "Error: loading *.yaml files. Specify 1st: path to core yaml file folder and 2nd: path to associated validation folder containing the dataTypeAbbreviation.yaml and the prefix.yaml" + Style.RESET_ALL)
        os.sys.exit(1)

    try:
        data_type_list_1, err_count_1 = discover_object_data_types(yml_root_path=YML_DIR_PATH, yml_files=yml_files)
        data_type_list_2, err_count_2 = discover_object_data_types(yml_root_path=ADD_YAML_FILES, yml_files=add_yaml_files)

        data_type_list = data_type_list + data_type_list_1 + data_type_list_2
        error_count = err_count_1 + err_count_2

    except Exception:
        print(
            Fore.RED + "Error while discovering dataTypes specified in *.yaml files: Moving forward without loading additional dataTypes!" + Style.RESET_ALL)


    for file in add_yaml_files:
        cls_name, err_count, = file_validation(yml_file_path=ADD_YAML_FILES / file, dt_list=data_type_list, p_list=p_list, mandatorty_attributes=MANDATORY_ATTRIBUTES)
        defined_classes.append(cls_name)
        error_count += err_count
        print('--------------')

    for file in yml_files:
        cls_name, err_count, = file_validation(yml_file_path=YML_DIR_PATH / file, dt_list=data_type_list, p_list=p_list, mandatorty_attributes=MANDATORY_ATTRIBUTES)
        defined_classes.append(cls_name)
        error_count += err_count
        print('--------------')

    # Use one file per class in Conceptual model, e.g. provider.yaml for class Provider
    duplicate_list = [item for item, count in collections.Counter(defined_classes).items() if count > 1]
    if len(duplicate_list) > 0:
        print(
            Fore.RED + "ERROR "
            + " -- " + "class(es) " + str(duplicate_list) + " defined in more than one file" + Style.RESET_ALL)
        error_count += 1
        print('--------------')

    if error_count > 0:
        print(Fore.RED + 'found {} error(s)'.format(error_count) + Style.RESET_ALL)
        os.sys.exit(error_count)
    else:
        print(Fore.GREEN + 'Semantic validation complete: 0 Errors found' + Style.RESET_ALL)