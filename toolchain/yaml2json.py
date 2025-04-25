from pathlib import Path

import yaml
import json
import sys
import re
import os
import fnmatch


def parseYAML(input):
    with open(input, "r") as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return data


def write_from_external_json(name, begin, end, file, lvl):

    try:
        with open(OUTPUT + name.lower() + ".json") as f:
            for i, line in enumerate(f):
                if i >= begin and i <= end:
                    file.write(lvl + line)
    except Exception as e:
        print("write_from_external_json" + str(e) + " - " + name + " - " + file.name)
        sys.exit(1)


def construct_example_line(attribute, lvl, nl):
    # if list of examples contains one element add example without comma separation
    if len(attribute['exampleValues']) == 1:
        examples = attribute['exampleValues'][0]
        examples = examples.replace('"', '\\"')
        line = lvl + "\"examples\": [\"" + str(examples) + "\"]" + nl

    # if list of examples is > 1 construct a comma seperated String
    else:
        examples = [str(xmpl).replace('"','\\"') for xmpl in attribute['exampleValues']]
        examples = ["\"" + str(xmpl) + "\"" for xmpl in examples]
        line = lvl + "\"examples\": [" + ','.join(map(str, examples)) + "]" + nl

    return line


def check_required(attribute):

    required = False

    if [*attribute.keys()].__contains__("cardinality"):
        if [*attribute.keys()].__contains__("cardinality"):
            if not re.match(r"[0-9]..([0-9]+|\*)", attribute["cardinality"]):
                raise Exception("The cardinality pattern isn't conform to the definition")
            min_count = int(attribute["cardinality"].split('..')[0])
            if min_count >= 1:
                required = True
            # for cardinalityValue in [*attribute["cardinality"].keys()]:
            #     if cardinalityValue == "minCount":
            #         min_count = attribute["cardinality"][cardinalityValue]
            #         if min_count >= 1:
            #             required = True
    return required


def construct_type_line(attribute, lvl, lvl_up, nl):
    # if list of examples contains one element add example without comma separation
    lvl2 = lvl + lvl_up

    out_line = ""

    attribute_type = compute_type(attribute)

    required = False
    min_count = None
    max_count = None
    if [*attribute.keys()].__contains__("cardinality"):
        if not re.match(r"[0-9]..([0-9]+|\*)", attribute["cardinality"]):
            raise Exception("The cardinality pattern isn't conform to the definition")
        min_count = int(attribute["cardinality"].split('..')[0])
        max_count = attribute["cardinality"].split('..')[1]
        if max_count != "*":
            max_count = int(max_count)
        else:
            max_count = None

        # if [*attribute.keys()].__contains__("cardinality"):
        #     for cardinalityValue in [*attribute["cardinality"].keys()]:
        #         if cardinalityValue == "minCount":
        #             min_count = attribute["cardinality"][cardinalityValue]
        #             if min_count >= 1:
        #                 required = True
        #         elif cardinalityValue == "maxCount":
        #             max_count = attribute["cardinality"][cardinalityValue]
        #         else:
        #             raise Exception("Unexpected cardinality value")
    if min_count is None and max_count is None:
        line = lvl + "\"type\": \"array\"" + ",\n"
        line_itm_open = lvl + "\"items\": {\n"
        line3 = lvl2 + "\"type\": \"" + attribute_type +"\"\n"
        line_itm_close = lvl + "},\n"
        out_line = out_line + line + line_itm_open + line3 + line_itm_close
    elif min_count >= 0 and (max_count is None or max_count > 1):
        line = lvl + "\"type\": \"array\"" + ",\n"
        line_itm_open = lvl + "\"items\": {\n"
        line3 = lvl2 + "\"type\": \"" + attribute_type + "\"\n"
        line_itm_close = lvl + "},\n"
        out_line = out_line + line + line_itm_open + line3 + line_itm_close

        if max_count is None:
            line_min_count = lvl + "\"minItems\":" + str(min_count) + nl
            out_line = out_line + line_min_count
        else:
            line_min_count = lvl + "\"minItems\":" + str(min_count) + ",\n"
            line_max_count = lvl + "\"maxItems\":" + str(max_count) + nl
            out_line = out_line + line_min_count + line_max_count

    elif min_count >= 0 and max_count == 1:
        line = lvl + "\"type\": \"" + attribute_type + "\"" + nl
        out_line = line

    else:
        raise Exception("Error constructing type: Undefined operation")

    return out_line, required


def write_property(jsonFile, starting_distance, attribute, simple_dataTypes,
                   last, complex_dataTypes, serial_list, copy_paste_map):  # description & examples

    """
    core method that is used to write a single property.
    """

    required = False
    distance = "\t"
    separator = ","
    nl = "\n"
    separator_nl = separator + nl

    full_name = attribute['prefix'] + ":" + attribute['title']
    line_start = starting_distance + "\"" + full_name + "\": {" + nl
    jsonFile.write(line_start)

    # description
    lvl2 = starting_distance + distance
    line = lvl2 + "\"description\": \"" + attribute['description'].replace('"', '\\"') + "\"" + separator_nl
    jsonFile.write(line)

    lvl3 = lvl2 + distance
    lvl4 = lvl3 + distance
    if attribute['dataType'] in simple_dataTypes:
        attribute_type = compute_type(attribute)

        # @type block
        if attribute['dataType'] in serial_list:
            line, required = construct_type_line(attribute=attribute, lvl=lvl2, lvl_up=distance, nl=separator_nl)
            line2 = construct_example_line(attribute=attribute, lvl=lvl2, nl=nl)

            jsonFile.write(line + line2)

        # type, value definition
        else:
            # description
            line = lvl2 + "\"type\": \"" + "object" + "\"" + separator_nl

            jsonFile.write(line)

            # adding reqruired
            line = lvl2 + "\"required\": [" + "\"@type\"" + "," + "\"@value\"" + "]" + separator_nl
            jsonFile.write(line)

            # open propoerties lvl3
            line = lvl2 + "\"properties\": {" + nl
            jsonFile.write(line)

            line0 = lvl3 + "\"@type\": {" + nl
            line1 = lvl4 + "\"type\": \"" + attribute_type + "\"" + separator_nl
            line2 = lvl4 + "\"const\":" + "\"" + attribute['dataType'] + "\"" + separator_nl
            line3 = lvl4 + "\"examples\":" + "[\"" + attribute['dataType'] + "\"]" + nl
            line4 = lvl3 + "}" + separator_nl
            jsonFile.write(line0 + line1 + line2 + line3 + line4)

            # value block
            line0 = lvl3 + "\"@value\": {" + nl
            # line1 = lvl4 + "\"type\": \"string\"" + separator_nl
            line1, required = construct_type_line(attribute=attribute, lvl=lvl4, lvl_up=distance, nl=separator_nl)
            line2 = construct_example_line(attribute=attribute, lvl=lvl4, nl=nl)
            line3 = lvl3 + "}" + nl

            jsonFile.write(line0 + line1 + line2 + line3)

            # closing property lvl3
            line = lvl2 + "}" + nl
            jsonFile.write(line)

    # @TODO write function for to outsource redundancies
    else:
        atr_name: str = str(attribute['dataType']).split(":")[1]
        required = check_required(attribute)

        if str(attribute['dataType']).startswith("gax-") or \
           str(attribute['dataType']).startswith("trusted-"):

            # for cases like e.g standard which can be either a URI or a in-place definition
            if atr_name in complex_dataTypes["blank_nodes"] and atr_name in complex_dataTypes["core_classes"]:
                lvl5 = lvl4 + distance

                # any of begin
                line00 = lvl2 + "\"anyOf\": [" + nl

                line01 = lvl3 + "{\n"
                line0 = lvl3 + "\"type\": \"object\"" + separator_nl
                line1 = lvl3 + "\"required\": [\"@id\"]" + separator_nl
                line2 = lvl4 + "\"properties\": {" + nl
                line3 = lvl4 + "\"@id\": {" + nl
                line4, required = construct_type_line(attribute=attribute, lvl=lvl5, lvl_up=distance, nl=separator_nl)
                line5 = construct_example_line(attribute=attribute, lvl=lvl5, nl=nl)
                line6 = lvl5 + "}" + nl
                line7 = lvl4 + "}" + nl
                line02 = lvl3 + "},\n"

                jsonFile.write(line00 + line01 + line0 + line1 + line2 + line3 + line4 + line5 + line6
                               + line7 + line02)

                line01 = lvl3 + "{\n"
                jsonFile.write(line01)

                start = copy_paste_map[atr_name.lower()]['start']
                end = copy_paste_map[atr_name.lower()]['end']
                write_from_external_json(name=atr_name, begin=start, end=end, file=jsonFile, lvl=lvl2)

                line02 = lvl3 + "}\n"
                jsonFile.write(line02)

                line03 = lvl2 + "]" + nl
                jsonFile.write(line03)

            # case only inplace definition copy paste from already existing file
            elif atr_name in complex_dataTypes["blank_nodes"] and not atr_name in complex_dataTypes["core_classes"]:
                start = copy_paste_map[atr_name.lower()]['start']
                end = copy_paste_map[atr_name.lower()]['end']
                write_from_external_json(name=atr_name, begin=start, end=end, file=jsonFile, lvl=starting_distance)

            # easy case simply load @id no in place definition`
            elif not atr_name in complex_dataTypes["blank_nodes"] and atr_name in complex_dataTypes["core_classes"]:

                line0 = lvl2 + "\"type\": \"object\"" + separator_nl
                line1 = lvl2 + "\"required\": [\"@id\"]" + separator_nl
                line2 = lvl2 + "\"properties\": {" + nl
                line3 = lvl3 + "\"@id\": {" + nl
                line4, required = construct_type_line(attribute=attribute, lvl=lvl4, lvl_up=distance, nl=separator_nl)
                line5 = construct_example_line(attribute=attribute, lvl=lvl4, nl=nl)
                line6 = lvl3 + "}" + nl
                line7 = lvl2 + "}" + nl

                jsonFile.write(line0 + line1 + line2 + line3 + line4 + line5 + line6 + line7)

            else:
                print(atr_name)
                print(attribute)
                print("COMPLEX: " + str(complex_dataTypes))
                print("SIMPLE: " + str(simple_dataTypes))
                print("CP-MAP: " + str(copy_paste_map))
                raise Exception('undefined')
        # default load
        else:
            try:
                start = copy_paste_map[atr_name.lower()]['start']
                end = copy_paste_map[atr_name.lower()]['end']
                write_from_external_json(name=atr_name, begin=start, end=end, file=jsonFile, lvl=starting_distance)
            except Exception as e:
                print(atr_name)
                print(attribute)
                print("COMPLEX: " + str(complex_dataTypes))
                print("SIMPLE: " + str(simple_dataTypes))
                print("CP-MAP: " + str(copy_paste_map))
                raise e

    # decide if after this property comes another property or not
    # important to close brackets correctly
    if last is False:
        line_end = starting_distance + "}" + separator_nl
    else:
        line_end = starting_distance + "}" + nl

    jsonFile.write(line_end)

    return required


def compute_type(atr):

    datatype = atr['dataType']
    d1_list = ['xsd:string']
    d2_list = ["xsd:decimal", "xsd:float", "xsd:double", "xsd:integer"]
    d3_list = ['xsd:boolean']

    if datatype in d1_list:
        return "string"
    elif datatype in d2_list:
        return "number"
    elif datatype in d3_list:
        return "boolean"
    else:
        return "string"


def createJson(name, data, output, simple_dataTypes, complex_dataTypes, serial_list, copy_paste_map):
    jsonFile = open(output, "w")
    print("Generating : " + str(name) + ".json")

    # define constant vars
    distance = "\t"
    separator = ","
    nl = "\n"
    separator_nl = separator + nl
    lvl_2 = distance + distance
    lvl_3 = lvl_2 + distance
    lvl_4 = lvl_3 + distance

    # begin Json file
    # setup
    jsonFile.write("{\n")
    jsonFile.write(distance + "\"$schema\": \"https://json-schema.org/draft/2020-12/schema\"" + separator_nl)
    jsonFile.write(str(distance + "\"$description\": \"A self description  of a(n) {0}\"" + separator_nl).format(name))
    jsonFile.write(distance + str("\"title\": \"{0}\"").format(name) + separator_nl)
    jsonFile.write(distance + str("\"type\": \"object\"") + separator_nl)

    # iterate over
    for key in [*data.keys()]:

        prefix = data[key]['prefix']
        subclassOf = data[key]['subClassOf']

        # each attribute with min_count >=1 is requireD
        required_attributes_base = []
        required_attributes = []
        if name.lower() in [str(x).lower() for x in complex_dataTypes['core_classes']]:
            required_attributes_base = ["\"@context\"", "\"@id\"", "\"@type\""]
        else:
            required_attributes_base = []

        lvl_2 = distance + distance
        lvl_3 = lvl_2 + distance
        lvl_4 = lvl_3 + distance

        # opening new attributes
        line = "\"properties\": {"
        jsonFile.write(distance + line + nl)

        if required_attributes_base:
            # opening basic required properties independent of yaml file
            # 1st: @context
            # 2nd: @id
            # 3rd: @type

            ####### Context ##########
            context_open = lvl_2 + "\"@context\": {" + nl
            context_1 = lvl_3 + "\"type\": \"object\" " + separator_nl
            context_2 = lvl_3 + "\"patternProperties\": {" + nl
            context_3 = lvl_4 + " \"^[a-z]\": { \"type\": \"string\" }" + nl
            context_close = lvl_3 + "}" + separator_nl
            context_close1 = lvl_3 + "\"additionalProperties\": false" + nl
            context_close2 = lvl_2 + "}" + separator_nl

            context = context_open + context_1 + context_2 + context_3 + \
                      context_close + context_close1 + context_close2
            jsonFile.write(context)

            ####### id ##########

            id_open = lvl_2 + "\"@id\": {" + nl
            id_1 = lvl_3 + "\"type\": \"string\" " + nl
            # id_1 = lvl_3 + "\"description\": \"string\" " + separator_nl
            id_close = lvl_2 + "}" + separator_nl

            id = id_open + id_1 + id_close
            jsonFile.write(id)

            ####### @type ##########
            type_open = lvl_2 + "\"@type\": {" + nl
            type_1 = lvl_3 + "\"type\": \"string\" " + nl
            type_close = lvl_2 + "}" + separator_nl

            type = type_open + type_1 + type_close
            jsonFile.write(type)

        for i, attribute in enumerate(data[key]["attributes"]):
            if i < len(data[key]["attributes"]) - 1:
                req = write_property(jsonFile, lvl_2, attribute, simple_dataTypes, False,
                                     complex_dataTypes, serial_list, copy_paste_map)
            else:
                req = write_property(jsonFile, lvl_2, attribute, simple_dataTypes, True,
                                     complex_dataTypes, serial_list, copy_paste_map)
            if req is True:
                full_name = attribute['prefix'] + ":" + attribute['title']
                required_attributes.append("\"" + full_name + "\"")

    required_attributes = required_attributes + required_attributes_base
    if len(required_attributes) > 0:
        line = distance + "}" + separator_nl
        jsonFile.write(line)
        required_line = distance + "\"required\": [" + ','.join(map(str, required_attributes)) + "]" + nl
        jsonFile.write(required_line)
    else:
        line = distance + "}" + nl
        jsonFile.write(line)


    jsonFile.write("}")

    jsonFile.close()


def sort_files(array, complex_dataTypes):
    """
    reorders the input array such that files that are necessary for the generation of other
    files are generated first
    """
    blank_nodes = complex_dataTypes['blank_nodes']
    prio = []
    for blank_node in blank_nodes:
        match = [x for x in array if blank_node.lower() in str(x)]
        prio = prio + match
    after_prio = [item for item in array if item not in prio]

    new_list = prio + after_prio
    return new_list


def iterateFolder(path, output, simple_data_types, complex_dataTypes, serial_list, copy_paste_map):
    """
    Iterates over all the input files.
    """
    files = fnmatch.filter(os.listdir(path), "*.yaml")
    files = sort_files(files, complex_dataTypes)
    if "trusted-cloud-service-offering.yaml" in files:
        files.remove("trusted-cloud-service-offering.yaml")
        files.append("trusted-cloud-service-offering.yaml")
    for file in files:
        input = path + file
        out = output + file.split(".")[0] + ".json"
        if file == "dataTypeAbbreviation.yaml" or file == "prefixes.yaml":
            continue
        else:
            data = parseYAML(input)
            createJson(file.split(".")[0], data, out, simple_data_types, complex_dataTypes, serial_list, copy_paste_map)


def get_gax_core_classes(path):
    core_classes = []
    blank_nodes = []

    files = fnmatch.filter(os.listdir(path), "*.yaml")
    for file in files:
        if file == "dataTypeAbbreviation.yaml" or file == "prefixes.yaml":
            continue
        else:
            input = path + file
            data = parseYAML(input)
            name = list(data.keys())[0]
            if str(data[name]['prefix']).startswith('gax-'):
                if data[name]['subClassOf']:
                    core_classes.append(name)
                else:
                    if name == "Measure":
                        blank_nodes.insert(0, name)
                    else:
                        blank_nodes.append(name)

    return core_classes, blank_nodes


if __name__ == "__main__":

    # use second output for loading new json examples in associated folder
    OUTPUT = "../yaml2json/"
    #OUTPUT = "../implementation/validation/instance_json_validation/"


    serial_list = ["xsd:string"] # string boolean string number

    # Defining which Json files have to be inserted in others.
    gax_core_exceptions = ['Resource', 'ServiceOffering', 'Participant', 'Standard', 'HardwareSpec']
    gax_blank_exceptions = ['Standard']

    # searching for core classes:
    # Not to be confused with gax-core. a Core class is a class that is a subclass of a gax_core_exception class.
    gax_core_classes, gax_blank_nodes = get_gax_core_classes("../allYaml/")
    tmp_core, tmp_blank = get_gax_core_classes("../single-point-of-truth/yaml/validation/")

    # adjusting for gax_blank_exceptions
    gax_blank_nodes = [blank for blank in gax_blank_nodes if blank in gax_core_classes]
    additional_core_classes = [core for core in gax_core_exceptions if core not in gax_core_classes]
    additional_blank_classes = [blank for blank in gax_blank_exceptions if blank not in gax_blank_nodes]

    # adjusting for files in validation folder/ Expected to not be core classes
    gax_core_classes = gax_core_classes + additional_core_classes + tmp_core
    gax_blank_nodes = gax_blank_nodes + additional_blank_classes + tmp_blank


    # @TODO write function computing which lines to copy over from json files
    # begin from first type to last required
    # for deploy we have 5 files from which we need to copy thus we define this mapping here manually to save time
    copy_paste_map = {"address": {"start": 4, "end": 27},
                      "agent": {"start": 4, "end": 38},
                      "measure": {"start": 4, "end": 17},
                      "standard": {"start": 4, "end": 50},
                      "endpoint": {"start": 4, "end": 94},
                      "flavor": {"start": 4, "end": 100},
                      }

    gax_complex_dataTypes = {"blank_nodes": gax_blank_nodes,
                             "core_classes": gax_core_classes}

    # Defining for which simple_dataTypes defined in the data_abbreviation list we do not require @value and @type syntax
    serial_list = ["xsd:string",
                   "xsd:decimal", "xsd:float", "xsd:double", "xsd:integer",
                   "xsd:boolean"]  # , "xsd:decimal"]

    dataTypeAbbreviation = Path('../single-point-of-truth/yaml/validation/dataTypeAbbreviation.yaml')
    simple_data_types = list(parseYAML(dataTypeAbbreviation).keys())

    print("Starting Json generation with target folder: " + OUTPUT)

    # adjust for corner case standard.yaml
    # hack it dirty :P
    data = parseYAML("../single-point-of-truth/yaml/gax-core/standard.yaml")
    createJson("standard", data, OUTPUT + "standard.json", simple_data_types, gax_complex_dataTypes, serial_list, copy_paste_map)
    ####

    iterateFolder(path="../single-point-of-truth/yaml/validation/", output=OUTPUT, simple_data_types=simple_data_types,
                  complex_dataTypes=gax_complex_dataTypes, serial_list=serial_list,
                  copy_paste_map=copy_paste_map)

    # This is just a temporary fix
    gax_complex_dataTypes['core_classes'].append('TrustedCloudServiceOfferingCertificates')
    gax_complex_dataTypes['core_classes'].append('TrustedCloudServiceOfferingArchitecture')
    gax_complex_dataTypes['core_classes'].append('TrustedCloudServiceOfferingOperativeProcesses')
    gax_complex_dataTypes['core_classes'].append('TrustedCloudServiceOfferingInteroperability')
    gax_complex_dataTypes['core_classes'].append('TrustedCloudServiceOfferingContracts')
    gax_complex_dataTypes['core_classes'].append('TrustedCloudServiceOfferingSecurity')
    gax_complex_dataTypes['core_classes'].append('TrustedCloudServiceOfferingDataProtection')
    gax_complex_dataTypes['core_classes'].append('TrustedCloudSubCompanies')

    iterateFolder(path="../allYaml/", output=OUTPUT, simple_data_types=simple_data_types,
                  complex_dataTypes=gax_complex_dataTypes, serial_list=serial_list,
                  copy_paste_map=copy_paste_map)
