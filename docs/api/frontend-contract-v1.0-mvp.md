# MVP V1.0 前后端接口契约

## 1. 文档说明

本文档定义 AI 宠物健康分析 MVP V1.0 中，微信小程序前端与 Python 后端之间的稳定接口契约。

前端页面和组件只依赖本文档定义的数据结构。后端内部字段、数据库字段、AI 原始输出可以不同，但必须在接口出口转换为本文档中的稳定结构。

---

## 2. 契约原则

- 后端对外响应统一包装为 `success / data / message / code`。
- 前端不直接调用 AI 服务，不保存任何 API Key、Token、Secret。
- 前端不直接适配后端内部字段。
- 后端负责微信登录、图片校验、图片 SHA256、缓存命中、AI 调用、次数限制和记录权限校验。
- AI 原始结果必须由后端清洗为结构化 `AnalysisResult`。
- 医疗相关文案必须避免“诊断、治疗、处方”等高风险表达。
- 接口错误码优先使用本文档定义的错误码。

---

## 3. 基础约定

### 3.1 Base URL

开发环境示例：

```txt
https://dev-api.example.com
```

生产环境示例：

```txt
https://api.example.com
```

真实域名由后端部署环境和前端 `config` 统一配置。

### 3.2 Content Type

- JSON 接口：`application/json`
- 图片上传接口：`multipart/form-data`

### 3.3 用户上下文

登录用户：

```http
Authorization: Bearer <session_token>
```

游客用户：

```http
X-Guest-Id: <guest_id>
```

说明：

- `session_token` 由后端登录接口返回。
- `guest_id` 由前端生成并保存在小程序本地，用于游客次数限制和最近一次分析记录。
- 后端不得把微信 `openid` 直接暴露给前端，除非业务明确需要。

---

## 4. 通用响应结构

成功：

```js
{
  success: true,
  data: {},
  message: ''
}
```

失败：

```js
{
  success: false,
  data: null,
  message: '错误提示',
  code: 'ERROR_CODE'
}
```

字段说明：

|字段|类型|说明|
|---|---|---|
|success|Boolean|请求是否成功|
|data|Object / Array / null|业务数据|
|message|String|面向用户的提示文案|
|code|String|错误码，成功时可为空|

---

## 5. 通用枚举

### 5.1 宠物类型

|值|说明|
|---|---|
|cat|猫|
|dog|狗|

### 5.2 风险等级

|值|说明|
|---|---|
|low|低风险|
|medium|中风险|
|high|高风险|
|observe|待观察|

---

## 6. 数据模型

### 6.1 User

```js
{
  id: 'user_001',
  nickname: '微信用户',
  avatarUrl: '',
  createdAt: '2026-05-16T10:00:00+08:00'
}
```

### 6.2 LoginResult

```js
{
  token: 'session_token_xxx',
  user: {
    id: 'user_001',
    nickname: '微信用户',
    avatarUrl: '',
    createdAt: '2026-05-16T10:00:00+08:00'
  }
}
```

### 6.3 UploadImageResult

```js
{
  imageUrl: 'https://example.com/images/poop_001.jpg',
  imageSha256: 'sha256_xxx',
  width: 1024,
  height: 768,
  size: 524288
}
```

### 6.4 AnalysisResult

```js
{
  id: 'analysis_001',
  score: 82,
  riskLevel: 'low',
  riskText: '低风险',
  summary: '从照片来看，便便颜色、形状和质地整体较稳定，可继续观察日常状态。',
  observationAdvice: [
    '建议观察 24 到 48 小时，注意饮食和精神状态变化',
    '保持充足饮水',
    '如持续异常，请咨询线下专业兽医'
  ],
  dietAdvice: '可适当增加高纤维食物，如南瓜、红薯等，帮助维持肠道健康。',
  needVet: false,
  imageUrl: 'https://example.com/images/poop_001.jpg',
  imageSha256: 'sha256_xxx',
  petType: 'dog',
  petName: '狗狗',
  createdAt: '2026-05-16T10:00:00+08:00'
}
```

### 6.5 HealthRecord

```js
{
  id: 'record_001',
  analysisId: 'analysis_001',
  imageUrl: 'https://example.com/images/poop_001.jpg',
  score: 82,
  riskLevel: 'low',
  riskText: '低风险',
  summary: '状态良好，继续保持',
  createdAt: '2026-05-16T10:00:00+08:00'
}
```

### 6.6 Pagination

```js
{
  page: 1,
  pageSize: 20,
  total: 1,
  hasMore: false
}
```

---

## 7. HTTP 接口

### 7.1 微信登录

```http
POST /api/v1/auth/wechat-login
Content-Type: application/json
```

入参：

```js
{
  code: 'wx_login_code'
}
```

出参：

```js
{
  success: true,
  data: {
    token: 'session_token_xxx',
    user: {
      id: 'user_001',
      nickname: '微信用户',
      avatarUrl: '',
      createdAt: '2026-05-16T10:00:00+08:00'
    }
  },
  message: ''
}
```

后端要求：

- 后端使用 `code` 调用微信服务换取用户身份。
- 前端不得接触微信 `AppSecret`。
- 登录失败返回 `LOGIN_FAILED`。

### 7.2 上传图片

```http
POST /api/v1/uploads/images
Content-Type: multipart/form-data
Authorization: Bearer <session_token>
X-Guest-Id: <guest_id>
```

入参：

|字段|类型|必填|说明|
|---|---|---|---|
|file|File|是|JPG / PNG 图片，最大 10MB|
|petType|String|否|`cat` 或 `dog`|

出参：

```js
{
  success: true,
  data: {
    imageUrl: 'https://example.com/images/poop_001.jpg',
    imageSha256: 'sha256_xxx',
    width: 1024,
    height: 768,
    size: 524288
  },
  message: ''
}
```

后端要求：

- 校验文件类型和大小。
- 生成图片 SHA256。
- 图片存储路径不得暴露本地文件系统路径。
- 上传失败返回 `UPLOAD_FAILED`。

### 7.3 提交 AI 分析

```http
POST /api/v1/analyses
Content-Type: application/json
Authorization: Bearer <session_token>
X-Guest-Id: <guest_id>
```

入参：

```js
{
  imageUrl: 'https://example.com/images/poop_001.jpg',
  imageSha256: 'sha256_xxx',
  petType: 'dog',
  petName: '狗狗'
}
```

出参：

```js
{
  success: true,
  data: {
    id: 'analysis_001',
    score: 82,
    riskLevel: 'low',
    riskText: '低风险',
    summary: '从照片来看，便便颜色、形状和质地整体较稳定，可继续观察日常状态。',
    observationAdvice: [
      '建议观察 24 到 48 小时，注意饮食和精神状态变化',
      '保持充足饮水',
      '如持续异常，请咨询线下专业兽医'
    ],
    dietAdvice: '可适当增加高纤维食物，如南瓜、红薯等，帮助维持肠道健康。',
    needVet: false,
    imageUrl: 'https://example.com/images/poop_001.jpg',
    imageSha256: 'sha256_xxx',
    petType: 'dog',
    petName: '狗狗',
    createdAt: '2026-05-16T10:00:00+08:00'
  },
  message: ''
}
```

后端要求：

- 先校验每日次数限制和 10 秒间隔限制。
- 先按 `imageSha256` 查询缓存，命中时直接返回结构化历史结果。
- 未命中缓存时才调用 AI 服务。
- AI 原始结果必须清洗为 `AnalysisResult`。
- 分析繁忙返回 `ANALYSIS_BUSY`。
- 次数超限返回 `ANALYSIS_LIMIT_EXCEEDED`。
- 请求过于频繁返回 `ANALYSIS_TOO_FREQUENT`。

### 7.4 获取最近一次记录

```http
GET /api/v1/records/recent
Authorization: Bearer <session_token>
X-Guest-Id: <guest_id>
```

出参：

```js
{
  success: true,
  data: {
    id: 'record_001',
    analysisId: 'analysis_001',
    imageUrl: 'https://example.com/images/poop_001.jpg',
    score: 82,
    riskLevel: 'low',
    riskText: '低风险',
    summary: '状态良好，继续保持',
    createdAt: '2026-05-16T10:00:00+08:00'
  },
  message: ''
}
```

无记录：

```js
{
  success: true,
  data: null,
  message: ''
}
```

### 7.5 获取健康记录列表

```http
GET /api/v1/records?page=1&pageSize=20
Authorization: Bearer <session_token>
```

出参：

```js
{
  success: true,
  data: {
    list: [
      {
        id: 'record_001',
        analysisId: 'analysis_001',
        imageUrl: 'https://example.com/images/poop_001.jpg',
        score: 82,
        riskLevel: 'low',
        riskText: '低风险',
        summary: '状态良好，继续保持',
        createdAt: '2026-05-16T10:00:00+08:00'
      }
    ],
    pagination: {
      page: 1,
      pageSize: 20,
      total: 1,
      hasMore: false
    }
  },
  message: ''
}
```

后端要求：

- 历史列表仅登录用户可访问。
- 未登录返回 `AUTH_REQUIRED`。
- 只能返回当前用户自己的记录。

### 7.6 保存健康记录

```http
POST /api/v1/records
Content-Type: application/json
Authorization: Bearer <session_token>
```

入参：

```js
{
  analysisId: 'analysis_001'
}
```

出参：

```js
{
  success: true,
  data: {
    id: 'record_001'
  },
  message: '保存成功'
}
```

后端要求：

- 保存记录必须登录。
- 只能保存当前用户或当前上下文允许访问的分析结果。
- 重复保存应幂等返回已有记录或明确成功。

### 7.7 删除健康记录

```http
DELETE /api/v1/records/{id}
Authorization: Bearer <session_token>
```

出参：

```js
{
  success: true,
  data: null,
  message: '删除成功'
}
```

后端要求：

- 删除记录必须登录。
- 只能删除当前用户自己的记录。
- 记录不存在或无权限返回 `RECORD_NOT_FOUND`。

---

## 8. Service 方法映射

|前端 service|HTTP 接口|
|---|---|
|`authService.loginByWechat`|`POST /api/v1/auth/wechat-login`|
|`uploadService.uploadImage`|`POST /api/v1/uploads/images`|
|`analysisService.submitAnalysis`|`POST /api/v1/analyses`|
|`recordService.getRecentRecord`|`GET /api/v1/records/recent`|
|`recordService.getRecords`|`GET /api/v1/records`|
|`recordService.saveRecord`|`POST /api/v1/records`|
|`recordService.deleteRecord`|`DELETE /api/v1/records/{id}`|

---

## 9. 错误码

|错误码|说明|推荐提示|
|---|---|---|
|AUTH_REQUIRED|需要登录|请先登录后继续|
|LOGIN_FAILED|登录失败|登录失败，请重试|
|IMAGE_REQUIRED|未选择图片|请先上传便便照片|
|IMAGE_TYPE_INVALID|图片类型不支持|仅支持 JPG、PNG 图片|
|IMAGE_SIZE_EXCEEDED|图片过大|图片不能超过 10MB|
|UPLOAD_FAILED|上传失败|图片上传失败，请重试|
|ANALYSIS_BUSY|分析繁忙|当前分析人数较多，请稍后再试|
|ANALYSIS_FAILED|分析失败|分析失败，请稍后重试|
|ANALYSIS_LIMIT_EXCEEDED|次数超限|今日分析次数已用完|
|ANALYSIS_TOO_FREQUENT|分析过于频繁|请 10 秒后再试|
|RECORD_NOT_FOUND|记录不存在|记录不存在或已删除|
|VALIDATION_ERROR|参数错误|请检查输入内容|
|SERVER_ERROR|服务异常|服务异常，请稍后再试|

---

## 10. Mock 数据

### 10.1 最近一次记录

```js
{
  success: true,
  data: {
    id: 'record_001',
    analysisId: 'analysis_001',
    imageUrl: '',
    score: 82,
    riskLevel: 'low',
    riskText: '低风险',
    summary: '状态良好，继续保持',
    createdAt: '2026-05-16T10:00:00+08:00'
  },
  message: ''
}
```

### 10.2 记录列表

```js
{
  success: true,
  data: {
    list: [
      {
        id: 'record_001',
        analysisId: 'analysis_001',
        imageUrl: '',
        score: 82,
        riskLevel: 'low',
        riskText: '低风险',
        summary: '状态良好，继续保持',
        createdAt: '2026-05-16T10:00:00+08:00'
      },
      {
        id: 'record_002',
        analysisId: 'analysis_002',
        imageUrl: '',
        score: 65,
        riskLevel: 'medium',
        riskText: '中风险',
        summary: '便便偏软，注意饮食',
        createdAt: '2026-05-15T14:20:00+08:00'
      },
      {
        id: 'record_003',
        analysisId: 'analysis_003',
        imageUrl: '',
        score: 35,
        riskLevel: 'high',
        riskText: '高风险',
        summary: '异常较明显，建议咨询线下专业兽医',
        createdAt: '2026-05-12T20:10:00+08:00'
      }
    ],
    pagination: {
      page: 1,
      pageSize: 20,
      total: 3,
      hasMore: false
    }
  },
  message: ''
}
```

### 10.3 AI 分析结果

```js
{
  success: true,
  data: {
    id: 'analysis_001',
    score: 82,
    riskLevel: 'low',
    riskText: '低风险',
    summary: '从照片来看，便便颜色、形状和质地整体较稳定，可继续观察日常状态。',
    observationAdvice: [
      '建议观察 24 到 48 小时，注意饮食和精神状态变化',
      '保持充足饮水',
      '如持续异常，请咨询线下专业兽医'
    ],
    dietAdvice: '可适当增加高纤维食物，如南瓜、红薯等，帮助维持肠道健康。',
    needVet: false,
    imageUrl: '',
    imageSha256: 'sha256_mock_low',
    petType: 'dog',
    petName: '狗狗',
    createdAt: '2026-05-16T10:00:00+08:00'
  },
  message: ''
}
```

---

## 11. 后端接入要求

- 后端实现时优先遵循本文档字段。
- 后端如果使用不同字段命名，必须在 API 出口转换。
- 后端不得要求前端传递任何 AI API Key。
- AI 原始返回结果必须由后端清洗为本文档中的 `AnalysisResult` 结构。
- 后端错误码应与本文档保持一致。
- 涉及接口字段变更时，必须先更新本文档，再修改代码。
