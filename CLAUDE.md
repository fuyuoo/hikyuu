# CLAUDE.md

本文档为 Claude Code (claude.ai/code) 在本项目中工作时提供指导。

## 项目简介

Hikyuu量化框架是一个基于C++/Python的开源超高速量化交易研究框架，用于策略分析及回测（目前主要用于国内A股市场）。专注于提供高性能计算能力和组件化架构，用于构建交易系统。

## 常用命令

### 编译
```bash
# 使用 setup.py 完整编译（需要 xmake）
python setup.py build

# 或直接使用 xmake
xmake -j 4 -b core
```

### 测试
```bash
# 运行最小范围测试（默认）
python setup.py test

# 运行全部测试
python setup.py test -all

# 运行指定测试用例
python setup.py test -case 测试用例名称
```

### 安装
```bash
python setup.py install
python setup.py install -j 4  # 指定并行任务数
```

### 打包 Wheel
```bash
python setup.py wheel
python setup.py wheel -j 4
```

### 清理
```bash
python setup.py clear
```

## 编译配置选项

通过 xmake 或 setup.py 可用选项：
- `--mysql`: 启用 MySQL 行情数据引擎（默认: true）
- `--hdf5`: 启用 HDF5 行情数据引擎（默认: true）
- `--sqlite`: 启用 SQLite 行情数据引擎（默认: true）
- `--tdx`: 启用 TDX 行情数据引擎（默认: true）
- `--ta_lib`: 启用 TA-Lib 支持（默认: true）
- `--low_precision`: 使用低精度模式
- `--serialize`: 启用序列化/pickle支持（默认: true）
- `-m release|debug|coverage`: 编译模式

## 架构

### 目录结构
- `hikyuu_cpp/` - C++ 核心库
  - `hikyuu/` - 核心类（Stock、KData、Indicator、TradingSystem）
  - `data_driver/` - 数据存储驱动（HDF5、MySQL、SQLite、TDX）
  - `indicator/` - 技术指标
  - `trade_sys/` - 交易系统组件
  - `strategy/` - 策略实现
  - `trade_manage/` - 交易管理
  - `factor/` - 因子定义
  - `plugin/` - 插件系统
- `hikyuu_pywrap/` - Python 绑定（使用 pybind11）
- `hikyuu/` - Python 包
  - `indicator/` - Python 指标封装
  - `trade_sys/` - Python 交易系统封装
  - `strategy/` - 策略实现
  - `trade_manage/` - 交易管理
  - `test/` - Python 测试
  - `examples/` - 示例 notebooks
  - `tools/` - 工具

### 核心概念

**交易系统组件**（抽象化的系统交易方法）：
1. 市场环境判断策略 - Market Condition判断
2. 系统有效条件 - System Valid Condition
3. 信号指示器 - Signal Indicator
4. 止损/止盈策略 - Stop Loss/Take Profit
5. 资金管理策略 - Money Management
6. 盈利目标策略 - Profit Goal
7. 移滑价差算法 - Slippage Algorithm

**数据管理**：
- `Stock` - 股票数据容器
- `KData` - K线（蜡烛图）数据
- `StockManager` - 管理所有股票数据

**核心类**：
- `KQuery` - 数据查询接口
- `Indicator` - 技术指标基类
- `TradingSystem` - 交易系统执行引擎

## 开发注意事项

- 需要 C++17 标准
- 使用 xmake 作为构建系统
- 依赖通过 xmake 管理（boost、hdf5、fmt、spdlog、pybind11 等）
- Python 包名为 `hikyuu`（import hikyuu）
- 测试数据位于 `test_data/` 目录
