class Ticket:
    _storage = {}
    _id_counter = 1

    def __init__(self, title: str, description: str, user_id: int, status: str):
        self.id = None
        self.title = title
        self.description = description
        self.user_id = user_id
        self.status = status

    @classmethod
    def add(cls, title: str, description: str, user_id: int, status: str):
        obj = cls(title, description, user_id, status)
        obj.id = cls._id_counter
        cls._storage[obj.id] = obj
        cls._id_counter += 1
        return obj

    @classmethod
    def update(cls, obj_id: int, **kwargs):
        obj = cls._storage.get(obj_id)
        if not obj:
            raise ValueError("Ticket not found.")

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

    # Métodos FollowUp

    @classmethod
    def addFollowUp(cls, ticket_id: int, comment: str):
        ticket = cls._storage.get(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found.")

        followup_id = ticket._followup_counter

        ticket._followups[followup_id] = {
            "id": followup_id,
            "comment": comment
        }

        ticket._followup_counter += 1

        return ticket._followups[followup_id]

    @classmethod
    def updateFollowUp(cls, ticket_id: int, followup_id: int, **kwargs):
        ticket = cls._storage.get(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found.")

        followup = ticket._followups.get(followup_id)
        if not followup:
            raise ValueError("FollowUp not found.")

        for key, value in kwargs.items():
            if key in followup:
                followup[key] = value

        return followup

    @classmethod
    def deleteFollowUp(cls, ticket_id: int, followup_id: int):
        ticket = cls._storage.get(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found.")

        if followup_id not in ticket._followups:
            raise ValueError("FollowUp not found.")

        del ticket._followups[followup_id]

    @classmethod
    def getFollowUp(cls, ticket_id: int, followup_id: int):
        ticket = cls._storage.get(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found.")

        return ticket._followups.get(followup_id)

    @classmethod
    def searchFollowUps(cls, ticket_id: int, **filters):
        ticket = cls._storage.get(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found.")

        results = []
        for followup in ticket._followups.values():
            if all(followup.get(k) == v for k, v in filters.items()):
                results.append(followup)

        return results

