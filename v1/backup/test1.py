#!/usr/bin/python3
# pylint: disable=superfluous-parens, missing-docstring, invalid-name
import matplotlib
matplotlib.use('Agg')

import argparse
import json
import sys
from datetime import datetime

import requests
from cycler import cycler
from matplotlib import pyplot, ticker, dates, transforms, RcParams
from mpl_finance import candlestick_ochl
import mplfinance as mpf

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
#from matplotlib.finance import quotes_historical_yahoo_ohlc, candlestick_ohlc


yearDateFormatter = dates.DateFormatter('%Y-%m-%d')
monthLocator = dates.MonthLocator()  # every month
dayLocator = dates.DayLocator()

currentDateTime = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')

a=datetime.now()

def bool_solver(x, pos):
    if x == 0:
        return ""
    elif x > 0:
        return "t"
    return "f"


bool_formatter = ticker.FuncFormatter(bool_solver)

dark_theme = RcParams({
    'axes.edgecolor': 'white',
    'axes.facecolor': '#1F2A34',
    'axes.labelcolor': 'white',
    'axes.prop_cycle': cycler('color',
                              ['#8dd3c7', '#feffb3',
                               '#bfbbd9', '#fa8174',
                               '#81b1d2', '#fdb462',
                               '#b3de69', '#bc82bd',
                               '#ccebc4', '#ffed6f']),
    'figure.edgecolor': '#1F2A34',
    'figure.facecolor': '#1F2A34',
    'grid.color': '#504958',
    'lines.color': 'white',
    'patch.edgecolor': 'white',
    'savefig.edgecolor': '#1F2A34',
    'savefig.facecolor': '#1F2A34',
    'text.color': 'white',
    'xtick.color': 'white',
    'ytick.color': 'white'})

queryChartConfig = """query chartConfig {
  chartConfig(strategy:"%s") {
    panels {
      name,
      height,
      indicators {
        label,
        name,
        style,
        type,
        interval,
        position,
        color,
        width
      }
    }
  }
}"""

indicators = ["label", "name", "style", "type", "interval",
              "position", "color", "width"]

query_template_chartconfig = """query chartConfig {{
    {market}
    chartConfig({query}){{
        panels {{
            name,
            height,
            indicators {{{indicators}}} }}}}}}"""


def make_config_request(market, strategy, report, conditions):
    screener_conditions = 'screener_conditions:"{}"'.format(conditions) if conditions else None
    strategy = 'strategy:"{}"'.format(strategy)
    report = 'report:"{}"'.format(report)
    market = 'market(id:"{}") {{symbol}},'.format(market)
    request = query_template_chartconfig.format(
        market=market,
        query=', '.join(filter(None, [screener_conditions, strategy, report])),
        indicators=', '.join(indicators)
    )

    if (args.log):
        print('\nRequest 1:\n' + request + '\n')
        with open(currentDateTime + "_request_1.txt", "w") as f:
            f.write(request)
            f.flush()

    return request


queryChartData = """query chartData {
  marketIndicators(
    strategy:"%s",
    market:"%s",
    limit:%s,
    indicators:"%s",
    optimizeIndicatorValuesForCharting:true,
    index:1
  ) {
    id,
    timestamp,
    open,
    high,
    low,
    close,
    volume,
    indicators
  }
}"""


def get_linestlyle_by_type(linestyle_type):
    linestyles = {
        'Solid': (0, ()),
        'ShortDash': (0, (3, 3)),
        'ShortDashDot': (0, (3, 1, 1, 1, 3, 1)),
        'ShortDashDotDot': (0, (3, 1, 1, 1, 1, 1)),
        'Dot': (0, (1, 1)),
        'Dash': (0, (5, 2)),
        'LongDash': (0, (7, 2)),
        'DashDot': (0, (5, 2, 1, 2)),
        'LongDashDot': (0, (7, 2, 1, 2)),
        'LongDashDotDot': (0, (7, 2, 1, 2, 1, 2))
    }

    return linestyles.get(linestyle_type, linestyles["Solid"])

def render_panel(axes, settings, data, default):

    # Create dict and add plots for this panel
    plots = {}
    for indicatorPlotConfig in settings["indicators"]:

        plots.update({
            indicatorPlotConfig["label"]: {
            # indicatorPlotConfig["name"]: {
                "x": [],
                "y": [],
                "indicator": indicatorPlotConfig["name"],
                "linestyle": get_linestlyle_by_type(indicatorPlotConfig["style"]),
                "color": indicatorPlotConfig["color"],
                "type": indicatorPlotConfig["type"]
            }
        })

    # Add the actual data to each plot
    for point in data:
        pointIndicators = json.loads(point["indicators"])
        for interval in pointIndicators.keys():

            for indicator in pointIndicators[interval]:
                # if indicator in plots.keys():
                for plot in plots:
                    if plots[plot]["indicator"] == indicator:
                        plots[plot]["x"].append(datetime.fromtimestamp(int(point['timestamp'])))
                        plots[plot]["y"].append(pointIndicators[interval][indicator])

    for plot in plots:
        linestyle = plots[plot]["linestyle"]

        color = plots[plot]["color"]
        xs = plots[plot]["x"]
        ys = plots[plot]["y"]

        if plots[plot]["type"] == "line":
            if color:
                axes.plot(xs, ys, linestyle=linestyle, label=plot, color=color,show_nontrading=False)
            else:
                axes.plot(xs, ys, linestyle=linestyle, label=plot,show_nontrading=False)
        elif plots[plot]["type"] == "bool":
            axes.get_yaxis().set_major_formatter(bool_formatter)
            neutral_x_axe, neutral_ys = [], []
            positive_xs, positive_ys = [], []
            negative_xs, negative_ys = [], []
            for x, y in zip(xs, ys):
                if y == 0 or y is None:
                    neutral_x_axe.append(x)
                    neutral_ys.append(y)
                elif y > 0:
                    positive_xs.append(x)
                    positive_ys.append(0.2)
                else:
                    negative_xs.append(x)
                    negative_ys.append(-0.2)
            if neutral_x_axe:
                axes.scatter(neutral_x_axe, neutral_ys, s=6, marker="_", color="gray", label=plot)
            if positive_xs:
                axes.scatter(positive_xs, positive_ys, s=6, marker="s", color="green", label=plot)
            if negative_xs:
                axes.scatter(negative_xs, negative_ys, s=6, marker="s", color="red", label=plot)
            ylim = axes.get_ylim()
            # axes.set_ylim(ylim[0]*5, ylim[1]*5)
            axes.set_ylim([-1.5, 1.5])

        elif plots[plot]["type"] == "bar":
            if color:
                axes.bar(xs, ys, label=plot, color=color)
            else:
                axes.bar(xs, ys, label=plot)
        elif plots[plot]["type"] == "text":
            pass
        axes.legend(loc="lower left", shadow=False, fontsize="xx-small")
        if settings["name"] != "default":
            axes.text(0.01, 0.95, settings["name"],
                      verticalalignment='top', horizontalalignment='left',
                      transform=axes.transAxes,
                      fontsize=10)
        axes.grid(True)

def determine_panel_height(panel):
   if panel["height"] == "large":
       return 0.8
   elif panel["height"] == "small":
        if "bool" in [i["type"] for i in panel["indicators"]]:
            return 0.1
        else:
            return 0.3
   else:
       return 0.5

def weekday_candlestick(ohlc_data, ax, fmt='%b %d', freq=7, **kwargs):
    """ Wrapper function for matplotlib.finance.candlestick_ohlc
        that artificially spaces data to avoid gaps from weekends """

    # Convert data to numpy array
    ohlc_data_arr = np.array(ohlc_data)
    ohlc_data_arr2 = np.hstack(
        [np.arange(ohlc_data_arr[:,0].size)[:,np.newaxis], ohlc_data_arr[:,1:]])
    ndays = ohlc_data_arr2[:,0]  # array([0, 1, 2, ... n-2, n-1, n])

    # Convert matplotlib date numbers to strings based on `fmt`
    dates = mdates.num2date(ohlc_data_arr[:,0])
    date_strings = []
    for date in dates:
        date_strings.append(date.strftime(fmt))

    # Plot candlestick chart
    candlestick_ochl(ax, ohlc_data_arr2, **kwargs)

def get_data(url, token, strategy, market, report, conditions, numberOfBars, footer):
    before_request_1=datetime.now()
    response_config = requests.post(url,
                             headers={'Accept': 'application/json', 'Authorization': 'Bearer {}'.format(token)},
                             data={"query": make_config_request(
                                 market,
                                 strategy,
                                 report,
                                 conditions
                             )})
    if response_config.status_code != 200:
        print("Request failed with status:{} /nmessage:{}".format(response_config.status_code, response_config.text))
        return

    after_request_1=datetime.now()
    
    print('Request 1:',  (after_request_1-before_request_1).seconds )

    data = response_config.json().get("data")

    if (args.log):
        print('\nResponse 1:')
        json.dump(response_config.json(), sys.stdout, indent=4)
        json.dump(data, open(currentDateTime + "_response_1.js", "w"))

    market_name = data['market']['symbol']

    assert data, "Unexpected response: {}".format(data)

    chartConfig = data.get("chartConfig")
    assert chartConfig, "No chartConfig field found in: {}".format(data)

    panels = chartConfig.get("panels")
    height_ratios = []
    for panel, coef in zip(panels, range(len(panels))):
        panel_height = determine_panel_height(panel)
        height_ratios.append(panel_height)

    print(height_ratios)

    # Price and Volume relative height
    height_ratios[0] = 1.5

    grid = pyplot.GridSpec(len(panels), 1, height_ratios=height_ratios)
    default = pyplot.subplot(grid[0, 0])

    default.grid(True)
    title = "{}".format(market_name)
    default.text(0.4, 0.9, title,
                 verticalalignment='top', horizontalalignment='left',
                 transform=default.transAxes,
                 alpha=0.15,
                 fontsize=20)
    axs = [default]

    '''
    for idx in range(len(panels)):
        if idx == 0:  # default pane
            pass
        else:
            ax = pyplot.subplot(grid[idx, 0], sharex=default)
            axs.append(ax)
            # ax.xaxis.set_major_locator(ticker.MaxNLocator(10))
    assert panels, "No panels found in: {}".format(data)
    '''

    indicator_names = []
    for pan in panels:
        indicator_names += [i['name'] for i in pan['indicators']]

    # Make list unique
    # indicator_names = list(set(indicator_names))
    
    
    print(indicator_names)
    indicator_names=['']

    print({"query": queryChartData % (strategy, market, numberOfBars, ",".join(indicator_names))})

    before_request_2=datetime.now()

    response_chart_data = requests.post(
        url,
        headers={'Accept': 'application/json', 'Authorization': 'Bearer {}'.format(token)},
        data={"query": queryChartData % (strategy, market, numberOfBars, ",".join(indicator_names))})

    if (args.log):
        print('\n\nRequest 2:\n')
        print(queryChartData % (strategy, market, numberOfBars, ",".join(indicator_names)))

    after_request_2=datetime.now()
    
    print('Request 2:',  (after_request_2-before_request_2).seconds )


    data = response_chart_data.json().get("data")

    if (args.log):
        print('\nResponse 2:\n')
        json.dump(response_chart_data.json(), sys.stdout, indent=4)
        json.dump(data, open(currentDateTime + "_response_2.js", "w"))

    assert data, "Unexpected response: {}".format(data)
    marketIndicators = data.get("marketIndicators")
    assert marketIndicators, "No marketIndicators field found in {}".format(data)

    # price panel
    candlesticks = []
    neg_time_scale = []
    pos_time_scale = []
    neg_volume_scale = []
    pos_volume_scale = []
    for marketIndicator in marketIndicators:
        time_value = (dates.date2num(datetime.fromtimestamp(int(marketIndicator['timestamp']))))
        print(time_value)
        candlesticks.append((time_value,
                             marketIndicator['open'],
                             marketIndicator['close'],
                             marketIndicator['high'],
                             marketIndicator['low']))
        if marketIndicator['open'] <= marketIndicator['close']:
            pos_volume_scale.append(marketIndicator["volume"])
            pos_time_scale.append(time_value)
        else:
            neg_volume_scale.append(marketIndicator["volume"])
            neg_time_scale.append(time_value)

#    candlestick_ochl(default, candlesticks, width=0.5, colorup='g', colordown='r', alpha=1)
    weekday_candlestick(candlesticks, default, fmt='%b %d', freq=3, width=0.5)
    
    # default.set_ylabel("Price and Volume", size=20)
    ylim = default.get_ylim()
    print(ylim)
    print(ylim[0] / 1.2, ylim[1])
    default.set_ylim(ylim[0] / 1.2, ylim[1])

    volume_bar = default.twinx()
    volume_bar.yaxis.set_label_position("right")
    volume_bar.set_position(transforms.Bbox([[0.125, 0.1], [0.9, 0.32]]))
    volume_bar.bar(pos_time_scale, pos_volume_scale, color="green", alpha=.4)
    volume_bar.bar(neg_time_scale, neg_volume_scale, color="red", alpha=.4)
    ylim = volume_bar.get_ylim()
    print(ylim)
    volume_bar.set_ylim(ylim[0], ylim[1] * 4)

#    for panel, axes in zip(panels, axs):
#        render_panel(axes, panel, marketIndicators, default)

    # post format
    for ax in axs[:-1]:
        ax.get_xaxis().set_ticks([])
        ax.xaxis.set_major_locator(monthLocator)

    axs[-1].xaxis.set_major_locator(monthLocator)
    axs[-1].xaxis.set_minor_locator(dayLocator)

    axs[-1].xaxis.set_major_formatter(yearDateFormatter)
    screen.text(0.9, 0.17, footer,
                verticalalignment='top', horizontalalignment='right',
                transform=axs[-1].transAxes,
                fontsize=20)
    screen.text(0.13, 0.17, title,
                verticalalignment='top', horizontalalignment='left',
                transform=axs[-1].transAxes,
                fontsize=20)


parser = argparse.ArgumentParser()
parser.add_argument("-u", "--api_query_endpoint", help="url to query", default="https://engine.therationalinvestor.com/api/")
parser.add_argument("-t", "--api_client_token", help="auth token")
parser.add_argument("-s", "--strategy", help="strategy uuid")
parser.add_argument("-m", "--market", help="market uuid")
parser.add_argument("-n", "--number_of_bars", help="limit the number of bars shown on the chart", default="0")
parser.add_argument("-r", "--report", help="report uuid", default="")
parser.add_argument("-o", "--output", help="filepath to output file.")
parser.add_argument("-d", "--dpi", default=100, help="resolution of resulting png. Default is 100.")
parser.add_argument("-c", "--conditions", default=None, help="custom screener conditions. Json string.")
parser.add_argument("-f", "--footer", default="", help="plot footer.")
parser.add_argument("-l", "--log", default=None, help="If set all requests and response will get logged to the current path")
parser.add_argument("--theme", default="light", help="theme for output png. Maybe light or dark.")

args = parser.parse_args()

if __name__ == "__main__":
    url_ = args.api_query_endpoint
    token_ = args.api_client_token
    strategy_ = args.strategy
    market_ = args.market
    report_ = args.report
    conditions_ = args.conditions
    numberOfBars_ = args.number_of_bars

    if not all([token_, strategy_, market_]):
        parser.print_help()
        sys.exit(0)

    # matplotlib global settings
#    if args.theme == "dark":
#        pyplot.style.use(dark_theme)
    screen = pyplot.figure(figsize=(15, 15))
    screen.autofmt_xdate()  # date autoformat
    before_get_data=datetime.now()
    get_data(url_, token_, strategy_, market_, report_, conditions_, numberOfBars_, args.footer)
    after_get_data=datetime.now()
    print( 'Get Data: ',(after_get_data-before_get_data).seconds )
    screen.align_xlabels()
    pyplot.subplots_adjust(hspace=0)  #
    pyplot.rc('ytick', labelsize=5)

    before_render=datetime.now()
    if args.output:
        pyplot.savefig(args.output, dpi=int(args.dpi), bbox_inches='tight')
    else:
        pyplot.show()
    after_render=datetime.now()
    print('Render: ', (after_render-before_render).seconds)

    b=datetime.now()
    print('Total: ', (b-a).seconds )
