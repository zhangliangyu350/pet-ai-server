# MVP V1.0 本地接口联调说明

## 1. 启动服务

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

默认地址：

```txt
http://127.0.0.1:8000
```

## 2. 健康检查

```bash
curl http://127.0.0.1:8000/api/v1/health
```

## 3. 微信登录

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/wechat-login \
  -H 'Content-Type: application/json' \
  -d '{"code":"wx_login_code"}'
```

说明：

- 需要配置 `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET`。
- 返回的 `token` 后续通过 `Authorization: Bearer <token>` 传递。

## 4. 图片上传

```bash
curl -X POST http://127.0.0.1:8000/api/v1/uploads/images \
  -F 'file=@/path/to/image.png' \
  -F 'petType=dog'
```

限制：

- 仅支持 JPG / PNG。
- 最大 10MB。

## 5. 提交分析

游客：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/analyses \
  -H 'Content-Type: application/json' \
  -H 'X-Guest-Id: guest_001' \
  -d '{
    "imageUrl":"http://127.0.0.1:8000/static/uploads/image.png",
    "imageSha256":"sha256_xxx",
    "petType":"dog",
    "petName":"狗狗"
  }'
```

登录用户：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/analyses \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -d '{
    "imageUrl":"http://127.0.0.1:8000/static/uploads/image.png",
    "imageSha256":"sha256_xxx",
    "petType":"dog",
    "petName":"狗狗"
  }'
```

## 6. 健康记录

最近记录：

```bash
curl http://127.0.0.1:8000/api/v1/records/recent \
  -H 'X-Guest-Id: guest_001'
```

历史列表：

```bash
curl http://127.0.0.1:8000/api/v1/records?page=1&pageSize=20 \
  -H 'Authorization: Bearer <token>'
```

保存记录：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/records \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -d '{"analysisId":"analysis_001"}'
```

删除记录：

```bash
curl -X DELETE http://127.0.0.1:8000/api/v1/records/record_001 \
  -H 'Authorization: Bearer <token>'
```

## 7. 依赖服务

完整联调需要：

- MySQL
- Redis
- MinIO，或将 `UPLOAD_STORAGE=local` 用于本地临时调试
- 微信小程序登录配置
- AI 服务配置
