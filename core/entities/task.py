from uuid import UUID
from datetime import datetime
from typing import Optional

class Task:
    def __init__(
        self,
        id: UUID,
        title: str,
        description: str,
        completed: bool,
        user_id: UUID,
        created_at: datetime,
        updated_at: datetime
    ):
        self.id = id
        self.title = title
        self.description = description
        self.completed = completed
        self.user_id = user_id
        self.created_at = created_at
        self.updated_at = updated_at 