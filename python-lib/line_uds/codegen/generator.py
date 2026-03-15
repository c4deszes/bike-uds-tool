import os
import sys
import argparse
import json
from dataclasses import dataclass
from typing import List
from jinja2 import Environment, PackageLoader, select_autoescape

from ..profile import UdsProfile
from ..loader import load_profile

@dataclass
class CodegenConfig:
    profiles: List[UdsProfile]

def codegen(config: CodegenConfig, output_path: str):
    env = Environment(
        loader=PackageLoader('line_uds', 'codegen'),
        autoescape=select_autoescape()
    )
    template = env.get_template('header.jinja2')
    output = template.render(config=config)
    os.makedirs(output_path, exist_ok=True)
    with open(os.path.join(output_path, 'uds_gen.h'), 'w+') as f:
        f.write(output)

    template = env.get_template('source.jinja2')
    output = template.render(config=config)
    os.makedirs(output_path, exist_ok=True)
    with open(os.path.join(output_path, 'uds_gen.c'), 'w+') as f:
        f.write(output)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    parser.add_argument('--output', required=False, default=os.curdir)
    args = parser.parse_args()

    config = CodegenConfig([])
    with open(args.config) as json_file:
        json_config = json.load(json_file)
        for name, profile in json_config.items():
            # TODO: path should be relative to the config file
            uds_profile = load_profile(os.path.join(os.path.dirname(args.config), profile['profile']))
            uds_profile.name = name
            uds_profile.channel = int(profile['channel'])
            config.profiles.append(uds_profile)
    codegen(config, args.output)

    return 0

if __name__ == '__main__':
    sys.exit(main())
