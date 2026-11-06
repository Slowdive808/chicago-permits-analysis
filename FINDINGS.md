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