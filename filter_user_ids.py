import csv

WITH_PRICES = False

hotel_data = open("hotel_data_with_prices.csv")
hotel_data.readline()
reader = csv.reader(hotel_data)

no_star_rating = set()
for record in reader:
    hotel_id, _, _, star_rating, bubble_score, reviews, _, _, _ = record[:9]
    if not star_rating or not bubble_score or int(reviews) == 0:
        no_star_rating.add(hotel_id)
        continue

    if WITH_PRICES:
        zipcode, price = record[-2], record[-1]
        if not zipcode or int(float(price)) == 0:
            no_star_rating.add(hotel_id)

data = open("activity_data.csv")
data.readline()

user_ids = set()
user_id_booking_count = {}
user_id_devices = {}
user_id_countries = {}
user_id_no_rating = {}
user_id_booking_count = {}

for line in data:
    record = line.strip().split(',')
    user_id = record[1]
    user_action = record[-1]
    device = record[3]
    country = record[2]
    hotel = record[-2]

    if user_id not in user_ids:
        user_ids.add(user_id)
        user_id_no_rating[user_id] = False
        user_id_booking_count[user_id] = 0

    # device
    if user_id not in user_id_devices:
        user_id_devices[user_id] = set([device])
    else:
        user_id_devices[user_id].add(device)

    # country
    if user_id not in user_id_countries:
        user_id_countries[user_id] = set([country])
    else:
        user_id_countries[user_id].add(country)

    # hotel
    if hotel in no_star_rating:
        user_id_no_rating[user_id] = True

    # booking
    if user_action == "booking":
        user_id_booking_count[user_id] += 1

data.close()
hotel_data.close()

# total_users = len(user_ids)
filtered_users = [user_id for user_id in user_ids if (len(user_id_devices[user_id]) == 1 and len(user_id_countries[user_id]) == 1 and not user_id_no_rating[user_id] and user_id_booking_count[user_id] == 1)]

# print(total_users)
# print(filtered_users)
# print(filtered_users/total_users)

output_file = open("filtered_user_ids.txt", 'w')
for user_id in filtered_users:
    output_file.write("%s\n" % user_id)
output_file.close()
