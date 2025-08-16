from flask import Flask, request, jsonify, render_template, session
import re
import difflib
import math
import ollama
import os
import urllib.parse
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Needed for session management

# Structured campus data with coordinates
campus_data = {
    "gate": {"lat": 17.05973, "lng": 81.86922, "description": "Main campus entrance"},
    "globe": {"lat": 17.05997, "lng": 81.86928, "description": "Globe monument near entrance"},
    "main block parking": {"lat": 17.05957, "lng": 81.86877, "description": "Parking near main block"},
    "parking 2": {"lat": 17.06213, "lng": 81.86849, "aliases": ["fc"], "description": "Parking near food court"},
    "atm": {"lat": 17.06000, "lng": 81.86913, "description": "ATM machine location"},
    "main block": {"lat": 17.05975, "lng": 81.86875, "description": "Main academic building"},
    "saraswati devi": {"lat": 17.06026, "lng": 81.86875, "description": "Saraswati Devi statue"},
    "amphitheatre": {"lat": 17.06055, "lng": 81.86902, "description": "Open-air amphitheater"},
    "vishwesaraya block": {"lat": 17.06089, "lng": 81.86833, "description": "Engineering department building"},
    "juice shop": {"lat": 17.06146, "lng": 81.86780, "description": "Juice and snack bar"},
    "food stalls": {"lat": 17.06141, "lng": 81.86795, "description": "Street food vendors"},
    "food court": {"lat": 17.06148, "lng": 81.86780, "description": "Main food court area"},
    "Stationery shop": {"lat": 17.06153, "lng": 81.86790, "description": "Stationery and supplies store"},
    "mechanical labs": {"lat": 17.06434, "lng": 81.86786, "description": "Mechanical engineering laboratories"},
    "boys mess": {"lat": 17.06179, "lng": 81.86716, "description": "Boys hostel dining hall"},
    "girls hostel": {"lat": 17.06202, "lng": 81.86674, "description": "Girls accommodation block"},
    "basketball court": {"lat": 17.06213, "lng": 81.86769, "description": "Basketball playing area"},
    "football court": {"lat": 17.06259, "lng": 81.86766, "description": "Football/soccer field"},
    "transport office": {"lat": 17.06040, "lng": 81.86828, "description": "Transport office for bus passes and inquiries"},

    "mining block": {"lat": 17.06284, "lng": 81.86721, "description": "Mining engineering department"},
    "bamboos": {"lat": 17.06223, "lng": 81.86861, "description": "Bamboo garden area"},
    "yummpys": {"lat": 17.06323, "lng": 81.86791, "aliases": ["yummy"], "description": "Yummpy's snack shop"},
    "boys hostel": {"lat": 17.06313, "lng": 81.86563, "description": "Boys accommodation block"},
    "saibaba temple": {"lat": 17.06331, "lng": 81.86706, "description": "Saibaba temple on campus"},
    "pharmacy block": {"lat": 17.06360, "lng": 81.86576, "description": "Pharmacy department building"},
    "library": {"lat": 17.06410, "lng": 81.86618, "description": "Main campus library", "hours": "8AM-10PM"},
    "rk block": {"lat": 17.06426, "lng": 81.86590, "description": "RK academic block"},
    "central food court": {"lat": 17.06459, "lng": 81.86744, "aliases": ["cfc"], "description": "Central dining area"},
    "diploma block": {"lat": 17.06513, "lng": 81.86574, "description": "Diploma studies building"},
    "international boys hostel": {"lat": 17.06584, "lng": 81.86564, "description": "Hostel for international students"},
    "cricket ground": {"lat": 17.06493, "lng": 81.86880, "description": "Cricket playing field"},
    "bus ground": {"lat": 17.06479, "lng": 81.86598, "description": "Bus parking and pickup area"},
    "automobile engineering lab": {"lat": 17.06449, "lng": 81.86969, "description": "Automotive engineering lab"},
    "lakepond": {"lat": 17.06875, "lng": 81.86769, "description": "Lake and pond area"},
    "cv raman block": {"lat": 17.06846, "lng": 81.86727, "description": "CV Raman science block"},
    "spicehub": {"lat": 17.06896, "lng": 81.86838, "description": "SpiceHub food court"},
    "giet parking 3": {"lat": 17.06936, "lng": 81.86837, "description": "Parking area near SpiceHub"},
    "degree block": {"lat": 17.07090, "lng": 81.86853, "description": "Degree programs building"},
    "events ground": {"lat": 17.07154, "lng": 81.86830, "description": "Events and festival ground"},
    "lake": {"lat": 17.07146, "lng": 81.86981, "description": "Main campus lake"},
    
    # New locations
    "guest": {"lat": 17.07323, "lng": 81.86631, "description": "Guest house for visitors"},
    "farm": {"lat": 17.07226, "lng": 81.86741, "description": "College farm area"},
    "nursery": {"lat": 17.06052, "lng": 81.86946, "description": "Plant nursery"},
    "zigzag": {"lat": 17.06300, "lng": 81.86775, "description": "Zigzag sitting area"},
    "sitting place 1": {"lat": 17.06092, "lng": 81.86921, "description": "Sitting area near amphitheatre"},
    "sitting place 2": {"lat": 17.06265, "lng": 81.86929, "description": "Sitting area near mining block"},
    "transport office": {"lat": 17.06042, "lng": 81.86829, "description": "Transport office for bus passes and inquiries"},
    "med plus": {"lat": 17.05994, "lng": 81.86895, "description": "Med plus medicine shop and checkup center"},
    "admission block": {"lat": 17.05971, "lng": 81.86871, "description": "Admission and administrative block"},
    
    # Restrooms
    "main block 1st floor girls washroom": {"lat": 17.05975, "lng": 81.86875, "description": "Girls washroom on 1st floor of main block"},
    "main block 2nd floor girls washroom": {"lat": 17.05975, "lng": 81.86875, "description": "Girls washroom on 2nd floor of main block"},
    "main block 3rd floor girls washroom": {"lat": 17.05975, "lng": 81.86875, "description": "Girls washroom on 3rd floor of main block"},
    "main block 4th floor boys washroom": {"lat": 17.05975, "lng": 81.86875, "description": "Boys washroom on 4th floor of main block"},
    "girls washroom": {"lat": 17.06042, "lng": 81.86829, "description": "Girls washroom beside transport office"},
    "vb block boys washroom": {"lat": 17.06089, "lng": 81.86833, "description": "Boys washroom in Visvesvarayya block beside vb seminar hall"},
    "mining block girls washroom": {"lat": 17.06284, "lng": 81.86721, "description": "Mining engineering department girls washroom in second floor"},
    "mining block boys washroom":{"lat": 17.06284, "lng": 81.86721, "description": "Mining engineering department boys washroom in third floor"},

        
    # Seminar halls
    "vb seminar hall": {"lat": 17.06089, "lng": 81.86833, "description": "Seminar hall in Visvesvarayya block"},
    "pharmacy block seminar hall": {"lat": 17.06360, "lng": 81.86576, "description": "Seminar hall in Pharmacy block"},
    "rk block seminar hall": {"lat": 17.06426, "lng": 81.86590, "description": "Seminar hall in RK block"},
    "giet seminar hall": {"lat": 17.05975, "lng": 81.86875, "description": "Main seminar hall in GIET engineering college"},
    "degree block seminar hall": {"lat": 17.07090, "lng": 81.86853, "description": "Seminar hall in Degree block"}
}

# Create alias mapping
alias_mapping = {}
for name, data in campus_data.items():
    aliases = data.get("aliases", [])
    for alias in aliases:
        alias_mapping[alias.lower()] = name
    alias_mapping[name.lower()] = name
    alias_mapping["mainblock"] = "main block"
    alias_mapping["main building"] = "main block"


# Precompute all location names for fuzzy matching
all_location_names = list(campus_data.keys()) + list(alias_mapping.keys())

def find_location(location_str):
    """Find location in database using name or alias with fuzzy matching"""
    if not location_str or location_str.strip() == "":
        return None
        
    location_str = location_str.lower().strip()
    
    # 1. Check direct match
    if location_str in alias_mapping:
        return alias_mapping[location_str]
    
    # 2. Check for similar matches
    matches = [name for name in campus_data.keys() if location_str in name.lower()]
    if matches:
        return matches[0]
    
    # 3. Try partial matches
    for name in campus_data.keys():
        if location_str in name.lower().replace(" ", ""):
            return name
            
    # 4. Fuzzy matching using difflib
    matches = difflib.get_close_matches(location_str, all_location_names, n=1, cutoff=0.5)
    if matches:
        return alias_mapping.get(matches[0].lower(), matches[0])
    
    return None

def calculate_distance(start, end):
    """Calculate distance using Haversine formula (in meters)"""
    # Convert decimal degrees to radians
    lat1, lon1 = math.radians(campus_data[start]['lat']), math.radians(campus_data[start]['lng'])
    lat2, lon2 = math.radians(campus_data[end]['lat']), math.radians(campus_data[end]['lng'])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    # Radius of earth in meters (6371 km)
    return 6371000 * c

def generate_directions(start, end):
    """Generate detailed directions with properly formatted Google Maps link"""
    if start == end:
        return f"🚶 You're already at {start.capitalize()}!"
    
    start_coords = f"{campus_data[start]['lat']},{campus_data[start]['lng']}"
    end_coords = f"{campus_data[end]['lat']},{campus_data[end]['lng']}"
    
    # Properly formatted Google Maps URL
    maps_url = (
        f"https://www.google.com/maps/dir/?api=1&"
        f"origin={start_coords}&"
        f"destination={end_coords}&"
        "travelmode=walking"
    )
    
    distance = calculate_distance(start, end)
    walking_time = distance / 67  # 67 meters per minute (average walking speed)
    
    # Create directions with steps
    directions = [
        f"🚶 Directions from {start.capitalize()} to {end.capitalize()}:",
        f"📍 Distance: Approximately {distance:.0f} meters",
        f"⏱️ Walking time: {max(1, int(walking_time))} minutes",
        f"🗺️ [Open in Google Maps]({maps_url})"
    ]
    
    # Add route guidance based on distance
    if distance < 100:
        directions.append(f"\n🔍 {end.capitalize()} is very close to {start.capitalize()} - you should see it nearby!")
    else:
        # Calculate bearing for cardinal direction
        lat1 = math.radians(campus_data[start]['lat'])
        lon1 = math.radians(campus_data[start]['lng'])
        lat2 = math.radians(campus_data[end]['lat'])
        lon2 = math.radians(campus_data[end]['lng'])
        
        y = math.sin(lon2-lon1) * math.cos(lat2)
        x = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(lon2-lon1)
        bearing = math.degrees(math.atan2(y, x))
        
        # Convert bearing to cardinal direction
        cardinals = ["North", "North-East", "East", "South-East", "South", "South-West", "West", "North-West"]
        idx = round(bearing / 45) % 8
        cardinal_dir = cardinals[idx]
        
        directions.append(f"\n🧭 Head {cardinal_dir} from {start.capitalize()}")
    
    # Add destination info
    if "description" in campus_data[end]:
        directions.append(f"\nℹ️ About this location: {campus_data[end]['description']}")
    
    if "hours" in campus_data[end]:
        directions.append(f"\n🕒 Hours: {campus_data[end]['hours']}")
    
    return "\n".join(directions)

def get_food_locations():
    """Return all food-related locations with emojis"""
    food_spots = {
        "food court": "🍽️ Main food court area",
        "central food court": "🍕 Central dining area (CFC)",
        "spicehub": "🌶️ SpiceHub food court",
        "juice shop": "🍹 Juice and snack bar",
        "food stalls": "🍢 Street food vendors",
        "yummpys": "🍔 Yummpy's snack shop"
    }
    return "\n".join([f"- {name.capitalize()}: {desc}" for name, desc in food_spots.items()])

def get_sports_locations():
    """Return all sports facilities with emojis"""
    sports = {
        "basketball court": "🏀 Basketball playing area",
        "football court": "⚽ Football/soccer field",
        "cricket ground": "🏏 Cricket playing field",
        "events ground": "🏟️ Events and festival ground"
    }
    return "\n".join([f"- {name.capitalize()}: {desc}" for name, desc in sports.items()])

def get_prayer_locations():
    """Return prayer locations with emojis"""
    prayer = {
        "saibaba temple": "🛕 Saibaba temple on campus",
        "saraswati devi": "🙏 Saraswati Devi statue"
    }
    return "\n".join([f"- {name.capitalize()}: {desc}" for name, desc in prayer.items()])

def get_restrooms():
    """Return all restroom locations with emojis"""
    restrooms = {
        "main block 1st floor girls washroom": "🚺 Girls washroom on 1st floor",
        "main block 2nd floor girls washroom": "🚺 Girls washroom on 2nd floor",
        "main block 3rd floor girls washroom": "🚺 Girls washroom on 3rd floor",
        "main block 4th floor boys washroom": "🚹 Boys washroom on 4th floor",
        "transport office girls washroom": "🚺 Girls washroom beside transport office",
        "vb block boys washroom": "🚹 Boys washroom in Visvesvarayya block beside vb seminar hall" 
    }
    return "\n".join([f"- {name.capitalize()}: {desc}" for name, desc in restrooms.items()])

def get_seminar_halls():
    """Return all seminar halls with emojis"""
    halls = {
        "vb seminar hall": "🎤 Seminar hall in Visvesvarayya block",
        "pharmacy block seminar hall": "🎤 Seminar hall in Pharmacy block",
        "rk block seminar hall": "🎤 Seminar hall in RK block",
        "giet seminar hall": "🎤 Main seminar hall in GIET engineering college",
        "degree block seminar hall": "🎤 Seminar hall in Degree block"
    }
    return "\n".join([f"- {name.capitalize()}: {desc}" for name, desc in halls.items()])

def get_parking_locations():
    """Return all parking locations with emojis"""
    parking_spots = {name: data['description'] for name, data in campus_data.items() if "parking" in name}
    return "\n".join([f"- {name.capitalize()}: 🚗 {desc}" for name, desc in parking_spots.items()])
def get_sit_rest_locations():
    """Return scenic/sitting/photo locations with emojis"""
    locations = {
        "amphitheatre": "🎭 Open-air amphitheater",
        "bamboos": "🎋 Bamboo garden area",
        "yummpys": "🍔 Yummpy's snack shop (chill spot)",
        "zigzag": "🌀 Zigzag sitting area",
        "sitting place 1": "🪑 Sitting area near amphitheatre",
        "sitting place 2": "🪑 Sitting area near mining block",
        "lake": "🌅 Lake — peaceful view"
    }
    return "\n".join([f"- {name.capitalize()}: {desc}" for name, desc in locations.items()])


def generate_stationery_directions():
    """Special function for stationery shop directions with proper link"""
    start = "gate"
    end = "Stationery shop"
    
    if end not in campus_data or start not in campus_data:
        return "Couldn't find stationery shop location information."
    
    # Generate proper Google Maps URL
    start_coords = f"{campus_data[start]['lat']},{campus_data[start]['lng']}"
    end_coords = f"{campus_data[end]['lat']},{campus_data[end]['lng']}"
    maps_url = (
        f"https://www.google.com/maps/dir/?api=1&"
        f"origin={start_coords}&"
        f"destination={end_coords}&"
        "travelmode=walking"
    )
    
    distance = calculate_distance(start, end)
    walking_time = distance / 67
    
    # Create detailed response
    return (
        "📚 You're looking for a place to buy a book! 📖\n\n"
        "You can find the Stationery shop near the Main Block building 🔵. "
        "It's a convenient spot to grab your favorite books, stationery supplies, and more! 🎉\n\n"
        "Here are the step-by-step directions:\n\n"
        "**From the Gate:**\n"
        "1. Head towards the Globe monument 🌍\n"
        "2. Turn left towards the Main Block building 🔵\n"
        "3. Walk straight for about 150 meters 👣\n"
        "4. You'll find the Stationery shop on your right-hand side 📚\n\n"
        f"**Approximate distance:** {distance:.0f} meters 📍\n"
        f"**Walking time:** {max(1, int(walking_time))} minutes ⏰\n\n"
        f"🗺️ [Open in Google Maps]({maps_url})\n\n"
        "Hope this helps! 😊"
    )

def has_whole_word(keywords, message):
    return any(re.search(rf"\b{re.escape(word)}\b", message) for word in keywords)

def process_special_queries(user_message):
    """Handle special queries with strict keyword detection"""
    user_message = user_message.lower()

    # Stationery / Books
    if has_whole_word(["book", "books", "stationery", "notebook", "pen", "pencil", "xerox", "photocopy", "buy book"], user_message):
        return generate_stationery_directions()
    
    # Food
    if has_whole_word(["food", "eat", "hungry", "restaurant", "canteen", "snack", "dine", "dining", "juice", "spicehub", "yummpy"], user_message):
        return (
            "🍴 Here are all food locations on campus:\n\n"
            f"{get_food_locations()}\n\n"
            "Ask 'How to get to [location]?' for directions to any of these!"
        )
    
    # Prayer
    if has_whole_word(["pray", "temple", "worship", "god", "religious", "statue", "saibaba", "saraswati"], user_message):
        return (
            "🙏 Here are prayer locations on campus:\n\n"
            f"{get_prayer_locations()}\n\n"
            "Ask for directions to any of these!"
        )

    # Sports
    if has_whole_word(["play", "sports", "game", "basketball", "football", "cricket", "ground", "field", "court"], user_message):
        for name in ["basketball court", "football court", "cricket ground", "events ground"]:
            if name in user_message:
                return generate_directions("gate", name)
    
    # return (
    #     "🏅 Here are the sports facilities available on campus:\n\n"
    #     f"{get_sports_locations()}\n\n"
    #     "Ask something like 'How to get to basketball court?' for directions!"
    # )

    # Administrative / Fee / Transport Office
    if has_whole_word(["fee", "fees", "administrative", "admin block", "principal", "transport office", "admission", "pay", "tc", "scholarship"], user_message):
        return generate_directions("gate", "main block") + (
            "\n\n🧾 The Administrative Block is in the **Main Block (Ground Floor)**. "
            "You can visit here to:\n"
            "- Pay fees 💰\n"
            "- Submit transport or admission forms 🚌\n"
            "- Meet the principal or officials 📋\n"
        )
    
    # Restrooms
    if has_whole_word(["restroom", "washroom", "toilet", "bathroom", "wc", "lavatory","piss"], user_message):
        return (
            "🚽 Here are restroom locations on campus:\n\n"
            f"{get_restrooms()}\n\n"
            "Ask for directions to any specific restroom!"
        )
    
    # Seminar halls
    if has_whole_word(["seminar hall", "seminar", "conference", "lecture hall", "presentation"], user_message):
        return (
            "🎤 Here are seminar halls on campus:\n\n"
            f"{get_seminar_halls()}\n\n"
            "Ask for directions to any seminar hall!"
        )
    
    if has_whole_word(["transport", "bus details"], user_message):
        return generate_directions("gate", "transport office") + (
            "\n\n🚌 The Transport Office is located near the Main Block. "
            "You can visit here for:\n"
            "- Bus passes 🚌\n"
            "- Vehicle parking inquiries 🚗\n"
            "- Transport schedules 📅\n"
        )
    # Parking
    if has_whole_word(["parking", "park my vehicle", "vehicle parking", "car parking", "bike parking","park"], user_message):
        return (
            "🚗 Here are the parking locations on campus:\n\n"
            f"{get_parking_locations()}\n\n"
            "Ask 'How to get to [parking name]' for directions to a specific spot!"
        )
        # Best places to visit
    if has_whole_word(["best places", "best place", "must see", "top spots", "recommend place", "where should i go", "beautiful spots", "visit", "tour", "explore"], user_message):
        return (
            "🌟 Top spots to visit on campus:\n\n"
            f"{get_sit_rest_locations()}\n\n"
            "Ask for directions to any of these beautiful locations!"
        )
        
    # Sit / Rest / Photo / View
    if has_whole_word(["sit", "rest", "photo", "photograph", "selfie", "view", "scenic", "relax","photos","locations","place","places","location", "zigzag", "photography", "chill"], user_message):
        return (
            "🌿 Here are peaceful or scenic places to sit, relax or take photos:\n\n"
            f"{get_sit_rest_locations()}\n\n"
            "Ask for directions to any of these for a great view or rest!"
        )

    # ATM / Cash
    if has_whole_word(["atm", "cash", "withdraw", "money"], user_message):
        return generate_directions("gate", "atm") + (
            "\n\n🏧 There's an ATM near the main gate where you can withdraw cash easily."
        )
    # Library
    if has_whole_word(["library", "books", "study", "reading room", "quiet place"], user_message):
        return generate_directions("gate", "library") + (
            "\n\n📚 The Library is located near the Main Block. "
            "It's a great place to study, borrow books, and find resources. "
            "It is open from 8AM to 10PM daily."
        )
    # Admission / Fee Payment
    if has_whole_word(["admission", "fee payment", "pay fees", "scholarship", "tuition"], user_message):
        return generate_directions("gate", "admission block") + (
            "\n\n📝 The Admission Block is where you can handle all admission-related tasks, "
            "including fee payments, scholarship applications, and more."
        )
    # Guest House
    if has_whole_word(["guest house", "stay", "visitors", "accommodation"], user_message):
        return generate_directions("gate", "guest") + (
            "\n\n🏨 The Guest House is available for visitors and guests. "
            "It's a comfortable place to stay during your visit."
        )
    # Farm / Nursery
    if has_whole_word(["farm", "nursery", "plants", "gardening"], user_message):
        return generate_directions("gate", "farm") + (
            "\n\n🌱 The Farm/Nursery is a great place to explore various plants and gardening techniques. "
            "It's located near the Sports Complex and is open from 9AM to 5PM."
        )
    # Zigzag / Sitting Places
    if has_whole_word(["zigzag", "sitting places", "chill spots", "relax areas"], user_message):
        return (
            "🪑 Here are some great zigzag paths and sitting areas on campus:\n\n"
            f"{get_zigzag_sitting_locations()}\n\n"
            "Ask for directions to any of these relaxing spots!"
        )
    # Default response for unhandled queries
    return "🤔 I'm not sure about that. Can you please provide more details or rephrase your question?"

def generate_system_prompt():
    """Generate comprehensive system prompt for Llama"""
    locations = "\n".join([f"- {name}: {data['description']}" for name, data in campus_data.items()])
    
    return (
        "You are a comprehensive assistant for GIET University (Godavari Institute of Engineering and Technology), "
        "which is also recognized as Godavari Global University (GGU). You can help with:\n"
        "1. Campus navigation and directions\n"
        "2. Location information and descriptions\n"
        "3. General college information and queries\n"
        "4. Campus facilities and services\n"
        "5. Multilingual support in English, Telugu, and Hindi\n\n"
        
        "**College Information**:\n"
        "- Full Name: Godavari Institute of Engineering and Technology (GIET)\n"
        "- Also Known As: Godavari Global University (GGU)\n"
        "- Official website: www.giet.ac.in \n"
        "- Contact email: giet@gmail.com\n"
        "- Phone: +91-XXXXX-XXXXX\n"
        "- Academic programs: Engineering, Pharmacy, Management, Sciences\n"
        "- Key departments: Computer Science, Mechanical, Civil, Electronics, Pharmacy, AIML , DataScience, CyberSecurity ,IT ,Electrical\n"
        "- Campus life: Sports facilities, cultural events, tech fests\n\n"
        
        "**Language Support**:\n"
        "- Use English by default\n"
        "- If user prefers Telugu, respond in Telugu (తెలుగు)\n"
        "- If user prefers Hindi, respond in Hindi (हिंदी)\n"
        "- Important terms should include English in parentheses\n\n"
        
        "**Campus Locations**:\n"
        f"{locations}\n\n"
        
        "**When answering questions**:\n"
        "- For navigation: Provide step-by-step directions, distance, walking time, and Google Maps link\n"
        "- For location info: Include description, hours, and nearby places\n"
        "- For general questions: Answer knowledgeably about college programs, events, and campus life\n"
        "- Use emojis to make responses engaging\n"
        "- Format responses with clear sections and bullet points\n\n"
        
        "**Examples**:\n"
        "User: 'What engineering programs are offered?'\n"
        "Response: 'GIET offers various engineering programs: 🛠️ Mechanical, 💻 Computer Science, 🔌 Electrical, 🏗️ Civil, and more! Visit www.giet.edu/programs for details.'\n\n"
        
        "User: 'When is the tech fest?'\n"
        "Response: 'The annual tech fest usually happens in March! 🎉 Check www.giet.edu/events for this year's schedule.'\n\n"
        
        "Be friendly and helpful to all users!"
    )

def detect_language(text):
    """Detect if text contains Telugu or Hindi characters"""
    # Telugu Unicode range: 0x0C00-0x0C7F
    if re.search(r'[\u0C00-\u0C7F]', text):
        return 'te'
    # Hindi Unicode range: 0x0900-0x097F
    elif re.search(r'[\u0900-\u097F]', text):
        return 'hi'
    return 'en'

def translate_response(response, target_lang):
    """Translate response to target language while preserving technical terms"""
    if target_lang == 'en':
        return response
        
    try:
        # Preserve technical terms by including English in parentheses
        preserved_terms = {
            'GIET': 'GIET (గోదావరి ఇన్స్టిట్యూట్ ఆఫ్ ఇంజనీరింగ్ అండ్ టెక్నాలజీ)',
            'library': 'లైబ్రరీ (library)',
            'seminar hall': 'సెమినార్ హాల్ (seminar hall)',
            'washroom': 'పాయిఖానా (washroom)',
            'canteen': 'కాంటీన్ (canteen)',
            'pharmacy': 'ఫార్మసీ (pharmacy)',
            'engineering': 'ఇంజనీరింగ్ (engineering)',
            'admission': 'ప్రవేశం (admission)',
            'transport': 'రవాణా (transport)',
            'GGU': 'GGU (గోదావరి గ్లోబల్ యూనివర్సిటీ)',
            'Godavari': 'గోదావరి (Godavari)',
            'campus': 'క్యాంపస్ (campus)',
            'block': 'బ్లాక్ (block)',
            'hostel': 'హాస్టల్ (hostel)',
            'food court': 'ఫుడ్ కోర్ట్ (food court)',
            'lab': 'ల్యాబ్ (lab)'
        }
        
        # Replace terms before translation
        for term, replacement in preserved_terms.items():
            if target_lang == 'te':
                response = response.replace(term, replacement)
        
        # Translate through Ollama
        messages = [
            {
                'role': 'system',
                'content': f'You are a professional translator. Translate the following text to {target_lang} while keeping technical terms in English inside parentheses. Only output the translated text.'
            },
            {
                'role': 'user',
                'content': response
            }
        ]
        
        result = ollama.chat(model='llama3', messages=messages)
        return result['message']['content']
    except Exception as e:
        print(f"Translation error: {e}")
        return response

def query_llama(user_message, conversation_history=[]):
    """Query Llama model with campus context and language support"""
    system_prompt = generate_system_prompt()
    user_lang = detect_language(user_message)
    
    # Store language preference in session
    session['user_lang'] = user_lang
    
    messages = [
        {"role": "system", "content": system_prompt},
        *conversation_history[-3:],
        {"role": "user", "content": user_message}
    ]
    
    try:
        response = ollama.chat(
            model='llama3',
            messages=messages,
            options={'temperature': 0.5}
        )
        
        english_response = response['message']['content']
        
        # Translate if needed
        if user_lang != 'en':
            return translate_response(english_response, user_lang)
        return english_response
        
    except Exception as e:
        print(f"Llama error: {str(e)}")
        return "I'm having trouble understanding. Could you please rephrase your question?"

def get_help_response(lang='en'):
    """Get help response in appropriate language"""
    responses = {
        'en': (
            "🌟 I'm your campus navigation assistant! I can help with:\n"
            "- Directions between locations\n"
            "- Finding places (food courts, sports grounds, temples)\n"
            "- Information about locations\n"
            "- Campus map with all locations\n"
            "- General college information\n\n"
            "Try asking:\n"
            "- 'Where can I buy books?'\n"
            "- 'How to go to library?'\n"
            "- 'Directions from gate to main block'\n"
            "- 'What engineering programs are offered?'\n"
            "- 'Show me the campus map'"
        ),
        'te': (
            "🌟 నేను మీ క్యాంపస్ నావిగేషన్ అసిస్టెంట్! నేను సహాయం చేయగలను:\n"
            "- ప్రదేశాల మధ్య దారి చూపడం\n"
            "- ప్రదేశాలను కనుగొనడం (ఫుడ్ కోర్టులు, స్పోర్ట్స్ గ్రౌండ్లు, దేవాలయాలు)\n"
            "- ప్రదేశాల గురించి సమాచారం\n"
            "- అన్ని ప్రదేశాలతో క్యాంపస్ మ్యాప్\n"
            "- సాధారణ కళాశాల సమాచారం\n\n"
            "ఇలా అడగండి:\n"
            "- 'పుస్తకాలు ఎక్కడ కొనాలి?'\n"
            "- 'లైబ్రరీకి ఎలా వెళ్ళాలి?'\n"
            "- 'గేట్ నుండి మెయిన్ బ్లాక్కు దారి'\n"
            "- 'ఏ ఇంజనీరింగ్ కోర్సులు అందుబాటులో ఉన్నాయి?'\n"
            "- 'క్యాంపస్ మ్యాప్ చూపించు'"
        ),
        'hi': (
            "🌟 मैं आपका कैंपस नेविगेशन सहायक हूँ! मैं सहायता कर सकता हूँ:\n"
            "- स्थानों के बीच रास्ता बताना\n"
            "- जगहें ढूँढना (खाने की जगह, खेल मैदान, मंदिर)\n"
            "- स्थानों के बारे में जानकारी\n"
            "- सभी स्थानों के साथ कैंपस का नक्शा\n"
            "- सामान्य कॉलेज जानकारी\n\n"
            "इस तरह पूछें:\n"
            "- 'किताबें कहाँ खरीदें?'\n"
            "- 'लाइब्रेरी कैसे जाएँ?'\n"
            "- 'गेट से मेन ब्लॉक तक का रास्ता'\n"
            "- 'कौन से इंजीनियरिंग कोर्स उपलब्ध हैं?'\n"
            "- 'मुझे कैंपस का नक्शा दिखाएं'"
        )
    }
    return responses.get(lang, responses['en'])

def process_message(user_message):
    """Process user message with special handling for book/shopping queries"""
    cleaned_msg = user_message.strip().lower()
    direct_location = find_location(cleaned_msg)
    if direct_location and direct_location in campus_data:
        return generate_directions("gate", direct_location)
    special_response = process_special_queries(user_message)
    if special_response:
        return special_response

    # Get language from session or detect
    user_lang = session.get('user_lang', detect_language(user_message))
    
    # Patterns for different types of queries
    from_to_pattern = r'(?:from|between)\s+(.+?)\s+(?:to|and)\s+(.+)'
    to_pattern = r'(?:to|for|towards|near|reach|get to|go to)\s+(.+)'
    where_pattern = r'(?:where(\'s| is)|find|locate|show me|how to get to|directions? to)\s+(.+)'
    info_pattern = r'(?:info|information|details|about|tell me about)\s+(.+)'
    help_pattern = r'(?:help|what can you do|options|features|commands|సహాయం|मदद)'
    map_pattern = r'(?:map|campus map|whole map|complete map)'
    simple_directions_pattern = r'(.+?)\s+to\s+(.+)'
    current_location_pattern = r'(?:where am i|my location|current location)'
    general_college_pattern = r'(?:about|college|giet|university|program|course|faculty|event|fest|admission|fee|scholarship|academic|department)'
    
    start = None
    end = None
    
    try:
        # Check for help request
        if re.search(help_pattern, user_message, re.IGNORECASE):
            return get_help_response(user_lang)
        
        # Check for map request
        if re.search(map_pattern, user_message, re.IGNORECASE):
            # Create Google Maps URL with all markers
            markers = "&markers=" + "|".join([f"{data['lat']},{data['lng']}" for data in campus_data.values()])
            map_url = f"https://www.google.com/maps?{markers}&q=17.05973,81.86922"
            return (
                "🗺️ Here's the complete campus map:\n"
                f"📍 [View Campus Map on Google Maps]({map_url})\n\n"
                "Key locations include:\n"
                "- " + "\n- ".join([name.capitalize() for name in list(campus_data.keys())[:10]]) + "\n...and more!"
            )
        
        # Check for location information request
        if info_match := re.search(info_pattern, user_message, re.IGNORECASE):
            loc_str = info_match.group(1).strip()
            location = find_location(loc_str)
            
            if location and location in campus_data:
                data = campus_data[location]
                # Create direct Google Maps link
                maps_url = f"https://www.google.com/maps/search/?api=1&query={data['lat']},{data['lng']}"
                
                response = f"ℹ️ Information about {location.capitalize()}:\n"
                response += f"- Description: {data['description']}\n"
                response += f"- 📍 [View on Google Maps]({maps_url})\n"
                
                if "hours" in data:
                    response += f"- Hours: {data['hours']}\n"
                
                # Find nearby locations
                nearby = []
                for other_name, other_data in campus_data.items():
                    if other_name != location:
                        dist = calculate_distance(location, other_name)
                        if dist < 200:  # within 200 meters
                            nearby.append((other_name, dist))
                
                if nearby:
                    response += "\n📍 Nearby locations:\n"
                    for name, dist in sorted(nearby, key=lambda x: x[1])[:3]:
                        response += f"- {name.capitalize()} ({dist:.0f}m)\n"
            else:
                response = f"❌ Sorry, I couldn't find information about '{loc_str}'"
            return response
        
        # Check for "where am I" request
        if re.search(current_location_pattern, user_message, re.IGNORECASE):
            # Create Google Maps URL with all markers
            markers = "&markers=" + "|".join([f"{data['lat']},{data['lng']}" for data in campus_data.values()])
            map_url = f"https://www.google.com/maps?{markers}&q=17.05973,81.86922"
            return (
                "📍 I can't determine your exact location, but here's the campus map:\n"
                f"🗺️ [View Campus Map on Google Maps]({map_url})\n\n"
                "You can ask:\n"
                "- 'Where is [place]' to find locations\n"
                "- 'Directions to [place]' for navigation"
            )
        
        # Check for "where is" request
        if where_match := re.search(where_pattern, user_message, re.IGNORECASE):
            # Handle different regex group positions
            loc_str = where_match.group(2) if where_match.group(2) else where_match.group(1)
            location = find_location(loc_str)
            
            if location and location in campus_data:
                data = campus_data[location]
                # Create direct Google Maps link
                maps_url = f"https://www.google.com/maps/search/?api=1&query={data['lat']},{data['lng']}"
                
                response = f"📍 {location.capitalize()} is located at:\n"
                response += f"- Description: {data['description']}\n"
                response += f"- 📍 [View on Google Maps]({maps_url})\n"
                
                # Find nearby locations
                nearby = []
                for other_name, other_data in campus_data.items():
                    if other_name != location:
                        dist = calculate_distance(location, other_name)
                        if dist < 200:  # within 200 meters
                            nearby.append((other_name, dist))
                
                if nearby:
                    response += "\n📍 Nearby locations:\n"
                    for name, dist in sorted(nearby, key=lambda x: x[1])[:3]:
                        response += f"- {name.capitalize()} ({dist:.0f}m)\n"
            else:
                response = f"❌ Sorry, I couldn't find '{loc_str}'"
            return response
        
        # Check for directions request patterns
        if from_to_match := re.search(from_to_pattern, user_message, re.IGNORECASE):
            start_str, end_str = from_to_match.groups()
            start = find_location(start_str)
            end = find_location(end_str)
        elif simple_match := re.search(simple_directions_pattern, user_message, re.IGNORECASE):
            start_str, end_str = simple_match.groups()
            start = find_location(start_str)
            end = find_location(end_str)
        elif to_match := re.search(to_pattern, user_message, re.IGNORECASE):
            end_str = to_match.group(1).strip()
            start = "gate"  # Default to main gate as starting point
            end = find_location(end_str)
        
        # Generate directions if we have both points
        if start and end:
            if end not in campus_data:
                return f"❌ Sorry, I couldn't find '{end}'"
            if start not in campus_data:
                return f"❌ Sorry, I couldn't find '{start}'"
            return generate_directions(start, end)
        
        # Check for general college questions
        if re.search(general_college_pattern, user_message, re.IGNORECASE):
            return query_llama(user_message)
                
        # No pattern matched - use Llama
        return query_llama(user_message)
    
    except Exception as e:
        return f"❌ Sorry, I encountered an error: {str(e)}"

@app.route('/')
def home():
    # Initialize session language
    if 'user_lang' not in session:
        session['user_lang'] = 'en'
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat_handler():
    user_message = request.json['message']
    response = process_message(user_message)
    return jsonify({"response": response})

@app.route('/map')
def campus_map():
    return jsonify(campus_data)

@app.route('/set_language', methods=['POST'])
def set_language():
    """Endpoint to manually set language preference"""
    lang = request.json.get('language', 'en')
    if lang in ['en', 'te', 'hi']:
        session['user_lang'] = lang
        return jsonify({"status": "success", "language": lang})
    return jsonify({"status": "error", "message": "Invalid language"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)