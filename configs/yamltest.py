import yaml

def __file_satisfies_conditions(file_name):
    extensions = ['.py', '.c']
    for extension in extensions:
        if file_name.endswith(extension):
            return True
    return False

with open ('python.yaml', 'r') as f:
    config = yaml.safe_load(f)

print(type(config['extensions']))
