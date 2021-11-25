class MyDict(dict):
    def __init__(self):
        super().__init__()

    def __getattr__(self, attr):
        if str(attr).startswith("__"):
            return super(MyDict, self).__getattr__(attr)
        return self[attr]

    def __setattr__(self, key, value):
        if str(key).startswith("__"):
            return super(MyDict, self).__setattr__(key, value)
        self[key] = value
