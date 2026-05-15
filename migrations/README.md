# Database Migrations

使用 Alembic 管理数据库迁移。

常用命令：

```bash
alembic revision --autogenerate -m "create initial tables"
alembic upgrade head
```

迁移会读取 `DATABASE_URL` 环境变量；未设置时使用 `app.core.config.Settings` 中的默认值。

