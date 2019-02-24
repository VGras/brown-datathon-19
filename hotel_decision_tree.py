import pandas as pd
from xgboost import XGBClassifier, XGBRegressor
from sklearn.model_selection import train_test_split
from scipy.stats.mstats import gmean
from numpy import mean
import csv

WITH_PRICES = False

# extract hotel data
hotel_data = open("hotel_data_with_prices.csv")
hotel_data.readline()
reader = csv.reader(hotel_data)

hotel_records = {}

for record in reader:
    hotel_id, _, city_name, stars, bubbles, reviews, _, _, _, zipcode, price = record
    if not stars or not bubbles:
        continue
    hotel_records[hotel_id] = (float(stars), float(bubbles), int(reviews), zipcode, float(price), city_name)

data = open("activity_data.csv")
data.readline()

filtered_user_ids = set([line.strip() for line in open("filtered_user_ids.txt")])

device_ids = {}
country_ids = {}
hotel_type_ids = {}
location_ids = {}
city_name_ids = {}
zipcode_ids = {}

def lookup_id(raw, ids):
    if raw not in ids:
        ids[raw] = len(ids)
    return ids[raw]

# build inputs and labels
input_data = {}
for line in data:
    record = line.strip().split(',')
    _, user_id, country, device, hotel, action = record

    # only take from filtered users list
    if user_id not in filtered_user_ids:
        continue

    # fetch data from hotel table
    stars, bubbles, reviews, zipcode, price, city_name = hotel_records[hotel]

    # convert to IDs
    device_id = lookup_id(device, device_ids)
    country_id = lookup_id(country, country_ids)
    city_name_id = lookup_id(city_name, city_name_ids)
    zipcode_id = lookup_id(zipcode, zipcode_ids)

    # add new user_id record if not present
    if user_id not in input_data:
        input_data[user_id] = {"country": country_id,
                "device": device_id,
                "reviews": [],
                "stars": [],
                "bubbles": [],
                "prices": [],
                "book_star": None,
                "book_loc": None,
                "book_zip": None
            }

    # update user_id record
    user_data = input_data[user_id]
    user_data["reviews"].append(reviews)
    user_data["stars"].append(stars)
    user_data["bubbles"].append(bubbles)
    user_data["prices"].append(price)
    if action == "booking":
        user_data["book_star"] = int(2*stars)
        user_data["book_loc"] = city_name_id
        user_data["book_zip"] = zipcode_id

# reduce data (take averages and mins and maxes)
for user_id, user_data in input_data.items():
    stars, bubbles, reviews, prices = user_data["stars"], user_data["bubbles"], user_data["reviews"], user_data["prices"]

    stars_min, stars_max, stars_avg = min(stars), max(stars), mean(stars)
    bubbles_min, bubbles_max, bubbles_avg = min(bubbles), max(bubbles), mean(bubbles)
    reviews_min, reviews_max, reviews_avg = min(reviews), max(reviews), gmean(reviews)
    prices_min, prices_max, prices_avg = min(prices), max(prices), mean(prices)
    n_hotels = len(stars)

    user_data["stars_min"], user_data["stars_max"], user_data["stars_avg"] = stars_min, stars_max, stars_avg
    user_data["bubbles_min"], user_data["bubbles_max"], user_data["bubbles_avg"] = bubbles_min, bubbles_max, bubbles_avg
    user_data["reviews_min"], user_data["reviews_max"], user_data["reviews_avg"] = reviews_min, reviews_max, reviews_avg
    user_data["prices_min"], user_data["prices_max"], user_data["prices_avg"] = prices_min, prices_max, prices_avg
    user_data["n_hotels"] = n_hotels

    del user_data["reviews"]
    del user_data["stars"]
    del user_data["bubbles"]
    del user_data["prices"]

input_df = pd.DataFrame.from_dict(input_data, orient="index")
features = list(input_df.columns)
features.remove("book_star")
features.remove("book_loc")
features.remove("book_zip")
if not WITH_PRICES:
    features.remove("prices_min")
    features.remove("prices_max")
    features.remove("prices_avg")
#    features.remove("stars_min")
#    features.remove("stars_max")
#    features.remove("stars_avg")
    labels = "book_star"
else:
    labels = "book_zip"


train, test = train_test_split(input_df)

model = XGBClassifier()
model.fit(train[features], train[labels])

# print(model.score(test[features], test[labels]))
print(model.feature_importances_)
print(str(features))

pred = model.predict(test[features])
actual = test[labels]
correct = 0
for i in range(len(test)):
    if abs(pred[i] - actual[i]) <= 1:
        correct += 1
print(correct/len(test))
