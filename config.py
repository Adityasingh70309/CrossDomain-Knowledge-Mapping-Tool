from decouple import config

# --- Neo4j Database Configuration ---
# These lines read the values from your .env file.
# If a value is missing, it will raise an error, except for the default.
NEO4J_URI = config("NEO4J_URI", default="bolt://localhost:7687")
NEO4J_USER = config("NEO4J_USER", default="neo4j")

# For the password, we don't set a default.
# This ensures the app will fail to start if the password isn't set in your .env file.
NEO4J_PASSWORD = config("NEO4J_PASSWORD")

