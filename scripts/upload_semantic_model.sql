-- Upload the semantic model to a Snowflake stage for Cortex Analyst access.
-- Run this after creating the database and tables.

CREATE STAGE IF NOT EXISTS PAAS_COMMAND_CENTER.PUBLIC.SEMANTIC_MODELS
  DIRECTORY = (ENABLE = TRUE);

-- Then from your local machine:
-- snowsql -q "PUT file://semantic_model/paas_command_center.yaml @PAAS_COMMAND_CENTER.PUBLIC.SEMANTIC_MODELS AUTO_COMPRESS=FALSE OVERWRITE=TRUE;"
-- Or via SnowCLI:
-- snow stage copy semantic_model/paas_command_center.yaml @PAAS_COMMAND_CENTER.PUBLIC.SEMANTIC_MODELS --overwrite
