# Data Quality Log

Source: City of Chicago Building Permits (data.cityofchicago.org, dataset ydr8-5enu),
downloaded November 4, 2026. 852,143 permits, 117 columns.

| Issue | Rows affected | How it was handled |
|---|---|---|
| IDs with an `N` prefix (e.g. `N2886972`) | 53,153 | Stored `permit_id` as text instead of integer |
| Missing application date | 349 | Allowed `application_date_key` to be NULL |
| Issue date before application date | 81 | Set `processing_days` to NULL for these permits |
| Community area coded as `0` (unknown) | 134 | Set to NULL; excluded from neighborhood analysis |
| Reported cost missing | 38,519 | Left as NULL |
| Reported cost of $0 | 21,120 | Kept; excluded from cost analysis |
| Negative reported cost | 1 | Kept in database; excluded from cost analysis |
| Reported cost over $1 billion (max $10B, median $5,000) | 5 | Kept in database; treated as likely entry errors in analysis |
| Paid fee components vs. `SUBTOTAL_PAID` | 0 mismatches | Verified, then dropped the redundant subtotal columns |
| Money stored as text (`$7,500.00`) | All rows | Stripped `$` and commas, stored as DECIMAL |
| Dates stored as text (`MM/DD/YYYY`) | All rows | Parsed and linked to `dim_date` |
| Contacts stored in 15 wide column slots | All rows | Unpivoted into `dim_contact` and `bridge_permit_contact` |
| Owner contacts (often private individuals) | 589,154 entries | Excluded for privacy |
| License numbers prefixed to contractor names (`PL058130279-LONE STAR PLUMBING`) | 8,679 | Stripped the prefix |
| Same contact listed twice on one permit | 682 | Removed duplicates |
| State written as `ILL` | Not counted | Mapped to `IL` |
| Zip codes with trailing dashes (`60025-`) | Not counted | Kept the first five digits |
| Misspelled cities (`MERRIVILLE`, `PARKRIDGE`) | Not yet measured | Open item |
