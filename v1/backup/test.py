from datetime import datetime

timestamp = 1583884800
dt_object = datetime.fromtimestamp(timestamp)

print("dt_object =", dt_object)
print("type(dt_object) =", type(dt_object))

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mpl_finance
print(dir(mpl_finance))
from matplotlib.finance import quotes_historical_yahoo, candlestick_ochl



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

    # Format x axis
    ax.set_xticks(ndays[::freq])
    ax.set_xticklabels(date_strings[::freq], rotation=45, ha='right')
    ax.set_xlim(ndays.min(), ndays.max())

    plt.show()
    
    
# Get data using quotes_historical_yahoo_ohlc
date1, date2 = [(2006, 6, 1), (2006, 8, 1)]
date3, date4 = [(2006, 5, 15), (2008, 4, 1)]
data_1 = quotes_historical_yahoo_ohlc('INTC', date1, date2)
data_2 = quotes_historical_yahoo_ohlc('INTC', date3, date4)

# Create figure with 2 axes
fig, axes = plt.subplots(ncols=2, figsize=(14, 6))

weekday_candlestick(data_1, ax=axes[0], fmt='%b %d', freq=3, width=0.5)
weekday_candlestick(data_2, ax=axes[1], fmt='%b %d %Y', freq=30)

# Set the plot titles
axes[0].set_title('Shorter Range Stock Prices')
axes[1].set_title('Longer Range Stock Prices')