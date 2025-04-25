import argparse
import toolchain_helper
import yaml2mermaid

if __name__ == '__main__':
    #parser = argparse.ArgumentParser(description='CI/CD pipeline for self-description schema.')
    parser = argparse.ArgumentParser()
    sub_parser = parser.add_subparsers(dest="output")

    # setup parser for yaml2mermaid
    yaml2mermaid_parser = sub_parser.add_parser("yaml2mermaid", help="Creates mermaid diagrams for given classes.")
    yaml2mermaid_parser.add_argument('-s', '--src', type=str, required=True,
                                     help='Path to SPoT folder for yaml files.')
    yaml2mermaid_parser.add_argument('-c', '--className', action='append', required=True,
                                     help='Full yaml name of class, which should be part of mermaid diagram. '
                                          'Full yaml class name is a concatenation of ecosystem-prefix and class name,'
                                          'e.g. gax-core:Participant or gax-trust-framework:Compute.')
    yaml2mermaid_parser.add_argument('-d', '--draw-attributes', action=argparse.BooleanOptionalAction,
                                     help='If set, class attributes are drawn.')


    # setup parser for yaml2json

    # setup parser for yaml2shacl

    # setup parser for yaml2ttl

    args = parser.parse_args()
    yamlFiles = toolchain_helper.get_list_of_yaml_files(args.src)
    all_yaml_file_definitions = toolchain_helper.load_yaml_definition_of_classes(yamlFiles)

    if args.output == "yaml2mermaid":
        diagram = yaml2mermaid.draw_mermaid_diagram(args.className, all_yaml_file_definitions,
                                                    draw_attributes=args.draw_attributes, print_logs=True)
        print('########################################################')
        print('# Mermaid diagram:')
        print('########################################################')
        print(diagram)



