# Investing Strategies

A tool to evaluate the performance of different strategies (Hold, Divest, Cash) for employee RSU (Restricted Stock Unit) grants.

## Strategies Explained

- **Hold**:  
  RSUs are held long-term. Shares are only sold as needed to cover taxes at vesting.

- **Divest**:  
  RSUs are immediately sold upon vesting, with proceeds reinvested into a broad-market index fund.

- **Cash**:  
  Grants are assumed as immediate cash compensation rather than RSUs. This cash is immediately invested into a broad-market fund.

## Setup & Configuration

**1. Configure Settings and Grants:**

All settings are managed in `user_settings.yaml`.  
Grant specifications are handled as such:  

### Grant Definitions  
Fields align with information typically found in E-Trade grant documentation.

#### Field Descriptions:

- **grant_reason** *(optional)*:  
  Reference for user convenience (e.g., "new hire," "promotion").

- **grant_value** *(numeric)*:  
  Total dollar amount of the grant.

- **grant_date** *(MM/DD/YYYY)*:  
  Date for the calendar month used to calculate RSU quantity based on the average closing stock price.  
  **Note**: Usually differs from the actual `grant_date` in E-Trade documentation.

  > RSUs are estimated as:  
  > `RSUs = grant_value / (avg. closing price during grant_month)`

- **vest_qty** *(numeric)*:  
  Total number of RSUs vested to date.

- **sellable_qty** *(numeric)*:  
  Number of vested RSUs available for sale after tax withholding.

  > Used together with `vest_qty` to estimate the sell-to-cover withholding rate.

- **vest_plan** *(structure)*:  
  Defines the quarterly vesting schedule percentages for each year (`y0` to `y4`):

  ```yaml
  vest_plan:
    y0: [a, b, c, d]  # Grant year (matches grant_month calendar year)
    y1: [e, f, g, h]  # Year after grant year
    # ... up to y4
  ```
  
  Each list `[a, b, c, d]` represents percentages vesting on the four quarterly vest dates of the specified year, as per the defined `VEST_SCHEDULE`.

---

**Example:**

```yaml
grants:
  - grant_reason: "Example Grant"
    grant_value: 100000
    grant_date: "01/01/2024"
    vest_qty: 1000
    sellable_qty: 600
    vest_plan:
      y0: [0, 0, 0, 0]
      y1: [0.25, 0.0625, 0.0625, 0.0625]
      y2: [0.0625, 0.0625, 0.0625, 0.0625]
      y3: [0.0625, 0.0625, 0.0625, 0.0625]
      y4: [0.0625, 0, 0, 0]
```