/*
  Model: mart_hospital_readmissions
  
  State and condition level summary of hospital readmission performance.
  One row per state per medical condition.
  
  Business questions answered:
  - Which states have the highest excess readmission ratios?
  - Which conditions drive the most readmissions?
*/

with readmissions as (
    select * from {{ ref('stg_hospital_readmissions') }}
),

state_condition_summary as (
    select
        state,
        measure_name,
        count(distinct facility_id)                             as hospital_count,
        avg(excess_readmission_ratio)                           as avg_excess_readmission_ratio,
        min(excess_readmission_ratio)                           as min_excess_readmission_ratio,
        max(excess_readmission_ratio)                           as max_excess_readmission_ratio,
        count(case when excess_readmission_ratio > 1.0 then 1 end)
                                                                as hospitals_above_expected,
        count(case when excess_readmission_ratio < 1.0 then 1 end)
                                                                as hospitals_below_expected,
        sum(number_of_readmissions)                             as total_readmissions,
        sum(number_of_discharges)                               as total_discharges,
        round(
            sum(number_of_readmissions) * 100.0
            / nullif(sum(number_of_discharges), 0),
            2
        )                                                       as readmission_rate_pct,
        case
            when avg(excess_readmission_ratio) >= 1.1 then 'HIGH RISK'
            when avg(excess_readmission_ratio) >= 1.0 then 'ABOVE EXPECTED'
            when avg(excess_readmission_ratio) >= 0.9 then 'BELOW EXPECTED'
            else 'LOW RISK'
        end                                                     as state_risk_category,
        min(measurement_start_date)                             as earliest_measurement,
        max(measurement_end_date)                               as latest_measurement

    from readmissions
    group by state, measure_name
)

select
    *,
    rank() over (
        partition by measure_name
        order by avg_excess_readmission_ratio desc
    )                                                           as state_rank_by_condition

from state_condition_summary
order by avg_excess_readmission_ratio desc