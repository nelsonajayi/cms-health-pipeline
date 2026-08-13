/*
  Model: stg_hospital_readmissions
  Source: CMS_HEALTH.RAW.RAW_HOSPITAL_READMISSIONS
  
  Cleans raw hospital readmissions data:
  - Casts string numbers to numeric types
  - Standardizes text fields
  - Filters suppressed/null records
*/

with source as (
    select * from {{ source('cms_raw', 'raw_hospital_readmissions') }}
),

renamed as (
    select
        facility_id,
        upper(trim(facility_name))                      as facility_name,
        upper(trim(state))                              as state,
        trim(measure_name)                              as measure_name,

        -- TRY_CAST returns NULL for non-numeric values like 'N/A' or 'Too Few to Report'
        try_cast(number_of_discharges as integer)       as number_of_discharges,
        try_cast(excess_readmission_ratio as float)     as excess_readmission_ratio,
        try_cast(predicted_readmission_rate as float)   as predicted_readmission_rate,
        try_cast(expected_readmission_rate as float)    as expected_readmission_rate,
        try_cast(number_of_readmissions as integer)     as number_of_readmissions,
        try_cast(start_date as date)                    as measurement_start_date,
        try_cast(end_date as date)                      as measurement_end_date,
        footnote,
        _loaded_at,
        current_timestamp()                             as _transformed_at

    from source
),

cleaned as (
    select *
    from renamed
    where
        facility_id is not null
        and facility_name is not null
        and state is not null
        and excess_readmission_ratio is not null
)

select * from cleaned