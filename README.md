# StockAnalysisSystem
This program is designed for Chinese market and Chinese accounting policies (currently). So this document will only provide Chinese version.
  
# Gitee
https://gitee.com/SleepySoft/StockAnalysisSystem  
  
# Github
https://github.com/SleepySoft/StockAnalysisSystem  
  
# 网盘下载：  
应网友要求，对于网络访问受限的用户，提供网盘下载（离线数据同样在此下载）：  
链接: https://pan.baidu.com/s/1LJ11m5nHkaknQXqHSzdLMA  
提取码: 8871  
  
# 最近更新内容： 
将访问接口扩展为sasApi和sasInterface，并将界面与服务彻底分离  
如果想使用之前一体式的版本（不会更新），请checkout One-Piece  
  
如何运行:  
* 环境准备看下面  
* 首先按需要修改doc/config_example.json，没有或不清楚的项目不需要改，更名为config.json并复制到运行目录下  
> 由于界面和服务分离，所以无法像之前一样检测配置并弹出配置窗口（后面再做），故需要先把配置文件准备好。  
* 运行方式1：直接运行main.py，在弹出的窗口中选择local interface  
> 这种方式将会调用本地接口，即和之前一样，界面和服务运行在同一个进程内  
* 运行方式2：先运行main_service.py，再运行main.py，在弹出的窗口中选择remote interface  
> 这种方式将会调用远程接口，通过网络连接服务器，关闭界面不影响服务运行  
  
移除功能：
* 年报下载插件  
> 网站接口变化，现在已无法下载。如果有可用的库，欢迎推荐。谢谢。之前下载的年报可以在网盘下载，很大。  
* 证监会立案调查数据  
> 网站不再提供该服务，如果有替代数据源，欢迎推荐。谢谢。  
  
已知问题：  
* 本次改动比较大（指ui和sas的接口，内部结构并未变化），而数据源也有所改变，故问题可能较多。欢迎大家提出bug，使程序更加完善。多谢。  
* 界面对更新进度显示有误，服务器仍在更新，但界面有可能显示更新完成（我看看怎么修）。  
* 无法获得服务器状态，故ui无法展示服务器配置错误等状态（接口预留，待加功能）。  
* 网盘可能会被举报失效（莫名其妙）  
  
# 视频讲解（未更新，不过内部结构没变）  
安装配置：https://www.bilibili.com/video/BV14z411b7AE/  
设计与框架：https://www.bilibili.com/video/BV1nK411p7uD/  
服务框架请看doc/design.vsd  
  
# 运行环境  
* 由于图表引入了pyqtgraph，导致pyinstaller打包出现问题，并且尝试py2exe也不成功，故暂停以EXE形式发布Release  
  
## 只想看结果  
* 打开analysis_report.xlsx  
  
## 大神看这里  
* 需要安装MongoDB  
* Python3.7，推荐Anaconda  
* requirements.txt你们懂的  
* 从main.py运行  
  
## 新手看这里  
* 从网盘下载MongoDB及Anaconda并安装  
* 按WIN键，输入：“cmd”，选择用管理员运行命令行  
* 在命令行中执行命令：“conda create -n sas python=3.7”，需要确认就输入y回车  
* 如果提示找不到conda，请参考这篇文章，将你的anaconda加入到系统目录中：https://blog.csdn.net/u013211009/article/details/78437098  
* 如果一切正常，运行命令：“conda activate sas”，这时你的命令行会出现(sas)字样  
* 执行以下命令切换到代码目录：“cd "你的代码目录"”比如：cd "D:\Code\git\StockAnalysisSystem"  
* 切换到代码目录后运行命令：“pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple”  
* 如果提示pip版本太旧，按提示运行命令：“python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple” 完成后再执行上一条命令  
* 最后一步，运行命令：“python main.py”  
------------------------------------------------------------  
* 以后运行只需要打开cmd并切换到代码目录（一个简单的方法，用文件管理器打开代码目录，在上方的地址栏直接输入cmd回车即可）  
* 先运行命令：“conda activate sas”  
* 再运行命令：“python main.py”  
  
# 联系作者
如果有任何意见及建议，或者对此项目感兴趣的，请联系我：  
微博：SleepySoft  
邮箱：sleepysoft##163.com  
QQ群：931499339，进群验证码：SleepySoft  
如果遇到BUG，可以给我发邮件，或直接在git上提交issue  
  
----------------------------------------------------------------------------------------------------------------------
  
# 本程序的目的  
1. 自动选择合适的数据抓取模块和数据源下载所需要的数据  
2. 数据抓取模块能够进行有效性检测，并且能够方便地扩充和替换，可以通过适配器接入其它的库  
3. 增加一个数据源以及将其本地化所需的代码应尽可能少  
4. 能进行离线分析  
5. 分析模块（策略模块）应该可以动态扩充和组合  
6. 最终能生成矩阵式excel报告：以证券为行，以分析方法为列，相交点为此分析方法对此证券的评分；最后一列为该证券的总分  
  
----------------------------------------------------------------------------------------------------------------------
  
# 功能说明  
  
## 主要功能  
* 报告格式说明  
  
报告为表格矩阵，以股票代码为列，以分析算法为行，相交格子为该算法对此股票的评分（0 - 100）  
> 0：VETO  
> 1 -50：FAIL  
> 51 - 75：FLAW  
> 76 - 90：WELL  
> 91 - 100：PASS  
  
结果分为两页，第一页为评分，第二页为分析算法输出的详细信息，以供人工核对及查阅  
绿色为PASS，红色为FAIL，灰色为不适用，或因数据缺失导致无法分析  
最后一列为总评分，在一行中，只要有一个评分为FAIL，则总评分为FAIL；如果不存在FAIL但存在灰色结果，则总评分为灰色的PASS  
当前分析算法还不够完善，结果仅供参考，遇到和自己分析存在偏差的情况，请参阅详细信息并进行人工复核  
  
## 扩展功能  
  
* Stock Memo  
  
![image](res/StockMemo_00.png)
![image](res/StockMemo_01.png)
![image](res/StockMemo_02.png)
  
----------------------------------------------------------------------------------------------------------------------
  
# 开发计划：
  
* 接入更多数据  
> 限售股解禁: https://tushare.pro/document/2?doc_id=160  
> 回购数据  
> 增减持数据: https://tushare.pro/document/2?doc_id=175  
> 实际控制人数据（巨潮）: http://webapi.cninfo.com.cn/#/dataBrowse?id=266  
* 加入更多分析算法  
> 量价分析  
* 整合测试入口，执行一个文件即可运行所有测试  
* 加入实时数据  
* 盯盘  
* 投资图谱  
* 做成WebService，通过APP操作  
