
#### TODO

1.  TODO - Find out why ARN commmissions are only 3/11/17 and beyond.
2.  TODO - Find out why so much PH commission is still pending.

#### PH - Delayed and approved commissions

``` sql
-- TODO - resolve long delayed payments
-- Pending commissions include long delays
select
  metric_day,
  sum(publisher_commission) as pending_commission
from
(
  select distinct
    metric_day,
    p.conversion_id,
    p.outbound_id,
    p.publisher_commission,
    p.conversion_status
  from 
    goseek_partner.public.view_ph_pending p
  where 
    not exists
    (
      select *
      from 
        goseek_partner.public.view_ph_approved a
      where 
        a.conversion_id = p.conversion_id
     )
)
group by 1
order by 1
```

``` sql
-- Compare outstanding pending payments to approved.
select 
  metric_day,
  sum(publisher_commission) as approved_commission
from 
  goseek_partner.public.view_ph_approved a
group by 1
order by 1
```

``` r
names(delayed) <- names(delayed) %>%
  tolower() %>%
  gsub('_| ', '.', .)
names(approved) <- names(approved) %>%
  tolower() %>%
  gsub('_| ', '.', .)
delayed <- delayed %>%
  mutate(metric.day = ymd(metric.day))
approved <- approved %>%
  mutate(metric.day = ymd(metric.day))

formattable(
  approved %>% 
    left_join(delayed, by=c('metric.day')) %>%
    mutate(
      metric.day = ymd(metric.day),
      year = year(metric.day),
      month = month(metric.day)) %>%
    group_by(year, month) %>%
    summarise(
      pending.commission = sum(pending.commission),
      approved.commission = sum(approved.commission)) %>%
    mutate(
      pct.delayed = percent(
        pending.commission / 
          (pending.commission + approved.commission)),
      pending.commission = currency(pending.commission, digits = 0),
      approved.commission = currency(approved.commission, digits = 0))
)
```

<table class="table table-condensed">
<thead>
<tr>
<th style="text-align:right;">
year
</th>
<th style="text-align:right;">
month
</th>
<th style="text-align:right;">
pending.commission
</th>
<th style="text-align:right;">
approved.commission
</th>
<th style="text-align:right;">
pct.delayed
</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:right;">
2017
</td>
<td style="text-align:right;">
2
</td>
<td style="text-align:right;">
$11,020
</td>
<td style="text-align:right;">
$7,456
</td>
<td style="text-align:right;">
59.65%
</td>
</tr>
<tr>
<td style="text-align:right;">
2017
</td>
<td style="text-align:right;">
3
</td>
<td style="text-align:right;">
$14,627
</td>
<td style="text-align:right;">
$26,694
</td>
<td style="text-align:right;">
35.40%
</td>
</tr>
<tr>
<td style="text-align:right;">
2017
</td>
<td style="text-align:right;">
4
</td>
<td style="text-align:right;">
$14,043
</td>
<td style="text-align:right;">
$31,082
</td>
<td style="text-align:right;">
31.12%
</td>
</tr>
<tr>
<td style="text-align:right;">
2017
</td>
<td style="text-align:right;">
5
</td>
<td style="text-align:right;">
$14,194
</td>
<td style="text-align:right;">
$42,895
</td>
<td style="text-align:right;">
24.86%
</td>
</tr>
<tr>
<td style="text-align:right;">
2017
</td>
<td style="text-align:right;">
6
</td>
<td style="text-align:right;">
$21,518
</td>
<td style="text-align:right;">
$35,882
</td>
<td style="text-align:right;">
37.49%
</td>
</tr>
<tr>
<td style="text-align:right;">
2017
</td>
<td style="text-align:right;">
7
</td>
<td style="text-align:right;">
$3,946
</td>
<td style="text-align:right;">
$5,288
</td>
<td style="text-align:right;">
42.73%
</td>
</tr>
</tbody>
</table>
``` r
currency.formatter <- function(x) {
  currency(x, digits = 0)  
}
ggplot(
  data = delayed, 
  mapping = aes(x = metric.day, y = pending.commission)) + 
  geom_point(alpha = .3) + 
  stat_smooth(method = 'loess') +
  labs(
    title = 'Still-pending commission from Performance Horizon',
    x = 'Day',
    y = 'Pending commission'
  ) +
  theme(
    axis.title.x = element_blank(),
    axis.text.x = element_blank(),
    axis.ticks.x = element_blank()
  ) +
  scale_y_continuous(labels = currency.formatter) 
```

![](revenue-analysis_files/figure-markdown_github/delayed.daily-1.png)

#### Snaptravel

<table class="table table-condensed">
<thead>
<tr>
<th style="text-align:right;">
year
</th>
<th style="text-align:right;">
month
</th>
<th style="text-align:right;">
commission
</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:right;">
2017
</td>
<td style="text-align:right;">
1
</td>
<td style="text-align:right;">
$2,548
</td>
</tr>
<tr>
<td style="text-align:right;">
2017
</td>
<td style="text-align:right;">
2
</td>
<td style="text-align:right;">
$9,578
</td>
</tr>
<tr>
<td style="text-align:right;">
2017
</td>
<td style="text-align:right;">
3
</td>
<td style="text-align:right;">
$14,851
</td>
</tr>
<tr>
<td style="text-align:right;">
2017
</td>
<td style="text-align:right;">
4
</td>
<td style="text-align:right;">
$13,923
</td>
</tr>
<tr>
<td style="text-align:right;">
2017
</td>
<td style="text-align:right;">
5
</td>
<td style="text-align:right;">
$16,392
</td>
</tr>
<tr>
<td style="text-align:right;">
2017
</td>
<td style="text-align:right;">
6
</td>
<td style="text-align:right;">
$17,728
</td>
</tr>
<tr>
<td style="text-align:right;">
2017
</td>
<td style="text-align:right;">
7
</td>
<td style="text-align:right;">
$2,096
</td>
</tr>
</tbody>
</table>
#### ARN

``` r
names(arn) <- names(arn) %>%
  tolower() %>%
  gsub('_| ', '.', .)
formattable(
  arn %>%
    mutate(
      year = year(metric.day),
      month = month(metric.day)
    ) %>%
    group_by(year, month) %>%
    summarise(
      commission = currency(sum(commission), digits = 0)
    )
)  
```

<table class="table table-condensed">
<thead>
<tr>
<th style="text-align:right;">
year
</th>
<th style="text-align:right;">
month
</th>
<th style="text-align:right;">
commission
</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:right;">
2017
</td>
<td style="text-align:right;">
3
</td>
<td style="text-align:right;">
$561
</td>
</tr>
<tr>
<td style="text-align:right;">
2017
</td>
<td style="text-align:right;">
4
</td>
<td style="text-align:right;">
$1,808
</td>
</tr>
<tr>
<td style="text-align:right;">
2017
</td>
<td style="text-align:right;">
5
</td>
<td style="text-align:right;">
$1,007
</td>
</tr>
<tr>
<td style="text-align:right;">
2017
</td>
<td style="text-align:right;">
6
</td>
<td style="text-align:right;">
$919
</td>
</tr>
<tr>
<td style="text-align:right;">
2017
</td>
<td style="text-align:right;">
7
</td>
<td style="text-align:right;">
$108
</td>
</tr>
</tbody>
</table>
