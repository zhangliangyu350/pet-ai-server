# Pet AI Server

AI 宠物健康分析微信小程序后端服务。

## 本地启动

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

健康检查：

```bash
curl http://127.0.0.1:8000/api/v1/health
```

## 配置

通过环境变量配置服务。可参考 `.env.example` 创建本地 `.env`，但不要提交真实 `.env`。

