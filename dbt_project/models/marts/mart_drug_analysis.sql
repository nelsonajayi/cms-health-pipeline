/*
  Model: mart_drug_analysis
  
  National drug prescribing cost analysis.
  One row per drug.
  
  Business questions answered:
  - What are the highest-cost drugs nationally?
  - Which drugs have the most prescribers?
*/

with prescribing as (
    select * from {{ ref('stg_drug_prescribing') }}
),

drug_national_summary as (
    select
        brand_drug_name,
        generic_drug_name,
        count(distinct provider_npi)                    as unique_prescribers,
        sum(total_claim_count)                          as national_claim_count,
        sum(beneficiary_count)                          as national_beneficiary_count,
        sum(total_drug_cost)                            as national_total_cost,
        avg(cost_per_claim)                             as avg_cost_per_claim,
        round(
            sum(total_drug_cost)
            / nullif(sum(total_claim_count), 0),
            2
        )                                               as national_avg_cost_per_claim,
        count(distinct provider_state)                  as states_with_prescribing

    from prescribing
    group by brand_drug_name, generic_drug_name
),

ranked as (
    select
        *,
        rank() over (order by national_total_cost desc)     as cost_rank,
        rank() over (order by national_claim_count desc)    as volume_rank

    from drug_national_summary
)

select * from ranked
where national_claim_count >= 100
order by national_total_cost desc