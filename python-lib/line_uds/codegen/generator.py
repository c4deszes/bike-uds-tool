import os
import sys
import argparse
from jinja2 import Environment, PackageLoader, select_autoescape

from ..profile import UdsProfile, UdsNumericProperty, UdsBooleanProperty, UdsEnumProperty
from ..loader import load_profile

def codegen(profile: UdsProfile, output_path: str):
    env = Environment(
        loader=PackageLoader('line_uds', 'codegen'),
        autoescape=select_autoescape()
    )
    template = env.get_template('header.jinja2')
    output = template.render(profile=profile)
    os.makedirs(output_path, exist_ok=True)
    with open(os.path.join(output_path, 'uds_gen.h'), 'w+') as f:
        f.write(output)

    template = env.get_template('source.jinja2')
    output = template.render(profile=profile)
    os.makedirs(output_path, exist_ok=True)
    with open(os.path.join(output_path, 'uds_gen.c'), 'w+') as f:
        f.write(output)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('profile')
    parser.add_argument('--output', required=False, default=os.curdir)
    args = parser.parse_args()

    profile = load_profile(args.profile)

    codegen(profile, args.output)

    return 0

if __name__ == '__main__':
    sys.exit(main())
