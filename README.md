# Investing Strategies

A tool to evaluate the performance of different strategies (Hold, Divest, Cash) for employee RSU (Restricted Stock Unit) grants.

## Strategies Explained

- **Hold**: RSUs are held long-term. Shares are only sold as needed to cover taxes at vesting.

- **Divest**: RSUs are immediately sold upon vesting, with proceeds reinvested into a broad-market index fund.

- **Cash**: Grants are assumed as immediate cash compensation rather than RSUs. This cash is immediately invested into a broad-market fund.

## Setup & Configuration

All settings are managed in `user_settings.yaml`.  

### Global Settings
These settings apply to the analysis engine and data pull behavior:

- `STOCK`: The RSU stock ticker (e.g., `TSLA`)
- `MARKET`: The comparison market index ticker (e.g., `VTI`)
- `DESIRED_TICKER_ATTRIBUTE`: Usually `Close`, defines which price attribute is used for historical data
- `ANALYSIS_START_DATE`: Analysis window start date (in `YYYY-MM-DD`). Must precede the first vest for accuracy.
- `WORK_END_DATE`: Last date for vesting eligibility, if applicable. Set as `None` otherwise.

--- 

### Vest Schedule
`VEST_SCHEDULE` defines the [month, date] on which vesting may occur in any year.

```yaml
VEST_SCHEDULE:
  - [3, 5]
  - [6, 5]
  - [9, 5]
  - [12, 5]
```

---

### Grant Definitions  
Fields align with information typically found in E-Trade grant documentation.  
You may define vesting logic in one of two ways:
- By explicitly specifying a `vest_plan`, or
- By supplying a simplified `vest_model`, which will auto-generate the full vest_plan.

Only one of these two (`vest_plan` or `vest_model`) should be defined per grant.

#### Field Descriptions:

- `grant_reason` *(optional)*:  
  Reference for user convenience (e.g., "new hire," "promotion").

- `grant_value` *(numeric)*:  
  Total dollar amount of the grant.

- `grant_date` *(YYYY-MM-DD)*:  
  Date for the calendar month used to calculate RSU quantity based on the average closing stock price.  
  Note: This usually differs from the actual `grant_date` in E-Trade documentation.

  > RSUs are estimated as:  
  > `RSUs = grant_value / (avg. closing price during grant_month)`

- `vest_qty` *(numeric)*:  
  Total number of RSUs vested to date.

- `sellable_qty` *(numeric)*:  
  Number of vested RSUs available for sale after tax withholding.

  > Used together with `vest_qty` to estimate the sell-to-cover withholding rate.

#### Option 1: Manual `vest_plan`

```yaml
vest_plan:
  y0: [a, b, c, d]
  y1: [e, f, g, h]
  ...
```

Each key `y0`, `y1`, ..., represents a year of vesting relative to the grant date year.  
Each value is a list of percentages for each defined vest date in the year (based on `VEST_SCHEDULE`).

##### Validation Rules:
- Percentages must sum to exactly `1.0` across all years.
- Each year must contain as many entries as `VEST_SCHEDULE`. Use `0` values to pad as needed (e.g., for cliffs).

---

#### Option 2: Auto-generated `vest_plan` via `vest_model`

```yaml
vest_model:
  duration_years: 4
  cliff_skipped_vests: 1
  cliff_vest_qty: 0.25
```

When `vest_model` is supplied, the tool will automatically generate a `vest_plan` according to the following:

- `duration_years`: Total number of years the grant vests over.
- `cliff_skipped_vests` *(optional)*: Number of vest dates (from `VEST_SCHEDULE`) intentionally skipped due to a cliff.
- `cliff_vest_qty` *(optional)*: Proportion of the total RSUs that vests immediately after the cliff period.
- Any vesting dates in year 0 that occur before the `grant_date` are automatically excluded.

The remainder of the grant is evenly divided across the remaining vest events.

---

#### Example: Manual `vest_plan`

```yaml
grants:
  - grant_reason: "Example Grant"
    grant_value: 100000
    grant_date: "2024-01-01"
    vest_qty: 1000
    sellable_qty: 600
    vest_plan:
      y0: [0, 0, 0, 0]
      y1: [0.25, 0.0625, 0.0625, 0.0625]
      y2: [0.0625, 0.0625, 0.0625, 0.0625]
      y3: [0.0625, 0.0625, 0.0625, 0.0625]
      y4: [0.0625, 0, 0, 0]
```

#### Example: Auto-generated via `vest_model`

```yaml
grants:
  - grant_reason: "New Hire Grant"
    grant_value: 80000
    grant_date: "2023-06-19"
    vest_qty: 120
    sellable_qty: 72
    vest_model:
      duration_years: 4
      cliff_skipped_vests: 1
      cliff_vest_qty: 0.25
```