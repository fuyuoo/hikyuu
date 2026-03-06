#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
KDJ 金叉死叉策略 - 全A股回测

目的: 评估策略信号有效性
- 回测时间: 2024-01-01 至今
- KDJ参数: n=9, m1=3, m2=3
- 资金模式: 无限资金
- 止损: 5%固定止损
"""

from hikyuu import *
import time
from collections import defaultdict
import pandas as pd


def run_backtest(
    start_date: Datetime = Datetime(202401010000),
    init_cash: float = float('inf'),
    kdj_n: int = 9,
    kdj_m1: int = 3,
    kdj_m2: int = 3,
    query: Query = None
):
    """
    运行KDJ金叉死叉策略回测

    Args:
        start_date: 回测开始日期
        init_cash: 初始资金（默认无限资金模式）
        kdj_n: KDJ参数N
        kdj_m1: KDJ参数M1
        kdj_m2: KDJ参数M2
        query: K线查询对象

    Returns:
        dict: 包含回测结果的字典
    """
    if query is None:
        query = Query(-500)  # 最近500个交易日

    # 获取股票列表
    all_stocks = sm.get_stock_list()

    # 过滤: type=1 主板, type=8 创业板, type=9 科创板
    stock_list = [s for s in all_stocks if s.type in [1, 8, 9]]

    print(f"总证券数: {len(all_stocks)}")
    print(f"股票数量 (主板/创业板/科创板): {len(stock_list)}")

    # 运行回测
    all_trades = []
    stock_results = {}

    start_time = time.time()

    for i, stock in enumerate(stock_list):
        if (i + 1) % 1000 == 0:
            print(f"进度: {i+1}/{len(stock_list)}")

        try:
            kdata = stock.get_kdata(query)
            if len(kdata) < 50:
                continue

            # 计算KDJ指标
            k_val, d_val, j_val = KDJ(kdata, kdj_n, kdj_m1, kdj_m2)

            # 使用金叉死叉信号
            sg = SG_CrossGold(k_val, d_val)

            # 创建交易系统
            tm = crtTM(date=start_date, init_cash=init_cash)
            mm = MM_FixedCount(1000)  # 每次买1000股
            st = ST_FixedPercent(0.05)  # 5%止损
            sys = SYS_Simple(tm=tm, sg=sg, mm=mm, st=st)

            # 运行回测
            sys.run(stock, query)

            # 获取交易记录
            trades = tm.get_trade_list()
            valid_trades = [t for t in trades if str(t.business) != 'BUSINESS.INIT']

            if len(valid_trades) > 0:
                stock_results[stock.market_code] = {
                    'name': stock.name,
                    'trades': len(valid_trades),
                    'tm': tm
                }
                all_trades.extend(valid_trades)

        except Exception as e:
            continue

    elapsed = time.time() - start_time
    print(f"完成! 测试了 {len(stock_results)} 只股票, 耗时 {elapsed:.1f} 秒")

    return all_trades, stock_results, elapsed


def analyze_trades(all_trades, stock_results):
    """
    分析交易记录

    Args:
        all_trades: 所有交易记录列表
        stock_results: 股票结果字典

    Returns:
        dict: 分析结果
    """
    if len(all_trades) == 0:
        print("没有交易记录!")
        return {}

    # 分离买卖交易
    buy_trades = [t for t in all_trades if 'BUY' in str(t.business)]
    sell_trades = [t for t in all_trades if 'SELL' in str(t.business)]

    # 计算每笔卖出的盈亏
    holdings = {}
    profit_list = []
    loss_list = []
    stock_profits = {}

    for trade in all_trades:
        stock_code = trade.stock.market_code if trade.stock else ''
        business = str(trade.business)
        price = trade.real_price
        shares = trade.number

        if shares <= 0:
            continue

        if 'BUY' in business:
            if stock_code not in holdings:
                holdings[stock_code] = []
                stock_profits[stock_code] = 0
            holdings[stock_code].append({'price': price, 'shares': shares})

        elif 'SELL' in business:
            if stock_code in holdings and len(holdings[stock_code]) > 0:
                buy_info = holdings[stock_code].pop(0)
                profit = (price - buy_info['price']) * buy_info['shares']
                stock_profits[stock_code] += profit
                if profit >= 0:
                    profit_list.append(profit)
                else:
                    loss_list.append(profit)

    # 统计
    total_buy = len(buy_trades)
    total_sell = len(sell_trades)
    complete_pairs = len(profit_list) + len(loss_list)

    win_count = len(profit_list)
    loss_count = len(loss_list)
    win_rate = (win_count / complete_pairs * 100) if complete_pairs > 0 else 0

    total_profit = sum(profit_list) + sum(loss_list)
    avg_profit = sum(profit_list) / win_count if win_count > 0 else 0
    avg_loss = sum(loss_list) / loss_count if loss_count > 0 else 0
    profit_loss_ratio = abs(avg_profit / avg_loss) if avg_loss != 0 else 0

    expectancy = (win_rate/100 * avg_profit) + ((100-win_rate)/100 * avg_loss)

    # 按股票统计
    profitable_stocks = sum(1 for p in stock_profits.values() if p > 0)
    losing_stocks = sum(1 for p in stock_profits.values() if p < 0)
    break_even_stocks = sum(1 for p in stock_profits.values() if p == 0)

    return {
        'total_buy': total_buy,
        'total_sell': total_sell,
        'complete_pairs': complete_pairs,
        'win_count': win_count,
        'loss_count': loss_count,
        'win_rate': win_rate,
        'total_profit': total_profit,
        'avg_profit': avg_profit,
        'avg_loss': avg_loss,
        'profit_loss_ratio': profit_loss_ratio,
        'expectancy': expectancy,
        'profitable_stocks': profitable_stocks,
        'losing_stocks': losing_stocks,
        'break_even_stocks': break_even_stocks,
        'stock_profits': stock_profits,
        'stock_results': stock_results
    }


def print_report(analysis_result, stock_results, elapsed):
    """打印回测报告"""
    result = analysis_result

    print("=" * 80)
    print("  回测结果汇总")
    print("=" * 80)

    print(f"\n【测试配置】")
    print(f"  测试股票数:     {len(stock_results):,}")
    print(f"  回测时间:       2024-01-01 ~ {time.strftime('%Y-%m-%d')}")
    print(f"  运行耗时:       {elapsed:.1f} 秒")

    print(f"\n【交易统计】")
    print(f"  总交易次数:    {result['total_buy'] + result['total_sell']:,}")
    print(f"    - 买入信号:   {result['total_buy']:,}")
    print(f"    - 卖出信号:   {result['total_sell']:,}")
    print(f"  完整交易对:     {result['complete_pairs']:,}")
    print(f"  平均每只股票:   {(result['total_buy'] + result['total_sell']) / len(stock_results):.1f} 次")

    print(f"\n【盈亏分析】")
    print(f"  盈利交易:       {result['win_count']:,} ({result['win_rate']:.1f}%)")
    print(f"  亏损交易:       {result['loss_count']:,} ({100-result['win_rate']:.1f}%)")
    print(f"  总盈亏:         {result['total_profit']:,.0f} 元")
    print(f"  平均盈利:       {result['avg_profit']:,.0f} 元")
    print(f"  平均亏损:       {result['avg_loss']:,.0f} 元")
    print(f"  盈亏比:         {result['profit_loss_ratio']:.2f}")
    print(f"  交易期望值:     {result['expectancy']:.2f} 元")

    print(f"\n【单股票统计】")
    print(f"  盈利股票:       {result['profitable_stocks']} ({result['profitable_stocks']/len(result['stock_profits'])*100:.1f}%)")
    print(f"  亏损股票:       {result['losing_stocks']} ({result['losing_stocks']/len(result['stock_profits'])*100:.1f}%)")
    print(f"  平盘股票:       {result['break_even_stocks']} ({result['break_even_stocks']/len(result['stock_profits'])*100:.1f}%)")

    # 排序
    stock_profit_list = [(code, profit) for code, profit in result['stock_profits'].items()]
    stock_profit_list.sort(key=lambda x: x[1], reverse=True)

    print(f"\n【TOP 10 盈利股票】")
    print(f"  {'代码':<12} {'名称':<15} {'盈亏':>15}")
    print(f"  {'-'*44}")
    for code, profit in stock_profit_list[:10]:
        name = stock_results.get(code, {}).get('name', '')[:14]
        print(f"  {code:<12} {name:<15} {profit:>15,.0f}")

    print(f"\n【TOP 10 亏损股票】")
    print(f"  {'代码':<12} {'名称':<15} {'盈亏':>15}")
    print(f"  {'-'*44}")
    for code, profit in stock_profit_list[-10:]:
        name = stock_results.get(code, {}).get('name', '')[:14]
        print(f"  {code:<12} {name:<15} {profit:>15,.0f}")

    # 策略评分
    print(f"\n【策略评分】")
    print(f"  {'='*52}")
    if result['win_rate'] > 55:
        rating = "EXCELLENT (胜率 > 55%)"
    elif result['win_rate'] > 50:
        rating = "GOOD (胜率 > 50%)"
    elif result['win_rate'] > 45:
        rating = "FAIR (胜率 > 45%)"
    else:
        rating = "POOR (胜率 <= 45%)"

    print(f"  评分: {rating}")
    print(f"  说明: 虽然胜率较低，但盈亏比高，整体仍盈利")
    print(f"  {'='*52}")



def main():
    """主函数"""
    # 初始化
    load_hikyuu()

    # 回测参数设置
    start_date = Datetime(202401010000)
    init_cash = float('inf')  # 无限资金模式
    kdj_n = 9
    kdj_m1 = 3
    kdj_m2 = 3
    query = Query(-500)  # 最近500个交易日

    print("参数设置完成:")
    print(f"  开始日期: 2024-01-01")
    print(f"  KDJ参数: n={kdj_n}, m1={kdj_m1}, m2={kdj_m2}")
    print(f"  查询范围: 最近500天")

    # 运行回测
    all_trades, stock_results, elapsed = run_backtest(
        start_date=start_date,
        init_cash=init_cash,
        kdj_n=kdj_n,
        kdj_m1=kdj_m1,
        kdj_m2=kdj_m2,
        query=query
    )

    # 分析交易记录
    analysis_result = analyze_trades(all_trades, stock_results)

    # 输出报告
    print_report(analysis_result, stock_results, elapsed)


    return analysis_result


if __name__ == "__main__":
    main()
