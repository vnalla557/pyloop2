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


yearDateFormatter = dates.DateFormatter('%Y-%m-%d')
monthLocator = dates.MonthLocator()  # every month
dayLocator = dates.DayLocator()


a=datetime.now()

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


query_template_chartconfig = """query chartConfig {{
    {market}
    chartConfig({query}){{
        panels {{
            name,
            height,
            indicators {{{indicators}}} }}}}}}"""

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


class Financial_Analysis():
    def __init__(self,url,token,strategy,market,report,conditions,number_of_bars,footer,show_indicators):
        self.log=args.log
        self.url=url
        self.token=token
        self.strategy=strategy
        self.market=market
        self.report=report
        self.conditions=conditions
        self.number_of_bars=number_of_bars
        self.footer=footer
        self.show_indicators=show_indicators
        self.log_file_name = datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'logs.txt'

        self.indicators = ["label", "name", "style", "type", "interval",
                      "position", "color", "width"]


        self.screen = pyplot.figure(figsize=(15, 15))
        self.screen.autofmt_xdate()  # date autoformat

        self.process()
        
    def process(self):
        self.get_data()
        
    def get_data(self):

        response_config = requests.post(
            self.url,
            headers={'Accept': 'application/json', 'Authorization': 'Bearer {}'.format(self.token)},
            data={"query": self.make_config_request()}
            )

        if response_config.status_code != 200:
            print("Request failed with status:{} /nmessage:{}".format(response_config.status_code, response_config.text))
            return


        data = response_config.json().get("data")
        
        if (self.log):
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
            panel_height = self.determine_panel_height(panel)
            height_ratios.append(panel_height)
        
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


        # hide x axis title for candlestick
        default.get_xaxis().set_ticklabels([])


        for idx in range(len(panels)):
            print(idx)
            if idx == 0:  # default pane
                pass
            else:
                ax = pyplot.subplot(grid[idx, 0], sharex=default)
                axs.append(ax)

                # hide x-axis titles for all except last one                
#                if idx<2:
#                    ax.get_xaxis().set_ticklabels([])
                    


                # ax.xaxis.set_major_locator(ticker.MaxNLocator(10))
        assert panels, "No panels found in: {}".format(data)



    
        indicator_names = []
        for pan in panels:
            indicator_names += [i['name'] for i in pan['indicators']]


        response_chart_data = requests.post(
            self.url,
            headers={'Accept': 'application/json', 'Authorization': 'Bearer {}'.format(self.token)},
            data={"query": queryChartData % (self.strategy, self.market, self.number_of_bars, ",".join(indicator_names))})
#            data={"query": queryChartData % (self.strategy, self.market, self.number_of_bars, ",".join(indicator_names))})
            
        data = response_chart_data.json().get("data")
    
        if (self.log):
            print('\nResponse 2:')
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
        ohlc_data_arr2 = np.hstack(
            [np.arange(ohlc_data_arr[:,0].size)[:,np.newaxis], ohlc_data_arr[:,1:]])

        ndays = ohlc_data_arr2[:,0]  # array([0, 1, 2, ... n-2, n-1, n])
        
        npdates = mdates.num2date(ohlc_data_arr[:,0])

        print( len(pos_time_scale), len(neg_time_scale),len(ohlc_data_arr2) )
        
        fmt='%Y-%m-%d'
        date_strings = []
        for date in npdates:
            date_strings.append(date.strftime(fmt))
            
        candlestick_ochl(default, ohlc_data_arr2, width=0.5, colorup='g', colordown='r', alpha=0.6)
#        candlestick_ohlc(ax, ohlc_data_arr2, **kwargs)
#        candlestick_ochl(default, candlesticks, width=0.5, colorup='g', colordown='r', alpha=1)


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
        print(ylim)
        volume_bar.set_ylim(ylim[0], ylim[1] * 4)

        for panel, axes in zip(panels, axs):
            self.render_panel(axes, panel, marketIndicators, default)


        '''
        for ax in axs[:-1]:
            ax.get_xaxis().set_ticks([])
            ax.xaxis.set_major_locator(monthLocator)
    
        axs[-1].xaxis.set_major_locator(monthLocator)
        axs[-1].xaxis.set_minor_locator(dayLocator)
    
        axs[-1].xaxis.set_major_formatter(yearDateFormatter)
        self.screen.text(0.9, 0.17, self.footer,
                    verticalalignment='top', horizontalalignment='right',
                    transform=axs[-1].transAxes,
                    fontsize=20)
        self.screen.text(0.13, 0.17, title,
                    verticalalignment='top', horizontalalignment='left',
                    transform=axs[-1].transAxes,
                    fontsize=20)
        '''


        start_day= int(date_strings[0][-2:])
        start_date= date_strings[0]
        
        ndays=list(ndays)
        
        padded_start_dates=[]
        padded_start_ids=[]
        date_id=-1
        for mid in range( 1,start_day  ):
            ldt=start_date[:-2]+ str(mid).zfill(2)
            if datetime.strptime(ldt, '%Y-%m-%d').weekday() not in [5,6]:
                padded_start_dates.append( ldt  )
                padded_start_ids.append(date_id)
                date_id=date_id-1

        date_strings=padded_start_dates+date_strings
        ndays=list(reversed(padded_start_ids)) + ndays

        end_day= int(date_strings[-1][-2:])
        end_date= date_strings[-1]

        padded_end_dates=[]
        padded_end_ids=[]
        max_date_id = max(ndays)
        for mid in range( end_day,31+1):
            try:
                ldt= end_date[:-2]+ str(mid).zfill(2)
                if datetime.strptime(ldt, '%Y-%m-%d').weekday() not in [5,6]:
                    padded_end_dates.append(  ldt )
                    max_date_id=max_date_id+1
                    padded_end_ids.append(max_date_id)
            except ValueError:
                continue

        last_date = datetime.strptime(padded_end_dates[-1],'%Y-%m-%d')+timedelta(days=1)
        padded_end_dates.append(last_date.strftime('%Y-%m-%d'))

        last_date_id=padded_end_ids[-1]+1
        padded_end_ids.append(last_date_id)

        date_strings=date_strings+padded_end_dates
        ndays=ndays+padded_end_ids

                
        print(date_strings,ndays)
        
        


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
        default.xaxis.set_minor_locator(ml)

        # Format x axis

#        default.set_xticks(ndays[::30])
#        default.set_xticklabels(date_strings[::30])

#        print(ndays)
#        print(ndays[::30])
#        print(date_strings[::30])
        default.set_xlim( min(ndays), max(ndays))

        self.screen.align_xlabels()
        pyplot.subplots_adjust(hspace=0)  #
        pyplot.rc('ytick', labelsize=5)


        pyplot.savefig('new.png', dpi=int(72), bbox_inches='tight')
        b=datetime.now()
        
        print(   (b-a).seconds  )

        pyplot.show()





    def make_config_request(self):
        screener_conditions = 'screener_conditions:"{}"'.format(self.conditions) if self.conditions else None
        strategy = 'strategy:"{}"'.format(self.strategy)
        report = 'report:"{}"'.format(self.report)
        market = 'market(id:"{}") {{symbol}},'.format(self.market)
        request = query_template_chartconfig.format(
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
    parser.add_argument("-i", "--show_indicators", default=None, help="Accepted Values 1 or 0.")
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


    fin_obj = Financial_Analysis(url_, token_, strategy_, market_, report_, conditions_, numberOfBars_, args.footer,show_indicators)
    
