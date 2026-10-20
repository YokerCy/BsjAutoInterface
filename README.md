[Allure报告项目地址](https://github.com/allure-framework/allure2/releases)

简介: 采用 API Object 与 DDT(Data-Driven Testing) 数据驱动思想构建基础架构

- 执行全部用例
``python main.py``
- 只运行单个文件
``python main.py -f tests/test_user_tree.py``
- 按模块（目录）执行
``python main.py -d tests/vehicle/``
- 按标签执行（需要配合 @pytest.mark）
- 在用例上标记了 @pytest.mark.smoke
``python main.py -m smoke``

- 传递环境变量
``python main.py -env prod``


- 生成报告

 `allure generate ./allure-results -o ./allure-report --clean`

- 打开报告

`allure open ./allure-report`

- 临时分享
``allure serve ./allure-results -h ip -p 8888``

两个接口有上下关联,可以使用: pytest.mark.dependency 来管理它们的依赖关系

语法
``@pytest.mark.parametrize("参数名1, 参数名2, ...", 数据列表)``

### 说明
- 每个test_文件中都需要实列化 cfg = Config()
- 测试函数中使用参数化
  - ``@pytest.mark.parametrize(
      "user_tree",
      cfg.get_cases_by_interface("user_expect", "get_user_tree")
  )``
  - 第一个值为参数名，参数名需要与数据列表对应
  - 数据列表 通过方法`get_cases_by_interface`从`yaml`文件中获取对应的方法名
  - yaml 文件中第一个参数为yaml文件名,第二个参数key为: interface; 列如上述示列中的值为: get_user_tree
    

- 预期结果与实际结果在allure中的展示
- 重新封装了attach函数, 在test_方法中引用,如下
- ``allure_attach_comparison()``
- 第一个参数为预期结果,第二个参数为实际结果,第三个参数为验证别称 默认显示数据对比


### 目录说明
- base 基础通用方法/封装函数
- conf 配置文件/测试函数预期结果等
  - 配置文件中定义了环境,接口路由,**账号密码不写在里面**（见下节）
  - 所有接口路由统一放在这里进行管理 ``endpoints`` 段下面添加, 接口方法中只需要传入对应的key名
- profes 接口方法
- test_case 测试方法

### 凭据配置（本仓库是公开仓库，禁止提交真实凭据）

`conf/config.yaml` 里所有凭据都是 `${变量名}` 占位符，实际值按优先级注入：

1. **环境变量**（CI / 服务器推荐）：`TEST_USERNAME`、`TEST_PASSWORD`、`OPEN_API_KEY`、`MAILSLURP_API_KEY` …
2. **`conf/config.local.yaml`**（本地开发）：`secrets` 段下同名键
3. 两者都没有 → 启动即报错，不会静默用空值登录

首次使用：

```bash
copy conf\config.local.example.yaml conf\config.local.yaml   # 然后填入真实值
```

`config.local.yaml` 已被 `.gitignore` 忽略。缺密钥时的报错信息里会直接给出这两种配置方式。

### 测试运行流程-大概
- 每个测试用例运行前都会先运行根目录下`conftest` 文件，里面封装了登录接口，且登录接口中进行了通配消息头
- 这样在请求其他接口时,消息体中的token自动传递,GET/POST等请求中的`parameter`因为也是通用的
- 所以这部分也进行了通配操作,接口中不需要额外传参.


### 目录说明
- base 基础通用方法/封装函数
- conf 配置文件/测试函数预期结果等
  - 配置文件中定义了环境,接口路由,**账号密码不写在里面**（见下节）
  - 所有接口路由统一放在这里进行管理 ``endpoints`` 段下面添加, 接口方法中只需要传入对应的key名
- profes 接口方法
- test_case 测试方法

---

## UI 自动化层（Playwright）

接口层覆盖业务逻辑，UI 层只做冒烟（约 10%），验证**用户真正看得见的状态**：
按钮置灰、弹窗弹不弹、日历蓝点、告警红色、文件下载。

### 目录

| 目录 | 职责 |
|---|---|
| `base/ui/` | 基础设施：配置读取、登录态快照、context 构建 |
| `ui/pages/` | Page Object，**locator 只允许写在这里** |
| `ui/flows/` | 业务流程（多页面串联） |
| `ui/test_smoke/` | 冒烟用例，每条带 `@allure.id` 对应手工用例编号 |

### 执行

```bash
# 全部 UI 冒烟
python -m pytest ui/ -v --alluredir=./allure-results-ui

# 只跑 P0
python -m pytest ui/ -m p0 -v

# 有头模式（看得到浏览器操作过程，排查用）
python -m pytest ui/ -v --headed

# 看报告
allure serve ./allure-results-ui
```

### 浏览器内核

默认用本机安装的 **Chrome**（`channel=chrome`）——平台用户绝大多数用 Chrome，
自动化用同一内核，渲染差异、兼容性问题和用户看到的才一致。

渠道按 `conf/ui.yaml -> browser` 决策，顺序是：

1. 命令行 `--browser-channel xxx`（最高优先级，临时排查用）
2. `channel: "chrome"`
3. `fallback_channels: ["msedge"]`（本机没装 Chrome 时自动降级，不用改代码）
4. 都没有才用 Playwright 自带 chromium（需先 `python -m playwright install chromium`）

**不需要下载内核**：直接驱动系统已安装的 Chrome。安装路径支持用户级安装
（`%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe`），不只查 Program Files。

**UA 处理**：无头模式会带上 `HeadlessChrome` 标记，部分前端环境判断或风控会据此
走不同分支，导致"自动化跑的和用户看到的不一样"。`mask_headless_ua: true`（默认）
会把 UA 修正为真实版本号（如 `Chrome/155.0.0.0`），`navigator.userAgentData`
也会显示 `Google Chrome`。

### 登录态

首次运行会真实登录一次并写入 `logs/ui_state.json`，**12 小时内复用**，过期自动重登。
删掉该文件即可强制重新登录。

### 失败留证

失败时自动在 `logs/ui_artifacts/` 留存：

- `<case>.zip` —— Playwright trace：`playwright show-trace logs/ui_artifacts/xxx.zip`
  可完整回放现场（DOM 快照 + 网络请求 + 控制台日志）
- `<case>.png` —— 失败瞬间全页截图

### 两个页面 fixture（别混用）

- `anon_page` —— **无登录态**，用于登录页自身（登录成功/失败/表单校验）
- `app_page` —— **带登录态**，用于业务页，免去每条用例重复登录

混用会导致登录用例假绿：带登录态打开登录页会被路由守卫直接弹走。