from __future__ import annotations

import importlib
from typing import Any

from airflow.models import BaseOperator
from airflow.models.dag import DAG
from airflow.utils.task_group import TaskGroup

from cosmos.core.graph.entities import Task
from cosmos.log import get_logger

logger = get_logger(__name__)


def get_airflow_task(task: Task, dag: DAG, task_group: TaskGroup | None = None) -> BaseOperator:
    """
    Get the Airflow Operator class for a Task.

    :param task: The Task to get the Operator for

    :return: The Operator class
    :rtype: BaseOperator
    """
    # first, import the operator class from the
    # fully qualified name defined in the task
    module_name, class_name = task.operator_class.rsplit(".", 1)
    module = importlib.import_module(module_name)
    Operator = getattr(module, class_name)

    task_kwargs: dict[str, Any] = {}
    if task.owner != "":
        task_kwargs["owner"] = task.owner

    for k, v in task.airflow_task_config.items():
        task_kwargs[k] = v

    airflow_task = Operator(
        task_id=task.id,
        dag=dag,
        task_group=task_group,
        **task_kwargs,
        **({} if class_name == "EmptyOperator" else {"extra_context": task.extra_context}),
        **task.arguments,
    )

    if not isinstance(airflow_task, BaseOperator):
        raise TypeError(f"Operator class {task.operator_class} is not a subclass of BaseOperator")

    return airflow_task
