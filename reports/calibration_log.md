# Calibration Log

## Iteration 0
- Date: 2026-04-14
- Scenario: baseline_1990_country_a
- Status: initialized

### Initial observations
- Parameters seeded from defaults registry.
- Validation gates all pass in current scaffold model.

### Next calibration actions
1. Wire scenario loading into runtime state initialization.
2. Add tracked objective metrics for inflation, unemployment, debt ratio, trust, and unrest.
3. Run 120-tick baseline and record drift.

## Iteration 1
- Date: 2026-04-14T23:52:28.395403+00:00
- Scenario: baseline_1990_country_a
- Run: 120 ticks
- Price: 169.755058
- Wage: 13323.467102
- Unemployment: 0.000000
- Debt: 218327607756.118927
- Reserves: -59999999034.000000
- Population: 12288000.000000
- Trust: 0.000000
- Legitimacy: 88.000000
- Unrest: 0.000000

## Iteration 2
- Date: 2026-04-15T00:04:33.230961+00:00
- Scenario: baseline_1990_country_a
- Run: 120 ticks
- Price: 169.755058
- Wage: 13323.467102
- Unemployment: 0.000000
- Debt: 194238443215.760040
- Reserves: 72000000000.000000
- Population: 12288000.000000
- Trust: 59.320020
- Legitimacy: 84.400000
- Unrest: 10.763301

### Calibration observations
1. Reserve drift is now bounded and remains positive through 120 ticks.
2. Trust and unrest no longer collapse to hard lower bounds in the baseline run.
3. Debt path is still elevated and remains a priority for further tuning.

## Iteration 3
- Date: 2026-04-15T00:06:39.788788+00:00
- Scenario: baseline_1990_country_a
- Run: 120 ticks
- Price: 169.755058
- Wage: 2090.733408
- Unemployment: 0.045000
- Debt: 194238443215.760040
- Reserves: 72000000000.000000
- Population: 12288000.000000
- Trust: 59.320020
- Legitimacy: 84.400000
- Unrest: 12.113301

### Calibration observations
1. Unemployment floor realism improved; baseline no longer collapses to zero.
2. Reserve path remains stable and positive in the 120-tick baseline.
3. Debt remains elevated and banking-panic wage response is still too extreme.

## Iteration 1
- Date: 2026-04-15T00:12:56.114956+00:00
- Scenario: baseline_1990_country_a
- Run: 120 ticks
- Price: 169.755058
- Wage: 2090.733408
- Unemployment: 0.045000
- Debt: 160613522908.714874
- Reserves: 72000000000.000000
- Population: 12288000.000000
- Trust: 59.310107
- Legitimacy: 80.436580
- Unrest: 29.826717

## Iteration 1
- Date: 2026-04-15T00:19:36.728685+00:00
- Scenario: baseline_1990_country_a
- Run: 120 ticks
- Price: 522.883672
- Wage: 25478.429687
- Unemployment: 0.045000
- Debt: 65078441812.357399
- Reserves: 72000000000.000000
- Population: 12288000.000000
- Trust: 58.969479
- Legitimacy: 0.000000
- Unrest: 48.043272

## Iteration 1
- Date: 2026-04-15T00:20:24.096291+00:00
- Scenario: baseline_1990_country_a
- Run: 120 ticks
- Price: 137.260502
- Wage: 1386.254594
- Unemployment: 0.045000
- Debt: 65078441812.357399
- Reserves: 72000000000.000000
- Population: 12288000.000000
- Trust: 59.236230
- Legitimacy: 79.721589
- Unrest: 29.903329

## Iteration 1
- Date: 2026-04-15T00:27:19.914898+00:00
- Scenario: baseline_1990_country_a
- Run: 120 ticks
- Price: 207.585174
- Wage: 1533.611416
- Unemployment: 0.045000
- Debt: 659240742407.322388
- Reserves: 69025757037.251495
- Population: 12288000.000000
- Trust: 59.082227
- Legitimacy: 72.930836
- Unrest: 31.476414

## Iteration 1
- Date: 2026-04-15T00:28:04.343673+00:00
- Scenario: baseline_1990_country_a
- Run: 120 ticks
- Price: 207.772530
- Wage: 1533.903516
- Unemployment: 0.045000
- Debt: 659289785689.356689
- Reserves: 63010421681.423965
- Population: 12288000.000000
- Trust: 59.081448
- Legitimacy: 72.886725
- Unrest: 31.484749
