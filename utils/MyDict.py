class MyDict(dict):
    def __init__(self):
        super().__init__()

    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, key, value):
        self[key] = value
