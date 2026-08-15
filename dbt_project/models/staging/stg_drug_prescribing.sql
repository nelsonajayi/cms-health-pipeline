/*
  Model: stg_drug_prescribing
  Source: CMS_HEALTH.RAW.RAW_DRUG_PRESCRIBING
  
  Note: Column names match the 2022 CMS Part D CSV format
  (PRSCRBR_NPI, BRND_NAME, GNRC_NAME, TOT_CLMS, TOT_DRUG_CST etc.)
  Different years may have different column names.
*/

with source as (
    select * from {{ source('cms_raw', 'raw_drug_prescribing') }}
),

renamed as (
    select
        prscrbr_npi                                     as provider_npi,
        upper(trim(prscrbr_last_org_name))              as provider_last_name,
        upper(trim(prscrbr_first_name))                 as provider_first_name,
        upper(trim(prscrbr_city))                       as provider_city,
        upper(trim(prscrbr_state_abrvtn))               as provider_state,
        trim(prscrbr_type)                              as provider_specialty,
        trim(brnd_name)                                 as brand_drug_name,
        trim(gnrc_name)                                 as generic_drug_name,

        try_cast(tot_clms as integer)                   as total_claim_count,
        try_cast(tot_30day_fills as float)              as total_30day_fills,
        try_cast(tot_drug_cst as float)                 as total_drug_cost,
        try_cast(tot_day_suply as integer)              as total_day_supply,
        try_cast(tot_benes as integer)                  as beneficiary_count,

        -- Calculated field
        case
            when try_cast(tot_clms as integer) > 0
            then try_cast(tot_drug_cst as float)
                 / try_cast(tot_clms as integer)
            else null
        end                                             as cost_per_claim

    from source
),

cleaned as (
    select *
    from renamed
    where
        provider_npi is not null
        and brand_drug_name is not null
        and total_claim_count is not null
        and total_drug_cost is not null
)

select * from cleaned