class ITILFollowUp:
    _storage = {}
    _id_counter = 1

    def __init__(self, ticket_id: int, comment: str):
        self.id = None
        self.ticket_id = ticket_id
        self.comment = comment

    @classmethod
    def add(cls, ticket_id: int, comment: str):
        obj = cls(ticket_id, comment)
        obj.id = cls._id_counter
        cls._storage[obj.id] = obj
        cls._id_counter += 1
        return obj

    @classmethod
    def update(cls, obj_id: int, **kwargs):
        obj = cls._storage.get(obj_id)
        if not obj:
            raise ValueError("ITILFollowUp not found.")

        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)

        return obj

    @classmethod
    def delete(cls, obj_id: int):
        if obj_id in cls._storage:
            del cls._storage[obj_id]

    @classmethod
    def get(cls, obj_id: int):
        return cls._storage.get(obj_id)

    @classmethod
    def search(cls, **kwargs):
        return [
            obj for obj in cls._storage.values()
            if all(getattr(obj, k, None) == v for k, v in kwargs.items())
        ]
