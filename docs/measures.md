# Measures

Generated from the model (`pbip/Fleet Dashboard.SemanticModel/definition/tables/_Measures_.tmdl`).
All measures live in the `_Measures_` table, grouped into display folders.

## Fleet

### Total Fleet Trucks
Format: `#,0`

```dax
DISTINCTCOUNT(DimTruck[Truck ID])
```

### Total Recorded Operating Cost
Format: `\$#,0`

```dax
[Total Fuel Cost] +
[Total Maintenance Cost]
```

### Operating Cost by Category
Format: `\$#,0`

```dax
SWITCH(
    SELECTEDVALUE('Cost Category'[Cost Type]),
    "Fuel", [Total Fuel Cost],
    "Maintenance", [Total Maintenance Cost]
)
```

### Total Operating Cost by Truck
Format: `\$#,0`

```dax
[Total Fuel Cost] + [Total Maintenance Cost]
```

### Total Operating Cost
Fuel cost + maintenance cost (USD)
Format: `\$#,0`

```dax
[Total Fuel Cost] + [Total Maintenance Cost]
```

### Operating Cost per KM
Format: `\$0.000`

```dax
DIVIDE([Total Operating Cost], [Total Distance])
```

### Fuel Share of Operating Cost
Format: `0.0%`

```dax
DIVIDE([Total Fuel Cost], [Total Operating Cost])
```

## Fuel

### Total Fuel Cost
Format: `\$#,0`

```dax
SUM(Fuel[Fuel Cost USD])
```

### Total Fuel Litres
Format: `#,0`

```dax
SUM(Fuel[Fill / Lit])
```

### Total Distance
Format: `#,0`

```dax
SUM(Fuel[Dist Covered])
```

### Average Fuel Efficiency
Kilometres per litre (total km / total litres)
Format: `0.00`

```dax
DIVIDE([Total Distance], [Total Fuel Litres])
```

### Average Fuel Price
Format: `\$0.00`

```dax
DIVIDE([Total Fuel Cost], [Total Fuel Litres])
```

### Fuel Transactions
Format: `#,0`

```dax
COUNTROWS(Fuel)
```

### Trucks Fuelled
Format: `#,0`

```dax
DISTINCTCOUNT(Fuel[Truck ID])
```

### Fuel Cost per KM
Format: `\$0.000`

```dax
DIVIDE([Total Fuel Cost], [Total Distance])
```

## Maintenance

### Total Maintenance Cost
Format: `\$#,0`

```dax
SUM(Maintenance[Cost_USD])
```

### Total Maintenance Jobs
Format: `#,0`

```dax
COUNTROWS(Maintenance)
```

### Total Downtime
Downtime in days
Format: `#,0.0`

```dax
SUM(Maintenance[Downtime_Days])
```

### Preventive Jobs
Format: `#,0`

```dax
CALCULATE(
    [Total Maintenance Jobs],
    Maintenance[Maintenance Type] = "Preventive"
)
```

### Corrective Jobs
Format: `#,0`

```dax
CALCULATE(
    [Total Maintenance Jobs],
    Maintenance[Maintenance Type] = "Corrective"
)
```

### Critical Jobs
Format: `#,0`

```dax
CALCULATE(
    [Total Maintenance Jobs],
    Maintenance[Priority] = "Critical"
)
```

### Average Maintenance Cost
Format: `\$#,0`

```dax
DIVIDE([Total Maintenance Cost], [Total Maintenance Jobs])
```

### Average Downtime
Average downtime days per job
Format: `0.0`

```dax
DIVIDE([Total Downtime], [Total Maintenance Jobs])
```

### Preventive Maintenance %
Format: `0.0%`

```dax
DIVIDE([Preventive Jobs], [Total Maintenance Jobs])
```

### Maintenance Cost per KM
Format: `\$0.000`

```dax
DIVIDE([Total Maintenance Cost], [Total Distance])
```

## Driver

### Average Safety Score
Format: `0.0`

```dax
AVERAGE(DriverPerformance[Safety Score])
```

### Total Trips
Format: `#,0`

```dax
SUM(DriverPerformance[Trips Completed])
```

### Total Late Deliveries
Format: `#,0`

```dax
SUM(DriverPerformance[Late Deliveries])
```

### Total Harsh Braking
Format: `#,0`

```dax
SUM(DriverPerformance[Harsh Braking Events])
```

### Total Over Speeding
Format: `#,0`

```dax
SUM(DriverPerformance[Over-Speeding Events])
```

### Excessive Idling Hours
Format: `#,0`

```dax
DIVIDE(SUM(DriverPerformance[Excessive Idling Mins]), 60)
```

### Total Hours Driven
Format: `#,0`

```dax
SUM(DriverPerformance[Total Hours Driven])
```

### Late Delivery Rate
Format: `0.0%`

```dax
DIVIDE([Total Late Deliveries], [Total Trips])
```

### Drivers
Format: `#,0`

```dax
DISTINCTCOUNT(DriverPerformance[Driver Name])
```

### Harsh Braking per 100 Trips
Harsh braking events per 100 completed trips, so drivers with more trips are compared fairly
Format: `0.0`

```dax
DIVIDE([Total Harsh Braking], [Total Trips]) * 100
```

### Over-Speeding per 100 Trips
Format: `0.0`

```dax
DIVIDE([Total Over Speeding], [Total Trips]) * 100
```

### Idling % of Hours Driven
Format: `0.0%`

```dax
DIVIDE([Excessive Idling Hours], [Total Hours Driven])
```

## Checks

### Trucks with Driver Data
Format: `#,0`

```dax
DISTINCTCOUNT(DriverPerformance[Truck ID])
```

### Trucks Missing Driver Data
Format: `#,0`

```dax
[Total Fleet Trucks] -
[Trucks with Driver Data]
```

### Coupon Use Count
How many fuel records carry this coupon number (all dates, all trucks)
Format: `#,0`

```dax
CALCULATE(COUNTROWS(Fuel), ALLEXCEPT(Fuel, Fuel[Coupon #]))
```

### Duplicate Coupon Numbers
Format: `#,0`

```dax
COUNTROWS(FILTER(VALUES(Fuel[Coupon #]), [Coupon Use Count] > 1)) + 0
```

### Check - Fuel Rows
Format: `#,0`

```dax
COUNTROWS(Fuel)
```

### Check - Fuel Duplicate SN
Format: `#,0`

```dax
COUNTROWS(Fuel) - DISTINCTCOUNT(Fuel[SN])
```

### Check - Maintenance Rows
Format: `#,0`

```dax
COUNTROWS(Maintenance)
```

### Check - Maintenance Duplicate SN
Format: `#,0`

```dax
COUNTROWS(Maintenance) - DISTINCTCOUNT(Maintenance[SN])
```

### Check - Invalid ODO Rows
Format: `#,0`

```dax
COUNTROWS(FILTER(Fuel, Fuel[ODO Validation] <> "Valid" || Fuel[Dist Covered] <> Fuel[End ODO] - Fuel[Start ODO])) + 0
```

### Check - Fuel Cost vs Litres x Rate
Difference between recalculated fuel cost (litres x pump rate) and recorded cost
Format: `\$#,0;-\$#,0;\$0`

```dax
SUMX(Fuel, Fuel[Fill / Lit] * Fuel[Pump Rate USD]) - SUM(Fuel[Fuel Cost USD])
```

### Check - Jobs Reconcile
Format: `#,0`

```dax
[Total Maintenance Jobs] - [Preventive Jobs] - [Corrective Jobs]
```

### Check - Driver Trips vs Fuel Records
Format: `#,0`

```dax
CALCULATE([Total Trips], REMOVEFILTERS()) - CALCULATE(COUNTROWS(Fuel), REMOVEFILTERS())
```

## Insights

### Insight - Overview

```dax
VAR topTruck = TOPN(1, VALUES(DimTruck[Truck ID]), [Total Operating Cost], DESC)
VAR topName = MAXX(topTruck, DimTruck[Truck ID])
VAR topCost = MAXX(topTruck, [Total Operating Cost])
RETURN "Fuel is " & FORMAT([Fuel Share of Operating Cost], "0%") & " of operating cost, so fuel efficiency is the biggest cost lever. The fleet spends " & FORMAT([Operating Cost per KM], "$0.000") & " per km. Highest-cost truck: " & topName & " (" & FORMAT(topCost, "$#,0") & ")."
```

### Insight - Fuel

```dax
VAR t = TOPN(1, FILTER(VALUES(DimTruck[Truck ID]), NOT ISBLANK([Average Fuel Efficiency])), [Average Fuel Efficiency], ASC)
VAR worst = MAXX(t, DimTruck[Truck ID])
VAR worstKmL = MAXX(t, [Average Fuel Efficiency])
RETURN "Fleet average is " & FORMAT([Average Fuel Efficiency], "0.00") & " km/L. Least efficient truck: " & worst & " at " & FORMAT(worstKmL, "0.00") & " km/L. " & FORMAT([Duplicate Coupon Numbers], "#,0") & " coupon numbers appear on more than one fill and should be checked."
```

### Insight - Maintenance

```dax
VAR top5 = TOPN(5, VALUES(DimTruck[Truck ID]), [Total Maintenance Cost], DESC)
VAR top5Cost = CALCULATE([Total Maintenance Cost], top5)
VAR share5 = DIVIDE(top5Cost, [Total Maintenance Cost])
RETURN "Preventive work is " & FORMAT([Preventive Maintenance %], "0%") & " of jobs. The 5 costliest trucks take " & FORMAT(share5, "0%") & " of maintenance spend. " & FORMAT([Critical Jobs], "#,0") & " critical jobs; each job costs " & FORMAT([Average Downtime], "0.0") & " days of downtime on average."
```

### Insight - Driver

```dax
VAR t = TOPN(1, FILTER(VALUES(DimDriver[Driver Name]), NOT ISBLANK([Harsh Braking per 100 Trips])), [Harsh Braking per 100 Trips], DESC)
VAR nm = MAXX(t, DimDriver[Driver Name])
VAR v = MAXX(t, [Harsh Braking per 100 Trips])
RETURN "Rankings are per 100 trips: a few drivers did about twice the trips, so raw counts overstate their risk. Highest harsh-braking rate: " & nm & " (" & FORMAT(v, "0.0") & " per 100 trips vs fleet " & FORMAT([Harsh Braking per 100 Trips], "0.0") & ")."
```
