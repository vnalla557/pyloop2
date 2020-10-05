#!/usr/bin/python3
# pylint: disable=superfluous-parens, missing-docstring, invalid-name

import sys
import json
import argparse
import requests
import numpy as np
from datetime import datetime
from datetime import timedelta
import matplotlib
matplotlib.use('QT5Agg')
from cycler import cycler
from matplotlib import pyplot, ticker, dates, transforms, RcParams
import matplotlib.dates as mdates
from mpl_finance import candlestick_ochl
from matplotlib.ticker import MultipleLocator
ml = MultipleLocator(1)



a=datetime.now()



class Financial_Analysis():
    def __init__(self,url,token,strategy,market,report,conditions,number_of_bars,footer,show_indicators,theme,symbol):
        self.log=args.log
        self.url=url
        self.token=token
        self.strategy=strategy
        self.market=market
        self.report=report
        self.conditions=conditions
        self.number_of_bars=number_of_bars
        self.footer=footer
        self.theme=theme
        self.symbol=symbol
        self.show_indicators=int(show_indicators)




        self.process()
        
    def process(self):
        self.declare_variables()
        self.get_chart_config()
        self.prepare_chart()



    def prepare_chart(self):
        if self.show_indicators:
            self.prepare_normal_chart()
        else:
            self.prepare_fast_chart()



        if self.theme=='dark':
            pyplot.style.use(self.dark_theme)

        if self.show_indicators:
            
            print('Normal Mode')
            
            self.screen = pyplot.figure(figsize=(15, 15))
#            self.screen.autofmt_xdate()  # date autoformat
    
            chartConfig = self.config_data.get("chartConfig")
            assert chartConfig, "No chartConfig field found in: {}".format(data)
    
            panels = chartConfig.get("panels")
            height_ratios = []
            for panel, coef in zip(panels, range(len(panels))):
                panel_height = self.determine_panel_height(panel)
                height_ratios.append(panel_height)
            
            # Price and Volume relative height
            height_ratios[0] = 1.5

            grid = pyplot.GridSpec(len(panels), 1, height_ratios=height_ratios)
            default = pyplot.subplot(grid[0, 0])
            default.grid(True)

            title = "{}".format(symbol)
            default.text(0.4, 0.9, title,
                         verticalalignment='top', horizontalalignment='left',
                         transform=default.transAxes,
                         alpha=0.15,
                         fontsize=20)

            axs = [default]

            for idx in range(len(panels)):
                print(idx)
                if idx == 0:  # default pane
                    pass
                else:
                    ax = pyplot.subplot(grid[idx, 0], sharex=default)
                    axs.append(ax)
            assert panels, "No panels found in: {}".format(data)

            self.indicator_names = []
            for pan in panels:
                self.indicator_names += [i['name'] for i in pan['indicators']]

            self.get_chart_data()

            marketIndicators = self.chart_data.get("marketIndicators")
            assert marketIndicators, "No marketIndicators field found in {}".format(data)

    
            # price panel
            candlesticks = []
            neg_time_scale = []
            pos_time_scale = []
            neg_volume_scale = []
            pos_volume_scale = []
            for marketIndicator in marketIndicators:
                time_value = (mdates.date2num(datetime.fromtimestamp(int(marketIndicator['timestamp']))))
                candlesticks.append((time_value,
                                     marketIndicator['open'],
                                     marketIndicator['close'],
                                     marketIndicator['high'],
                                     marketIndicator['low']))
                if marketIndicator['open'] <= marketIndicator['close']:
    
                    neg_volume_scale.append(0)
    
                    pos_volume_scale.append(marketIndicator["volume"])
                    pos_time_scale.append(time_value)
                else:
                    pos_volume_scale.append(0)
    
                    neg_volume_scale.append(marketIndicator["volume"])
                    neg_time_scale.append(time_value)
    
    
            ohlc_data_arr = np.array(candlesticks)
            ohlc_data_arr2 = np.hstack( [np.arange(ohlc_data_arr[:,0].size)[:,np.newaxis], ohlc_data_arr[:,1:]])
    
            ndays = ohlc_data_arr2[:,0]  # array([0, 1, 2, ... n-2, n-1, n])
            
            npdates = mdates.num2date(ohlc_data_arr[:,0])
            
            fmt='%Y-%m-%d'
            date_strings = []
            for date in npdates:
                date_strings.append(date.strftime(fmt))
                
            candlestick_ochl(default, ohlc_data_arr2, width=0.5, colorup='g', colordown='r', alpha=0.6)
        
            ylim = default.get_ylim()
            default.set_ylim(ylim[0] / 1.2, ylim[1])
            
            pos_time_scale=[]
            neg_time_scale=[]
            cnt=0
            for kk in ohlc_data_arr2:
                pos_time_scale.append(cnt)
                neg_time_scale.append(cnt)
                cnt=cnt+1
    
            volume_bar = default.twinx()
            volume_bar.yaxis.set_label_position("right")
            volume_bar.set_position(transforms.Bbox([[0.125, 0.1], [0.9, 0.32]]))
            volume_bar.bar(pos_time_scale, pos_volume_scale, color="green", alpha=.4)
            volume_bar.bar(neg_time_scale, neg_volume_scale, color="red", alpha=.4)
            ylim = volume_bar.get_ylim()
            volume_bar.set_ylim(ylim[0], ylim[1] * 4)


            for panel, axes in zip(panels, axs):
                self.render_panel(axes, panel, marketIndicators, default)

        else:

            print('Fast Mode')

            self.screen = pyplot.figure(figsize=(12.5, 7))
            self.screen.autofmt_xdate()  # date autoformat

            self.get_chart_data()

            marketIndicators = self.chart_data.get("marketIndicators")
            assert marketIndicators, "No marketIndicators field found in {}".format(data)

            
            height_ratios=[1]
            grid = pyplot.GridSpec(1, 1, height_ratios=height_ratios)
            default = pyplot.subplot(grid[0, 0])
            axs = [default]


            
            default.grid(True)
            title = "{}".format(symbol)
    
            default.text(0.4, 0.9, title,
                         verticalalignment='top', horizontalalignment='left',
                         transform=default.transAxes,
                         alpha=0.15,
                         fontsize=20)
    
    
    
            # price panel
            candlesticks = []
            neg_time_scale = []
            pos_time_scale = []
            neg_volume_scale = []
            pos_volume_scale = []
            for marketIndicator in marketIndicators:
                time_value = (mdates.date2num(datetime.fromtimestamp(int(marketIndicator['timestamp']))))
                candlesticks.append((time_value,
                                     marketIndicator['open'],
                                     marketIndicator['close'],
                                     marketIndicator['high'],
                                     marketIndicator['low']))
                if marketIndicator['open'] <= marketIndicator['close']:
    
                    neg_volume_scale.append(0)
    
                    pos_volume_scale.append(marketIndicator["volume"])
                    pos_time_scale.append(time_value)
                else:
                    pos_volume_scale.append(0)
    
                    neg_volume_scale.append(marketIndicator["volume"])
                    neg_time_scale.append(time_value)
    
    
            ohlc_data_arr = np.array(candlesticks)
            ohlc_data_arr2 = np.hstack( [np.arange(ohlc_data_arr[:,0].size)[:,np.newaxis], ohlc_data_arr[:,1:]])
    
            ndays = ohlc_data_arr2[:,0]  # array([0, 1, 2, ... n-2, n-1, n])
            
            npdates = mdates.num2date(ohlc_data_arr[:,0])
            
            fmt='%Y-%m-%d'
            date_strings = []
            for date in npdates:
                date_strings.append(date.strftime(fmt))
                
            candlestick_ochl(default, ohlc_data_arr2, width=0.5, colorup='g', colordown='r', alpha=0.6)
    
    
            ylim = default.get_ylim()
            print(ylim)
            print(ylim[0] / 1.2, ylim[1])
            default.set_ylim(ylim[0] / 1.2, ylim[1])
            
            pos_time_scale=[]
            neg_time_scale=[]
            cnt=0
            for kk in ohlc_data_arr2:
                pos_time_scale.append(cnt)
                neg_time_scale.append(cnt)
                cnt=cnt+1
    
            volume_bar = default.twinx()
            volume_bar.yaxis.set_label_position("right")
            volume_bar.set_position(transforms.Bbox([[0.125, 0.1], [0.9, 0.32]]))
            volume_bar.bar(pos_time_scale, pos_volume_scale, color="green", alpha=.4)
            volume_bar.bar(neg_time_scale, neg_volume_scale, color="red", alpha=.4)
            ylim = volume_bar.get_ylim()
            volume_bar.set_ylim(ylim[0], ylim[1] * 4)

        xtick_id=[]
        xtick_value=[]
        prev=0
        for xid in range(0,len(date_strings)):
            
            if xid==0 or len(date_strings)==xid+1:
                xtick_id.append(ndays[xid])
                xtick_value.append(date_strings[xid])
                prev= int(date_strings[xid][-2:])
            else:
                if int(date_strings[xid][-2:]) < prev:
                    xtick_id.append(ndays[xid])
                    xtick_value.append(date_strings[xid])

            prev= int(date_strings[xid][-2:])


        default.set_xticks(xtick_id)
        default.set_xticklabels(xtick_value)
        if self.show_indicators:
            default.xaxis.set_minor_locator(ml)
        default.set_xlim( min(ndays)-2, max(ndays)+2)
        
        self.screen.align_xlabels()
        pyplot.subplots_adjust(hspace=0)  #
        pyplot.rc('ytick', labelsize=5)
        pyplot.tight_layout()
        pyplot.savefig('new.png', dpi=int(72))

        pyplot.show()




    def get_chart_config(self):
        
        if not self.show_indicators:
            return;
        
        response_config = requests.post(
            self.url,
            headers={'Accept': 'application/json', 'Authorization': 'Bearer {}'.format(self.token)},
            data={"query": self.make_config_request()}
            )

        if response_config.status_code != 200:
            print("Request failed with status:{} /nmessage:{}".format(response_config.status_code, response_config.text))
            sys.exit(1)

        self.config_data = response_config.json().get("data")
        
        if (self.log):
            print('\nResponse 1:')
            json.dump(response_config.json(), sys.stdout, indent=4)
            json.dump(self.config_data, open(currentDateTime + "_response_1.js", "w"))

        assert self.config_data, "Unexpected response: {}".format(self.config_data)


    def get_chart_data(self):
        if self.show_indicators:
            tmp_data = {"query": self.queryChartData_with_indicators% (self.strategy, self.market, self.number_of_bars, ",".join(self.indicator_names))}
        else:
            tmp_data = {"query": self.queryChartData  % (self.strategy, self.market, self.number_of_bars)}

        response_chart_data = requests.post(
            self.url,
            headers={'Accept': 'application/json', 'Authorization': 'Bearer {}'.format(self.token)},
            data=tmp_data
            )
            
        self.chart_data = response_chart_data.json().get("data")
    
        if (self.log):
            print('\nResponse 2:')
            json.dump(response_chart_data.json(), sys.stdout, indent=4)
            json.dump(self.chart_data, open(currentDateTime + "_response_2.js", "w"))

        assert self.chart_data, "Unexpected response: {}".format(self.chart_data)





    def make_config_request(self):
        screener_conditions = 'screener_conditions:"{}"'.format(self.conditions) if self.conditions else None
        strategy = 'strategy:"{}"'.format(self.strategy)
        report = 'report:"{}"'.format(self.report)
        market = 'market(id:"{}") {{symbol}},'.format(self.market)
        request = self.query_template_chartconfig.format(
            market=market,
            query=', '.join(filter(None, [screener_conditions, strategy, report])),
            indicators=', '.join(self.indicators)
        )
        
    
        if (self.log):
            self.call_log(request)
    
        return request


    
    def determine_panel_height(self,panel):
       if panel["height"] == "large":
           return 0.8
       elif panel["height"] == "small":
            if "bool" in [i["type"] for i in panel["indicators"]]:
                return 0.1
            else:
                return 0.3
       else:
           return 0.5


    def call_log(self,msg):
        print('Request 1:' + msg)
        with open(self.log_file_name, "a") as f:
            f.write('Request 1: '+msg)
            f.flush()



    def get_linestlyle_by_type(self,linestyle_type):
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

    
    def render_panel(self,axes, settings, data, default):
    
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
                
                xid=[]
                for lx in range(0,len(ys)):
                    xid.append(lx)
                
                
                if color:
                    axes.plot(xid, ys, linestyle=linestyle, label=plot, color=color)
                else:
                    axes.plot(xid, ys, linestyle=linestyle, label=plot)
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

                xid=[]
                for lx in range(0,len(ys)):
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

    def declare_variables(self):
        self.log_file_name = datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'logs.txt'

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
        
        self.queryChartData = """query chartData {
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
    parser.add_argument("-n", "--number_of_bars", help="limit the number of bars shown on the chart", default="0")
    parser.add_argument("-r", "--report", help="report uuid", default="")
    parser.add_argument("-o", "--output", help="filepath to output file.")
    parser.add_argument("-d", "--dpi", default=100, help="resolution of resulting png. Default is 100.")
    parser.add_argument("-c", "--conditions", default=None, help="custom screener conditions. Json string.")
    parser.add_argument("-f", "--footer", default="", help="plot footer.")
    parser.add_argument("-l", "--log", default=None, help="If set all requests and response will get logged to the current path")
    parser.add_argument("-i", "--show_indicators", default=1, help="Accepted Values 1 or 0.")
    parser.add_argument("-z", "--symbol", default='', help="Ticker ex. APP")
    parser.add_argument("--theme", default="light", help="theme for output png. Maybe light or dark.")
    args = parser.parse_args()

    url_ = args.api_query_endpoint
    token_ = args.api_client_token
    strategy_ = args.strategy
    market_ = args.market
    report_ = args.report
    conditions_ = args.conditions
    numberOfBars_ = args.number_of_bars
    show_indicators=args.show_indicators
    theme=args.theme
    symbol=args.symbol


    fin_obj = Financial_Analysis(url_, token_, strategy_, market_, report_, conditions_, numberOfBars_, args.footer,show_indicators,theme,symbol)
    
