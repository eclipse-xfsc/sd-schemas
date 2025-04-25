import argparse

import csv
import language_preprocessing


# Command Line Interface for the script check_yaml
if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='automatically translates the english single source of truth to target language')
    sub_parser = parser.add_subparsers(title="Output to be generated", dest="output")

    # Setup parser for sd-attribute command
    parser_lt = sub_parser.add_parser("language_translator",
                                       help="automatically translates the english single source of truth to target language")
    parser_lt.add_argument('-s', '--srcFile', type=str, required=True,
                            help='Path to CSV file specifying where fo find specific files')
    parser_lt.add_argument('-e', '--ecosystems', action='append', required=True,
                            help='Select ecosystem, if ecosystem depends on other ecosystem please specify as list e.g ( --ecosystem gax-core --ecosystem trusted-cloud')
    parser_lt.add_argument('-l', '--languages', action='append', required=True,
                            help='target language')
    parser_lt.add_argument('-t', '--targetPath', type=str, required=True,
                            help='target folder')

    args = parser.parse_args()
    if args.output == "language_translator":

        src_path: str = args.srcFile
        target_path: str = args.targetPath
        ecosystems: str = list(args.ecosystems)
        languages: list = list(args.languages)


        with open(src_path, encoding='utf-8') as file:
            csvreader = csv.reader(file)
            dict_from_csv = {}
            for row in csvreader:
                dict_from_csv[row[0]] = row[1]

        root_path: str = dict_from_csv['SSOT_root_path']
        validation_path: str = dict_from_csv['SSOT_validation_path']

        language_preprocessing.translate_files(root_path=root_path,
                                      ecosystems=ecosystems,
                                      languages=languages,
                                               target_path=target_path)
