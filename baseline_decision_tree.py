import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split

data = open("activity_data.csv")
data.readline()

user_ids = set()
user_id_booked = {}
user_id_devices = {}
user_id_countries = {}
device_ids = {}
country_ids = {}

# generate IDs on the fly
n_devices = 0
n_countries = 0

# first pass for filtering user IDs
for line in data:
    record = line.strip().split(',')
    user_id = record[1]
    user_action = record[-1]
    device = record[3]
    country = record[2]

    # device and country to ID
    if device not in device_ids:
        device_ids[device] = n_devices
        n_devices += 1
    if country not in country_ids:
        country_ids[country] = n_countries
        n_countries += 1

    # get device and country IDs
    device_id = device_ids[device]
    country_id = country_ids[country]

    user_ids.add(user_id)

    # device
    if user_id not in user_id_devices:
        user_id_devices[user_id] = set([device_id])
    else:
        user_id_devices[user_id].add(device_id)

    # country
    if user_id not in user_id_countries:
        user_id_countries[user_id] = set([country_id])
    else:
        user_id_countries[user_id].add(country_id)

filtered_user_ids = set([user_id for user_id in user_ids if (len(user_id_devices[user_id]) == 1 and len(user_id_countries[user_id]) == 1)])

# reopen dataset
data.close()
data = open("activity_data.csv")
data.readline()

# build inputs and labels
input_data = {}
for i, line in enumerate(data):
    record = line.strip().split(',')
    _, user_id, country, device, _, action = record

    # get IDs
    device_id = device_ids[device]
    country_id = country_ids[country]

    # filter
    if user_id not in filtered_user_ids:
        continue

    # add new user_id if not present
    if user_id not in input_data:
        input_data[user_id] = {"country": country_id, "device": device_id, "n_views": 0, "n_website_click": 0, "n_price_click": 0, "booked": False}

    # get data associated with user_id, and update the action count
    user_data = input_data[user_id]
    if action == "view":
        user_data["n_views"] += 1
    elif action == "hotel_website_click":
        user_data["n_website_click"] += 1
    elif action == "price_click":
        user_data["n_price_click"] += 1
    elif action == "booking":
        user_data["booked"] = True

input_df = pd.DataFrame.from_dict(input_data, orient="index")
features = input_df.columns[:5]
labels = input_df.columns[5]

train, test = train_test_split(input_df)

model = XGBClassifier()
model.fit(train[features], train[labels])

print(model.score(test[features], test[labels]))
