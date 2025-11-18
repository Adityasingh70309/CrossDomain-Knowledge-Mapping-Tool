import csv
import random

print("Starting data generation...")

# --- Define Entities by Type ---
CROPS = ["Wheat", "Rice", "Maize (Corn)", "Soybeans", "Barley", "Potatoes", "Cassava", "Sorghum", "Grapes", "Apples", "Coffee", "Cotton", "Sugarcane"]
PRACTICES = ["No-tillage farming", "Cover cropping", "Crop rotation", "Drip irrigation", "Flood irrigation", "Contour plowing", "Terracing", "Integrated pest management (IPM)", "Organic farming", "Agroforestry", "Precision agriculture"]
CLIMATE_EFFECTS = ["Drought", "Increased flooding", "Rising temperatures", "Heatwaves", "Soil salinization", "Extreme weather events", "Sea level rise", "Ocean acidification", "Altered precipitation patterns", "Reduced chill hours"]
EMISSIONS = ["Methane (CH4)", "Nitrous Oxide (N2O)", "Carbon Dioxide (CO2)", "Greenhouse Gases (GHG)"]
RESOURCES = ["Freshwater aquifers", "Groundwater", "Arable land", "River systems", "Glacial meltwater"]
SOIL_TYPES = ["Loam", "Clay soil", "Sandy soil", "Peat soil", "Chalky soil", "Silty soil"]
OUTCOMES = ["Crop yield", "Food security", "Soil health", "Soil erosion", "Water scarcity", "Biodiversity loss", "Farm profitability", "Pest outbreaks", "Desertification"]
MITIGATIONS = ["Carbon sequestration", "Biofuel production", "Water conservation", "Genetic modification (GM)", "Sustainable intensification"]

# --- All Entities Mapped to Types ---
ENTITY_MAP = {
    "Crop": CROPS,
    "Practice": PRACTICES,
    "Climate Effect": CLIMATE_EFFECTS,
    "Emission": EMISSIONS,
    "Resource": RESOURCES,
    "Soil": SOIL_TYPES,
    "Outcome": OUTCOMES,
    "Climate Mitigation": MITIGATIONS,
}

# --- Define Relation Templates (SourceType, Relation, TargetType, Weight) ---
# We use weights to make some relationships appear more frequently
RELATION_TEMPLATES = [
    # Climate > Agriculture
    ("Climate Effect", "REDUCES", "Crop", 15),
    ("Climate Effect", "DECREASES", "Crop yield", 15),
    ("Climate Effect", "INCREASES", "Water scarcity", 10),
    ("Climate Effect", "THREATENS", "Food security", 10),
    ("Climate Effect", "WORSENS", "Soil erosion", 10),
    ("Climate Effect", "AFFECTS", "Soil", 10),
    ("Climate Effect", "INCREASES", "Pest outbreaks", 8),
    ("Rising temperatures", "REDUCES", "Crop", 10),
    ("Drought", "CAUSES", "Water scarcity", 10),

    # Agriculture > Climate
    ("Practice", "REDUCES", "Emission", 12),
    ("Practice", "INCREASES", "Emission", 10),
    ("Practice", "IMPROVES", "Climate Mitigation", 12),
    ("No-tillage farming", "INCREASES", "Carbon sequestration", 10),
    ("Livestock", "PRODUCES", "Methane (CH4)", 10),
    ("Nitrogen Fertilizers", "RELEASES", "Nitrous Oxide (N2O)", 10),
    ("Deforestation (for farming)", "INCREASES", "Carbon Dioxide (CO2)", 10),

    # Internal Agriculture Relations
    ("Practice", "IMPROVES", "Soil health", 15),
    ("Practice", "REDUCES", "Soil erosion", 10),
    ("Practice", "AFFECTS", "Crop yield", 10),
    ("Pesticides", "REDUCES", "Biodiversity loss", 5),
    ("Drip irrigation", "CONSERVES", "Resource", 10),
    ("Crop", "REQUIRES", "Soil", 8),
    ("Crop", "REQUIRES", "Resource", 8),
    
    # Internal Climate Relations
    ("Emission", "CAUSES", "Climate Effect", 15),
    ("Methane (CH4)", "CAUSES", "Rising temperatures", 10),
    ("CO2 Levels", "CAUSES", "Ocean acidification", 5),
]

# Create a weighted list of relation templates
weighted_relations = []
for (src, rel, tgt, weight) in RELATION_TEMPLATES:
    weighted_relations.extend([(src, rel, tgt)] * weight)

# --- Generation Function ---
def generate_csv(filename="agri_climate_relations_1000.csv", lines=1000):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write Header
        writer.writerow(["source", "target", "relation", "source_type", "target_type"])
        
        generated_lines = 0
        while generated_lines < lines:
            # 1. Pick a random relation template
            source_type_key, relation, target_type_key = random.choice(weighted_relations)

            # 2. Get the specific entity lists for those types
            # If the key is a specific entity (like "Drought"), use it directly
            if source_type_key in ENTITY_MAP:
                source_list = ENTITY_MAP[source_type_key]
                source = random.choice(source_list)
            else:
                source = source_type_key # It's a specific entity
                source_type_key = "Specific Entity" # Placeholder type

            if target_type_key in ENTITY_MAP:
                target_list = ENTITY_MAP[target_type_key]
                target = random.choice(target_list)
            else:
                target = target_type_key # It's a specific entity
                target_type_key = "Specific Entity" # Placeholder type

            # 3. Resolve the "Specific Entity" placeholders
            if source_type_key == "Specific Entity":
                for key, values in ENTITY_MAP.items():
                    if source in values:
                        source_type_key = key
                        break
            
            if target_type_key == "Specific Entity":
                for key, values in ENTITY_MAP.items():
                    if target in values:
                        target_type_key = key
                        break
            
            # Avoid self-loops (e.g., "Wheat" RELATES "Wheat")
            if source == target:
                continue

            # 4. Write the row
            writer.writerow([source, target, relation, source_type_key, target_type_key])
            generated_lines += 1

    print(f"✅ Successfully generated {generated_lines} lines in {filename}")

# --- Run the Script ---
if __name__ == "__main__":
    generate_csv(lines=1000)