from google.appengine.api.taskqueue import Task, Queue


def push_taskqueue(queue_name, target_module, url, params, async=True):

    # Create task
    task = Task(target=target_module, url=url, params=params)

    # Push!
    async_call = Queue(queue_name).add_async(task)
    if async:
        return async_call
    else:
        return async_call.get_result()
