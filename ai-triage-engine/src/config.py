import yaml


def load_config(path="config/config.yaml"):
    file = open(path, "r")
    config = yaml.safe_load(file)
    file.close()
    return config
