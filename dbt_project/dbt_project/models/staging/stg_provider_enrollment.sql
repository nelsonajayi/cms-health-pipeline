/*
  Model: stg_provider_enrollment
  Source: CMS_HEALTH.RAW.RAW_PROVIDER_ENROLLMENT
  
  Note: Column names match the 2026 CMS Provider Enrollment CSV format
*/

with source as (
    select * from {{ source('cms_raw', 'raw_provider_enrollment') }}
),

renamed as (
    select
        npi                                             as provider_npi,
        multiple_npi_flag,
        pecos_asct_cntl_id,
        enrlmt_id,
        provider_type_cd,
        trim(provider_type_desc)                        as provider_type_desc,
        upper(trim(state_cd))                           as state_cd,
        upper(trim(first_name))                         as first_name,
        trim(mdl_name)                                  as middle_name,
        upper(trim(last_name))                          as last_name,
        upper(trim(org_name))                           as org_name,
        _loaded_at,
        current_timestamp()                             as _transformed_at

    from source
),

cleaned as (
    select *
    from renamed
    where
        provider_npi is not null
        and state_cd is not null
)

select * from cleaned