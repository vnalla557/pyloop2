# Keep below imports top most to avoid x-window errors in servers
import matplotlib
matplotlib.use('Agg')

#!/usr/bin/python3
# pylint: disable=superfluous-parens, missing-docstring, invalid-name

import sys
import json
import argparse

from datetime import datetime
a=datetime.now()

import requests
import numpy as np
from cycler import cycler
import matplotlib.dates as mdates
from mpl_finance import candlestick_ochl
from matplotlib.ticker import MultipleLocator
from matplotlib import pyplot, ticker, transforms, RcParams



class FinancialAnalysis:
    def __init__(self, url, token, strategy, market, report, conditions,
                 number_of_bars, footer, show_indicators, theme, symbol, dpi, logs):
        self.log = int(logs)
        self.url = url
        self.token = token
        self.strategy = strategy
        self.market = market
        self.report = report
        self.conditions = conditions
        self.number_of_bars = int(number_of_bars)
        self.footer = footer
        self.theme = theme
        self.symbol = symbol
        self.dpi = dpi
        self.show_indicators = int(show_indicators)

    def process(self):
        self.declare_variables()
        self.prepare_chart()

    def prepare_chart(self):
        if self.show_indicators:
            self.prepare_normal_chart()
        else:
            self.prepare_fast_chart()

    def prepare_fast_chart(self):

        if self.theme == "dark":
            pyplot.style.use(self.dark_theme)

        self.screen = pyplot.figure(figsize=(14, 8))
        grid = pyplot.GridSpec(1, 1)
        default = pyplot.subplot(grid[0, 0])
        default.grid(True)
        axs = [default]

        if self.number_of_bars == 0:
            self.number_of_bars = 50

        payload2={"query": self.queryChartData_without_indicators % (self.strategy, self.market, self.number_of_bars)}

        self.call_log('Chart data request:')
        self.call_log(payload2)

        response_chart_data = requests.post(
            self.url,
            headers={'Accept': 'application/json', 'Authorization': 'Bearer {}'.format(self.token)},
            data=payload2)

        if response_chart_data.status_code != 200:
            self.call_log("Chart data request failed with status:{} message:{}".format(response_chart_data.status_code, response_chart_data.text))
            return

        data = response_chart_data.json().get("data")

        self.call_log('Chart data response:')
        self.call_log(json.dumps(data))

        market_indicators=None
        try:
            market_indicators = data.get("marketIndicators")
            assert market_indicators
        except Exception as e:
            self.call_log('Market indicators field not found.')

        if market_indicators:
            # price panel
            candlesticks = []
            neg_volume_scale = []
            pos_volume_scale = []
            for marketIndicator in market_indicators:
                time_value = (mdates.date2num(datetime.fromtimestamp(int(marketIndicator['timestamp']))))
                candlesticks.append((time_value,
                                     marketIndicator['open'],
                                     marketIndicator['close'],
                                     marketIndicator['high'],
                                     marketIndicator['low']))
                if marketIndicator['open'] <= marketIndicator['close']:
                    neg_volume_scale.append(0)
                    pos_volume_scale.append(0 if marketIndicator["volume"] is None else marketIndicator["volume"])
                else:
                    pos_volume_scale.append(0)
                    neg_volume_scale.append(0 if marketIndicator["volume"] is None else marketIndicator["volume"])

            # convert the datalist into numpy array and
            # change index as number series instead of date
            ohlc_data_arr = np.array(candlesticks)
            ohlc_data_arr2 = np.hstack([np.arange(ohlc_data_arr[:, 0].size)[:, np.newaxis], ohlc_data_arr[:, 1:]])
            ndays = ohlc_data_arr2[:, 0]
            npdates = mdates.num2date(ohlc_data_arr[:, 0])

            # store dates as strings for axis labels
            date_strings = []
            for date in npdates:
                date_strings.append(date.strftime('%Y-%m-%d'))

            candlestick_ochl(default, ohlc_data_arr2, width=0.5, colorup='g', colordown='r', alpha=0.6)

            ylim = default.get_ylim()
            default.set_ylim(ylim[0] / 1.2, ylim[1])

            # use number series as x axis instead of date  for quantity bars
            pos_time_scale = []
            neg_time_scale = []
            for cnt, val in enumerate(ohlc_data_arr2):
                pos_time_scale.append(cnt)
                neg_time_scale.append(cnt)

            volume_bar = default.twinx()
            volume_bar.yaxis.set_label_position("right")
            volume_bar.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.0f}'.format(x/1000000) + 'M'))
            volume_bar.set_position(transforms.Bbox([[0.125, 0.1], [0.9, 0.32]]))
            volume_bar.bar(pos_time_scale, pos_volume_scale, color="green", alpha=.4)
            volume_bar.bar(neg_time_scale, neg_volume_scale, color="red", alpha=.4)
            ylim = volume_bar.get_ylim()
            volume_bar.set_ylim(ylim[0], ylim[1] * 4)

            # show ticks for first date,last date, start date of each month
            xtick_id = []
            xtick_value = []
            prev = 0
            for xid, ds in enumerate(date_strings):
                if xid == 0 or len(date_strings) == xid+1:
                    xtick_id.append(ndays[xid])
                    xtick_value.append(ds)
                    prev = int(ds[-2:])
                else:
                    if int(ds[-2:]) < prev:
                        xtick_id.append(ndays[xid])
                        xtick_value.append(ds)
    
                prev = int(ds[-2:])
    
            default.set_xticks(xtick_id)
            default.set_xticklabels(xtick_value)
    
            # X axis limit
            default.set_xlim(min(ndays)-2, max(ndays)+2)

        # watermark fast chart
        default.text(0.35, 0.8, self.footer,
                     verticalalignment='top', horizontalalignment='left',
                     transform=default.transAxes,
                     alpha=0.15,
                     fontsize=20)

        # ticker fast chart
        title = "{}".format(self.symbol)
        self.screen.text(0.014, 0.85, title,
                         verticalalignment='top', horizontalalignment='left',
                         transform=default.transAxes,
                         fontsize=20)

        self.screen.align_xlabels()
        pyplot.subplots_adjust(hspace=0)
        pyplot.rc('ytick', labelsize=5)
        pyplot.savefig('new.png', dpi=int(self.dpi), bbox_inches='tight')

    def prepare_normal_chart(self):

        if self.theme == "dark":
            pyplot.style.use(self.dark_theme)

        self.screen = pyplot.figure(figsize=(15, 15))

        payload={"query": self.make_config_request()}
        response_config = requests.post(
            self.url,
            headers={'Accept': 'application/json', 'Authorization': 'Bearer {}'.format(self.token)},
            data=payload
            )

        self.call_log('Chart config request:')
        self.call_log(payload)

        if response_config.status_code != 200:
            self.call_log("Chart config request failed with status:{} /nmessage:{}".format(response_config.status_code, response_config.text))
            return

        data = response_config.json().get("data")

        self.call_log('Chart config response:')
        self.call_log( json.dumps(data) )

        try:
            assert data
        except Exception as e:
            self.call_log('Unexpected Response from chart config: {}'.format(data))
            self.call_log('Retrying fast chart >>>')
            self.prepare_fast_chart()
            return

        try:
            market_name = data['market']['symbol']
        except Exception as e:
            self.call_log('Unable to retrieve market name: '+str(e))
            market_name=''

        try:
            chart_config = data.get("chartConfig")
            assert chart_config
        except Exception as e:
            self.call_log('Chart config field not found. '+str(e))
            self.call_log('Retrying fast chart >>>')
            self.prepare_fast_chart()
            return
            
        try:
            panels = chart_config.get("panels")
            assert panels
        except Exception as e:
            self.call_log('Panel config not found. '+str(e))
            self.call_log('Retrying fast chart >>>')
            self.prepare_fast_chart()
            return

        height_ratios = []
        for panel, coef in zip(panels, range(len(panels))):
            panel_height = self.determine_panel_height(panel)
            height_ratios.append(panel_height)

        # Price and Volume relative height
        height_ratios[0] = 1.5

        grid = pyplot.GridSpec(len(panels), 1, height_ratios=height_ratios)
        default = pyplot.subplot(grid[0, 0])

        axs = [default]

        for idx in range(len(panels)):
            if idx == 0:  # default pane
                pass
            else:
                ax = pyplot.subplot(grid[idx, 0], sharex=default)
                axs.append(ax)
        assert panels, "No panels found in: {}".format(data)

        indicator_names = []
        for pan in panels:
            indicator_names += [i['name'] for i in pan['indicators']]

        payload2={"query": self.queryChartData_with_indicators % (self.strategy, self.market, self.number_of_bars, ",".join(indicator_names))}

        response_chart_data = requests.post(
            self.url,
            headers={'Accept': 'application/json', 'Authorization': 'Bearer {}'.format(self.token)},
            data=payload2)
        
        self.call_log('Chart data request:')
        self.call_log(payload2)

        if response_chart_data.status_code != 200:
            self.call_log("Chart data request failed with status:{} /nmessage:{}".format(response_chart_data.status_code, response_chart_data.text))
            return

        data = response_chart_data.json().get("data")

        self.call_log('Chart data response:')
        self.call_log( json.dumps(data) )

        market_indicators=None
        try:
            market_indicators = data.get("marketIndicators")
            assert market_indicators
        except Exception as e:
            self.call_log('Market indicators field not found.')

        if market_indicators:
            # price panel
            candlesticks = []
            neg_volume_scale = []
            pos_volume_scale = []
            for marketIndicator in market_indicators:
                time_value = (mdates.date2num(datetime.fromtimestamp(int(marketIndicator['timestamp']))))
                candlesticks.append((time_value,
                                     marketIndicator['open'],
                                     marketIndicator['close'],
                                     marketIndicator['high'],
                                     marketIndicator['low']))
                if marketIndicator['open'] <= marketIndicator['close']:
                    neg_volume_scale.append(0)
                    pos_volume_scale.append(0 if marketIndicator["volume"] is None else marketIndicator["volume"])
                else:
                    pos_volume_scale.append(0)
                    neg_volume_scale.append(0 if marketIndicator["volume"] is None else marketIndicator["volume"])

            # convert the datalist into numpy array and change index as number series instead of date
            ohlc_data_arr = np.array(candlesticks)
            ohlc_data_arr2 = np.hstack([np.arange(ohlc_data_arr[:, 0].size)[:, np.newaxis], ohlc_data_arr[:, 1:]])
            ndays = ohlc_data_arr2[:, 0]
            npdates = mdates.num2date(ohlc_data_arr[:, 0])

            # store dates as strings for axis labels
            date_strings = []
            for date in npdates:
                date_strings.append(date.strftime('%Y-%m-%d'))

            candlestick_ochl(default, ohlc_data_arr2, width=0.5, colorup='g', colordown='r', alpha=0.6)

            ylim = default.get_ylim()
            default.set_ylim(ylim[0] / 1.2, ylim[1])

            # use number series as x axis instead of date  for quantity bars
            pos_time_scale = []
            neg_time_scale = []
            for cnt, val in enumerate(ohlc_data_arr2):
                pos_time_scale.append(cnt)
                neg_time_scale.append(cnt)

            volume_bar = default.twinx()
            volume_bar.yaxis.set_label_position("right")
            volume_bar.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.0f}'.format(x/1000000) + 'M'))
            volume_bar.set_position(transforms.Bbox([[0.125, 0.1], [0.9, 0.32]]))
            volume_bar.bar(pos_time_scale, pos_volume_scale, color="green", alpha=.4)
            volume_bar.bar(neg_time_scale, neg_volume_scale, color="red", alpha=.4)
            ylim = volume_bar.get_ylim()
            volume_bar.set_ylim(ylim[0], ylim[1] * 4)
    
            for panel, axes in zip(panels, axs):
                self.render_panel(axes, panel, market_indicators, default)

            # show ticks for first date,last date, start date of each month
            xtick_id = []
            xtick_value = []
            prev = 0

            for xid, ds in enumerate(date_strings):
                if xid == 0 or len(date_strings) == xid+1:
                    xtick_id.append(ndays[xid])
                    xtick_value.append(ds)
                    prev = int(ds[-2:])
                else:
                    if int(ds[-2:]) < prev:
                        xtick_id.append(ndays[xid])
                        xtick_value.append(ds)
    
                prev = int(ds[-2:])
    
            default.set_xticks(xtick_id)
            default.set_xticklabels(xtick_value)
            default.xaxis.set_minor_locator(MultipleLocator(1))
    
            # X axis limit
            default.set_xlim(min(ndays)-5, max(ndays)+5)

        # watermark normal chart
        default.text(0.35, 0.8, self.footer,
                     verticalalignment='top', horizontalalignment='left',
                     transform=default.transAxes,
                     alpha=0.15,
                     fontsize=20)

        # ticker normal chart
        title = "{}".format(market_name)
        self.screen.text(0.015, 0.978, title,
                         verticalalignment='top', horizontalalignment='left',
                         transform=default.transAxes,
                         fontsize=20)

        self.screen.align_xlabels()

        pyplot.subplots_adjust(hspace=0)
        pyplot.rc('ytick', labelsize=5)
        pyplot.savefig('new.png', dpi=int(self.dpi), bbox_inches='tight')

    def make_config_request(self):
        screener_conditions = 'screener_conditions:"{}"'.format(self.conditions) if self.conditions else None
        strategy = 'strategy:"{}"'.format(self.strategy) if self.strategy else None
        report = 'report:"{}"'.format(self.report)
        market = 'market(id:"{}") {{symbol}},'.format(self.market)
        request = self.query_template_chartconfig.format(
            market=market,
            query=', '.join(filter(None, [screener_conditions, strategy, report])),
            indicators=', '.join(self.indicators)
        )

        return request

    def determine_panel_height(self, panel):
        if panel["height"] == "large":
            return 0.8
        elif panel["height"] == "small":
            if "bool" in [i["type"] for i in panel["indicators"]]:
                return 0.1
            else:
                return 0.3
        else:
            return 0.5

    def call_log(self, msg):
        if self.log:
            print('\n')
            print(msg)
            self.f_log.write('\n\n')
            self.f_log.write(str(msg))
            self.f_log.flush()

    def get_linestlyle_by_type(self, linestyle_type):
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

    def render_panel(self, axes, settings, data, default):

        # Create dict and add plots for this panel
        plots = {}
        for indicatorPlotConfig in settings["indicators"]:

            plots.update({
                indicatorPlotConfig["label"]: {
                    # indicatorPlotConfig["name"]: {
                    "x": [],
                    "y": [],
                    "indicator": indicatorPlotConfig["name"],
                    "linestyle": self.get_linestlyle_by_type(indicatorPlotConfig["style"]),
                    "color": indicatorPlotConfig["color"],
                    "type": indicatorPlotConfig["type"]
                }
            })

        # Add the actual data to each plot
        for point in data:
            point_indicators = json.loads(point["indicators"])
            for interval in point_indicators.keys():

                for indicator in point_indicators[interval]:
                    # if indicator in plots.keys():
                    for plot in plots:
                        if plots[plot]["indicator"] == indicator:
                            plots[plot]["x"].append(datetime.fromtimestamp(int(point['timestamp'])))
                            plots[plot]["y"].append(point_indicators[interval][indicator])

        for plot in plots:
            linestyle = plots[plot]["linestyle"]

            color = plots[plot]["color"]
            xs = plots[plot]["x"]
            ys = plots[plot]["y"]

            if plots[plot]["type"] == "line":

                xid = []
                for lx in range(0, len(ys)):
                    xid.append(lx)

                if color:
                    axes.plot(xid, ys, linestyle=linestyle, label=plot, color=color)
                else:
                    axes.plot(xid, ys, linestyle=linestyle, label=plot)
            elif plots[plot]["type"] == "bool":

                axes.get_yaxis().set_major_formatter(self.bool_formatter)
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
                # ylim = axes.get_ylim()
                # axes.set_ylim(ylim[0]*5, ylim[1]*5)
                axes.set_ylim([-1.5, 1.5])

            elif plots[plot]["type"] == "bar":

                xid = []
                for lx in range(0, len(ys)):
                    xid.append(lx)

                if color:
                    axes.bar(xid, ys, label=plot, color=color)
                else:
                    axes.bar(xid, ys, label=plot)
            elif plots[plot]["type"] == "text":
                pass
            axes.legend(loc="lower left", shadow=False, fontsize="xx-small")
            if settings["name"] != "default":
                axes.text(0.01, 0.95, settings["name"],
                          verticalalignment='top', horizontalalignment='left',
                          transform=axes.transAxes,
                          fontsize=10)
            axes.grid(True)

    def bool_solver(self, x, pos):
        if x == 0:
            return ""
        elif x > 0:
            return "t"
        return "f"

    def declare_variables(self):
        self.log_file_name = 'logs_'+datetime.now().strftime('%Y_%m_%d')+'.txt'
        self.currentDateTime = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')

        self.f_log = open(self.log_file_name,'a')
        self.f_log.write('\n-----------------'+self.currentDateTime+'-----------------')
        print('\n-----------------'+self.currentDateTime+'-----------------')

        self.bool_formatter = ticker.FuncFormatter(self.bool_solver)

        self.indicators = ["label", "name", "style", "type", "interval",
                           "position", "color", "width"]

        self.dark_theme = RcParams({
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

        self.queryChartConfig = """query chartConfig {
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

        self.query_template_chartconfig = """query chartConfig {{
            {market}
            chartConfig({query}){{
                panels {{
                    name,
                    height,
                    indicators {{{indicators}}} }}}}}}"""

        self.queryChartData_without_indicators = """query chartData {
          marketIndicators(
            strategy:"%s",
            market:"%s",
            limit:%s,
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

        self.queryChartData_with_indicators = """query chartData {
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--api_query_endpoint", help="url to query", default="https://engine.therationalinvestor.com/api/")
    parser.add_argument("-t", "--api_client_token", help="auth token")
    parser.add_argument("-s", "--strategy", help="strategy uuid")
    parser.add_argument("-m", "--market", help="market uuid")
    parser.add_argument("-n", "--number_of_bars", default="0", help="limit the number of bars shown on the chart")
    parser.add_argument("-r", "--report", help="report uuid", default="")
    parser.add_argument("-o", "--output", help="filepath to output file.")
    parser.add_argument("-d", "--dpi", default=100, help="resolution of resulting png. Default is 100.")
    parser.add_argument("-c", "--conditions", default=None, help="custom screener conditions. Json string.")
    parser.add_argument("-f", "--footer", default="", help="plot footer.")
    parser.add_argument("-l", "--log", default=0, help="If set all requests and response will get logged to the current path")
    parser.add_argument("-i", "--show_indicators", default=1, help="Accepted Values 1 or 0.")
    parser.add_argument("-z", "--symbol", default='', help="Ticker ex. APP")
    parser.add_argument("--theme", default="light", help="theme for output png. Maybe light or dark.")
    args = parser.parse_args()

    _dpi = args.dpi
    _theme = args.theme
    _logs  = args.log
    _symbol = args.symbol
    _market = args.market
    _report = args.report
    _footer = args.footer
    _strategy = args.strategy
    _conditions = args.conditions
    _token = args.api_client_token
    _url = args.api_query_endpoint
    _number_of_bars = args.number_of_bars
    _show_indicators = args.show_indicators

    # main routine
    fin_obj = FinancialAnalysis(_url, _token, _strategy, _market, _report, _conditions, _number_of_bars, _footer, _show_indicators, _theme, _symbol, _dpi, _logs)
    fin_obj.process()
    fin_obj.f_log.close()
    b=datetime.now()
    print( (b-a).seconds,(b-a).microseconds/10000)
