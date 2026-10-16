from __future__ import annotations

from pathlib import Path

import aws_cdk as cdk
from aws_cdk import aws_batch as batch
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr_assets as ecr_assets
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from constructs import Construct


class PixelOpticsBatchStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        max_vcpus = int(self.node.try_get_context("maxVcpus") or 16)
        retain_data = bool(self.node.try_get_context("retainData"))
        if not 1 <= max_vcpus <= 256:
            raise ValueError("maxVcpus must be between 1 and 256")

        bucket = s3.Bucket(
            self,
            "SimulationData",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            versioned=True,
            removal_policy=(
                cdk.RemovalPolicy.RETAIN if retain_data else cdk.RemovalPolicy.DESTROY
            ),
            auto_delete_objects=not retain_data,
        )

        vpc = ec2.Vpc(
            self,
            "BatchVpc",
            max_azs=2,
            nat_gateways=1,
        )

        image = ecr_assets.DockerImageAsset(
            self,
            "SimulationImage",
            directory=str(Path(__file__).resolve().parents[1]),
        )

        task_role = iam.Role(
            self,
            "BatchTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )
        bucket.grant_read(task_role, "input/*")
        bucket.grant_write(task_role, "results/*")

        instance_role = iam.Role(
            self,
            "BatchInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonEC2ContainerServiceforEC2Role"
                )
            ],
        )
        instance_profile = iam.CfnInstanceProfile(
            self,
            "BatchInstanceProfile",
            roles=[instance_role.role_name],
        )

        security_group = ec2.SecurityGroup(
            self,
            "BatchSecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,
            description="No inbound access; Batch workers only need outbound access",
        )

        launch_template = ec2.CfnLaunchTemplate(
            self,
            "BatchLaunchTemplate",
            launch_template_data=ec2.CfnLaunchTemplate.LaunchTemplateDataProperty(
                metadata_options=ec2.CfnLaunchTemplate.MetadataOptionsProperty(
                    http_endpoint="enabled",
                    http_tokens="required",
                    http_put_response_hop_limit=2,
                )
            ),
        )

        compute_environment = batch.CfnComputeEnvironment(
            self,
            "ComputeEnvironment",
            type="MANAGED",
            state="ENABLED",
            compute_resources=batch.CfnComputeEnvironment.ComputeResourcesProperty(
                type="SPOT",
                allocation_strategy="SPOT_CAPACITY_OPTIMIZED",
                bid_percentage=70,
                minv_cpus=0,
                desiredv_cpus=0,
                maxv_cpus=max_vcpus,
                instance_types=["optimal"],
                instance_role=instance_profile.attr_arn,
                launch_template=batch.CfnComputeEnvironment.LaunchTemplateSpecificationProperty(
                    launch_template_id=launch_template.ref,
                    version=launch_template.attr_latest_version_number,
                ),
                subnets=[subnet.subnet_id for subnet in vpc.private_subnets],
                security_group_ids=[security_group.security_group_id],
            ),
        )

        job_queue = batch.CfnJobQueue(
            self,
            "JobQueue",
            priority=10,
            compute_environment_order=[
                batch.CfnJobQueue.ComputeEnvironmentOrderProperty(
                    order=1,
                    compute_environment=compute_environment.ref,
                )
            ],
        )

        log_group = logs.LogGroup(
            self,
            "JobLogs",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        job_definition = batch.CfnJobDefinition(
            self,
            "JobDefinition",
            type="container",
            platform_capabilities=["EC2"],
            retry_strategy=batch.CfnJobDefinition.RetryStrategyProperty(attempts=3),
            timeout=batch.CfnJobDefinition.TimeoutProperty(attempt_duration_seconds=3600),
            container_properties=batch.CfnJobDefinition.ContainerPropertiesProperty(
                image=image.image_uri,
                job_role_arn=task_role.role_arn,
                resource_requirements=[
                    batch.CfnJobDefinition.ResourceRequirementProperty(type="VCPU", value="1"),
                    batch.CfnJobDefinition.ResourceRequirementProperty(type="MEMORY", value="2048"),
                ],
                environment=[
                    batch.CfnJobDefinition.EnvironmentProperty(
                        name="CASES_S3_URI",
                        value=f"s3://{bucket.bucket_name}/input/cases.jsonl",
                    ),
                    batch.CfnJobDefinition.EnvironmentProperty(
                        name="RESULTS_S3_PREFIX",
                        value=f"s3://{bucket.bucket_name}/results/starter-run/",
                    ),
                ],
                log_configuration=batch.CfnJobDefinition.LogConfigurationProperty(
                    log_driver="awslogs",
                    options={"awslogs-group": log_group.log_group_name},
                ),
            ),
        )

        # ISSUE-007: instance selection and bid percentage remain intentionally
        # generic. Measure a real solver before choosing production instance types.
        cdk.CfnOutput(self, "BucketName", value=bucket.bucket_name)
        cdk.CfnOutput(self, "JobQueueArn", value=job_queue.attr_job_queue_arn)
        cdk.CfnOutput(self, "JobDefinitionArn", value=job_definition.ref)
        cdk.CfnOutput(self, "MaxVcpus", value=str(max_vcpus))


