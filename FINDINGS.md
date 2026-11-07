   # Findings

   ## 1. How fast are Chicago's fast-track permit programs?

   From 2006 to 2023, the city's two fast-track programs issued most permits the same day:
   87% of Easy permits and 55% of Express permits, compared with 35% of standard permits.
   Median times hide a long tail in Express: its median was 0 days, but the slowest 10%
   took 25 days or more, and its average was 23.7 days.

   In late 2023 the city ended the Easy Permit program and moved that work into Express.
   Express volume jumped from about 12,500 permits in 2023 to over 21,000 in 2024, and its
   median rose from 0 to 2 to 3 days.

   Standard permits changed far more. Within the same permit types, medians rose sharply after
   2023: new construction from 3 to 52 days, renovation from 5 to 51, and signs from 10 to 35.
   Some simple permit types (scaffolding) moved to Express, but that shift is too small to
   explain the jump.

   **Caveat:** a 3-day median for new construction before 2024 is implausibly fast, which
   suggests the old system may have started the clock later in the process. The post-2023
   increase may partly reflect a change in measurement rather than slower reviews.

   Queries: `sql/01_processing_time_by_program.sql`

   ## 2. Which neighborhoods are growing and shrinking?

Permit activity fell citywide, from about 48,500 permits in 2019 to about 32,000 in 2025.
Comparing three-year averages, the city dropped 27.6% from 2015-2017 to 2023-2025.

Against that baseline, most of the South and Southwest Side held up better than the city.
Ashburn (+34%) and Calumet Heights (+17%) grew outright. The busiest North Side and
near-downtown areas fell faster than the city: Logan Square (-43%), Avondale (-41%),
West Town (-39%), and the Loop (-37%).

Single-year changes are noisy at neighborhood scale. Lincoln Square led all areas from
2024 to 2025 (+25%) but is down 19% over the longer period, so the three-year comparison
is the more reliable measure.

Permit counts and dollar value tell different stories. From 2021 to 2025, Hyde Park ranked
35th by permit count but 8th by reported value, and Woodlawn 36th and 9th, driven by large
institutional projects such as a medical center and the presidential center museum at
Jackson Park. Before cleaning, typos on rooftop solar permits (up to $872 million each)
pushed several areas into the top 10 by value. Removing 91 implausible fast-track costs
removed six areas from the top 20.

Queries: `sql/02_community_area_trends.sql`. Cost cleaning: `db/views.sql`.