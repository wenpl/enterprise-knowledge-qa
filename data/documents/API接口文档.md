# API接口文档

## 概述

本文档描述了ABC公司内部系统的API接口规范。所有接口均采用RESTful风格，数据格式为JSON。

## 认证方式

### Token认证

所有API请求需要在Header中携带Token：

```
Authorization: Bearer <your_token>
```

Token获取方式：
1. 调用登录接口获取Token
2. Token有效期为24小时
3. Token过期后需重新登录获取

## 接口列表

### 1. 用户登录

**接口地址**：`POST /api/v1/auth/login`

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码（MD5加密） |

**请求示例**：

```json
{
    "username": "zhangsan",
    "password": "e10adc3949ba59abbe56e057f20f883e"
}
```

**响应参数**：

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | int | 状态码，0表示成功 |
| message | string | 提示信息 |
| data | object | 返回数据 |
| data.token | string | 认证Token |
| data.expire_time | string | Token过期时间 |

**响应示例**：

```json
{
    "code": 0,
    "message": "登录成功",
    "data": {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "expire_time": "2024-01-02 18:00:00"
    }
}
```

### 2. 获取用户信息

**接口地址**：`GET /api/v1/user/info`

**请求头**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer Token |

**响应参数**：

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | int | 状态码 |
| data | object | 用户信息 |
| data.user_id | int | 用户ID |
| data.username | string | 用户名 |
| data.email | string | 邮箱 |
| data.department | string | 部门 |
| data.role | string | 角色 |

**响应示例**：

```json
{
    "code": 0,
    "data": {
        "user_id": 10001,
        "username": "张三",
        "email": "zhangsan@abc.com",
        "department": "技术部",
        "role": "开发工程师"
    }
}
```

### 3. 创建订单

**接口地址**：`POST /api/v1/order/create`

**请求头**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer Token |
| Content-Type | string | 是 | application/json |

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| product_id | int | 是 | 产品ID |
| quantity | int | 是 | 数量 |
| address | string | 是 | 收货地址 |
| remark | string | 否 | 备注 |

**请求示例**：

```json
{
    "product_id": 1001,
    "quantity": 2,
    "address": "北京市朝阳区xxx街道xxx号",
    "remark": "请在工作日配送"
}
```

**响应参数**：

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | int | 状态码 |
| data | object | 订单信息 |
| data.order_id | string | 订单号 |
| data.total_price | float | 总价 |
| data.status | string | 订单状态 |

**响应示例**：

```json
{
    "code": 0,
    "data": {
        "order_id": "202401020001",
        "total_price": 299.00,
        "status": "待支付"
    }
}
```

### 4. 查询订单列表

**接口地址**：`GET /api/v1/order/list`

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| status | string | 否 | 订单状态筛选 |

**响应示例**：

```json
{
    "code": 0,
    "data": {
        "total": 100,
        "page": 1,
        "page_size": 20,
        "list": [
            {
                "order_id": "202401020001",
                "product_name": "产品A",
                "total_price": 299.00,
                "status": "已完成",
                "create_time": "2024-01-02 10:00:00"
            }
        ]
    }
}
```

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1001 | Token无效或已过期 |
| 1002 | 参数错误 |
| 1003 | 用户不存在 |
| 1004 | 密码错误 |
| 2001 | 产品不存在 |
| 2002 | 库存不足 |
| 3001 | 系统错误 |

## 调用频率限制

- 每个Token每分钟最多调用100次
- 超过限制将返回错误码4001
- 建议在客户端实现请求队列和重试机制
