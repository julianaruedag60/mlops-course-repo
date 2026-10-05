-- Runs once, when MySQL initializes an empty data volume.
-- Loads data/penguins.csv (mounted read-only in /import) into penguins_raw.
USE penguins;

CREATE TABLE IF NOT EXISTS penguins_raw (
    species           VARCHAR(20),
    island            VARCHAR(20),
    bill_length_mm    DOUBLE,
    bill_depth_mm     DOUBLE,
    flipper_length_mm DOUBLE,
    body_mass_g       DOUBLE,
    sex               VARCHAR(10)
);

LOAD DATA INFILE '/import/penguins.csv'
INTO TABLE penguins_raw
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(species, island, @bill_length_mm, @bill_depth_mm, @flipper_length_mm, @body_mass_g, @sex)
SET bill_length_mm    = NULLIF(@bill_length_mm, ''),
    bill_depth_mm     = NULLIF(@bill_depth_mm, ''),
    flipper_length_mm = NULLIF(@flipper_length_mm, ''),
    body_mass_g       = NULLIF(@body_mass_g, ''),
    sex               = NULLIF(@sex, '');
