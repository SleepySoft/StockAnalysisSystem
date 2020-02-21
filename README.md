# StockAnalysisSystem
This program is designed for Chinese market and Chinese accounting policies (currently). So this document will only provide Chinese version.

# 注意(NOTICE)
由于空间占用问题，旧的github仓库已经废弃，请重新clone代码并手动合并你的更改（如果有的话）  
Because the space occupancy issue. The old github repo was deprecated. Please re-clone and merge your updates manually (if has)   
  
# Gitee
https://gitee.com/SleepySoft/StockAnalysisSystem  

# Github
https://github.com/SleepySoft/StockAnalysisSystem  
  
# 网盘下载：
应网友要求，对于网络访问受限的用户，提供网盘下载：  
链接：https://pan.baidu.com/s/1H-viluqOoKrKRNJJmU17jg  
提取码：4r3u  
  
# 最后更新内容：
接入交易数据 -> 20200221: Done  
  
# 联系作者
如果有任何意见及建议，或者对此项目感兴趣的，请联系我：  
微博：SleepySoft  
邮箱：sleepysoft##163.com  
QQ群：931499339，进群验证码：SleepySoft  
如果遇到BUG，可以给我发邮件，或直接在git上提交issue  
  
----------------------------------------------------------------------------------------------------------------------
  
# 股票分析系统
  
更确切的说，应该叫上市公司财报分析系统。当初写这个程序的目的就是能够快速高效地分析和排除上市公司。这一想法来源于《手把手教你读财报》里的一句话：财报是用来排除公司的。
现在量化非常流行，但比较流行的做法还是将技术分析程序化。常见的开源库也专注于获取交易数据。然而本人还是倾向于稳，所以从去年开始学习财务知识和财务分析方法，希望通过寻找优秀的股票，以稳定的增长达到财富自由。
  
好了梦想说完了，下面是程序的说明。
  
----------------------------------------------------------------------------------------------------------------------
  
# 本程序的目的：
1. 自动选择合适的数据抓取模块和数据源下载所需要的数据  
2. 数据抓取模块能够进行有效性检测，并且能够方便地扩充和替换，可以通过适配器接入其它的库  
3. 增加一个数据源以及将其本地化所需的代码应尽可能少  
4. 能进行离线分析  
5. 分析模块（策略模块）应该可以动态扩充和组合  
6. 最终能生成矩阵式excel报告：以证券为行，以分析方法为列，相交点为此分析方法对此证券的评分；最后一列为该证券的总分  
  
----------------------------------------------------------------------------------------------------------------------
  
# 使用方法及软件依赖与配置
  
## 懒人看这里 
1. 对于打包好的程序，直接运行main.exe即可
2. 程序现在提供了脚本帮助用户自动配置python环境，请直接运行“build.bat -e”，为当前的Python环境安装依赖库  
3. 程序第一次启动时，会自动检查配置并弹出配置界面，请按照提示填写即可。同时这个界面提供mongodb数据的一键导入功能：  
> 请将offline_data/StockAnalysisSystem.zip.1解压到当前文件夹，导入时选择解压出来的StockAnalysisSystem其文件夹即可  
> 如果不导入数据，可以通过数据管理界面重新下载（需要正确配置Ts Token）  
4. 如果是直接运行EXE的用户，导入数据的同时，sAsUtility.db需要手动拷贝到Data目录  
  
## 环境及软件依赖
1. 使用python3，推荐python3.7. IDE推荐pycharm（如果需要调试）：https://www.jetbrains.com/pycharm/download/#section=windows  
2. 依赖pandas，推荐使用anaconda的环境：https://www.anaconda.com/distribution/  
3. 需要安装sqlite：https://www.sqlite.org/index.html  
4. 需要安装mongodb（免费的社区版即可）：https://www.mongodb.com/what-is-mongodb  
5. 当前数据采集依赖于tushare的pro接口（未来会加入其它采集方式）  
> 1.1 在当前运行的python环境中安装tushare：pip install tushare  
> 1.2 注册一个tushare的账号：https://tushare.pro/register?reg=271027  
> 1.3 想办法获取500以上的积分（如果没有，无法更新数据，但可以使用离线数据）：https://tushare.pro/document/1?doc_id=13  
> 1.4 获取你的token并填入配置界面：https://tushare.pro/document/1?doc_id=39  
6. 其它的依赖项请参照build.bat，或者在当前环境下直接运行build.bat -e  
  
# 软件配置
当前软件配置全部通过界面进行，请按照界面提示操作即可  
  
 # 软件运行
请直接运行main.py，如果有库缺失，请下载依赖库
对于使用打包好的程序的用户，请直接运行main.exe
如果不想运行，也可以直接打开analysis_report.xlsx查看分析结果。  
  
# 报告格式说明
报告为表格矩阵，以股票代码为列，以分析算法为行，相交格子为该算法对此股票的评分（0 - 100），默认50分以上为PASS  
结果分为两页，第一页为评分，第二页为分析算法输出的详细信息，以供人工核对及查阅  
绿色为PASS，红色为FAIL，灰色为不适用，或因数据缺失导致无法分析  
最后一列为总评分，在一行中，只要有一个评分为FAIL，则总评分为FAIL；如果不存在FAIL但存在灰色结果，则总评分为灰色的PASS  
当前分析算法还不够完善，结果仅供参考，遇到和自己分析存在偏差的情况，请参阅详细信息并进行人工复核  
  
----------------------------------------------------------------------------------------------------------------------
  
# 开发计划：
0. TODO:  
1. 生成EXCEL格式的报告 -> 20200129: Done  
2. 编写数据更新的管理界面  -> 20200130: Done  
> 硬编码过多，待重构数据结构解决  -> 20200201: Partly done  
> data_update_ui: 将线程任务打包，并正确显示各个项目的进度  -> 20200212: Done  
3. 编写策略选择界面  -> 20200131: Done  
4. 策略运行进度显示  -> 20200131: Done  
5. 界面集成  -> 20200201: Done  
6. 完善设计文档  -> 2020.2.2: Partly done  
7. 加入配置界面，而非写入config.py，使程序便于打包成EXE  -> 20200203: Done  
8. 加入配置检查功能  -> 20200203: Done  
9. 加入打包功能，使程序能打包成EXE直接执行  -> 20200204: Done  
10. 改善mongodb读写性能和内存使用  ->20200214: Done  
> 加入connection计数与限制，超过后关闭client以释放连接及内存  ->20200214: Done  
> 为nosql数据库加入索引，提升查询和upsert速度  ->20200214: Done  
11. 接入更多财务数据  
> 股权质押数据 -> 20200212: Done  
> 回购数据  
> 增减持数据  
12. 接入交易数据 -> 20200221: Done  
13. 加入更多分析算法  
> 存贷双高  -> 20200206: Done  
> 股权质押过高  
> 去年及未来一年有减持计划  
14. 将数据迁移到MongoDB
> UpdateTable -> 20200209: Done  
> XList Table  
15. 废弃旧仓库，重新建立仓库以减少空间占用，并同时迁移数据到gitee（今后代码会同时提交到两个仓库）  -> 20200218: Done  
16. 整合测试入口，执行一个文件即可运行所有测试  
17. 策略参数可配置可保存  
18. 接入交易数据  
19. 加入实时数据  















