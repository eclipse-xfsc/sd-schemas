import toolchain_helper as th

from typing import List, Dict, Tuple


def _add_full_mermaid_class_name_to_yaml_definition_of_classes(all_yaml_file_definitions: dict) -> Dict[str, Dict]:
    """
    Full yaml class name is a concatenation of ecosystem-prefix, such as gax-core ot gax-trust-framework.
    Mermaid does no support class names containing a colon. This method converts yaml class name in a name
    mermaid is able to process, by replacing colon by underscore, e.g. gax-core:Participant is converted to
    gaxCore_Participant, and adds this name to set of yaml definitions for further processing.

    @param all_yaml_file_definitions dict with all yaml definition of all files in source dir. Top-Level key is yaml
    class name, e.g. gax-core:Participant
    @return dict with all yaml definition
    """
    for full_class_name in all_yaml_file_definitions.keys():
        full_mermaid_class_name = get_full_mermaid_class_name(full_class_name)
        all_yaml_file_definitions[full_class_name]['mermaidClassName'] = full_mermaid_class_name

    return all_yaml_file_definitions


def _draw_class_and_all_references(full_class_name: str,
                                   all_yaml_file_definitions: dict,
                                   drawn_classes: List[str] = None,
                                   drawn_inheritance: List[Tuple[str, str]] = None,
                                   draw_attributes: bool = False,
                                   print_logs: bool = False) -> str:
    """
    Returns mermaid definition for given class. This contains
    - the class and its attributes itself,
    - all classes this class refers
    - all super classes of this class
    - all sub classes of this class
    - all classes, which are referenced by this class
    - all classes, which reference this class

    @param full_class_name: full class name of class to be drawn in mermaid, e.g. gax-core:Participant
    @type full_class_name: string
    @param all_yaml_file_definitions: dict of yaml representation of all classes. Top level key is full class name
    @type all_yaml_file_definitions: dict
    @param drawn_classes: List of classes (defined by full name e.g. gax-core:Participant), which are already
    @type drawn_classes: List[Tuple[str, str]]
    drawn in mermaid. This information is needed to avoid duplicate classes and associations.
    @param drawn_inheritance: List of drawn inheritance relationships, stored as tuple (parent class, child class)
    @type drawn_inheritance: List[Tuple[str, str]]
    @param draw_attributes: if true, class' attributes will be drawn
    @type draw_attributes: bool
    @param print_logs: if true, log statements are printed
    @type print_logs: bool

    @return mermaid diagram content of given class as string
    @rtype string
    """
    mermaid = ""
    if drawn_classes is None:
        drawn_classes = list()
    if drawn_inheritance is None:
        drawn_inheritance = list()

    _, class_name = full_class_name.split(":")

    # draw class definition
    if print_logs:
        print("...draw mermaid diagram of " + full_class_name)
    if full_class_name not in drawn_classes:
        mermaid += _draw_single_class(full_class_name, all_yaml_file_definitions, drawn_classes=drawn_classes,
                                      draw_attributes=draw_attributes)

    # draw super class inheritance
    if print_logs:
        print("   ...add super classes")
    for full_super_class_name in all_yaml_file_definitions[full_class_name][class_name]['subClassOf']:
        mermaid += _draw_inheritance(full_super_class_name,
                                     full_class_name,
                                     all_yaml_file_definitions,
                                     drawn_classes=drawn_classes,
                                     drawn_inheritance=drawn_inheritance,
                                     draw_attributes=draw_attributes)

    # draw subclass inheritance
    if print_logs:
        print("   ...add sub classes")
    all_class_names = all_yaml_file_definitions.keys()
    for full_sub_class_name in all_class_names:
        _, sub_class_name = full_sub_class_name.split(":")
        try:
            if full_class_name in all_yaml_file_definitions[full_sub_class_name][sub_class_name]['subClassOf']:
                mermaid += _draw_inheritance(full_class_name,
                                             full_sub_class_name,
                                             all_yaml_file_definitions,
                                             drawn_classes=drawn_classes,
                                             drawn_inheritance=drawn_inheritance,
                                             draw_attributes=draw_attributes)
        except KeyError as e:
            # referencing class does not have attribute 'suberClassOf'
            continue

    # draw all classes, which are referenced by this class
    if print_logs:
        print("   ...add all classes, which are referenced by this class")
    for att in all_yaml_file_definitions[full_class_name][class_name]['attributes']:
        if att['dataType'] in all_class_names:
            mermaid += _draw_association(full_class_name, att['dataType'], att['cardinality'],
                                         att['title'], all_yaml_file_definitions, drawn_classes=drawn_classes,
                                         draw_attributes=draw_attributes)

    # draw all classes, which references this class
    if print_logs:
        print("   ...add all classes, which references this class")
    for full_referencing_class_name in all_class_names:
        _, referencing_class_name = full_referencing_class_name.split(":")
        for att in all_yaml_file_definitions[full_referencing_class_name][referencing_class_name]['attributes']:
            if att['dataType'] == full_class_name and full_class_name != full_referencing_class_name:
                mermaid += _draw_association(full_referencing_class_name, full_class_name, att['cardinality'],
                                             att['title'], all_yaml_file_definitions, drawn_classes=drawn_classes,
                                             draw_attributes=draw_attributes)
    return mermaid


def _draw_inheritance(full_super_class_name: str,
                      full_sub_class_name: str,
                      all_yaml_file_definitions: dict,
                      drawn_classes: List[str] = None,
                      drawn_inheritance: List[Tuple[str, str]] = None,
                      draw_attributes: bool = False) -> str:
    """
    Draw inheritance relation between given super class and subclass.

    @param full_super_class_name: full class name of super class to be drawn in mermaid, e.g. gax-core:Participant
    @type full_super_class_name: string
    @param full_sub_class_name: full class name of subclass to be drawn in mermaid, e.g. gax-trust-framework:LegalPerson
    @type full_sub_class_name: string
    @param all_yaml_file_definitions: dict of yaml representation of all classes. Top level key is full class name
    @type all_yaml_file_definitions: dict
    @param drawn_classes: List of classes (defined by full name e.g. gax-core:Participant), which are already
    @type drawn_classes: List[Tuple[str, str]]
    drawn in mermaid. This information is needed to avoid duplicate classes and associations.
    @param drawn_inheritance: List of drawn inheritance relationships, stored as tuple (parent class, child class)
    @type drawn_inheritance: List[Tuple[str, str]]
    @param draw_attributes: if true, class' attributes will be drawn
    @type draw_attributes: bool

    @return mermaid definition as string
    @rtype string

    """
    mermaid = ""
    try:
        full_mermaid_super_class_name = all_yaml_file_definitions[full_super_class_name]['mermaidClassName']
        mermaid += _draw_single_class(full_super_class_name,
                                      all_yaml_file_definitions,
                                      drawn_classes=drawn_classes,
                                      draw_attributes=draw_attributes)
    except KeyError:
        full_mermaid_super_class_name = get_full_mermaid_class_name(full_super_class_name)

    try:
        full_mermaid_sub_class_name = all_yaml_file_definitions[full_sub_class_name]['mermaidClassName']
        mermaid += _draw_single_class(full_sub_class_name,
                                      all_yaml_file_definitions,
                                      drawn_classes=drawn_classes,
                                      draw_attributes=draw_attributes)
    except KeyError as e:
        full_mermaid_sub_class_name = get_full_mermaid_class_name(full_sub_class_name)

    if (full_super_class_name, full_sub_class_name) not in drawn_inheritance:
        mermaid += full_mermaid_super_class_name + " <|-- " + full_mermaid_sub_class_name + "\n\n"
        drawn_inheritance.append((full_super_class_name, full_mermaid_sub_class_name))

    return mermaid


def _draw_association(full_origin_class_name: str,
                      full_target_class_name: str,
                      cardinality: str,
                      assoc_name: str,
                      all_yaml_file_definitions: dict,
                      drawn_classes: List[str] = None,
                      draw_attributes: bool = False):
    """
    Draw association relation between given origin and destination class.

    @param full_origin_class_name: full class name of origin class to be drawn in mermaid.
    @type full_origin_class_name: string
    @param full_target_class_name: full class name of destination class  to be drawn in mermaid
    @type full_target_class_name: string
    @param all_yaml_file_definitions: dict of yaml representation of all classes. Top level key is full class name
    @type all_yaml_file_definitions: dict
    @param drawn_classes: List of classes (defined by full name e.g. gax-core:Participant), which are already
    @type drawn_classes: List[Tuple[str, str]]
    drawn in mermaid. This information is needed to avoid duplicate classes and associations.
    @param draw_attributes: if true, class' attributes will be drawn
    @type draw_attributes: bool

    @return mermaid definition as string
    @rtype string

    """
    mermaid = ""

    full_mermaid_origin_class_name = all_yaml_file_definitions[full_origin_class_name]['mermaidClassName']
    full_mermaid_target_class_name = all_yaml_file_definitions[full_target_class_name]['mermaidClassName']

    if full_origin_class_name not in drawn_classes:
        mermaid += _draw_single_class(full_origin_class_name,
                                      all_yaml_file_definitions,
                                      drawn_classes=drawn_classes,
                                      draw_attributes=draw_attributes)
        drawn_classes.append(full_origin_class_name)

    if full_target_class_name not in drawn_classes:
        mermaid += _draw_single_class(full_target_class_name,
                                      all_yaml_file_definitions,
                                      drawn_classes=drawn_classes,
                                      draw_attributes=draw_attributes,
                                      draw_assoc=False)
        drawn_classes.append(full_target_class_name)

    return mermaid + full_mermaid_origin_class_name + " --> \"" + cardinality + \
           "\" " + full_mermaid_target_class_name + ": " + assoc_name + "\n\n"


def _draw_single_class(full_class_name: str,
                       all_yaml_file_definitions: dict,
                       drawn_classes: List[str] = None,
                       draw_attributes: bool = False,
                       draw_assoc: bool = True) -> str:
    """
        Returns mermaid class name of a given full yaml class name. Full yaml class name is a concatenation
        of ecosystem-prefix, such as gax-core ot gax-trust-framework. Mermaid does no support class names containing a
        colon. This method converts yaml class name in a name mermaid is able to process, by replacing colon by
        underscore, e.g. gax-core:Participant is converted to gaxCore_Participant.

        @param full_class_name: full class name of class, e.g. gax-core:Participant
        @return full mermaid class name, e.g. gaxCore_Participant

        """

    mermaid = ""
    if full_class_name not in drawn_classes:
        class_name = full_class_name.split(':')[1]
        yaml_definition_of_class = all_yaml_file_definitions[full_class_name]
        full_mermaid_class_name = yaml_definition_of_class["mermaidClassName"]
        mermaid += "class " + full_mermaid_class_name + "{\n"

        try:
            if yaml_definition_of_class[class_name]['abstract']:
                mermaid = mermaid + "<<abstract>>\n\n"
        except KeyError as e:
            pass

        if draw_attributes:
            all_class_names = all_yaml_file_definitions.keys()
            if yaml_definition_of_class[class_name]['attributes'] is not None:
                for att in yaml_definition_of_class[class_name]['attributes']:
                    data_type = att['dataType']
                    if draw_assoc and data_type not in all_class_names:
                        # mermaid = mermaid + att['title'] + ": " + data_type + "\n"
                        mermaid = mermaid + att['title'] + "\n"
                    else:
                        mermaid = mermaid + att['title'] + "\n"

            drawn_classes.append(full_class_name)

        if mermaid.endswith("{\n"):
            # no abstract class and no attributes will result in empty class definition
            # which is cause syntax error in mermaid
            return ""
        return mermaid + "}\n\n"
    else:
        return ""


def get_full_mermaid_class_name(full_class_name):
    class_name = full_class_name.split(':')[1]
    class_prefix = full_class_name.split(':')[0]
    class_prefix_segments = class_prefix.split('-')

    full_mermaid_class_name = class_prefix_segments[0]

    for i in range(1, len(class_prefix_segments)):
        full_mermaid_class_name = full_mermaid_class_name + class_prefix_segments[i].capitalize()

    return full_mermaid_class_name + "_" + class_name


def draw_mermaid_diagram(full_class_names: List[str], all_yaml_file_definitions: dict,
                         draw_attributes: bool = False, print_logs: bool = False) -> str:
    """
    Return mermaid diagram of all given classes, including

    - every given class and its attributes,
    - all classes, which are refered by on of the given classes
    - all super classes of each given class
    - all sub classes of each given class

    @param full_class_names: list of full class name of class to be drawn in mermaid, e.g. gax-core:Participant
    @param all_yaml_file_definitions: dict of yaml representation of all classes. Top level key is full class name
    @param draw_attributes: if true, class' attributes will be drawn

    """
    if print_logs:
        print("########################################################")
        print("# Draw mermaid diagram ")
        print("########################################################")

    # mermaid = "```mermaid\n"
    mermaid = "classDiagram\n\n"

    drawn_classes = list()
    drawn_inheritance = list()
    all_yaml_file_definitions = _add_full_mermaid_class_name_to_yaml_definition_of_classes(all_yaml_file_definitions)

    for name in full_class_names:
        try:
            all_yaml_file_definitions[name]
        except KeyError:
            raise LookupError("No definition for class '" + name + "' found. Please check if yaml file exist!")
        mermaid = mermaid + _draw_class_and_all_references(name,
                                                           all_yaml_file_definitions,
                                                           drawn_classes=drawn_classes,
                                                           drawn_inheritance=drawn_inheritance,
                                                           draw_attributes=draw_attributes,
                                                           print_logs=print_logs)
    # return mermaid + "\n```"
    return mermaid + "\n"
