-- Seed initial external nutrition data sources.

INSERT INTO data_sources (
  code,
  name,
  country,
  publisher,
  source_url,
  license_name,
  license_url,
  attribution_text,
  version
) VALUES
  (
    'NEVO',
    'NEVO online version 2025/9.0',
    'Netherlands',
    'RIVM - National Institute for Public Health and the Environment',
    'https://www.rivm.nl/en/dutch-food-composition-database/use-of-nevo-online/request-dataset',
    'NEVO online conditions of use',
    'https://www.rivm.nl/documenten/conditions-for-use-of-nevo-online-version',
    'Based on data from NEVO online version 2025/9.0, RIVM, Bilthoven.',
    '2025/9.0'
  ),
  (
    'ANSES_CIQUAL',
    'Ciqual French food composition table 2025',
    'France',
    'ANSES / Ciqual',
    'https://ciqual.anses.fr/cms/en/2025-anses-ciqual-table',
    'Creative Commons Attribution 4.0 International; Etalab Open License 2.0',
    'https://zenodo.org/records/17550133',
    'Anses. 2025. Ciqual French food composition table.',
    '2025'
  )
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  country = VALUES(country),
  publisher = VALUES(publisher),
  source_url = VALUES(source_url),
  license_name = VALUES(license_name),
  license_url = VALUES(license_url),
  attribution_text = VALUES(attribution_text),
  version = VALUES(version);
