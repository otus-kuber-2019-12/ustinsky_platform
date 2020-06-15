#!/usr/bin/env python3
import yaml
from jinja2 import Environment, FileSystemLoader

if __name__ == "__main__":
    config_data = yaml.load(open('./variables.yaml'))
    print(config_data)

    env = Environment(loader = FileSystemLoader('./templates'), trim_blocks=True, lstrip_blocks=True)
    template = env.get_template('./pipeline-template.yaml')

    with open('./generated.yaml', 'w') as file:
        file.write(template.render(config_data))