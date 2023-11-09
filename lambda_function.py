import pandas as pd
import googlemaps
from datetime import datetime
import math
import requests
import os
from constants import GOOGLE_API_KEY_ID

def load_isd_locations():
    ## Load isd station location data
    isd_history='https://www.ncei.noaa.gov/pub/data/noaa/isd-history.txt'
    data = pd.read_fwf(isd_history, skiprows=20)
    return data

def get_city_geodata_via_geocoding_api(citi_name):
    ## Get geometry data via Google map API
    gmaps = googlemaps.Client(key=GOOGLE_API_KEY_ID)
    geocode_result = gmaps.geocode(citi_name)
    # print(geocode_result)
    return geocode_result

def get_closest_stns_in_isd_data(geocode_result):
    data = load_isd_locations()

    ## Find closest station in isd stn location file
    latlon=geocode_result[0]['geometry']['location']

    cloest_stns = data[(data['LAT']>math.floor(latlon['lat'])) & (data['LAT']<math.ceil(latlon['lat'])) & (data['LON']>math.floor(latlon['lng'])) & (data['LON']<math.ceil(latlon['lng']))]
    cloest_stns['Distance to Spot A (km)'] = cloest_stns.apply(lambda row: haversine_distance(latlon['lat'], latlon['lng'], row['LAT'], row['LON']), axis=1)
    stn_list = cloest_stns[cloest_stns['Distance to Spot A (km)']<5].sort_values(['Distance to Spot A (km)'])

    return stn_list

# Function to calculate the Haversine distance between two points
def haversine_distance(lat1, lon1, lat2, lon2):
    # Radius of the Earth in kilometers
    earth_radius = 6371.0

    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Haversine formula
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = earth_radius * c

    return distance

def get_isd_data(stn_list, data_year):
    ## Get ISD data of the closest station
    stn_USAF = stn_list.iloc[0]['USAF']
    stn_WBAN = stn_list.iloc[0]['WBAN']
    print(stn_list)

    isd_file_daily=f'https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/{data_year}/{stn_USAF}{stn_WBAN}.csv'
    data = pd.read_csv(isd_file_daily, header=0)
    return data

def lambda_handler(event, context):
    data_year = 2013
    if event is not None:
        citi_name = event['cityName']
    else:
        citi_name = 'taipei'    

    geocode_result = get_city_geodata_via_geocoding_api(citi_name)
    stn_list = get_closest_stns_in_isd_data(geocode_result)
    isd_data = get_isd_data(stn_list, data_year)

    return isd_data['TEMP'].to_json()
