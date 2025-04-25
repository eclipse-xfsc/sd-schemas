from rdflib import Graph
import os

def mergeOntology(ont1, ont2, output):
    g = Graph()
    g.parse(ont1, format='turtle')
    g.parse(ont2, format='turtle')
    g.serialize(output, format='turtle')