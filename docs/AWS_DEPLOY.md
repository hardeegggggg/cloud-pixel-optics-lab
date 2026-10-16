# AWS 部署说明

本说明只适用于公开、虚构的仿真参数。不要使用个人 AWS 账户上传公司内部像素结构、材料参数、测量结果或许可证。

## 费用提醒

这个模板会创建一个 NAT Gateway、Elastic IP、AWS Batch 托管计算环境、S3、CloudWatch Logs 和容器镜像资产。即使没有运行 Batch 任务，NAT Gateway 仍可能按小时收费。实验结束后请执行清理脚本并在 AWS 控制台确认资源已删除。

默认 `maxVcpus=16`，数据桶随栈删除并自动清空。若希望保留结果，可将 `infra/cdk.json` 中的 `retainData` 改为 `true`；此时销毁栈后需要自行管理和删除桶。

## 前置条件

- Python 3.10+
- Node.js 20+ 与 npm
- Docker Desktop，且 Docker daemon 正在运行
- AWS CLI v2
- 一个有权部署 VPC、IAM、Batch、ECR、S3、CloudWatch Logs 和 CloudFormation 的 AWS 身份
- 已选择 AWS 区域并确认 EC2 Spot/vCPU 配额

不要把长期访问密钥写入仓库。优先使用 AWS IAM Identity Center、短期凭证或组织批准的身份方式。

## 1. 本地准备

在项目根目录运行：

```powershell
.\scripts\prepare.ps1
```

该脚本只安装本地依赖、生成 1240 个公开案例并运行测试，不创建 AWS 资源。第一次成功执行后，应把生成的 `infra/package-lock.json` 纳入版本控制，以固定完整的 CDK CLI 依赖树。

## 2. 部署基础设施

先确认当前 AWS 身份：

```powershell
aws sts get-caller-identity --profile YOUR_PROFILE
```

然后部署：

```powershell
.\scripts\deploy.ps1 `
  -AccountId 123456789012 `
  -Region ap-northeast-1 `
  -Profile YOUR_PROFILE `
  -MaxVcpus 16
```

脚本依次执行 bootstrap、`cdk synth --strict`、`cdk diff`，然后要求输入大写 `DEPLOY` 才会真正创建资源。已经 bootstrap 的账户可以增加 `-SkipBootstrap`。

## 3. 提交数组任务

```powershell
.\scripts\submit.ps1 `
  -RunId public-demo-001 `
  -Profile YOUR_PROFILE `
  -Region ap-northeast-1
```

脚本会：

1. 从 CloudFormation 读取桶、队列和任务定义；
2. 上传 `data/cases.jsonl`；
3. 按文件中的案例数量提交 Batch 数组任务；
4. 把父任务 ID 和结果路径保存到 `deployment/last-run.json`。

查询父任务状态：

```powershell
.\scripts\status.ps1 -Profile YOUR_PROFILE -Region ap-northeast-1
```

结果位于：

```text
s3://<generated-bucket>/results/<run-id>/
```

## 4. 清理

确保结果已经下载，再运行：

```powershell
.\scripts\destroy.ps1 -Profile YOUR_PROFILE
```

脚本要求输入大写 `DESTROY`。默认配置会删除栈和其中的 S3 数据。完成后仍需检查 CloudFormation、EC2、NAT Gateway、ECR、S3 和 CloudWatch Logs，确认没有遗留收费资源。CDK bootstrap 创建的 `CDKToolkit` 栈可供其他 CDK 项目复用，不要随意删除。

## 常见问题

- `NoCredentials`：先完成 AWS 登录，再运行 `aws sts get-caller-identity`。
- Docker asset 构建失败：确认 Docker Desktop 已启动。
- `InsufficientInstanceCapacity`：换区域、实例类型或稍后重试；它不是 vCPU 配额错误。
- `InstanceLimitExceeded`：提高相应 Spot/EC2 vCPU 配额，或降低 `MaxVcpus`。
- 任务一直停留在 `RUNNABLE`：检查计算环境、Spot 容量、vCPU 配额和 Batch 服务角色。
- 无结果文件：查看 `/aws/batch` 对应日志组，并确认任务角色有目标 S3 前缀权限。

