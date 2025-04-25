# YAML Files

Single Point of Truth of Self-Description Schema. [See Governance Process](../documentation/governance-process.md) for more details.

## YAML Validation

All yaml files will be validated at every merge request. There is a syntactical check by checking *.yaml files against [json schema](single-point-of-truth/yaml/validation/schema.json) and there is a semantic check done by [check_yaml.py](toolchain/check_yaml.py).

**NOTE: Any changes to this list have to result in an update to the validation script (check_yaml.py)**

## Guidelines for writing valid YAML files

* Use one file per class in taxonomy

* Use appropriate folder to create yaml file in: 
    - _gax-core_ for all classes that belong to the Gaia-X Conceptual Model as described in the Gaia-X Architecture Document
    - _gax-trust-framework_ for all classes that belong to the Gaia-X Trust Framework as described in the Gaia-X Trust Framework Document
    - _gax-trust-framework_ for all classes that extend and refine the Gaia-X Trust Framework for specific data, platform, and infrastructure services as defined by the Gaia-X Service Characteristics Workgroup hierarchy. 

* YAML file name must start with lower case character. File name must be equal to name of class in the respective source of information, e.g., the Gaia-X Conceptual Model or Trust Framework.  For example, `provider.yaml` for the class `Provider`. If the name in Conceptual Model is a composed one, such as `Service Offering`, spaces are replace by dashes and each word starts with a lower case character. E.g., the YAML file for `Service Offering` should be called `service-offering.yaml`.

* The first element of each YAML file must be the name of the class in the Self-Description taxonomy using CamelCase notation. E.g., "Service Offering" is rendered as `ServiceOffering`.

* Key `subClassOf` is mandatory for a `class`. Its value must be a list with super classes in upper CamelCase notation. For each list item in `subClassOf` an additional yaml file must exist. If class has no super class, use an empty list. 

* Key `abstract` is optional and indicates that his class is not allowed for instantiation.

* Key `attributes` is mandatory for a `class`. It must be a list of attribute. Each attribute has to consist of six mandatory keys (`title`, `prefix`, `dataType`, `cardinality`, `description`, `exampleValues`). 

* Value of `title` is mandatory for an `attribute`. It must be unique within each file as it is used as ID of a Self-Description attribute.

* Value of `prefix` is mandatory for an `attribute`. It must be an abbreviation defined in [prefixes.yaml](validation/prefixes.yaml).  
It is needed to define the origin of the attribute to correctly generate subsequent files. 

* Value of `dataType` is mandatory for an `attribute`. It must be an abbreviation listed in [dataTypeAbbreviation.yaml](validation/dataTypeAbbreviation.yaml). Mapping of abbreviation in `dataTypeAbbreviation.yaml` must be a valid data type in Self-Description ontology.

* Key `cardinality` is mandatory for an `attribute`. It is represented by a string of the form 'minCount..maxCount'. E.g., if an attribute has to be defined at least once and at most 5 times, the correct string would be '1..5'. It is important that the values of _minCount_ and _maxCount_ are separated by exactly '..' in the string. If there is no _minCount_ the proper value is '0', and if there is no _maxCount_ the proper value is '\*', or otherwise the values are positive integers. So the cardinality string describing that an attribute has no _minCount_ and no _maxCount_ restrictions would be '0..*'.

* Value of `description` is mandatory for an `attribute`. It must be at least one human readable sentence.

* Value of `exampleValues` is mandatory for an `attribute`. It must be a list. There must be at least one list item.

Note: _Relationships_ between classes are modeled as (non-)mandatory "attributes", too.

## Developer Support

The schema of the YAML files is formally described as JSON Schema in the 'schema.json' file. In the future this file might be publicly available, so it can be referenced directly.
This can be loaded into any IDE to get auto-completion.

* For VSCode: Install the 'YAML' Extension. In your users settings add:

    ```text
        "yaml.schemas": {
            "./yaml/validation/schema.json": ["/yaml/*"]
        },
    ```

* For IntelliJ: Add the schema.json to the Schema Mappings

If you've installed Docker, you can run

```bash
docker run --rm -v ${PWD}:/yaml 3scale/ajv test -s /yaml/validation/schema.json -d /yaml/<YourYaml>.yaml  --valid
```

inside the `yaml` folder to validate your file. To check all yaml files

```bash
 for f in ./*.yaml; do docker run --rm -v ${PWD}:/yaml 3scale/ajv test -s /yaml/validation/schema.json -d /yaml/$f --valid; done
```
