# MVP V1.0 后端架构说明

## 1. 目标

后端负责为微信小程序提供稳定 API，完成微信登录、图片上传、AI 分析、缓存命中、限流、健康记录管理和统一错误处理。

MVP 阶段优先保证：

- 接口契约稳定。
- AI 成本可控。
- 用户数据权限清晰。
- 医疗风险表达可控。
- 后续可平滑接入真实 MySQL、Redis、对象存储和 AI 服务。

---

## 2. 推荐技术栈

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- MySQL
- Redis
- pytest
- httpx

---

## 3. 推荐目录结构

```txt
app/
  main.py
  api/
    v1/
      auth.py
      uploads.py
      analyses.py
      records.py
  core/
    config.py
    exceptions.py
    responses.py
    security.py
    logging.py
  models/
    user.py
    image_asset.py
    analysis.py
    health_record.py
  repositories/
    user_repository.py
    image_repository.py
    analysis_repository.py
    record_repository.py
  schemas/
    auth.py
    upload.py
    analysis.py
    record.py
    common.py
  services/
    auth_service.py
    upload_service.py
    analysis_service.py
    record_service.py
    ai_service.py
    rate_limit_service.py
  utils/
    image.py
    hashing.py
    time.py
tests/
docs/
```

---

## 4. 模块职责

### 4.1 API 层

- 接收 HTTP 请求。
- 校验基础参数。
- 解析登录用户或游客上下文。
- 调用 service。
- 返回统一响应结构。

API 层不写复杂业务逻辑，不直接访问数据库，不直接调用 AI。

### 4.2 Service 层

- 编排业务流程。
- 处理微信登录、上传、分析、记录等业务规则。
- 调用 repository、Redis、AI client。
- 统一抛出业务异常。

### 4.3 Repository 层

- 封装数据库读写。
- 不处理 HTTP 细节。
- 不拼装前端响应结构。

### 4.4 Schema 层

- 定义请求参数。
- 定义响应结构。
- 定义内部 service 数据结构。

### 4.5 Core 层

- 配置读取。
- 统一响应。
- 统一异常。
- 登录态解析。
- 日志脱敏。

---

## 5. 核心流程

### 5.1 微信登录流程

```txt
前端 wx.login
  -> 后端 /auth/wechat-login
  -> 后端请求微信 code2session
  -> 查询或创建用户
  -> 生成 session_token
  -> 返回 LoginResult
```

注意：

- 微信 `AppSecret` 只允许保存在后端环境变量。
- 前端不接触 `openid`、`session_key`。

### 5.2 图片上传流程

```txt
前端选择图片
  -> 后端 /uploads/images
  -> 校验 JPG / PNG
  -> 校验 <= 10MB
  -> 读取宽高和大小
  -> 生成 imageSha256
  -> 存储图片
  -> 返回 UploadImageResult
```

注意：

- 文件名由后端生成。
- 不信任客户端文件名和 MIME。
- 上传接口不调用 AI。

### 5.3 AI 分析流程

```txt
前端提交 imageUrl + imageSha256
  -> 校验用户或游客上下文
  -> 校验每日次数限制
  -> 校验 10 秒间隔
  -> 查询 imageSha256 缓存
  -> 命中缓存：返回历史 AnalysisResult
  -> 未命中：调用 AI 服务
  -> 清洗 AI 原始输出
  -> 保存分析结果
  -> 写入缓存
  -> 返回 AnalysisResult
```

注意：

- 缓存命中不应重复调用 AI。
- AI 输出必须转成结构化 JSON。
- 医疗高风险表述必须清洗。

### 5.4 健康记录流程

```txt
保存记录
  -> 必须登录
  -> 校验 analysisId 可访问
  -> 创建或返回已有记录

查看最近记录
  -> 登录用户按 user_id 查询
  -> 游客按 guest_id 查询

查看历史列表
  -> 必须登录
  -> 按 user_id 分页查询

删除记录
  -> 必须登录
  -> 校验记录归属
  -> 删除记录
```

---

## 6. 数据表草案

### 6.1 users

|字段|类型|说明|
|---|---|---|
|id|varchar|用户 ID|
|openid|varchar|微信 openid，唯一|
|nickname|varchar|昵称|
|avatar_url|varchar|头像|
|created_at|datetime|创建时间|
|updated_at|datetime|更新时间|

### 6.2 image_assets

|字段|类型|说明|
|---|---|---|
|id|varchar|图片 ID|
|image_url|varchar|图片访问地址|
|image_sha256|varchar|图片 SHA256|
|width|int|宽度|
|height|int|高度|
|size|int|文件大小|
|created_at|datetime|创建时间|

### 6.3 analyses

|字段|类型|说明|
|---|---|---|
|id|varchar|分析 ID|
|user_id|varchar|登录用户 ID，可空|
|guest_id|varchar|游客 ID，可空|
|image_url|varchar|图片地址|
|image_sha256|varchar|图片 SHA256|
|pet_type|varchar|宠物类型|
|pet_name|varchar|宠物昵称|
|score|int|健康评分|
|risk_level|varchar|风险等级|
|risk_text|varchar|风险文案|
|summary|text|分析总结|
|observation_advice|json|观察建议|
|diet_advice|text|饮食建议|
|need_vet|boolean|是否建议咨询兽医|
|raw_ai_result|json|AI 原始结构化结果，内部使用|
|created_at|datetime|创建时间|

### 6.4 health_records

|字段|类型|说明|
|---|---|---|
|id|varchar|记录 ID|
|user_id|varchar|用户 ID|
|analysis_id|varchar|分析 ID|
|created_at|datetime|创建时间|
|deleted_at|datetime|软删除时间，可空|

---

## 7. Redis Key 草案

|Key|说明|示例|
|---|---|---|
|`analysis:sha256:{sha256}`|图片分析结果缓存|`analysis:sha256:abc123`|
|`analysis:daily:{identity}:{date}`|每日分析次数|`analysis:daily:user_001:20260516`|
|`analysis:last:{identity}`|最近一次分析时间|`analysis:last:user_001`|
|`guest:recent:{guest_id}`|游客最近一次分析 ID|`guest:recent:guest_xxx`|
|`session:{token}`|登录态|`session:token_xxx`|

说明：

- `identity` 可以是 `user:{user_id}` 或 `guest:{guest_id}`。
- 每日次数 key 建议设置自然日过期。
- 登录态过期时间按产品策略配置。

---

## 8. AI 输出清洗规则

AI 服务应返回结构化 JSON，后端必须二次校验：

- `score` 必须为 1 到 100 的整数。
- `riskLevel` 必须为 `low / medium / high / observe`。
- `riskText` 必须与风险等级匹配。
- `summary` 必须是健康参考表达，不得给出疾病诊断。
- `observationAdvice` 必须是数组。
- `dietAdvice` 不得包含药物或治疗建议。
- `needVet` 必须是布尔值。

如 AI 返回无法解析：

- 返回 `ANALYSIS_FAILED`。
- 不把 AI 原始错误暴露给前端。
- 日志记录需脱敏。

---

## 9. 环境变量草案

```txt
APP_ENV=development
APP_SECRET=change_me
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/pet_ai
REDIS_URL=redis://localhost:6379/0
WECHAT_APP_ID=
WECHAT_APP_SECRET=
AI_PROVIDER=deepseek
AI_API_KEY=
AI_API_BASE_URL=
UPLOAD_STORAGE=local
UPLOAD_LOCAL_DIR=./storage/uploads
PUBLIC_IMAGE_BASE_URL=http://localhost:8000/static/uploads
```

注意：

- `.env` 不允许提交。
- 生产环境密钥必须由部署平台注入。

---

## 10. 验收要点

- 所有接口响应符合 `docs/api/frontend-contract-v1.0-mvp.md`。
- 微信登录不暴露微信密钥。
- 图片上传校验格式和大小。
- 相同 `imageSha256` 不重复调用 AI。
- 游客每日 3 次限制生效。
- 登录用户每日 10 次限制生效。
- 分析 10 秒间隔限制生效。
- 记录列表、保存、删除都校验用户权限。
- AI 文案不包含诊断、治疗、处方等高风险表达。
