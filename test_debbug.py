car = {
  "brand": {"American":"Ford","German":"BMW"},
  "model": {"Oldi":"Mustang", "New":"i8"},
}

for value in car.values():
    for key2, value2 in value.items():
        print(value2)