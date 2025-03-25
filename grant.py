import math
import datetime
from datetime import datetime as dt
import yfinance as yf
from config import UserSettings

us = UserSettings()

class Grant:
    def __init__(self, grant_attrs):
        for key, value in grant_attrs.items():
            setattr(self, key, value)
            
        self.grant_date = dt.strptime(self.grant_date, "%m/%d/%Y").date()

        self._input_validation()

        self.grant_qty = self.get_grant_qty()
        self.vest_rate = self.sellable_qty/self.vest_qty # this is used to estimate the witholding rate for taxes

    def _input_validation(self):
        total_vesting = 0
        for year, vests in self.vest_plan.items():
            if len(vests) != len(us.VEST_SCHEDULE):
                raise ValueError(f"Vest plan for {self.grant_reason} grant must have {len(us.VEST_SCHEDULE)} vesting fractions")
            
            total_vesting += sum(vests)

        if total_vesting != 1:
            raise ValueError(f"Vest proportions for {self.grant_reason} grant must sum to 100%")
        
    def get_grant_qty(self):
        """
        Calculates grant_qty based on grant_value and average close price for grant month
        """

        start_date = datetime.date(self.grant_date.year, self.grant_date.month, 1)

        # end_date is set to the first date of the subsequent month
        # this ensures the Close price of the last day of the month is included
        end_date = datetime.date(
            self.grant_date.year + 1 if self.grant_date.month == 12 else self.grant_date.year,  # handles year if year rollover 
            1 if self.grant_date.month == 12 else self.grant_date.month + 1,                    # handles month year rollover
            1)                                                                                  # first day of the month

        stock = yf.Ticker(us.STOCK).history(
            start=start_date, 
            end=end_date) \
            .reset_index()
        
        avg_close = stock["Close"].mean()
        
        return math.ceil(self.grant_value/avg_close)