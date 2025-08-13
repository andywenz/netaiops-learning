# NetAIOps Learning Note - Week01 - August 2025

## 功能说明  / Function Description
- 这是一个使用LLM进行自动化网络设备命令行输入的程序
  
  This is a program that uses an LLM to automate command-line input for network devices.


- 接收客户的输入，通过LLM将输入的内容提取出Command、IP或Hostname

  It accepts user input and uses the LLM to extract the command, IP address, or hostname from the input.


- 通过本地yml文件查询该设备是否存在，如果存在，提取用户名、密码

  It queries a local YAML file to check if the device exists; if it does, it extracts the username and password.


- 使用netmiko向网络设备执行命令，返回回显

  It uses Netmiko to execute the command on the network device and returns the output.


## 核心知识点 / Core Concepts
- Netmiko 实现网络设备自动化

  Netmiko for Network Device Automation


- YAML 文件存储设备清单

  YAML File for Device Inventory


- LLM 提取命令与设备标识符

  LLM to Extract Commands and Device Identifiers


- LangChain 框架封装 LLM 调用

  LangChain to Encapsulate LLM Invocation


- 空命令过滤与异常处理

  Empty Command Filtering and Exception Handling


- 模块化设计与代码复用

  Modular Design and Code Reusability


## 使用示例 / Usage Example
![example](assets/week01_llm_show_output.png)