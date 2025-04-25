# GAIA-X Service Characteristics

This repository contains schema and documentation for developing compliant Gaia-X Credentials (formerly called Gaia-X Self-Descriptions / SDs).

Credentials ensure the fulfillment of the policies and rules agreed by the participants that decide to build a data ecosystem under the governance defined according to the Gaia-X Association.

To build and validate Credentials, the schema is made available through the [Gaia-X Compliance Services](https://gitlab.com/gaia-x/lab/compliance).

## GitLab Structure

Folders:
- `single-point-of-truth`: Single point of truth with respect to Self-Description Schema. Schema contains of a hierarchy of classes, called taxonomy and a set of attributes for each class. Attributes are encoded in YAML files. 
- `instances`: Sample credentials in JSON-LD.
- `toolchain`: Scripts and unit tests for our CI/CD pipeline.

## How to collaborate

- Write a YAML file in LinkML format to describe a Gaia-X resource (a resource describes a good or object of the Gaia-X Ecosystem). Learn how to do it in the [Single Point of Truth](./single-point-of-truth) section.
- Translate this LinkML schema to commonly used web standards, such a JSON, OWL and SHACL. You can get the artifacts either from the CI/CD outcomes or build them locally using the [LinkML generator tool](https://linkml.io/linkml/generators/index.html).       
- To check the validity of the shapes generated, you need to build and run unit tests. Visit the [Unit test](./toolchain/test-shacl) section to get more details.
- To validate JSON instances, take a look at the [Toolchain](./toolchain) section.    

Translating, testing and validation stages will be executed automatically as they are part of the CI/CD pipeline.  

## Releasing

For security reasons, only users with a minimum of `Maintainer` access level are allowed to create a new release of this project.

Releases are automatically created and published once a tag is created, to do so the following command can be used.

```bash
git checkout main
git tag -a v<YOUR_VERSION>
```

Tags must always be created from the `main` branch as it houses production ready code. `YOUR_VERSION` must be replaced 
with the version you are releasing (ie. `22.10` for October 2022's specification version).

## Organization

- All communication is done via Mailing List. Please use the [Gaia-X Onboarding formula](https://online2.superoffice.com/Cust26633/CS/scripts/customer.fcgi?action=formFrame&formId=F-kxJG6whD) to join our group.
- We meet weekly on Friday 08:00-09:00 (Central European (Summer) Time)
- Sources:
  - [GitLab](https://gitlab.com/gaia-x/technical-committee/service-characteristics/): source code
  - [Gaia-X Members Platform](https://membersplatform.gaia-x.eu/): meeting minutes and binary files
- Lead: Christoph Lange-Bever, Vice-Lead: Anja Strunk


