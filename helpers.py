import datetime
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime as dt
from datetime import timedelta as td
from tabulate import tabulate
from grant import Grant
from config import UserSettings

us = UserSettings()
DESIRED_TICKER_ATTRIBUTE = "Close"

# define ANALYSIS_START_DATE dynamically based on grant vesting logic
NUM_DAYS_PRECEDING_ANALYSIS = 30
ANALYSIS_START_DATE = min(
        [Grant(grant).first_vest_date for grant in us.grants]
    ) - td(days=NUM_DAYS_PRECEDING_ANALYSIS)

# define col names
VEST_COL_NAME = f"{us.STOCK} Vested"
CASH_VEST_COL_NAME = f"Cash Vested"

MARKET_SHARES_RSU_COL_NAME = f"{us.MARKET} Purchased (RSUs)"
MARKET_SHARES_CASH_COL_NAME = f"{us.MARKET} Purchased (Cash)"

VEST_CUMSUM_COL_NAME = f"Total {us.STOCK} Shares"
CASH_VEST_CUMSUM_COL_NAME = f"Total Cash Vested"
MARKET_SHARES_RSU_CUMSUM_COL_NAME = f"Total {us.MARKET} Shares (RSUs)"
MARKET_SHARES_CASH_CUMSUM_COL_NAME = f"Total {us.MARKET} Shares (Cash)"

STOCK_PORTFOLIO_COL_NAME = f"{us.STOCK} Portfolio Value"
MARKET_PORTFOLIO_RSU_COL_NAME = f"{us.MARKET} Portfolio Value (RSUs)"
MARKET_PORTFOLIO_CASH_COL_NAME = f"{us.MARKET} Portfolio Value (Cash)"

def _get_absolute_path(file_name):
    """
    generates absolute file path, assuming file_name is in same dir as __file__
    """
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, file_name)
    
def is_vest_date(query_date):
    """
    checks if query_date is a vesting date

    args:
        query_date (datetime): expects input as datetime Date object

    return:
        bool: True if query_date is a vesting date, False otherwise
    """

    vest_months = {date[0] for date in us.VEST_SCHEDULE}
    vest_days = {date[1] for date in us.VEST_SCHEDULE}

    return True if query_date.month in vest_months and query_date.day in vest_days else False

def calculate_vested_amount(query_date, assumeCashReward=False):
    """
    calculates the amount vested on query_date
    note that this is the vesting amount after an estimated withholding rate on the total shares released

    args:
        query_date (datetime): expects input as datetime Date object 

    return:
        if assumeCashReward is True:
            return total_vested as the $ value of cash released on query_date
        else:
            return total_vested as the number of shares vested on query_date
    """

    if not is_vest_date(query_date):
        # can not vest on non-vesting days
        return 0

    total_vested = 0
    for grant in us.grants:
        g = Grant(grant)

        for vest_year, fractions in g.vest_plan.items():
            for i, fraction in enumerate(fractions):
                vest_month, vest_day = us.VEST_SCHEDULE[i % 4]
                vest_date = datetime.date(vest_year, vest_month, vest_day)

                # Handle cases where vest_date is before the grant_date
                if vest_date < g.grant_date:
                    continue

                # sum fractions only if vesting occurrs prior WORK_END_DATE
                # since vesting cant occur after employment ends
                if us.WORK_END_DATE is not None:
                    try:
                        dt.strptime(us.WORK_END_DATE, "%Y-%m-%d").date()
                    except ValueError:
                        raise ValueError(f"WORK_END_DATE must be in YYYY-MM-DD format, or set to null.")
                
                if vest_date == query_date and (us.WORK_END_DATE is None or vest_date <= dt.strptime(us.WORK_END_DATE, "%Y-%m-%d").date()):
                    total_vested += fraction * g.vest_rate * (g.grant_value if assumeCashReward else g.grant_qty)

    return total_vested

def get_ticker_prices(ticker):
    """
    expects input as string
    returns pandas DataFrame
    """

    # Get historical price data
    # yfinance does not include end date in the date range, 
    # so by setting end date to tomorrow's date, you include current date price data
    hist = yf.Ticker(ticker).history(
        start=ANALYSIS_START_DATE, 
        end=dt.now().date() + td(days=1)) \
        .reset_index() # sets index to a Date col 
        
    if hist.empty:
        raise ValueError(f"No data found for {ticker} since {ANALYSIS_START_DATE}.")

    # stock.history() returns Date values as Timestamp object
    # convert to date Object for consistency
    hist["Date"] = hist["Date"].dt.date

    # various clean-up operations:
    #   drop unnecessary columns
    #   rename ticker price col to ticker 
    hist = hist[["Date", DESIRED_TICKER_ATTRIBUTE]]
    hist.rename(columns={DESIRED_TICKER_ATTRIBUTE: ticker}, inplace=True)

    return hist

def generate_results():
    # generate a df with all dates since ANALYSIS_START_DATE
    date_range = pd.date_range(
        start=ANALYSIS_START_DATE, 
        end=dt.now().date(),
        freq="D") \
        .date

    res = pd.DataFrame(date_range, columns=["Date"])

    # add STOCK and MARKET ticker values for all analysis dates
    res = res.merge(get_ticker_prices(us.STOCK), on="Date", how="left")
    res = res.merge(get_ticker_prices(us.MARKET), on="Date", how="left")

    # forward fill values for dates where price data was not available
    res = res.ffill()

    # calculate the vested amounts over the date range
    res[VEST_COL_NAME] = res["Date"].apply(lambda date: calculate_vested_amount(date))
    res[CASH_VEST_COL_NAME] = res["Date"].apply(lambda date: calculate_vested_amount(date, assumeCashReward=True))

    # calculate Hold strategy performance
    # for each date, calculate the number of shares vested on that date
    # also, track cumulative shares vested and running portfolio value
    res[VEST_CUMSUM_COL_NAME] = res[VEST_COL_NAME].cumsum()
    res[STOCK_PORTFOLIO_COL_NAME] = res[us.STOCK]*res[VEST_CUMSUM_COL_NAME]

    # calculate Divest strategy performance, assuming RSUs
    # the calculation assumes the vested shares are sold immediately to purchase market shares
    # we don't account for capital gains, as a negligible amount would be realized if shares are sold immediately at vest
    res[MARKET_SHARES_RSU_COL_NAME] = res[VEST_COL_NAME]*res[us.STOCK]/res[us.MARKET]
    res[MARKET_SHARES_RSU_CUMSUM_COL_NAME] = res[MARKET_SHARES_RSU_COL_NAME].cumsum()
    res[MARKET_PORTFOLIO_RSU_COL_NAME] = res[us.MARKET]*res[MARKET_SHARES_RSU_CUMSUM_COL_NAME]

    # calculate Divest strategy performance, assuming Cash award
    # its assumed that a certain amount is sold to cover for taxes
    res[CASH_VEST_CUMSUM_COL_NAME] = res[CASH_VEST_COL_NAME].cumsum()
    res[MARKET_SHARES_CASH_COL_NAME] = res[CASH_VEST_COL_NAME]/res[us.MARKET]
    res[MARKET_SHARES_CASH_CUMSUM_COL_NAME] = res[MARKET_SHARES_CASH_COL_NAME].cumsum()
    res[MARKET_PORTFOLIO_CASH_COL_NAME] = res[us.MARKET]*res[MARKET_SHARES_CASH_CUMSUM_COL_NAME]

    # limit values to 2 dec places
    res = res.round(2)

    try:
        file_name = 'results.csv'
        file_path = _get_absolute_path(file_name)
        res.to_csv(file_path, index=False)
    except PermissionError:
        print(f"Error: Unable to update {file_path}.\n")

    return res

def plot_results(res):
    STOCK_PORTFOLIO_LABEL = 'Hold Strategy'
    MARKET_PORTFOLIO_RSU_LABEL = 'Divest Strategy'
    MARKET_PORTFOLIO_CASH_LABEL = 'Cash Strategy'

    plt.figure(figsize=(12, 8))
    plt.plot(res['Date'], res[STOCK_PORTFOLIO_COL_NAME], label=STOCK_PORTFOLIO_LABEL)
    plt.plot(res['Date'], res[MARKET_PORTFOLIO_RSU_COL_NAME], label=MARKET_PORTFOLIO_RSU_LABEL)
    plt.plot(res['Date'], res[MARKET_PORTFOLIO_CASH_COL_NAME], label=MARKET_PORTFOLIO_CASH_LABEL)

    # Formatting
    plt.xlabel('Date')
    plt.ylabel('Portfolio Value ($)')
    plt.title('Portfolio Values for Different Strategies Over Time')
    plt.legend()
    plt.grid(True)

    header_text = f"""
    {STOCK_PORTFOLIO_LABEL}:
    {MARKET_PORTFOLIO_RSU_LABEL}:
    {MARKET_PORTFOLIO_CASH_LABEL}:
    """

    # $ chars are escaped since Matplotlib interprets $xyz$ as math text
    annotation_text = f"""
    No \\${us.STOCK} RSUs sold except what is sold to cover at vest. 
    \\${us.STOCK} RSUs sold immediately upon vest and reinvested into \\${us.MARKET}.
    Assumes grants are accepted as cash vs. RSUs; cash vests are immediately invested into \\${us.MARKET}.
    """

    plt.tight_layout(rect=[0, 0.075, 1, 1]) # extra bottom space for annotations

    plt.figtext(0.15, 0, header_text, ha='right', fontsize=10, style='oblique')
    plt.figtext(0.155, 0, annotation_text, ha='left', fontsize=10)
    
    try:
        file_name = 'results.png'
        file_path = _get_absolute_path(file_name)
        plt.savefig(file_path, bbox_inches='tight') # the kwarg ensures annotation texts are included
    except PermissionError:
        print(f"Error: Unable to update {file_path}.\n")
        
    return plt

def get_summary_table(res):
    # Portfolio values
    latest_data = res.iloc[-1]
    hold_strategy = latest_data[STOCK_PORTFOLIO_COL_NAME]
    divest_strategy = latest_data[MARKET_PORTFOLIO_RSU_COL_NAME]
    cash_strategy = latest_data[MARKET_PORTFOLIO_CASH_COL_NAME]

    # Calculate differences
    divest_diff = divest_strategy - hold_strategy
    cash_diff = cash_strategy - hold_strategy

    # Prepare data for tabulation
    data = [
        ["Hold Strategy", f"${hold_strategy:,.2f}", "-"],
        ["Divest Strategy", f"${divest_strategy:,.2f}", f"{"-" if divest_diff < 0 else ''}${abs(divest_diff):,.2f}"],
        ["Cash Strategy", f"${cash_strategy:,.2f}", f"{"-" if cash_diff < 0 else ''}${abs(cash_diff):,.2f}"]
    ]

    # Print formatted table
    print(f"Analysis results based on latest available price for ${us.STOCK} (${latest_data[us.STOCK]}):\n")
    table = tabulate(data, headers=["Strategy", "Portfolio Value", "Difference"], tablefmt="grid")
    
    return table