import json
import sys

import yaml
from typing import Dict
from pathlib import Path
import os
import warnings

################
# @Warning
# security warning 3rd party libary/ might contain exploits/ risk: very low
import ruamel.yaml
from ruamel.yaml.scalarstring import DoubleQuotedScalarString as dq
################

from googletrans import Translator, constants
from pprint import pprint


def parseYAML(input) -> Dict:
    with open(input, "r") as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return data


# code credit: https://stackoverflow.com/questions/56542746/read-and-dump-bracket-list-from-and-to-yaml-with-python
def FSlist(l):  # concert list into flow-style (default is block style)
    from ruamel.yaml.comments import CommentedSeq
    cs = CommentedSeq(l)
    cs.fa.set_flow_style()
    return cs


def translate_yaml_description(description: str, language: str):
    try:

        translator = Translator()

        detection = translator.detect(description)
        if detection == language:
            return description

        else:
            translation = translator.translate(description, dest=language)
            if translation.src != "en":
                warnings.warn(" Automatic Source language detection is not English! It is" + translation.src,
                              UserWarning)

        return translation.text

    except Exception as e:
        warnings.warn(" Automatic language translation failed: fallback -> return of source stream")
        warnings.warn(e)
        return description


def translate_yaml_file(path: Path, yaml_dict: dict, languages: list):
    yml_backup = yaml_dict.copy()

    cls_name: str = list(yaml_dict.keys())[0]
    yaml_file_attributes = yaml_dict[cls_name]["attributes"]
    warning_count = 0

    atr_list = {}
    for atr in yaml_file_attributes:
        atr_copy = atr.copy()
        description_obj = atr_copy["description"]

        if type(description_obj) is list:
            translations = {}

            for des in description_obj:
                key = list(des.keys())[0]
                value = list(des.values())[0]
                translations = {key: value}

            description = None
            try:
                description = translations['en']
            except:
                warnings.warn(" No english specification! : " + cls_name, UserWarning)
                # get a random language and use auto translate
                description = translations[list(translations.keys()[0])]

            for language in languages:
                if language not in list(translations.keys()):
                    translation: str = translate_yaml_description(description=description, language=language)

                    translations.update({language: dq(translation)})

            atr.update({"description": translations})

        elif type(description_obj) is str:
            translations = {}
            description = description_obj
            for language in languages:
                translation: str = translate_yaml_description(description=description, language=language)
                translations.update({language: dq(translation)})

            atr.update({"description": translations})

        else:
            warnings.warn(" Automatic Translation failed -- Skipping", UserWarning)
            warning_count = warning_count + 1

    if warning_count == 0:
        return yaml_dict, 0
    else:
        # returns unmodified backup
        return yml_backup, warnings


def surround_keys_with_double_quotes(yaml_dict: dict):
    for k, v in yaml_dict.items():
        if isinstance(v, dict):
            surround_keys_with_double_quotes(v)
        elif isinstance(v, list):
            tmp_list = [False if isinstance(x, dict) else True for x in v]
            if all(tmp_list):
                surround_list = []
                for itm in v:
                    surround_list.append(dq(itm))
                yaml_dict[k] = FSlist(surround_list)
            else:
                for itm in v:
                    if isinstance(itm, dict):
                        surround_keys_with_double_quotes(itm)
        else:
            yaml_dict[k] = dq(v)

    return yaml_dict


def translate_files(root_path: str, ecosystems: list, languages: list, target_path: str):
    yaml = ruamel.yaml.YAML()
    yaml.indent(sequence=4, offset=2)
    yaml.width = 4096

    for ecosystem in ecosystems:

        r_path: Path = Path(root_path) / ecosystem
        for root, dirs, files in os.walk(str(r_path)):
            for file in files:
                f_path: Path = Path(root) / file
                if f_path.name.endswith(".yaml"):
                    yaml_dict = parseYAML(str(f_path))
                    # translate
                    yaml_dict, warning_count = translate_yaml_file(path=f_path, yaml_dict=yaml_dict,
                                                                   languages=languages)
                    # surround with double qoaates
                    yaml_dict = surround_keys_with_double_quotes(yaml_dict=yaml_dict)
                    cls_name: str = list(yaml_dict.keys())[0]
                    # if cls_name == "Agent":
                    # print(yaml_dict)
                    # sys.exit()

                    if warning_count == 0:
                        i = 0
                        for x in reversed(f_path.parts):
                            if x != ecosystem:
                                i = i - 1
                            else:
                                i = i - 1
                                break
                        subpath = Path(*f_path.parts[i:])
                        final_target = Path(target_path) / subpath
                        final_target.parents[0].mkdir(parents=True, exist_ok=True)

                        with open(final_target, 'w') as outfile:
                            yaml.dump(yaml_dict, outfile)  # , allow_unicode=True)
                            print("Successfully with_automatic_translated_tooltips " + f_path.name)
                    else:
                        warning_count.warn(" Trace -- Skipping translation", UserWarning)
