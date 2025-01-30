import pandas as pd
import os
import re
import inspect
from collections import namedtuple

print("Starting the ingredients normalization process...")

# Create ArgSpec since it's removed in newer Python versions
ArgSpec = namedtuple('ArgSpec', ['args', 'varargs', 'keywords', 'defaults'])

# Add compatibility for getargspec
def getargspec_compatible(func):
    """Compatible get argument specifications for function in Python 2/3."""
    if hasattr(inspect, 'getfullargspec'):
        args = inspect.getfullargspec(func)
        return ArgSpec(
            args=args.args,
            varargs=args.varargs,
            keywords=args.varkw,
            defaults=args.defaults
        )
    else:
        return inspect.getargspec(func)

# Monkey patch inspect.getargspec
inspect.getargspec = getargspec_compatible

print("Initializing pymorphy2...")
import pymorphy2

# Initialize pymorphy2 analyzer
morph = pymorphy2.MorphAnalyzer()
print("Pymorphy2 initialized successfully")

# Get the relative path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
database_path = os.path.join(parent_dir, 'data', 'database.xlsx')
output_path = os.path.join(parent_dir, 'data', 'database_normalized.xlsx')

print(f"Reading from: {database_path}")
print(f"Will save to: {output_path}")

# Common units of measurement to remove
units = {'г', 'гр', 'грамм', 'кг', 'мг', 'л', 'мл', 'литр', 'литров', 'ст',
         'ст.л', 'ст.л.', 'ложка', 'ложки', 'стакан', 'стакана', 'стаканов',
         'шт', 'шт.', 'штук', 'штуки', 'по вкусу', 'щепотка', 'щепотки', 'чайн',
         'ч.л.', 'ч.л', 'чл', 'столовая', 'чайная'}

def normalize_ingredients(ingredients_str):
    # Remove '\xa0' symbols and normalize whitespace
    ingredients_str = ingredients_str.replace('\xa0', ' ').strip()

    # Split ingredients string into list
    ingredients_list = [ing.strip().lower() for ing in ingredients_str.split(',')]

    normalized_ingredients = []
    for ingredient in ingredients_list:
        # Remove numbers and their variations (1, 1.5, ½, etc.)
        ingredient = re.sub(r'[\d.,/½¼¾]+\s*', '', ingredient)

        # Split into words
        words = ingredient.split()

        # Filter out units of measurement
        content_words = [word for word in words if word not in units]

        if content_words:
            # Get the first content word (usually the main ingredient)
            main_word = content_words[0]

            # Get normal form using pymorphy2
            parsed = morph.parse(main_word)[0]
            normal_form = parsed.normal_form

            if normal_form and normal_form not in normalized_ingredients:  # Avoid duplicates
                normalized_ingredients.append(normal_form)

    # Join back into string
    return ', '.join(normalized_ingredients)

# Read the Excel file
print("Reading Excel file...")
df = pd.read_excel(database_path)
print(f"Found {len(df)} rows in the database")

# Apply normalization to ingredients column
print("Starting ingredients normalization...")
df['normalized_ingredients'] = df['ingredients'].apply(normalize_ingredients)
print("Normalization completed")

# Save the updated dataframe back to Excel
print("Saving results to Excel...")
df.to_excel(output_path, index=False)
print(f"Results saved to: {output_path}")
print("Process completed successfully!")
