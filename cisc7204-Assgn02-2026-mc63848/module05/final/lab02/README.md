# Module 05Final Lab02 — mc63848 LI SIWEI

解压后在此目录运行（或使用已安装好依赖的 CISC7204 环境）：

```powershell
python -m pip install -r requirements.txt
python DV0101EN-Final-Assign-Part-2-Questions.py
```

浏览器打开 http://127.0.0.1:8059/ ，按 Ctrl+C 停止。
支持 `--port` 更换端口；只绑定本机 127.0.0.1。
代码优先读取项目内部 data/automobile-sales.csv，ZIP 可独立运行。

Yearly Statistics 启用年份选择；Recession Period Statistics 禁用。四图按两行两列显示。
说明正文写 1980–2013，但 Task 的 range(1980, 2024) 提示和所给数据都是 1980–2023；这里保留完整数据范围。
月销售额使用所选年份的 sum；车型销量用 mean；广告费用 sum。disabled=False 表示启用。

screenshots/ 保留 Lab02 的实际代码和网页结果截图；Final 的两个报告图按实验指定名称保存。
