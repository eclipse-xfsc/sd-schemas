#!/usr/bin/env python3
import os
import pyshacl
import rdflib
import sys
from colorama import Fore, Style
import glob

def mergeDataGraphs(eco):
    graph = rdflib.Graph()
    root = '../implementation/instances/%s' % eco
    for path, subdirs, files in os.walk(root):
        for name in files:
            filename = os.path.join(path, name)
            file_name, file_extension = os.path.splitext(filename)
            if (file_extension != ".jsonld"):
                continue
            try:
                graph.parse(filename, format='json-ld')
            except Exception as e:
                raise Exception("An error occurred while parsing " + str(filename) + ": " + str(e))

    graph.serialize('mergedDataGraph.ttl', format='ttl')

def validation(eco):

    err_count = 0
    root = '../yaml2shacl/%s' % eco
    for path, subdirs, files in os.walk(root):
        for name in files:
            filename = os.path.join(path, name)
            file_name, file_extension = os.path.splitext(filename)
            if(file_extension != ".ttl"):
                continue
            print(filename)
            # Read in the file
            with open(filename, 'r') as file:
                filedata = file.read()

            # Replace the target string
            filedata = filedata.replace('{{BASE_URI}}', 'http://w3id.org/gaia-x')

            # Write the file out again
            with open(filename, 'w') as file:
                file.write(filedata)

            r = pyshacl.validate('mergedDataGraph.ttl', shacl_graph=filename, inference='rdfs')
            conforms, results_graph, results_text = r
            if not conforms:
                print(results_text)
                err_count += 1
    for filename in glob.glob('../single-point-of-truth/shacl/*.ttl'):
        print(filename)
        r = pyshacl.validate('mergedDataGraph.ttl', shacl_graph=filename, inference='rdfs')
        conforms, results_graph, results_text = r
        if not conforms:
            print(results_text)
            err_count += 1
    return err_count


if __name__ == '__main__':

    ecosystems = sys.argv[1:]
    err_overall = 0
    for eco in ecosystems:
        mergeDataGraphs(eco)
        err_count = validation(eco)
        err_overall += err_count

    if err_overall > 0:
        print(Style.BRIGHT + Fore.RED + 'found {} error(s)'.format(err_overall))
    os.sys.exit(err_overall)

