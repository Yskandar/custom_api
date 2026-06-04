from custom_api.api.tasks import TaskStore

GLOBAL_TASKSTORE = TaskStore().load_records()
