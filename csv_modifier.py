import pandas as pd

# Load the CSV file
file_path = './All_CrimeWatch_Data_20240925.csv'  # Replace with the correct file path
crime_data = pd.read_csv(file_path)

# Function to extract Latitude and Longitude from Location column
def extract_lat_long(location):
    if pd.isna(location):
        return pd.NA, pd.NA
    try:
        # Extracting coordinates
        location = location.replace("POINT (", "").replace(")", "")
        longitude, latitude = location.split()
        return float(latitude), float(longitude)
    except Exception as e:
        return pd.NA, pd.NA

# Apply the extraction function to the Location column
crime_data[['Latitude', 'Longitude']] = crime_data['Location'].apply(lambda loc: extract_lat_long(loc)).apply(pd.Series)

# Function to convert DateTime to Date Quarter
def get_date_quarter(date_time):
    if pd.isna(date_time):
        return pd.NA
    try:
        date_time = pd.to_datetime(date_time, format="%m/%d/%Y %I:%M:%S %p")
        quarter = (date_time.month - 1) // 3 + 1
        return f"{date_time.year} Q{quarter}"
    except Exception as e:
        return pd.NA

# Apply the Date Quarter function to the DateTime column
crime_data['Date Quarter'] = crime_data['DateTime'].apply(get_date_quarter)

# Save the updated DataFrame with new columns to a new CSV
output_file_path = './Modified_Updated_CrimeWatch_Data.csv'  # Replace with the desired output path
crime_data.to_csv(output_file_path, index=False)

print(f"Updated CSV saved to {output_file_path}")