from core.entities.task import Task
from uuid import UUID
from typing import List

class CreateTaskUseCase:
    def __init__(self, task_repository):
        self.task_repository = task_repository

    async def execute(self, user_id: UUID, title: str, description: str) -> Task:
        return await self.task_repository.create(user_id=user_id, title=title, description=description)

class GetUserTasksUseCase:
    def __init__(self, task_repository):
        self.task_repository = task_repository

    async def execute(self, user_id: UUID) -> List[Task]:
        return await self.task_repository.get_by_user_id(user_id)

class UpdateTaskUseCase:
    def __init__(self, task_repository):
        self.task_repository = task_repository

    async def execute(self, user_id: UUID, task_id: UUID, **kwargs) -> Task:
        return await self.task_repository.update(user_id=user_id, task_id=task_id, **kwargs)

class DeleteTaskUseCase:
    def __init__(self, task_repository):
        self.task_repository = task_repository

    async def execute(self, user_id: UUID, task_id: UUID) -> None:
        await self.task_repository.delete(user_id=user_id, task_id=task_id) 