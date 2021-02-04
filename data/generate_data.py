import json
import pickle


with open("data/drinks_dict.txt") as f:
    content = f.read()

data = json.loads(content.replace("'", '"').replace("\n", '')) 

# Generation of database of drinks
drinks_db = {}
count = 0

# Generation of user goals
drinks_user_goals = []
drinks_user_goals.append({'request_slots': {'DRINK': 'UNK', 'SIZE': 'UNK', 'TEMP': 'UNK'}, 'diaact': 'request', 'inform_slots': {}})


for drink_ind, drink in enumerate(data["DRINK"]):
    drinks_user_goals.append({'request_slots': {'SIZE': 'UNK', 'TEMP': 'UNK'}, 'diaact': 'request', 'inform_slots': {'DRINK': drink}})
    
    for temp_ind, temp in enumerate(data["TEMP"]):
        if data["Temps"][drink_ind][temp_ind] == '1':

            drinks_user_goals.append({'request_slots': {'SIZE': 'UNK', 'DRINK': 'UNK'}, 'diaact': 'request', 'inform_slots': {'TEMP': temp}})
            drinks_user_goals.append({'request_slots': {'SIZE': 'UNK'}, 'diaact': 'request', 'inform_slots': {'TEMP': temp, 'DRINK': drink}})

            for size_ind, size in enumerate(data["SIZE"]):
                if data["Sizes"][drink_ind][size_ind] == '1':

                    drinks_db[count] = {'DRINK': drink, 'SIZE': size, 'TEMP': temp}
                    count += 1
                    drinks_user_goals.append({'request_slots': {}, 'diaact': 'request', 'inform_slots': {'DRINK': drink,
                                            'SIZE': size, 'TEMP': temp}})
                    drinks_user_goals.append({'request_slots': {'TEMP': 'UNK'}, 'diaact': 'request', 'inform_slots': {'SIZE': size, 'DRINK': drink}})
       
        

# write to pickle files
with open('data/drinks_db.pkl', 'wb') as handle:
    pickle.dump(drinks_db, handle, protocol=pickle.HIGHEST_PROTOCOL)
with open('data/drinks_user_goals.pkl', 'wb') as handle2:
    pickle.dump(drinks_user_goals, handle2, protocol=pickle.HIGHEST_PROTOCOL)
with open('data/drinks_dict.pkl', 'wb') as handle3:
    pickle.dump(data, handle3, protocol=pickle.HIGHEST_PROTOCOL)

# write to text files
with open("data/drinks_db.txt", "w") as f:
    for key, value in drinks_db.items():
        print(key, value)
        f.write('{}: {}'.format(key, value) + "\n")
with open("data/drinks_user_goals.txt", 'w') as output:
    for row in drinks_user_goals:
        output.write(str(row) + '\n')
print("Nice job")