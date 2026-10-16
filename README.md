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

## 故意保留的问题

这些问题均有 `ISSUE-xxx` 标记。`tests/test_known_issues.py` 使用 `xfail` 固定当前缺陷，因此基础测试仍能通过；修复后应移除相应的 `xfail`。

| 编号 | 难度 | 当前问题 | 建议成果 |
|---|---:|---|---|
| ISSUE-001 | 入门 | Batch 索引没有业务层边界校验，越界时泄漏原始 `IndexError` | 自定义异常、明确日志和测试 |
| ISSUE-002 | 入门 | 结果键只有案例 ID；同一案例重跑会覆盖旧结果 | 引入 `run_id`、幂等写入与 manifest |
| ISSUE-003 | 中等 | 汇总直接算算术平均，没有对不等间隔角度加权 | 梯形积分或球面立体角权重 |
| ISSUE-004 | 中等 | 简化模型忽略方位角、偏振和材料色散 | 增加 `phi`、TE/TM 与波长相关复折射率 |
| ISSUE-005 | 中等 | 本地批处理逐个串行执行 | 有界进程池、失败隔离和断点续跑 |
| ISSUE-006 | 高级 | 长任务没有 checkpoint，Spot 中断会丢失当前案例进度 | checkpoint、重试和原子提交 |
| ISSUE-007 | 高级 | CDK 使用宽泛的实例类型与固定 Spot 出价比例，缺少成本保护 | 多实例族、预算告警和队列分层 |
| ISSUE-008 | 研究 | 当前是代理公式，没有与 FDTD/实测数据校准 | 接入真实求解器并建立误差报告 |

## 建议的提交顺序

1. 修复 ISSUE-001/002，建立可靠的批任务契约。
2. 修复 ISSUE-003/004，提高物理解释性。
3. 修复 ISSUE-005/006，展示云计算与容错能力。
4. 用公开模型接入 FDTD 或 RCWA，完成基准验证。

每个问题单独提交，并在 PR 中写清楚复现步骤、修复方法、测试证据和性能/成本变化。

