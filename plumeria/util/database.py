class DictCursor:
    def __init__(self, cursor):
        self.cursor = cursor

    def __iter__(self):
        columns = [e[0] for e in self.cursor.description]
        for row in self.cursor:
            yield {key: row[i] for i, key in enumerate(columns)}
