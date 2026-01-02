Flask 路由注册的完整流程：

## Flask 路由注册完整流程

### 阶段 1：应用启动（run.py）

```py
"""
应用启动入口
"""
import os
from app import create_app

# 从环境变量获取配置名称，默认为 development
config_name = os.getenv('FLASK_ENV', 'development')

# 创建应用实例
app = create_app(config_name)

if __name__ == '__main__':
    # 开发环境运行
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    )
```

执行步骤：
1. 导入 `create_app` 工厂函数
2. 调用 `create_app(config_name)` 创建 Flask 应用
3. 启动 Flask 开发服务器

---

### 阶段 2：创建 Flask 应用（app/__init__.py）

```py
def create_app(config_name='default'):
    """
    应用工厂函数
    
    Args:
        config_name: 配置名称，可选值: 'development', 'testing', 'production', 'default'
    
    Returns:
        Flask 应用实例
    """
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)

    # 配置 CORS（允许跨域请求）
    CORS(app, 
         resources={r"/api/*": {
             "origins": "*",
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "expose_headers": ["Content-Type"]
         }})

    # 初始化 Redis
    redis_client.init_app(app)
    
    # 初始化 Flasgger（配置已在 config 中设置）
    swagger.init_app(app)
    
    # 导入模型（让 Flask-Migrate 能够检测到表结构）
    from app import models
    
    # 注册蓝图
    from app.api.v1 import api_v1
    app.register_blueprint(api_v1, url_prefix='/api/v1')
    
    # 注册错误处理器
    from app.utils.exceptions import register_error_handlers
    register_error_handlers(app)
    
    # 注册CLI命令
    from app.commands.seed import register_commands
    register_commands(app)
    
    # 创建数据库表（仅用于开发环境）
    with app.app_context():
        # 注意：生产环境应该使用 Flask-Migrate 进行数据库迁移
        # db.create_all()
        pass
    
    return app
```

执行步骤：
1. 创建 Flask 应用实例：`app = Flask(__name__)`
2. 加载配置
3. 初始化扩展（数据库、Redis 等）
4. 注册蓝图：`app.register_blueprint(api_v1, url_prefix='/api/v1')`

---

### 阶段 3：创建 API 蓝图（app/api/v1/__init__.py）

```py
"""
API v1 版本蓝图
"""
from flask import Blueprint

api_v1 = Blueprint('api_v1', __name__)

# 导入并注册路由蓝图
from app.api.v1 import laboratory, auth, users, equipment, admin

# 注册路由蓝图
api_v1.register_blueprint(laboratory.lab_bp, url_prefix='/laboratories')
api_v1.register_blueprint(auth.auth_bp, url_prefix='/auth')
api_v1.register_blueprint(users.users_bp, url_prefix='/users')
api_v1.register_blueprint(equipment.equipment_bp, url_prefix='/equipments')
api_v1.register_blueprint(admin.admin_bp, url_prefix='/admin')


@api_v1.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return {'status': 'ok', 'version': '1.0.0'}, 200
```

执行步骤：
1. 创建 API v1 蓝图：`api_v1 = Blueprint('api_v1', __name__)`
2. 导入子蓝图模块（触发子蓝图的路由注册）
3. 注册子蓝图到 `api_v1`：
   - `users.users_bp` → `/users`
   - `auth.auth_bp` → `/auth`
   - 等等
4. 直接在 `api_v1` 上定义路由（如 `/health`）

---

### 阶段 4：创建子蓝图并定义路由（app/api/v1/users.py）

```py
# 创建蓝图
users_bp = Blueprint('users', __name__)


@users_bp.route('/me', methods=['GET'])
@login_required
@swag_from({
    'tags': ['用户管理'],
    'summary': '获取当前登录用户详细信息',
    'description': '获取当前登录用户的详细信息，包含实验室ID等信息',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': '成功返回用户信息',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 200},
                    'msg': {'type': 'string', 'example': 'success'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'string', 'example': '2021001'},
                            'name': {'type': 'string', 'example': '张三'},
                            'user_type': {'type': 'string', 'example': 'student'},
                            'lab_id': {'type': 'integer', 'example': 1},
                            'lab_name': {'type': 'string', 'example': '计算机实验室'}
                        }
                    }
                }
            }
        },
        401: {
            'description': '未授权'
        }
    }
})
def get_current_user_info():
```

执行步骤：
1. 创建子蓝图：`users_bp = Blueprint('users', __name__)`
2. 使用路由装饰器：`@users_bp.route('/me', methods=['GET'])`
3. 添加其他装饰器：`@login_required`、`@swag_from`
4. 定义视图函数：`def get_current_user_info():`

---

### 阶段 5：路由注册的完整链路

```
┌─────────────────────────────────────────────────────────────┐
│ 1. run.py 启动应用                                          │
│    app = create_app()                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. app/__init__.py - create_app()                           │
│    app = Flask(__name__)                                    │
│    app.register_blueprint(api_v1, url_prefix='/api/v1')    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. app/api/v1/__init__.py                                  │
│    api_v1 = Blueprint('api_v1', __name__)                   │
│    api_v1.register_blueprint(users.users_bp,                 │
│                           url_prefix='/users')               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. app/api/v1/users.py                                      │
│    users_bp = Blueprint('users', __name__)                  │
│    @users_bp.route('/me', methods=['GET'])                  │
│    def get_current_user_info():                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Flask 内部路由表                                          │
│    URL: /api/v1/users/me                                    │
│    Method: GET                                              │
│    View: get_current_user_info                              │
│    Decorators: [login_required, swag_from]                   │
└─────────────────────────────────────────────────────────────┘
```

---

### 阶段 6：URL 路径构建过程

```
步骤 1: 子蓝图路由路径
@users_bp.route('/me', methods=['GET'])
路径: /me

步骤 2: 子蓝图注册到 API 蓝图
api_v1.register_blueprint(users.users_bp, url_prefix='/users')
路径: /users + /me = /users/me

步骤 3: API 蓝图注册到 Flask 应用
app.register_blueprint(api_v1, url_prefix='/api/v1')
路径: /api/v1 + /users/me = /api/v1/users/me

最终 URL: http://localhost:5000/api/v1/users/me
```

---

### 阶段 7：请求处理流程

当用户发送请求时：

```http
GET /api/v1/users/me HTTP/1.1
Host: localhost:5000
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

Flask 处理流程：

```
1. Flask 接收 HTTP 请求
   ↓
2. 解析请求：方法=GET, 路径=/api/v1/users/me
   ↓
3. 在路由表中查找匹配的路由
   ├─ 找到：/api/v1/users/me (GET)
   └─ 对应的视图函数：get_current_user_info
   ↓
4. 执行装饰器链（从外到内）：
   a. @users_bp.route 已完成（路由已注册）
   b. @login_required 执行：
      - 调用 get_current_user()
      - 验证 JWT Token
      - 如果失败 → 返回 401，停止
      - 如果成功 → 继续
   c. @swag_from 已完成（文档已注册）
   ↓
5. 执行视图函数：get_current_user_info()
   ├─ 获取当前用户信息
   ├─ 查询数据库
   └─ 返回 JSON 响应
   ↓
6. 返回 HTTP 响应给客户端
```

---

### 阶段 8：完整代码示例

#### 步骤 1：创建子蓝图文件（app/api/v1/users.py）

```python
from flask import Blueprint
from app.utils.auth import login_required

# 1. 创建蓝图
users_bp = Blueprint('users', __name__)

# 2. 定义路由和视图函数
@users_bp.route('/me', methods=['GET'])
@login_required
def get_current_user_info():
    """获取当前用户信息"""
    # 业务逻辑
    return {'message': 'success'}, 200
```

#### 步骤 2：注册子蓝图到 API 蓝图（app/api/v1/__init__.py）

```python
from flask import Blueprint

# 1. 创建 API 蓝图
api_v1 = Blueprint('api_v1', __name__)

# 2. 导入子蓝图（触发路由注册）
from app.api.v1 import users

# 3. 注册子蓝图
api_v1.register_blueprint(users.users_bp, url_prefix='/users')
```

#### 步骤 3：注册 API 蓝图到 Flask 应用（app/__init__.py）

```python
from flask import Flask

def create_app():
    # 1. 创建 Flask 应用
    app = Flask(__name__)
    
    # 2. 导入 API 蓝图
    from app.api.v1 import api_v1
    
    # 3. 注册 API 蓝图
    app.register_blueprint(api_v1, url_prefix='/api/v1')
    
    return app
```

#### 步骤 4：启动应用（run.py）

```python
from app import create_app

# 创建应用
app = create_app()

# 启动服务器
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

---

### 阶段 9：路由注册时机

重要：路由注册发生在应用启动时，不是请求时。

```
应用启动时（一次性）：
├─ 导入模块
├─ 执行蓝图创建代码
├─ 执行 @route 装饰器（注册路由）
└─ 构建路由表

请求到达时（每次）：
├─ 查找路由表
├─ 执行装饰器链
└─ 执行视图函数
```

---

### 阶段 10：路由表结构（Flask 内部）

Flask 内部维护的路由表类似：

```python
# Flask 内部路由表（简化版）
routes = {
    'GET': {
        '/api/v1/users/me': {
            'view_func': get_current_user_info,
            'endpoint': 'users.get_current_user_info',
            'decorators': [login_required, swag_from]
        },
        '/api/v1/laboratories': {
            'view_func': get_labs,
            'endpoint': 'laboratory.get_labs',
            'decorators': []
        },
        # ... 更多路由
    },
    'POST': {
        '/api/v1/auth/login': {
            'view_func': login,
            'endpoint': 'auth.login',
            'decorators': []
        },
        # ... 更多路由
    }
}
```

---

## 完整流程图总结

```
┌──────────────────────────────────────────────────────────────┐
│                    应用启动阶段                                │
├──────────────────────────────────────────────────────────────┤
│ 1. run.py                                                    │
│    └─> create_app()                                          │
│                                                               │
│ 2. app/__init__.py                                           │
│    ├─> Flask(__name__)                                       │
│    └─> register_blueprint(api_v1, '/api/v1')                │
│                                                               │
│ 3. app/api/v1/__init__.py                                    │
│    ├─> Blueprint('api_v1')                                   │
│    ├─> import users (触发 users.py 执行)                      │
│    └─> register_blueprint(users_bp, '/users')                 │
│                                                               │
│ 4. app/api/v1/users.py                                       │
│    ├─> Blueprint('users')                                    │
│    └─> @users_bp.route('/me') ← 注册路由到 Flask             │
│                                                               │
│ 5. Flask 构建路由表                                          │
│    /api/v1/users/me → get_current_user_info                  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    请求处理阶段                                │
├──────────────────────────────────────────────────────────────┤
│ 1. 用户请求: GET /api/v1/users/me                           │
│                                                               │
│ 2. Flask 路由匹配                                            │
│    └─> 找到: get_current_user_info                           │
│                                                               │
│ 3. 执行装饰器链                                               │
│    ├─> @login_required: 验证 Token                            │
│    └─> 验证通过，继续执行                                     │
│                                                               │
│ 4. 执行视图函数                                               │
│    └─> get_current_user_info()                               │
│                                                               │
│ 5. 返回响应                                                   │
│    └─> JSON 数据                                             │
└──────────────────────────────────────────────────────────────┘
```

---