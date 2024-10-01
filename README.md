# SLR

## Description

This tool has been designed to help researchers in the process of searching scientific databases.

## Install

This project is managed using the [uv]([GitHub - astral-sh/uv: An extremely fast Python package and project manager, written in Rust.](https://github.com/astral-sh/uv)) project management tool. Please use uv itself, poetry, or pip-tools to install the dependencies.

## Usage

To start using the tool, the required API key needs to be set as an environment variable.

```bash
export ELSEVIER_API_KEY=*******
```

There is a help function for using the tool.

```bash
$ ./src/main.py --help
usage: main.py [-h] [-s] [-c] [-f] [-z] [-p] [-e] [-o] [-i]

This application queries different academic engines.

options:
  -h, --help            show this help message and exit
  -s, --scopus          Query Scopus.
  -c, --count           Count the documents for each search query.
  -f, --fill-publisher  Fill publisher.
  -z, --fill-continent  Fill continent.
  -p, --plot            Plot Data.
  -e, --fill-editorial  Fill editorial.
  -o, --fill-openaccess
                        Fill openaccess.
  -i, --init-database   Initialize DataBase
```

There is a config file, in which the year range, and the search terms that will be used during the search process are specified.

```bash
$ cat config.yaml 
---
date_range: 2018-2022
search_terms:
  - ['mlops']
  - ['devops']
  - ['aiops']
```

First, initialize the database file.

```bash
$ ./src/main.py -i
```

Finally, kick off the search process

```bash
$ ./src/main.py -s
```

## Cite

Please use the following bibtex entry for citing this work.

```latex
@article{diaz2023joint,
  title={A joint study of the challenges, opportunities, and roadmap of mlops and aiops: A systematic survey},
  author={Diaz-De-Arcaya, Josu and Torre-Bastida, Ana I and Zarate, Gorka and Minon, Raul and Almeida, Aitor},
  journal={ACM Computing Surveys},
  volume={56},
  number={4},
  pages={1--30},
  year={2023},
  publisher={ACM New York, NY, USA}
}
```

## Contributing

Contributions are always welcome! Please read the [contribution guidelines](https://docs.github.com/en/get-started/exploring-projects-on-github/contributing-to-a-project) first.

## License

See the [LICENSE](https://github.com/josu-arcaya/slr/blob/master/LICENSE) file for licensing information.
