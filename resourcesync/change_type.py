class ChangeType:
    """Change type indicated what type of change occurred to a resource"""
    CREATED, UPDATED, DELETED = range(3)

    def __init__(self):
        pass

    @staticmethod
    def get(change_type):
        """Constructor"""
        change_type = change_type.lower()
        if change_type == "created":
            return ChangeType.CREATED
        if change_type == "updated":
            return ChangeType.UPDATED
        if change_type == "deleted":
            return ChangeType.DELETED
        else:
           raise ValueError("Change type not supported")

    @staticmethod
    def str(engine_type):
        if engine_type is ChangeType.CREATED:
            return "created"
        if engine_type is ChangeType.UPDATED:
            return "updated"
        if engine_type is ChangeType.DELETED:
            return "deleted"
        else:
            raise ValueError("Not supported")