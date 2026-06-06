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


### 测试运行流程-大概
- 每个测试用例运行前都会先运行根目录下`conftest` 文件，里面封装了登录接口，且登录接口中进行了通配消息头
- 这样在请求其他接口时,消息体中的token自动传递,GET/POST等请求中的`parameter`因为也是通用的
- 所以这部分也进行了通配操作,接口中不需要额外传参.


### 目录说明
- base 基础通用方法/封装函数
- conf 配置文件/测试函数预期结果等
  - 配置文件中定义了环境,用户名/密码,接口路由
  - 所有接口路由统一放在这里进行管理 ``endpoints`` 段下面添加, 接口方法中只需要传入对应的key名
- profes 接口方法
- test_case 测试方法