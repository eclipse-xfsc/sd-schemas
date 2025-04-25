#!/usr/bin/env python3
import sys

import fnmatch
import os
import yaml
from pathlib import Path
from typing import Dict, List
from colorama import Fore, Style
import re
from datetime import datetime
import pytz

def parseYAML(input) -> Dict:
    with open(input, "r") as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return data


def load_yml_file_paths(yml_folder: Path, ecosystems: List) -> List:
    file_paths = []
    eco_sys: list = [str(yml_folder / str(eco)) for eco in ecosystems]
    print("loading files ...... ")
    for root, dirs, files in os.walk(str(yml_folder)):
        if root.startswith(tuple(eco_sys)):
            path = root.split(os.sep)
            print((len(path) - 1) * '---', os.path.basename(root))
            for file in files:
                if file.endswith(".yaml"):
                    file_paths.append(Path(root + "/" + file))
                elif file.endswith(".yml"):
                    print(Fore.YELLOW + " Warning file " + str(
                        root + "/" + file) + " -- " + "not considered. Rename to extension .yaml" + Style.RESET_ALL)
    return file_paths

def sort_by_ecosystem(root:Path, files: list, ecosystems: list) -> dict:
    # setup empty dictionary
    classified_by_ecosystem = { i : [] for i in ecosystems }

    for path in files:
        for eco in ecosystems:
            eco_path = str(root / eco)
            if str(path).startswith(eco_path):
                classified_by_ecosystem[eco].append(path)

    return classified_by_ecosystem

def string_escape(s, encoding='utf-8'):

    """
    A method used for escaping special chars in a string.
    """

    return (s.encode('latin1')  # To bytes, required by 'unicode-escape'
            .decode('unicode-escape')  # Perform the actual octal-escaping decode
            .encode('latin1')  # 1:1 mapping back to bytes
            .decode(encoding))  # Decode original encoding


def camel_case_split(str):
    """
    :param str:  A camelCase String.
    :return: a string that with spaces between camel Case.
    """
    strings = re.findall(r'[A-Za-z](?:[a-z]+|[A-Z]*(?=[AZ]|$))', str)

    result = ""
    for i, itm in enumerate(strings):
        result = result + itm
        if i + 1 < len(strings):
            result = result + " "

    return result


def generate_ontology_file(save_to: Path, name: str, yaml_base_files: List, simple_data_types: List, prefixes: dict,
                           prefix_metadata_dic: dict, ecosystems: List):

    """
    Computes *.ttl files that describe the ontology  and saves them to save_to: Path

    :param save_to: path to folder where *.ttl files will be saved
    :param name: name of prefix
    :param yaml_base_files: paths of yaml files that are associated with prefix = name
    :param simple_data_types: list of simple dataTypes that distinguish owl:DatatypeProperty and owl:ObjectProperty
    :param prefixes: List of prefixes to add at the beginning
    :param prefix_metadata_dic: Folder that defines description of prefixes (not defined in yaml files)
    """

    ## distance between name and value.
    distance = "\t\t"

    file_name = str(name) + "_generated.ttl"
    # parse list of Paths to list of filenames without full path
    base_files = [x.name for x in yaml_base_files]
    print("generating " + str(save_to / file_name))
    ttlFile = open((save_to / file_name), "w")

    #### Definition prefeix
    for prefix in prefixes["Prefixes"]:
        line = "@prefix %s: <%s> .\n" % (prefix["name"], prefix["value"])
        ttlFile.write(line)

    end_of_line = "\n\n"
    ttlFile.write(end_of_line)


    # generate prefix content
    line = name + ": \n"
    ttlFile.write(line)
    for itm in prefix_metadata_dic['OntologyDescription']:
        itm_name = itm['name']
        value = itm['value']
        if isinstance(value, list):
           value = ', '.join(value)

        line = itm_name + distance + value + " ;\n"
        ttlFile.write(line)

    today = datetime.now(pytz.timezone('Europe/Paris')).isoformat(' ', 'seconds').replace(" ", "T")
    line = 'dct:modified' + distance + "\"" + today + "\"^^xsd:dateTimeStamp ;\n"

    ttlFile.write(line)

    end_of_line = ".\n\n"
    ttlFile.write(end_of_line)

    ## END of prefix context ##

    # generate yaml file content
    print('considering ... ')
    for file in yaml_base_files:
        print(file)
        yml_dic = parseYAML(file)
        for key in [*yml_dic.keys()]:
            class_name = key
            prefix = yml_dic[key]["prefix"]
            subclasses = yml_dic[key]["subClassOf"]
            assert prefix == name
            full_class_name = prefix + ":" + class_name

            ttlFile.write('################## \n##{0}\n##################\n\n'.format(class_name))

            ttlFile.write(full_class_name)

            l0 = "\n\ta{0} owl:Class;".format(distance)
            l1 = "\n\trdfs:label{0} \"{1}\"@en ;".format(distance, camel_case_split(class_name))

            l2 = ""
            if subclasses:
                l2 = "\n\trdfs:subClassOf{0}".format(distance)

                subclasses_modified = []
                for sub_class in subclasses:
                    if str(sub_class).startswith("http"):
                        subclasses_modified.append("<" + sub_class + ">")
                    else:
                        subclasses_modified.append(sub_class)

                l2 = l2 + ', '.join(subclasses_modified)
                l2 = l2 + " ;"

            line_list = [l0, l1, l2]
            for itm in line_list:
                ttlFile.write(itm)

            end_of_line = "\n. \n\n"
            ttlFile.write(end_of_line)

            for attribute in yml_dic[key]["attributes"]:

                title = attribute['title']
                prefix = attribute['prefix']
                dataType = attribute['dataType']
                # removes any quotes in string
                description = attribute['description'].replace('"','\\"')

                indicator = True
                for ecosystem in ecosystems:
                    if ecosystem in prefix:
                        indicator = False
                        li0 = prefix + ":" + title
                        if dataType in simple_data_types:
                            li1 = "\n\ta{0} owl:DatatypeProperty ;".format(distance)
                        else:
                            li1 = "\n\ta{0} owl:ObjectProperty ;".format(distance)

                        li2 = "\n\trdfs:label{0} \"{1}\"@en ;".format(distance, camel_case_split(title).lower())
                        li3 = "\n\trdfs:domain{0} {1} ;".format(distance, full_class_name)
                        li4 = "\n\trdfs:range{0} {1} ;".format(distance, dataType)
                        li5 = "\n\trdfs:comment{0} \"{1}\" ;".format(distance, description)

                        line_list = [li0, li1, li2, li3, li4, li5]
                        for itm in line_list:
                            ttlFile.write(itm)

                        end_of_line = "\n. \n\n"
                        ttlFile.write(end_of_line)
                if indicator:
                    pass
                    print("Escaping: " + prefix + ":" + title)

    ttlFile.close()

def find_matches(files: list, prefixes: Dict, ecosystem: str) -> Dict:
    """ Returns a dic. containing a list of files that are associated with one prefix"""

    # creates output dictionary with expected prefixes
    keys = [p['name'] for p in prefixes["Prefixes"] if ecosystem in p['name']]
    matches = dict(zip(keys, [None] * len(keys)))

    # get prefix of yaml file
    for file in files:
        yaml_dic = parseYAML(file)

        name = list(yaml_dic.keys())
        prefix = yaml_dic[name[0]]['prefix']

        if prefix in keys:
            if matches[prefix] is None:
                matches[prefix] = [file]
            else:
                matches[prefix].append(file)
        else:
            print(Fore.YELLOW + "Warning"
                  + " -- " + str(file) + " uses " + str(prefix) + " current ecosystem is " + str(ecosystem) + " => file is ignored during ontology generation "  + Style.RESET_ALL) # the path that was originally here was a lie

    # remove prefixes that are not found
    for itm in list(matches.keys()):
        if matches[itm] is None:
            matches.pop(itm, None)

    return matches


