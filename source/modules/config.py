import hashlib
import os

import yaml

SESSIONS_PATH = ".sessions.yaml"
AWS_IAM_PATH = ".aws_iam.yaml"
AWS_CREDENTIALS_PATH = ".aws_credentials.yaml"


class ConfigSingletone:
    def __new__(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
            if not os.path.exists(cls.file_path):
                with open(cls.file_path, "w") as f:
                    f.write("")
            with open(cls.file_path, "r") as f:
                cls.config = yaml.safe_load(f)
            if cls.config is None:
                cls.config = {}
        return cls._instance

    def __init__(self):
        pass

    @classmethod
    def load_file(cls):
        with open(cls.file_path, "r") as f:
            cls.config = yaml.safe_load(f)

    @classmethod
    def save_file(cls):
        with open(cls.file_path, "w") as f:
            yaml.dump(cls.config, f)

    @classmethod
    def update(cls, data, original_id=None) -> str:
        data["name"] = data["name"].strip()
        new_id = cls.name2id(data["name"])
        if original_id:
            del cls.config[original_id]
        cls.config[new_id] = data
        cls.save_file()
        return new_id

    @classmethod
    def delete(cls, delete_id) -> str:
        del cls.config[delete_id]
        cls.save_file()

    @staticmethod
    def name2id(name: str) -> str:
        return hashlib.md5(name.strip().encode()).hexdigest()


class AWSIAMConfig(ConfigSingletone):
    file_path = AWS_IAM_PATH

    def __init__(self):
        super().__init__()


class SessionConfig(ConfigSingletone):
    file_path = SESSIONS_PATH

    def __init__(self):
        super().__init__()


if __name__ == ("__main__"):
    aws_iam_config = AWSIAMConfig()
    session_config = SessionConfig()
    aws_iam_config.update({"name": "xxx"})
    session_config.update({"name": "yyy"})
    print(aws_iam_config.config)
    print(session_config.config)
