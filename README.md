# StockAnalysisSystem
This program is designed for Chinese market and Chinese accounting policies (currently). So this document will only provide Chinese version.
  
# Gitee
https://gitee.com/SleepySoft/StockAnalysisSystem  
  
# Github
https://github.com/SleepySoft/StockAnalysisSystem  

# 新文档系列
01.开发环境配置 http://sleepysoft.xyz/archives/137  
02.SAS系统配置 http://sleepysoft.xyz/archives/166  
  
# 网盘下载：  
应网友要求，对于网络访问受限的用户，提供网盘下载： 

### 网盘（新）  
* 根目录  
链接（含提取码）: https://pan.baidu.com/s/1NkjEhXUuwC4F1WdC_kIIvg?pwd=7xu8  
  
* 由于之前的网盘账号会员到期，容量超限，所以新资源将用另一个账号发布，旧账号上的资源不再更新  
* 新网盘主要用于更新离线数据和分析报告，而旧网盘中的其它资源依旧有价值  
* 由于上传了大文件导致一些问题，于是彻底清理了大文件，以下文件放在度盘中：
> offline_analysis_result.zip (供服务使用)  
> analysis_report.xlsx (程序生成的分析报告，供人类阅读)  
  
### 网盘（旧）  
* 根目录  
链接: https://pan.baidu.com/s/1trY6GJ_ixj3ulXDA2JIGRg  
提取码: 4d9f  
* 离线数据
链接：https://pan.baidu.com/s/1ejiijSrFA0-ZIks_jmNgtw  
提取码：qxj9  
  
* 十年年报  
链接：https://pan.baidu.com/s/1bnjnlrwO4bekT7CpfvfteA  
提取码：x3zt  
  
* 软件及工具  
链接：https://pan.baidu.com/s/1p9psTFIdQc3nbEORTzSxyw  
提取码：y3yv  
  
# 微信服务  
  
服务器已建成，微信机器人可以使用，添加下方的账号可以体验此功能（可将机器人拉入群聊，@TA 即可获得回复）：  
![image](Doc/ID_Code_WeChat.jpg)  
或者wx公众号：  
![image](Doc/ID_Code_WeChatPub.jpg)  
如果有兴趣，也可以自己搭建一个机器人。欢迎入群交流。  
  
# 最近更新内容：
完成自动更新服务：update_service.py，可以在配置中启用该服务  
  
如何运行:  
* 环境准备看下面  
* 首先按需要修改doc/config_example.json，没有或不清楚的项目不需要改，更名为config.json并复制到运行目录下  
> 由于界面和服务分离，所以无法像之前一样检测配置并弹出配置窗口（后面再做），故需要先把配置文件准备好。  
* 运行方式1：直接运行main.py，在弹出的窗口中选择local interface  
> 这种方式将会调用本地接口，即和之前一样，界面和服务运行在同一个进程内  
* 运行方式2：先运行main_service.py，再运行main.py，在弹出的窗口中选择remote interface  
> 这种方式将会调用远程接口，通过网络连接服务器，关闭界面不影响服务运行  
  
已知问题：  
* 由于当前主要数据源tushare的接口限制经常更改，并且积分不同限制不仅仅是调用时间间隔不同， 
  而程序中的数据获取以5000分为标准实现。所以尽管调用时间间隔可以配置，然而一次能获取的数据范围却是无法配置的。
  所以不同用户可能会出现数据获取失败的情况（详见Doc/TushareApi.xlsx）这种情况建议使用离线数据。  
  
# 视频讲解（未更新，不过内部结构没变）  
安装配置：https://www.bilibili.com/video/BV14z411b7AE/  
设计与框架：https://www.bilibili.com/video/BV1nK411p7uD/  
服务框架请看doc/design.vsd  
  
# 运行环境  
* 由于图表引入了pyqtgraph，导致pyinstaller打包出现问题，并且尝试py2exe也不成功，故暂停以EXE形式发布Release  
  
## 只想看结果  
* 打开analysis_report.xlsx (注：已转移到了度盘“分析数据”中)  
  
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
* 再运行命令：“python main_service.py”和“python main.py”  
  
## 如何更新数据  
* 在配置文件中填入你的Ts Token  
> 如果不需要更新可以随便乱填，需要更新的话：  
> 注册一个tushare的账号：https://tushare.pro/register?reg=271027  
> 想办法获取500以上的积分（如果没有，无法更新数据，但可以使用离线数据）：https://tushare.pro/document/1?doc_id=13  
* 重要：根据你的权限修改StockAnalysisSystem\core\Utility\CollectorUtility.py中的TS_DELAYER_TABLE  
> 如果你不知道该你的积分的限制，可以先把注释后面的值填进去。如果出现"抱歉，您每分钟最多访问该接口x次"的错误，把x填到表中对应的接口位置  
* 启动程序，勾选需要更新的数据并点击更新按钮  
  
## 如何导入离线数据  
* 下载离线数据并解压到当前目录，得到offline_data文件夹一个（约7G）  
* 方法1：  
> 在安装数据库的机器上打开界面，选择Config->系统配置  
> 选择正确的MongoBin目录，如C:\Program Files\MongoDB\Server\4.x\bin  
> 点击Import，选择offline_data下你需要导入的数据库（每个都导入一次）  
  
* 方法2：  
> 使用命令行切换到offline_data目录下  
> 运行命令："C:\Program Files\MongoDB\Server\4.2\bin\mongorestore.exe" --host 127.0.0.1 --port 27017 -d StockAnalysisSystem StockAnalysisSystem  
> 注意：其中mongorestore.exe按实际情况选择目录；除StockAnalysisSystem外还需要分别导入SasCache和StockDaily，命令同理  
  
* 如果你的数据库有密码，请自行查阅命令手动导入  
  
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
  
# 历史更新  
  
移除功能：
* 年报下载插件  
> 网站接口变化，现在已无法下载。如果有可用的库，欢迎推荐。谢谢。之前下载的年报可以在网盘下载，很大。  
* 证监会立案调查数据  
> 网站不再提供该服务，如果有替代数据源，欢迎推荐。谢谢。  
  
将网络服务全部做成Sub Service，并将Service Provider等放入SubService下  
加入Sub Service管理，可以在config.json中配置需要启用或禁止的子服务  
> 参考config_example.json中的注释  
  
加入微信机器人，基于WeChatSpy。原因是新号无法使用网页微信，故无法使用wxpy  
> 可以添加微信号StockAnalysisSystem体验功能  
> 也可以添加公众号SleepySoft体验公众号功能  
> 注：由于没有云服务器，所以有时候服务可能无法使用（个人电脑偶尔要调试程序）
  
> 限售股解禁: https://tushare.pro/document/2?doc_id=160  
> 回购数据  
> 增减持数据: https://tushare.pro/document/2?doc_id=175  
  
# 开发计划：
  
* 接入更多数据  
> 实际控制人数据（巨潮）: http://webapi.cninfo.com.cn/#/dataBrowse?id=266  
* 加入更多分析算法  
> 量价分析  
* 整合测试入口，执行一个文件即可运行所有测试  
* 加入实时数据  
* 盯盘  
* 投资图谱  
* 做成WebService，通过APP操作  
  
----------------------------------------------------------------------------------------------------------------------
# 赞助此项目：  
如果此项目对您有用，欢迎资助，此资助将被用于服务器租用及数据购买。  
  
![image](Doc/Appreciation_Code_WeChat.png)  
  
  