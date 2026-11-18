# Review findings

This is a page-by-page review of the original dashboard, in the order the problems matter. Figures come from DAX queries against the model, not from reading the visuals.

## 1. Numbers that were wrong or misleading

**Safety score was summed.** The Driver page card showed "Sum of Safety Score: 3.511K", the total of 46 drivers' scores. An `Average Safety Score` measure (76.3) already existed in the model but was not used.

**Driver rankings rewarded driving less.** Four drivers completed 374 to 395 trips each; the other 42 completed 192 to 234. Ranked on raw counts, the busiest drivers topped the harsh-braking and late-delivery charts. Ranked per 100 trips:

| | Raw count rank | Per-trip rank |
|---|---|---|
| Lisa Hensley, harsh braking | 2nd (107 events) | 8th (27.1 per 100 trips) |
| Lisa Hensley, late deliveries | joint 1st (40) | 8th (10.1%) |
| Brittany Farmer, harsh braking | 3rd (77) | 1st (36.2 per 100 trips) |
| Ethan Adams, late deliveries | 3rd (35) | 1st (17.5%) |

**Dual-axis cost trend.** Fuel (about $70K to $90K a month) and maintenance (about $10K to $20K a month) were drawn as overlapping areas on separate axes. Where the areas crossed, maintenance appeared to cost more than fuel. Across the period, fuel is 84.5% of operating cost.

**Zero instead of blank.** Measures such as km/L used `DIVIDE(x, y, 0)`. A truck with no fuel records would score 0 km/L and top a "least efficient" chart. They now use `DIVIDE(x, y)`, which returns blank.

**Driver data has no dates.** `DriverPerformance` is one row per driver for the whole period and has no link to the date table. A date filter on the page would silently do nothing. The rebuilt Drivers page has no date filter and says why.

## 2. Data issues worth raising

- **Reused fuel coupons.** 56 coupon numbers appear on two fuel records each, always on different trucks and dates. In a real fleet this calls for a check with the fuel desk.
- **Coverage gap.** 4 of the 50 trucks have no driver record.
- **Driver-truck mismatch.** About 19% of fuel records (1,929 of 10,318) show a driver on a truck other than the one the driver table assigns them. This is fine if drivers rotate, but it should be confirmed.
- **Fuel cost rounding.** Litres x pump rate comes to $393.20 less than the recorded fuel cost, which is 0.02%.

Checks that passed: unique record IDs in both logs; every distance equals end odometer minus start odometer; preventive + corrective = total jobs; driver trips equal the number of fuel records.

## 3. Design

| Area | Original | Rebuilt |
|---|---|---|
| Theme | Black page, navy header, white cards | Light grey page, white cards, navy header strip |
| Number formats | `1.91480M`, `1.357K` (days), `119.3581K` (hours), `10.318K` (counts) | `$1.91M`, `1,357`, `10,318` |
| Colour | Different colour per bar (priorities, routes, drivers) | One colour per meaning |
| Long lists | All 50 trucks / 46 drivers in scrolling charts | Top or bottom 10, with a full scorecard table |
| Priority chart | Alphabetical order, random colours | Low > Medium > High > Critical; High and Critical highlighted |
| Monthly maintenance | Smoothed line (implies values between months) | Straight stacked columns, preventive vs corrective |
| Fuel by route | 8 near-identical bars of litres | Fuel cost per km by route |
| Layout faults | Driver slicer cut off under the header; donut labels overlapping; duplicate "Total Fuel Cost" card | Fixed |
| Story | No text | One insight line per page, driven by DAX so it updates with the filters |
