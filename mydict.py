class MyDict(dict):
    def incr(self, key, val=1):
        self[key] = self.get(key, 0) + val
