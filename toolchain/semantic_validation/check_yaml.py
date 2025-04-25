#!/usr/bin/env python3
import sys
import yaml

from pathlib import Path
import csv
import re

from typing import Dict, List
from colorama import Fore, Style

import collections
import os


def load_yaml_file(filepath: Path) -> Dict:
    with open(filepath, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(Fore.RED + "ERROR in file " + str(filepath) + " -- " + " unable to load yaml file" + Style.RESET_ALL)
            print(exc)
            return {}


# get all yaml or yml files except those who contain example in their name
def load_yml_file_paths(yml_folder: Path) -> List:
    file_paths = []
    print("loading files ...... ")
    for root, dirs, files in os.walk(str(yml_folder)):
        path = root.split(os.sep)
        print((len(path) - 1) * '---', os.path.basename(root))
        for file in files:
            if file.endswith(".yaml"):
                file_paths.append(Path(root + "/" + file))
            elif file.endswith(".yml"):
                print(Fore.YELLOW + " Warning file " + str(
                    root + "/" + file) + " -- " + "not considered. Rename to extension .yaml" + Style.RESET_ALL)
    return file_paths

def load_data_type_list(data_type_abbreviation_path: Path) -> List:

    data_types = load_yaml_file(data_type_abbreviation_path)

    # if yaml file is empty return empty list instead
    if data_types is not None:
        return list(data_types.keys())
    else:
        return []


def load_prefix_list(prefix_path: Path) -> List:
    prefix_dic = load_yaml_file(prefix_path)
    lvl0 = list(prefix_dic.keys())[0]
    prefixes = [p['name'] for p in list(prefix_dic[lvl0])]
    return prefixes


# goes through all yaml files and checks if all DataTypes exist defines DataTypes
def discover_object_data_types(yml_files: List) -> (List, int):
    additional_datatypes = []
    error_count = 0
    for file in yml_files:
        yml_dic = load_yaml_file(filepath=file)
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
    prefix = yml_dic[cls_name]['prefix']
    full_name = prefix + ":" + cls_name

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
                        print(Fore.RED + "ERROR in file " + str(yml_file_path)
                              + " -- " + "prefix " + val + " not defined in yaml/validation/prefixes.yaml " + Style.RESET_ALL)
                        err_count += 1

                # Element cardinality is optional. If its is missing, the attribute is considered to be optional.
                # Value of minCount and maxCount must be a positive integer
                if itm == 'cardinality':
                    if type(val) is str:
                        pattern = re.compile("(^[1-9]+[1-9]*$)|^([0-9]+[0-9]*[.]{2}([*]|[0-9]+[0-9]*))$")
                        if not pattern.match(val):
                            print(Fore.RED + "ERROR in file " + str(yml_file_path)
                                  + " -- " + itm + " does not match cardinality pattern " + Style.RESET_ALL)
                            err_count += 1
                        # check cardinality for sematic errors.
                        # E.g 2..1 not possible but 1..2 possible
                        else:
                            inside_pattern = re.compile("^[0-9]+[0-9]*[.]{2}[0-9]+[0-9]*$")
                            if inside_pattern.match(val):
                                values = str(val).split(sep='..')
                                min_count = values[0]
                                max_count = values[1]
                                if max_count < min_count:
                                    print(Fore.RED + "ERROR in file " + str(yml_file_path)
                                          + " -- " + itm + " -> " + val + " cannot have  a > b" + Style.RESET_ALL)
                                    err_count += 1

                    else:
                        print(Fore.RED + "ERROR in file " + str(yml_file_path)
                              + " -- " + itm + " is not a string" + Style.RESET_ALL)
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

    return full_name, err_count


def execute_validation(root_path: str, ecosystems: list, val_path: str, semantic_val_mandatory_attributes: str, ):
    print("Starting semantic validation of yaml files")

    # List of files
    error_count = 0

    # list of discovered classes in all files
    defined_classes = []

    with open(semantic_val_mandatory_attributes, newline='') as csvfile:
        print("1: mandatory attributes loaded")
        reader = csv.reader(csvfile, delimiter=',')
        mandatory_attributes = [atr[0] for atr in reader]

    yml_files = []
    data_type_list = []
    p_list = []
    print("2: loading associated files from ecosystems")
    for ecosystem in ecosystems:
        print("loading files from: " + ecosystem)
        yaml_path: Path = Path(root_path) / ecosystem
        prefix_path: Path = Path(val_path) / ecosystem / "prefixes.yaml"
        dta_path: Path = Path(val_path) / ecosystem / "dataTypeAbbreviation.yaml"

        yml_files = yml_files + load_yml_file_paths(yaml_path)
        data_type_list = data_type_list + load_data_type_list(dta_path)
        p_list = p_list + load_prefix_list(prefix_path)

    try:
        print("3: discovering additional datatypes")
        print("Loaded datatytpes :")
        data_type_list_1, err_count_1 = discover_object_data_types(yml_files=yml_files)
        data_type_list = data_type_list + data_type_list_1
        error_count = err_count_1
        print("-------------")
        print(data_type_list)
        print("-------------")

    except Exception:
        print(
            Fore.RED + "Error while discovering dataTypes specified in *.yaml files: Moving forward without loading additional dataTypes!" + Style.RESET_ALL)

    print("===========================================")
    print("Begin file validation")
    print("===========================================")

    for file in yml_files:
        cls_name, err_count, = file_validation(yml_file_path=file, dt_list=data_type_list, p_list=p_list,
                                               mandatorty_attributes=mandatory_attributes)
        defined_classes.append(cls_name)
        print('defined class -> ' + cls_name)
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
