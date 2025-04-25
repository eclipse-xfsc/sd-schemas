from pyshacl import validate
from typing import List
import unittest

from pyshacl import validate
from rdflib import Graph

import os
import sys

'''
Script to validate all Self-Description instances against a set of shacl shapes. 

Call script with two parameters. 
- First parameter: directory with SD instances as json-ld files. All json files will be considered.
- Second parameter: directory with shacl shapes. All shacl shapes will be considered   

'''


def get_all_files(dir: str, file_extension: str) -> List[str]:
    files = []

    for file in os.listdir(os.path.abspath(dir)):
        path = os.path.join(dir, file)
        if os.path.isdir(path):
            files.extend(get_all_files(path, file_extension))
        else:
            if path.endswith(file_extension):
                files.append(path)
    return files


if __name__ == '__main__':
    success = True
    instances = get_all_files(sys.argv[1], ".json")
    shapes = get_all_files(sys.argv[2], ".ttl")

    print("####################################")
    print("# Validating instances...")
    print("####################################")

    for ins_file in instances:
        print(" - Validating " + ins_file + "... ", end="")
        cons_conforms = True
        cons_results_text = ""
        for sh_file in shapes:
            conforms, _, results_text = validate(Graph().parse(source=ins_file, format="json-ld"),
                                                 shacl_graph=Graph().parse(source=sh_file),
                                                 inference='rdfs',
                                                 advanced=True,
                                                 js=True,
                                                 meta_shacl=True)

            cons_conforms = cons_conforms and conforms
            results_text = +results_text

            if cons_conforms:
                print("OK", end="\n")
            else:
                print("ERROR", end="\n")
                print(cons_results_text)
                success = False

    if success:
        sys.exit(0)
    else:
        sys.exit(1)