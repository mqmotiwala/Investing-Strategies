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
        
        self._input_validation()
        self._calculate_grant_qty()
        
        if hasattr(self, "vest_model"):
            self._create_vest_plan()

        self.first_vest_date = self._set_first_vest_date()
        self.vest_rate = self.sellable_qty/self.vest_qty # this is used to estimate the witholding rate for taxes

    def _input_validation(self):
        # general
        try:
            self.grant_date = dt.strptime(self.grant_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Invalid date format for grant_date: {self.grant_date}. Use yyyy-mm-dd format.")

        if not hasattr(self, "vest_plan") and not hasattr(self, "vest_model"):
            raise ValueError(f"{self.grant_reason} grant does not define vesting logic.")
        
        # vest_model specific input_validation
        if hasattr(self, "vest_model"): 
            if not isinstance(self.vest_model.get("duration_years"), int) or self.vest_model["duration_years"] < 1:
                raise ValueError("duration_years must be an integer ≥ 1")
            
            cliff_skipped_vests = self.vest_model.get("cliff_skipped_vests", 0)
            if not isinstance(cliff_skipped_vests, int) or cliff_skipped_vests < 0:
                raise ValueError("cliff_skipped_vests must be a non-negative integer")

            cliff_vest_qty = self.vest_model.get("cliff_vest_qty", 0)
            if not (0 <= cliff_vest_qty <= 1):
                raise ValueError("cliff_vest_qty must be between 0 and 1")
        
        # if no vest_model, vest_plan has been manually supplied
        # do specific input validation for this case
        if not hasattr(self, "vest_model") and hasattr(self, "vest_plan"): 
            total_vesting = 0
            for year, vests in self.vest_plan.items():
                if len(vests) != len(us.VEST_SCHEDULE):
                    raise ValueError(f"Vest plan for {self.grant_reason} grant must have {len(us.VEST_SCHEDULE)} vesting fractions")
                
                if int(year) < self.grant_date.year:
                    raise ValueError(f"Vest plan for {self.grant_reason} grant must not have a year prior to grant_date")
                
                total_vesting += sum(vests)

            if total_vesting != 1:
                raise ValueError(f"Vest proportions for {self.grant_reason} grant must sum to 100%")

    def _calculate_grant_qty(self):
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
        
        self.grant_qty = math.ceil(self.grant_value/avg_close)
    
    def _create_vest_plan(self):
        # missed_vests refers to the vest dates, as defined in VEST_SCHEDULE, that are missed
        # because the grant was issued after those dates 
        missed_vests = sum(
            1 for month, day in us.VEST_SCHEDULE
            if datetime.date(self.grant_date.year, month, day) < self.grant_date
        )
        
        missed = [0]*missed_vests

        # cliff_skipped_vests refers to the vest instances skipped due to the cliff
        cliff_skipped_vests = self.vest_model.get("cliff_skipped_vests", 0)
        cliff_vest_qty = self.vest_model.get("cliff_vest_qty", 0)
        cliffed = [0]*cliff_skipped_vests

        # accounts for case where, after the cliff, there is a one-time large vest
        cliff = [cliff_vest_qty] if cliff_vest_qty else []

        # handles remaining equitably distributed vests, aka standard_vests
        vests_per_year = len(us.VEST_SCHEDULE)
        total_num_vests = self.vest_model["duration_years"]*vests_per_year
        standard_vest_qty = 1/total_num_vests
        remaining_num_vests = int((1-cliff_vest_qty)/standard_vest_qty)
        standard = [standard_vest_qty]*remaining_num_vests

        # vest_qtys is a list of all vest instances
        vest_qtys = missed + cliffed + cliff + standard

        # handles small epsilon corrections
        total = sum(vest_qtys)
        if total != 1.0:
            vest_qtys[-1] += round(1.0 - total, 20)

        self.vest_plan = {}
        for i in range(math.ceil(len(vest_qtys)/vests_per_year)):
            start = i * vests_per_year
            end = start + vests_per_year
            self.vest_plan[self.grant_date.year + i] = vest_qtys[start:end]

    def _set_first_vest_date(self):
        for vest_year, vest_qtys in sorted(self.vest_plan.items()):
            for i, vest_qty in enumerate(vest_qtys):
                if vest_qty > 0:
                    return datetime.date(vest_year, us.VEST_SCHEDULE[i][0], us.VEST_SCHEDULE[i][1])