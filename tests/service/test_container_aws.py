#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import math
import unittest
from typing import List
from unittest.mock import call, MagicMock, patch
from uuid import uuid4

from fbpcp.entity.cloud_provider import CloudProvider

from fbpcp.entity.cluster_instance import Cluster, ClusterStatus
from fbpcp.entity.container_instance import ContainerInstance, ContainerInstanceStatus
from fbpcp.entity.container_permission import ContainerPermissionConfig
from fbpcp.entity.container_type import ContainerType, ContainerTypeConfig
from fbpcp.error.pcp import PcpError
from fbpcp.service.container_aws import AWS_API_INPUT_SIZE_LIMIT, AWSContainerService

TEST_INSTANCE_ID_1 = "test-instance-id-1"
TEST_INSTANCE_ID_2 = "test-instance-id-2"
TEST_INSTANCE_ID_DNE = "test-instance-id-dne"
TEST_REGION = "us-west-2"
TEST_KEY_ID = "test-key-id"
TEST_KEY_DATA = "test-key-data"
TEST_SESSION_TOKEN = "test-session-token"
TEST_CLUSTER = "test-cluster"
TEST_SUBNETS = ["test-subnet0", "test-subnet1"]
TEST_IP_ADDRESS = "127.0.0.1"
TEST_TASK_DEFNITION = "test-task-definition:1"
TEST_CONTAINER_DEFNITION = "test-container-definition"

TEST_ENV_VARS = {"k1": "v1", "k2": "v2"}
TEST_ENV_VARS_2 = {"k3": "v3", "k4": "v4"}
TEST_CMD_1 = "test_1"
TEST_CMD_2 = "test_2"
TEST_CONTAINER_TYPE = ContainerType.MEDIUM
TEST_CLOUD_PROVIDER = CloudProvider.AWS


class TestAWSContainerService(unittest.TestCase):
    @patch("fbpcp.gateway.ecs.ECSGateway")
    def setUp(self, MockECSGateway):
        self.container_svc = AWSContainerService(
            TEST_REGION, TEST_CLUSTER, TEST_SUBNETS, TEST_KEY_ID, TEST_KEY_DATA
        )
        self.container_svc.ecs_gateway = MockECSGateway()
        self.test_container_config: ContainerTypeConfig = (
            ContainerTypeConfig.get_config(TEST_CLOUD_PROVIDER, TEST_CONTAINER_TYPE)
        )

    def test_create_instances(self):
        # Arrange
        created_instances: List[ContainerInstance] = [
            ContainerInstance(
                TEST_INSTANCE_ID_1,
                TEST_IP_ADDRESS,
                ContainerInstanceStatus.STARTED,
                cpu=self.test_container_config.cpu,
                memory=self.test_container_config.memory,
            ),
            ContainerInstance(
                TEST_INSTANCE_ID_2,
                TEST_IP_ADDRESS,
                ContainerInstanceStatus.STARTED,
                cpu=self.test_container_config.cpu,
                memory=self.test_container_config.memory,
            ),
        ]

        self.container_svc.ecs_gateway.run_task = MagicMock(
            side_effect=created_instances
        )

        cmd_list = [TEST_CMD_1, TEST_CMD_2]
        run_task_calls: List[call] = [
            call(
                task_definition=TEST_TASK_DEFNITION,
                container=TEST_CONTAINER_DEFNITION,
                cmd=TEST_CMD_1,
                cluster=TEST_CLUSTER,
                subnets=TEST_SUBNETS,
                env_vars=TEST_ENV_VARS,
                cpu=self.test_container_config.cpu,
                memory=self.test_container_config.memory,
                task_role_arn=None,
            ),
            call(
                task_definition=TEST_TASK_DEFNITION,
                container=TEST_CONTAINER_DEFNITION,
                cmd=TEST_CMD_2,
                cluster=TEST_CLUSTER,
                subnets=TEST_SUBNETS,
                env_vars=TEST_ENV_VARS,
                cpu=self.test_container_config.cpu,
                memory=self.test_container_config.memory,
                task_role_arn=None,
            ),
        ]

        # Act
        container_instances: List[
            ContainerInstance
        ] = self.container_svc.create_instances(
            container_definition=f"{TEST_TASK_DEFNITION}#{TEST_CONTAINER_DEFNITION}",
            cmds=cmd_list,
            env_vars=TEST_ENV_VARS,
            container_type=TEST_CONTAINER_TYPE,
        )

        # Assert
        self.assertEqual(container_instances, created_instances)
        self.container_svc.ecs_gateway.run_task.assert_has_calls(
            run_task_calls, any_order=False
        )
        self.assertEqual(
            self.container_svc.ecs_gateway.run_task.call_count, len(created_instances)
        )

    def test_create_instances_with_list_of_env_vars(self):
        # Arrange
        created_instances: List[ContainerInstance] = [
            ContainerInstance(
                TEST_INSTANCE_ID_1,
                TEST_IP_ADDRESS,
                ContainerInstanceStatus.STARTED,
                cpu=self.test_container_config.cpu,
                memory=self.test_container_config.memory,
            ),
            ContainerInstance(
                TEST_INSTANCE_ID_2,
                TEST_IP_ADDRESS,
                ContainerInstanceStatus.STARTED,
                cpu=self.test_container_config.cpu,
                memory=self.test_container_config.memory,
            ),
        ]

        self.container_svc.ecs_gateway.run_task = MagicMock(
            side_effect=created_instances
        )

        cmd_list = [TEST_CMD_1, TEST_CMD_2]
        run_task_calls: List[call] = [
            call(
                task_definition=TEST_TASK_DEFNITION,
                container=TEST_CONTAINER_DEFNITION,
                cmd=TEST_CMD_1,
                cluster=TEST_CLUSTER,
                subnets=TEST_SUBNETS,
                env_vars=TEST_ENV_VARS,
                cpu=self.test_container_config.cpu,
                memory=self.test_container_config.memory,
                task_role_arn=None,
            ),
            call(
                task_definition=TEST_TASK_DEFNITION,
                container=TEST_CONTAINER_DEFNITION,
                cmd=TEST_CMD_2,
                cluster=TEST_CLUSTER,
                subnets=TEST_SUBNETS,
                env_vars=TEST_ENV_VARS_2,
                cpu=self.test_container_config.cpu,
                memory=self.test_container_config.memory,
                task_role_arn=None,
            ),
        ]

        # Act
        container_instances: List[
            ContainerInstance
        ] = self.container_svc.create_instances(
            container_definition=f"{TEST_TASK_DEFNITION}#{TEST_CONTAINER_DEFNITION}",
            cmds=cmd_list,
            env_vars=[TEST_ENV_VARS, TEST_ENV_VARS_2],
            container_type=TEST_CONTAINER_TYPE,
        )

        # Assert
        self.assertEqual(container_instances, created_instances)
        self.container_svc.ecs_gateway.run_task.assert_has_calls(
            run_task_calls, any_order=False
        )
        self.assertEqual(
            self.container_svc.ecs_gateway.run_task.call_count, len(created_instances)
        )

    def test_create_instances_with_permission(self):
        # Arrange
        expected_role_id = "test-role-id"
        permission = ContainerPermissionConfig(expected_role_id)

        created_instances: List[ContainerInstance] = [
            ContainerInstance(
                TEST_INSTANCE_ID_1,
                TEST_IP_ADDRESS,
                ContainerInstanceStatus.STARTED,
                cpu=self.test_container_config.cpu,
                memory=self.test_container_config.memory,
                permission=permission,
            ),
            ContainerInstance(
                TEST_INSTANCE_ID_2,
                TEST_IP_ADDRESS,
                ContainerInstanceStatus.STARTED,
                cpu=self.test_container_config.cpu,
                memory=self.test_container_config.memory,
                permission=permission,
            ),
        ]

        self.container_svc.ecs_gateway.run_task = MagicMock(
            side_effect=created_instances
        )

        cmd_list = [TEST_CMD_1, TEST_CMD_2]

        run_task_calls: List[call] = [
            call(
                task_definition=TEST_TASK_DEFNITION,
                container=TEST_CONTAINER_DEFNITION,
                cmd=TEST_CMD_1,
                cluster=TEST_CLUSTER,
                subnets=TEST_SUBNETS,
                env_vars=TEST_ENV_VARS,
                cpu=self.test_container_config.cpu,
                memory=self.test_container_config.memory,
                task_role_arn=expected_role_id,
            ),
            call(
                task_definition=TEST_TASK_DEFNITION,
                container=TEST_CONTAINER_DEFNITION,
                cmd=TEST_CMD_2,
                cluster=TEST_CLUSTER,
                subnets=TEST_SUBNETS,
                env_vars=TEST_ENV_VARS_2,
                cpu=self.test_container_config.cpu,
                memory=self.test_container_config.memory,
                task_role_arn=expected_role_id,
            ),
        ]

        # Act
        self.container_svc.create_instances(
            container_definition=f"{TEST_TASK_DEFNITION}#{TEST_CONTAINER_DEFNITION}",
            cmds=cmd_list,
            env_vars=[TEST_ENV_VARS, TEST_ENV_VARS_2],
            container_type=TEST_CONTAINER_TYPE,
            permission=permission,
        )

        # Assert
        self.container_svc.ecs_gateway.run_task.assert_has_calls(
            run_task_calls, any_order=False
        )
        self.assertEqual(
            self.container_svc.ecs_gateway.run_task.call_count, len(run_task_calls)
        )

    def test_create_instances_throw_with_invalid_list_of_env_vars(self):
        # Arrange
        cmd_list = [TEST_CMD_1, TEST_CMD_2, TEST_CMD_2]

        # Act & Assert
        with self.assertRaises(ValueError):
            self.container_svc.create_instances(
                container_definition=f"{TEST_TASK_DEFNITION}#{TEST_CONTAINER_DEFNITION}",
                cmds=cmd_list,
                env_vars=[TEST_ENV_VARS],
                container_type=TEST_CONTAINER_TYPE,
            )

        with self.assertRaises(ValueError):
            self.container_svc.create_instances(
                container_definition=f"{TEST_TASK_DEFNITION}#{TEST_CONTAINER_DEFNITION}",
                cmds=cmd_list,
                env_vars=[],
                container_type=TEST_CONTAINER_TYPE,
            )

    def test_create_instance(self):
        # Arrange
        created_instance: ContainerInstance = ContainerInstance(
            TEST_INSTANCE_ID_1,
            TEST_IP_ADDRESS,
            ContainerInstanceStatus.STARTED,
            cpu=self.test_container_config.cpu,
            memory=self.test_container_config.memory,
        )

        self.container_svc.ecs_gateway.run_task = MagicMock(
            return_value=created_instance
        )

        # Act
        container_instance: ContainerInstance = self.container_svc.create_instance(
            f"{TEST_TASK_DEFNITION}#{TEST_CONTAINER_DEFNITION}",
            TEST_CMD_1,
            TEST_ENV_VARS,
            container_type=TEST_CONTAINER_TYPE,
        )

        # Assert
        self.container_svc.ecs_gateway.run_task.assert_called_with(
            task_definition=TEST_TASK_DEFNITION,
            container=TEST_CONTAINER_DEFNITION,
            cmd=TEST_CMD_1,
            cluster=TEST_CLUSTER,
            subnets=TEST_SUBNETS,
            env_vars=TEST_ENV_VARS,
            cpu=self.test_container_config.cpu,
            memory=self.test_container_config.memory,
            task_role_arn=None,
        )
        self.assertEqual(container_instance, created_instance)

    def test_get_instance(self):
        container_instance = ContainerInstance(
            TEST_INSTANCE_ID_1,
            TEST_IP_ADDRESS,
            ContainerInstanceStatus.STARTED,
        )
        self.container_svc.ecs_gateway.describe_task = MagicMock(
            return_value=container_instance
        )
        instance = self.container_svc.get_instance(TEST_INSTANCE_ID_1)
        self.assertEqual(instance, container_instance)

    def test_get_instance_nonexistent(self):
        container_instance = None
        self.container_svc.ecs_gateway.describe_task = MagicMock(
            return_value=container_instance
        )
        instance = self.container_svc.get_instance(TEST_INSTANCE_ID_DNE)
        self.assertEqual(instance, container_instance)

    def test_get_instances(self):
        # Arrange
        num_instances = 134
        instance_ids = [uuid4() for _ in range(num_instances)]
        container_instances = [
            ContainerInstance(
                instance_id, TEST_IP_ADDRESS, ContainerInstanceStatus.UNKNOWN
            )
            for instance_id in instance_ids
        ]
        expected_container_shard_0 = [
            ContainerInstance(
                instance_id, TEST_IP_ADDRESS, ContainerInstanceStatus.UNKNOWN
            )
            for instance_id in instance_ids[0:AWS_API_INPUT_SIZE_LIMIT]
        ]
        expected_container_shard_1 = [
            ContainerInstance(
                instance_id, TEST_IP_ADDRESS, ContainerInstanceStatus.UNKNOWN
            )
            for instance_id in instance_ids[AWS_API_INPUT_SIZE_LIMIT:num_instances]
        ]

        self.container_svc.ecs_gateway.describe_tasks = MagicMock(
            side_effect=[expected_container_shard_0, expected_container_shard_1]
        )

        calls = [
            call(self.container_svc.cluster, instance_ids[0:AWS_API_INPUT_SIZE_LIMIT]),
            call(
                self.container_svc.cluster,
                instance_ids[AWS_API_INPUT_SIZE_LIMIT:num_instances],
            ),
        ]

        # Act
        instances = self.container_svc.get_instances(instance_ids=instance_ids)

        # Assert
        self.container_svc.ecs_gateway.describe_tasks.assert_has_calls(
            calls, any_order=False
        )
        self.assertEqual(
            self.container_svc.ecs_gateway.describe_tasks.call_count,
            math.ceil(num_instances / AWS_API_INPUT_SIZE_LIMIT),
        )
        self.assertEqual(instances, container_instances)

    def test_get_instances_nonexistent(self):
        container_instances = [
            ContainerInstance(
                TEST_INSTANCE_ID_1,
                TEST_IP_ADDRESS,
                ContainerInstanceStatus.STARTED,
            ),
            None,
            ContainerInstance(
                TEST_INSTANCE_ID_2,
                TEST_IP_ADDRESS,
                ContainerInstanceStatus.STARTED,
            ),
        ]

        self.container_svc.ecs_gateway.describe_tasks = MagicMock(
            return_value=container_instances
        )
        instances = self.container_svc.get_instances(
            [TEST_INSTANCE_ID_1, TEST_INSTANCE_ID_DNE, TEST_INSTANCE_ID_2]
        )
        self.assertEqual(instances, container_instances)

    def test_cancel_instances(self):
        instance_ids = [TEST_INSTANCE_ID_1, TEST_INSTANCE_ID_2]
        errors = [None, PcpError("instance id not found")]
        self.container_svc.ecs_gateway.stop_task = MagicMock(side_effect=errors)
        self.assertEqual(self.container_svc.cancel_instances(instance_ids), errors)

    def test_get_current_instances_count(self):
        # Arrange
        TEST_PENDING_TASKS_COUNT = 2
        TEST_RUNNING_TASKS_COUNT = 3
        TEST_TASKS_COUNT = TEST_PENDING_TASKS_COUNT + TEST_RUNNING_TASKS_COUNT
        self.container_svc.ecs_gateway.describe_cluster = MagicMock(
            return_value=Cluster(
                cluster_arn="test",
                cluster_name=TEST_CLUSTER,
                pending_tasks=TEST_PENDING_TASKS_COUNT,
                running_tasks=TEST_RUNNING_TASKS_COUNT,
            )
        )
        # Act
        count = self.container_svc.get_current_instances_count()
        # Assert
        self.assertEqual(count, TEST_TASKS_COUNT)

    def test_auth_keys_with_session_token(self):
        container_aws = AWSContainerService(
            region=TEST_REGION,
            cluster=TEST_CLUSTER,
            subnets=TEST_SUBNETS,
            access_key_id=TEST_KEY_ID,
            access_key_data=TEST_KEY_DATA,
            session_token=TEST_SESSION_TOKEN,
        )
        expected_config = {
            "aws_access_key_id": TEST_KEY_ID,
            "aws_secret_access_key": TEST_KEY_DATA,
            "aws_session_token": TEST_SESSION_TOKEN,
        }

        self.assertEqual(container_aws.ecs_gateway.config, expected_config)

    def test_auth_keys(self):
        container_aws = AWSContainerService(
            region=TEST_REGION,
            cluster=TEST_CLUSTER,
            subnets=TEST_SUBNETS,
            access_key_id=TEST_KEY_ID,
            access_key_data=TEST_KEY_DATA,
        )
        expected_config = {
            "aws_access_key_id": TEST_KEY_ID,
            "aws_secret_access_key": TEST_KEY_DATA,
        }

        self.assertEqual(container_aws.ecs_gateway.config, expected_config)

    def test_get_cluster_instance(self) -> None:
        # Arrange
        test_cluster_arn = "test_cluster_arn"
        test_cluster_name = TEST_CLUSTER
        test_pending_tasks_account = 2
        test_running_tasks_account = 3
        test_status = ClusterStatus.ACTIVE
        self.container_svc.ecs_gateway.describe_cluster = MagicMock(
            return_value=Cluster(
                cluster_arn=test_cluster_arn,
                cluster_name=test_cluster_name,
                pending_tasks=test_pending_tasks_account,
                running_tasks=test_running_tasks_account,
                status=test_status,
            )
        )
        expected_cluster_instance = Cluster(
            cluster_arn=test_cluster_arn,
            cluster_name=test_cluster_name,
            pending_tasks=test_pending_tasks_account,
            running_tasks=test_running_tasks_account,
            status=test_status,
        )
        # Act
        cluster_instance = self.container_svc.get_cluster_instance()
        # Assert
        self.assertEqual(cluster_instance, expected_cluster_instance)
