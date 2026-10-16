# Cloud Pixel Optics Lab

一个公开、安全的教学模板：用简化物理模型模拟 CMOS 像素的波长响应、入射角响应和相邻像素光学串扰，再把参数扫描映射到 AWS Batch 数组任务。

> 这不是流片级求解器，也不能替代 FDTD、RCWA、FEM 或商业光学软件。仓库只使用虚构结构和公开的简化公式，不应放入公司内部几何、材料、测量数据或许可证文件。

## 项目目标

- 本地生成 `波长 × 入射角 × 微透镜偏移` 参数矩阵。
- 每个任务独立运行一个参数组合，适合映射到 AWS Batch。
- 输出吸收率、角度效率、有效响应和左右邻像素串扰。
- 汇总成 CSV，便于后续画热力图或训练代理模型。
- 保留若干真实工程问题，供学习者修复并形成可审查的提交记录。

## 架构

```text
cases.jsonl -> AWS Batch array job -> one JSON result per case -> aggregate.csv
                    |                         |
                    +-- container ----------> S3
```

生产化后可以把 `pixelcloud.simulator.simulate()` 替换成真实求解器的无界面命令行调用；参数编排、任务索引、S3 输出和汇总层可以保持不变。

## 快速开始

要求 Python 3.10 或更高版本。

```powershell
cd cloud-pixel-optics-lab
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pixelcloud-generate --output data/cases.jsonl
pixelcloud-run --cases data/cases.jsonl --index 0 --output-dir output
pixelcloud-local-sweep --cases data/cases.jsonl --output-dir output --limit 50
pixelcloud-aggregate --input-dir output --output output/aggregate.csv
pytest
```

默认参数会生成 `31 × 8 × 5 = 1240` 个案例。先用 `--limit 50` 做烟雾测试，再运行全部案例。

## AWS Batch 运行约定

容器从以下环境变量读取参数：

- `AWS_BATCH_JOB_ARRAY_INDEX`：当前数组子任务编号。
- `CASES_S3_URI`：参数文件，例如 `s3://bucket/input/cases.jsonl`。
- `RESULTS_S3_PREFIX`：结果前缀，例如 `s3://bucket/results/run-001/`。

CDK 示例位于 `infra/`，创建：

- 加密且阻止公网访问的 S3 存储桶；
- 容器镜像资产；
- 使用 Spot 的托管 EC2 计算环境；
- Batch 队列和任务定义；
- 仅允许任务角色读取输入并写入结果的权限。

完整步骤见 [docs/AWS_DEPLOY.md](docs/AWS_DEPLOY.md)。部署前必须先确认预算、区域、配额和公司政策。准备环境：

```powershell
.\scripts\prepare.ps1
.\scripts\deploy.ps1 -AccountId ACCOUNT_ID -Region REGION -Profile PROFILE
.\scripts\submit.ps1 -RunId public-demo-001 -Profile PROFILE -Region REGION
.\scripts\status.ps1 -Profile PROFILE -Region REGION
```

部署脚本会先显示 `cdk diff`，只有输入 `DEPLOY` 才继续。不要把 `cdk deploy --hotswap` 用于生产环境。

项目根目录内已经包含应用、容器、基础设施、脚本、文档和测试，不依赖仓库外文件。`.venv`、本地输出和云端运行清单不会进入最终压缩包。

