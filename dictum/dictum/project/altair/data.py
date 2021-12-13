import dictum.project


class DictumData:
    def __init__(self, project: "dictum.project.Project"):
        self.project = project

    def to_dict(self):
        return {"name": "__dictum__"}
