import yaml
import re
import os
import fnmatch
import sys
import rdflib
from rdflib import Graph
from os.path import exists

def parseYAML(input):
    with open(input, "r") as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return data


def getName(title):
    words = re.split('(?=[A-Z])', title)
    name = ''
    for word in words:
        name += word + ' '
    name = name[:-1]
    return name.lower()


def addSuperClasses(classNames, ecosystem, ignoreClasses=None):
    """
    For a given list of classes, recursively find and return their yaml sources.
    """
    datas = []
    files = []
    if ignoreClasses is None:
        ignoreClasses = set()
    superClasses = set(classNames) - set(ignoreClasses)
    for className in superClasses:
        ecosystem = className.split(':')[0]
        className = className.split(':')[1]
        if ecosystem in ['gax-core', 'gax-trust-framework', 'trusted-cloud']:
            files = getYamlFilesFromFolder(getYamlLocation(ecosystem), ecosystem, True)
        for filename in files:
            if className.lower() in filename.lower().replace('-', ''):
                #print(className)
                data = parseYAML(filename)
                if isCorrectYamlForClass(data, className):
                    ignoreClasses.add(className)
                    datas.append(data)
                    newSuperClassNames = getSuperClassesFromYaml(data)
                    datas += (addSuperClasses(newSuperClassNames, ecosystem, ignoreClasses.union(set(classNames))))
    return datas


def appendObjectShapes(objectReferences, file, ecosystem, ignoreObjects=None):
    """
    Recursively append shapes for referenced objects to the output file
    """
    if ignoreObjects is None:
        ignoreObjects = []
    objectReferences = set(objectReferences) - set(ignoreObjects)
    if exists(getValidationYamlLocation(ecosystem)):
        files = getYamlFilesFromFolder(getValidationYamlLocation(ecosystem), ecosystem, False)
        for objectReference in objectReferences:
            prefix, suffix = objectReference.split(":")
            for filename in files:
                if suffix.lower() in filename.lower().replace('-', ''):
                    data = parseYAML(filename)
                    if isCorrectYamlForObject(data, objectReference):
                        names, newReferences = writeShapeToFile(data, file, ecosystem)
                        uniqueObjects = set(newReferences) - objectReferences
                        appendObjectShapes(uniqueObjects, file, ecosystem, set.union(objectReferences, ignoreObjects))


def getSuperClassesFromYaml(data):
    """
    For a given object from a YAML source, extract and return the referenced super classes.
    """
    superClassNames = []
    for key in [*data.keys()]:
        superClassNames += data[key]["subClassOf"]
    return superClassNames


def isCorrectYamlForObject(yamlData, objectReference):
    """
    Check for a given yaml definition and an object reference, if the suitable shape for the reference can be generated
    from the yaml
    """
    prefix, suffix = objectReference.split(":")
    yamlName = [*yamlData.keys()][0]
    yamlPrefix = yamlData[yamlName]["prefix"]
    if yamlName == suffix and yamlPrefix == prefix:
        return True
    return False


def isCorrectYamlForClass(yamlData, className):
    """
    For a given yaml definition and a class name, check if the yaml contains the data for the given class.
    """
    yamlName = [*yamlData.keys()][0]
    if yamlName == className:
        return True
    return False


def getShapeNameForObject(name, ecosystem):
    """
    For a given object reference name, find the suitable yaml definition and construct the name of the matching shape.
    """
    if exists(getValidationYamlLocation(ecosystem)):
        yamlLocation = getValidationYamlLocation(ecosystem)
        files = getYamlFilesFromFolder(yamlLocation, ecosystem, True)
        for file in files:
            data = parseYAML(file)
            if isCorrectYamlForObject(data, name):
                return "gax-validation:%sShape" % ([*data.keys()][0])
    return None


def writeShapeToFile(srcData, shaclFile, ecosystem):
    objectReferences = []
    names = []
    # Create shapes for each class defined in the YAML file
    for key in [*srcData.keys()]:
        prefix = srcData[key]["prefix"]
        superClassNames = srcData[key]["subClassOf"]
        superClassesDataList = addSuperClasses(superClassNames, ecosystem)
        dataList = [srcData] + superClassesDataList
        # Add sh:targetClass for the shape
        line = "\ngax-validation:%sShape\n\ta sh:NodeShape ;\n\tsh:targetClass %s:%s ;\n" % (
        key, prefix, key)
        names.append("%s:%s" % (prefix, key))
        shaclFile.write(line)
        for dataSet in dataList:
            key = [*dataSet.keys()][0]
            # Add constraints depending on the attributes defined in the YAML file
            order = 1
            for attribute in dataSet[key]["attributes"]:
                # Add sh:path constraint
                line = "\tsh:property [ sh:path %s:%s ;\n" % (attribute["prefix"], attribute["title"])
                shaclFile.write(line)

                # Add sh:name
                line = "\t\t\t\t  sh:name \"%s\" ;\n" % getName(attribute["title"])
                shaclFile.write(line)

                # Add sh:description
                for key in attribute["description"]:
                    value = attribute["description"][key]
                    line = "\t\t\t\t  sh:description \"%s\"@%s ;\n" % (value.replace('\"', '\''), key)
                    shaclFile.write(line)


                # Add skos:example
                if (key == "Address"):
                    line = "\t\t\t\t  skos:example \"%s\" ;\n" % str((attribute["exampleValues"])).replace('[', '')
                else:
                    line = "\t\t\t\t  skos:example \"%s\" ;\n" % str((attribute["exampleValues"])).replace('[', '').replace(']', '').replace('\"', '\'')
                shaclFile.write(line)


                # Add sh:order
                line = "\t\t\t\t  sh:order %s ;\n" % order
                shaclFile.write(line)
                order += 1

                # Add sh:minInclusive
                if [*attribute.keys()].__contains__("minValue"):
                    line = "\t\t\t\t  sh:minInclusive %s ;\n" % float(attribute["minValue"])
                    shaclFile.write(line)

                # Add sh:maxInclusive
                if [*attribute.keys()].__contains__("maxValue"):
                    line = "\t\t\t\t  sh:maxInclusive %s ;\n" % float(attribute["maxValue"])
                    shaclFile.write(line)

                # Add sh:in
                if list(attribute.keys()).__contains__("valueIn"):
                    line = "\t\t\t\t  sh:in (%s) ;\n" % str(attribute["valueIn"]).replace('[', '').replace(']', '').replace(',', '').replace('\'', '\"')
                    shaclFile.write(line)

                # Add sh:minCount / sh:maxCount constraints if defined in the YAML file
                if [*attribute.keys()].__contains__("length"):
                    minLength = attribute["length"].split('..')[0]
                    maxLength = attribute["length"].split('..')[1]
                    if minLength != "0":
                        line = "\t\t\t\t  sh:minLength %s ;\n" % (minLength)
                        shaclFile.write(line)
                    if maxLength != "*":
                        line = "\t\t\t\t  sh:maxLength %s ;\n" % (maxLength)
                        shaclFile.write(line)

                # Add sh:minLength / sh:maxLength constraints if defined in the YAML file
                if [*attribute.keys()].__contains__("cardinality"):
                    minCount = attribute["cardinality"].split('..')[0]
                    maxCount = attribute["cardinality"].split('..')[1]
                    if minCount != "0":
                        line = "\t\t\t\t  sh:minCount %s ;\n" % (minCount)
                        shaclFile.write(line)
                    if maxCount != "*":
                        line = "\t\t\t\t  sh:maxCount %s ;\n" % (maxCount)
                        shaclFile.write(line)

                # Add sh:pattern
                if [*attribute.keys()].__contains__("pattern"):
                    line = "\t\t\t\t  sh:pattern \"%s\" ;\n" % getName(attribute["pattern"])
                    shaclFile.write(line)

                # Add sh:flags
                if [*attribute.keys()].__contains__("flags"):
                    line = "\t\t\t\t  sh:flags \"%s\" ;\n" % getName(attribute["flags"])
                    shaclFile.write(line)

                # Add either sh:datatype or sh:class constraint depending on the defined range of the property
                if attribute["dataType"].__contains__("xsd"):
                    line = "\t\t\t\t  sh:datatype %s ] ;\n" % attribute["dataType"]
                    shaclFile.write(line)
                elif attribute["dataType"].__contains__("meaningfulString"):
                    line = "\t\t\t\t  sh:datatype xsd:string ] ;\n"
                    shaclFile.write(line)
                elif [*attribute.keys()].__contains__("dataType"):
                    shapeName = getShapeNameForObject(attribute["dataType"], ecosystem)
                    if shapeName:
                        objectReferences.append(attribute["dataType"])
                        line = "\t\t\t\t  sh:node %s ] ;\n" % shapeName
                    elif attribute["dataType"] in simple_data_types:
                        line = "\t\t\t\t  sh:class %s ] ;\n" % attribute["dataType"]
                    else:
                        line = "\t\t\t\t  sh:nodeKind sh:IRI ] ;\n"
                    shaclFile.write(line)





        # Add dot to close the shape
        line = ".\n"
        shaclFile.write(line)
        return (names, objectReferences)


def writeShaclFile(prefixes, data, output, ecosystem):
    # Create empty SHACL file
    shaclFile = open(output, "w")
    print(output)

    if prefixes:
        # Add SHACL and gax-validation prefix
        line = "@prefix sh: <http://www.w3.org/ns/shacl#> .\n"
        shaclFile.write(line)
        line = "@prefix gax-validation:  <http://w3id.org/gaia-x/validation#> .\n\n"
        shaclFile.write(line)

        # Add all prefixes defined in the YAML file
        for prefix in prefixes["Prefixes"]:
            line = "@prefix %s: <%s> .\n" % (prefix["name"], prefix["value"])
            shaclFile.write(line)

    names, objectReferences = writeShapeToFile(data, shaclFile, ecosystem)
    appendObjectShapes(objectReferences, shaclFile, ecosystem, names)
    shaclFile.close()

    # QUICK FIX TODO: Solve this properly for every possible shape
    g = Graph()
    g.parse(output, format='turtle')
    i = 0
    for s in g.subjects(rdflib.term.URIRef('http://www.w3.org/ns/shacl#path'),
                        rdflib.term.URIRef('http://w3id.org/gaia-x/gax-trust-framework#value')):
        i += 1
        if i > 1:
            g.remove((s, None, None))
            g.remove((None, rdflib.term.URIRef('http://www.w3.org/ns/shacl#property'), s))
    i = 0
    for s in g.subjects(rdflib.term.URIRef('http://www.w3.org/ns/shacl#path'),
                        rdflib.term.URIRef('http://w3id.org/gaia-x/gax-trust-framework#unit')):
        i += 1
        if i > 1:
            g.remove((s, None, None))
            g.remove((None, rdflib.term.URIRef('http://www.w3.org/ns/shacl#property'), s))
    g.serialize(output, format='turtle')

    shaclFile = open(output, "rt")
    dataOfShacl = shaclFile.read()
    dataOfShacl = dataOfShacl.replace('http://w3id.org/gaia-x', '{{BASE_URI}}')
    shaclFile.close()
    shaclFile = open(output, "wt")
    shaclFile.write(dataOfShacl)
    shaclFile.close()


def getYamlFilesFromFolder(path, ecosystem, includeSubdirectories=True):
    files = fnmatch.filter(os.listdir(path), "*.yaml")
    files = [os.path.join(path, f).replace("\\","/") for f in files if (f != "dataTypeAbbreviation.yaml" and f != "prefixes.yaml")]
    if includeSubdirectories:
        subdirectories = [x[0] for x in os.walk(path) if not x[0] == path]
        for directory in subdirectories:
            #if directory != "../single-point-of-truth/yaml/to-be-integrated" and directory != "../single-point-of-truth/yaml/%s/data-types" % ecosystem:
            if directory != "../single-point-of-truth/yaml/to-be-integrated" and directory != "../single-point-of-truth/yaml/%s/data-types" % ecosystem:
                files = files + getYamlFilesFromFolder(directory, ecosystem, True)
    return files


def getOutputFileLocationForYamlFilename(path, outputPath):
    filename = os.path.basename(path)
    return outputPath+ "/" +filename.split(".")[0]+"Shape.ttl"


def getValidationYamlLocation(ecosystem):
    #return "../single-point-of-truth/yaml/%s/data-types/" % ecosystem
    return "../preprocessed_yaml/%s/data-types/" % ecosystem

def getYamlLocation(ecosystem: str):
    return "../preprocessed_yaml/%s/" % ecosystem
    #return "../single-point-of-truth/yaml/%s/" % ecosystem

def iterateFolder(path, ecosystem):
    files = getYamlFilesFromFolder(path, ecosystem)

    for file in files:

        outputPath = os.path.dirname(file).replace('preprocessed_yaml/', 'yaml2shacl/')

        if not exists(outputPath):
            os.mkdir(outputPath)
        output = getOutputFileLocationForYamlFilename(file, outputPath)
        data = parseYAML(file)
        writeShaclFile(prefixes, data, output, ecosystem)


if __name__ == "__main__":

    ecosystems = sys.argv[1:]
    for item in ecosystems:
        path = "../yaml2shacl/%s/" % item
        if not exists(path):
            os.mkdir(path)
        dataTypeAbbreviation = '../single-point-of-truth/yaml/validation/%s/dataTypeAbbreviation.yaml' % item
        if os.stat(dataTypeAbbreviation).st_size > 0:
            simple_data_types = list(parseYAML(dataTypeAbbreviation).keys())
        else:
            simple_data_types = []
        prefixFile = "../single-point-of-truth/yaml/validation/%s/prefixes.yaml" % item
        prefixes = parseYAML(prefixFile)
        # True indicates from preprocessed folder created during preprocessing step
        # Turn False if source should be from ssot/yaml/
        iterateFolder(getYamlLocation(item), item)










