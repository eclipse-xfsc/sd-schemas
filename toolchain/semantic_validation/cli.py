import argparse

import csv

import check_yaml


# Command Line Interface for the script check_yaml
if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Validates the semantics of yaml files specified')
    sub_parser = parser.add_subparsers(title="Output to be generated", dest="output")

    # Setup parser for sd-attribute command
    y2j_parser = sub_parser.add_parser("semantic-validation",
                                       help="Creates a JSON (validation) file for each YAML (single source of truth) file")
    y2j_parser.add_argument('--srcFile', type=str, required=True,
                            help='Path to CSV file specifying where fo find specific files')
    y2j_parser.add_argument('-e', '--ecosystem', action='append', required=True,
                            help='Select ecosystem, if ecosystem depends on other ecosystem please specify as list e.g ( --ecosystem gax-core --ecosystem trusted-cloud')

    args = parser.parse_args()
    if args.output == "semantic-validation":

        src_path: str = args.srcFile
        ecosystems: list = list(args.ecosystem)

        with open(src_path, encoding='utf-8') as file:
            csvreader = csv.reader(file)
            dict_from_csv = {}
            for row in csvreader:
                dict_from_csv[row[0]] = row[1]

        root_path: str = dict_from_csv['SSOT_root_path']
        validation_path: str = dict_from_csv['SSOT_validation_path']
        semantic_val_mandatory_attributes: str = dict_from_csv["SEMANTIC_VALIDATION_MANDATORY_ATTRIBUTES"]

        check_yaml.execute_validation(root_path=root_path,
                                      ecosystems=ecosystems,
                                      val_path=validation_path,
                                      semantic_val_mandatory_attributes=semantic_val_mandatory_attributes)
