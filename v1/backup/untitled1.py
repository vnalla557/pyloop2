
    def prepare_fast_chart(self):
        self.screen = pyplot.figure(figsize=(12.5, 7))            
        grid = pyplot.GridSpec(1, 1)
        default = pyplot.subplot(grid[0, 0])    
        default.grid(True)
        axs = [default]

        
        title = "{}".format(self.symbol)
        default.text(0.4, 0.9, title,
                     verticalalignment='top', horizontalalignment='left',
                     transform=default.transAxes,
                     alpha=0.15,
                     fontsize=20)


        if self.number_of_bars==0:
            self.number_of_bars=50

        response_chart_data = requests.post(
            self.url,
            headers={'Accept': 'application/json', 'Authorization': 'Bearer {}'.format(self.token)},
            data={"query": self.queryChartData_without_indicators % (self.strategy, self.market, self.number_of_bars)}
            )

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
            else:
                pos_volume_scale.append(0)
                neg_volume_scale.append(marketIndicator["volume"])

        #convert the datalist into numpy array and change index as number series instead of date
        ohlc_data_arr = np.array(candlesticks)
        ohlc_data_arr2 = np.hstack([np.arange(ohlc_data_arr[:,0].size)[:,np.newaxis], ohlc_data_arr[:,1:]])
        ndays = ohlc_data_arr2[:,0]
        npdates = mdates.num2date(ohlc_data_arr[:,0])

        #store dates as strings for axis labels
        date_strings = []
        for date in npdates:
            date_strings.append(date.strftime('%Y-%m-%d'))


        candlestick_ochl(default, ohlc_data_arr2, width=0.5, colorup='g', colordown='r', alpha=0.6)


        ylim = default.get_ylim()
        default.set_ylim(ylim[0] / 1.2, ylim[1])

        # use number series as x axis instead of date  for quantity bars
        pos_time_scale=[]
        neg_time_scale=[]
        for cnt in range(0,len(ohlc_data_arr2)):
            pos_time_scale.append(cnt)
            neg_time_scale.append(cnt)
        
        volume_bar = default.twinx()
        volume_bar.yaxis.set_label_position("right")
        volume_bar.set_position(transforms.Bbox([[0.125, 0.1], [0.9, 0.32]]))
        volume_bar.bar(pos_time_scale, pos_volume_scale, color="green", alpha=.4)
        volume_bar.bar(neg_time_scale, neg_volume_scale, color="red", alpha=.4)
        ylim = volume_bar.get_ylim()
        volume_bar.set_ylim(ylim[0], ylim[1] * 4)

        self.screen.text(0.9, 0.17, self.footer,
                    verticalalignment='top', horizontalalignment='right',
                    transform=axs[-1].transAxes,
                    fontsize=20)
        self.screen.text(0.13, 0.17, title,
                    verticalalignment='top', horizontalalignment='left',
                    transform=axs[-1].transAxes,
                    fontsize=20)

        # show ticks for first date,last date, start date of each month
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
        default.set_xlim( min(ndays)-2, max(ndays)+2)

        self.screen.align_xlabels()

        pyplot.subplots_adjust(hspace=0)
        pyplot.rc('ytick', labelsize=5)
        pyplot.savefig('new.png', dpi=int(self.dpi), bbox_inches='tight')
        pyplot.show()
