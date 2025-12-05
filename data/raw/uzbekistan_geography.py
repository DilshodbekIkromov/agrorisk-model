"""
Uzbekistan Administrative Divisions
14 Regions (Viloyatlar) + 1 Autonomous Republic + 1 City

Each region contains districts (Tumanlar).
We also include approximate center coordinates for satellite data extraction.
"""

UZBEKISTAN_REGIONS = {
    "Tashkent City": {
        "center": (41.2995, 69.2401),
        "districts": {
            "Almazar": (41.3167, 69.2167),
            "Bektemir": (41.2167, 69.3333),
            "Chilanzar": (41.2833, 69.1833),
            "Yakkasaray": (41.2833, 69.2667),
            "Mirzo Ulugbek": (41.3500, 69.2833),
            "Mirabad": (41.3000, 69.2833),
            "Sergeli": (41.2333, 69.2000),
            "Shaykhantakhur": (41.3333, 69.2333),
            "Uchtepa": (41.3167, 69.1500),
            "Yashnabad": (41.2833, 69.3500),
            "Yunusabad": (41.3667, 69.2167),
        }
    },
    "Tashkent Region": {
        "center": (41.3167, 69.6500),
        "districts": {
            "Angren": (41.0167, 70.1333),
            "Bekabad": (40.2167, 69.2500),
            "Olmaliq": (40.8500, 69.6000),
            "Chirchiq": (41.4667, 69.5833),
            "Bostanliq": (41.6000, 70.2000),
            "Buka": (41.3333, 69.4667),
            "Chinaz": (40.9333, 68.7667),
            "Qibray": (41.3833, 69.4833),
            "Oqqorgon": (40.9167, 69.0500),
            "Parkent": (41.2833, 69.6667),
            "Piskent": (40.9000, 69.3500),
            "Tashkent": (41.3667, 69.4333),
            "Nurafshon": (41.0500, 69.2333),
            "Yangiyul": (41.1167, 69.0500),
            "Zangiota": (41.2167, 69.0667),
        }
    },
    "Andijan": {
        "center": (40.7833, 72.3442),
        "districts": {
            "Andijan City": (40.7833, 72.3442),
            "Altinkul": (40.8333, 72.1000),
            "Asaka": (40.6333, 72.2333),
            "Baliqchi": (40.8667, 72.4667),
            "Boz": (40.6833, 72.5667),
            "Buloqboshi": (40.6167, 72.3833),
            "Izboskan": (40.9167, 72.2500),
            "Jalaquduq": (40.7167, 72.6167),
            "Kurgontepa": (40.7333, 72.0833),
            "Marhamat": (40.5167, 72.3167),
            "Oltinkul": (40.8500, 72.1333),
            "Pakhtaabad": (40.9167, 72.5333),
            "Shahrikhan": (40.7000, 72.0500),
            "Ulugnar": (40.9500, 72.1833),
            "Khojaabad": (40.5500, 72.5500),
        }
    },
    "Bukhara": {
        "center": (39.7747, 64.4286),
        "districts": {
            "Bukhara City": (39.7747, 64.4286),
            "Alat": (39.5500, 63.9000),
            "Gijduvon": (40.1000, 64.6833),
            "Jondor": (39.7167, 64.1333),
            "Kogon": (39.7167, 64.5500),
            "Olot": (39.5500, 63.9167),
            "Peshku": (39.4833, 64.5500),
            "Qorakul": (39.5000, 63.8500),
            "Qorovulbozor": (39.5167, 64.8000),
            "Romitan": (39.9333, 64.3833),
            "Shofirkon": (40.1167, 64.5000),
            "Vobkent": (40.0167, 64.5167),
        }
    },
    "Fergana": {
        "center": (40.3842, 71.7889),
        "districts": {
            "Fergana City": (40.3842, 71.7889),
            "Quva": (40.5167, 72.0833),
            "Marg'ilon": (40.4667, 71.7167),
            "Qoqon": (40.5333, 70.9333),
            "Oltiariq": (40.4333, 71.4667),
            "Bag'dod": (40.3333, 71.2333),
            "Beshariq": (40.4667, 70.6000),
            "Buvayda": (40.6333, 71.0333),
            "Dang'ara": (40.5833, 70.9167),
            "Furqat": (40.2667, 71.5167),
            "Qoshtepa": (40.5500, 71.0833),
            "Quva": (40.5167, 72.0833),
            "Rishton": (40.3667, 71.2833),
            "Sokh": (39.9667, 71.1333),
            "Toshloq": (40.5333, 71.8500),
            "Uchkuprik": (40.5333, 71.0500),
            "Uzbekistan": (40.2333, 71.1333),
            "Yozyovon": (40.1333, 71.6000),
        }
    },
    "Jizzakh": {
        "center": (40.1158, 67.8422),
        "districts": {
            "Jizzakh City": (40.1158, 67.8422),
            "Arnasoy": (40.6000, 67.9667),
            "Bakhmal": (39.8167, 68.2500),
            "Dostlik": (40.5167, 67.7833),
            "Forish": (40.3333, 67.2333),
            "Gallaorol": (40.2167, 68.1000),
            "Mirzachul": (40.6500, 67.3500),
            "Pakhtakor": (40.2167, 67.7667),
            "Yangiobod": (39.9500, 68.5833),
            "Zomin": (39.9500, 68.4000),
            "Zafarobod": (40.5333, 68.2500),
            "Zarbdor": (40.4667, 67.5500),
        }
    },
    "Kashkadarya": {
        "center": (38.8608, 65.7981),
        "districts": {
            "Qarshi": (38.8608, 65.7981),
            "Chiroqchi": (38.9500, 66.5500),
            "Dehqonobod": (38.4000, 66.5000),
            "Guzor": (38.6167, 66.2500),
            "Qamashi": (38.8333, 65.6000),
            "Karshi": (38.8500, 65.7833),
            "Kasbi": (38.9333, 65.4333),
            "Kitob": (39.1333, 66.8833),
            "Koson": (39.0500, 65.5833),
            "Mirishkor": (38.8833, 65.2833),
            "Muborak": (39.3000, 65.2500),
            "Nishon": (38.5500, 65.4333),
            "Shahrisabz": (39.0500, 66.8333),
            "Yakkabog": (38.9833, 66.7333),
        }
    },
    "Khorezm": {
        "center": (41.5500, 60.6333),
        "districts": {
            "Urgench": (41.5500, 60.6333),
            "Bogot": (41.5000, 60.8333),
            "Gurlan": (41.6667, 60.4000),
            "Khonqa": (41.5167, 60.8167),
            "Hazorasp": (41.3167, 61.0667),
            "Khiva": (41.3833, 60.3500),
            "Qoshkopir": (41.5833, 61.0500),
            "Shovot": (41.6500, 60.5500),
            "Tuproqqala": (41.2000, 60.9167),
            "Yangiariq": (41.4000, 60.5500),
            "Yangibozor": (41.7167, 60.5833),
        }
    },
    "Namangan": {
        "center": (40.9983, 71.6726),
        "districts": {
            "Namangan City": (40.9983, 71.6726),
            "Chortoq": (41.0667, 71.0333),
            "Chust": (41.0000, 71.2333),
            "Kosonsoy": (41.2500, 71.5333),
            "Mingbuloq": (40.7667, 71.3000),
            "Namangan": (40.9833, 71.3833),
            "Norin": (40.9000, 71.9333),
            "Pop": (41.0167, 70.7833),
            "Torakurgan": (41.0167, 71.5000),
            "Uchqorgon": (41.1167, 71.0333),
            "Uychi": (41.0833, 71.9333),
            "Yangiqorgon": (41.2000, 71.7167),
        }
    },
    "Navoiy": {
        "center": (40.0844, 65.3792),
        "districts": {
            "Navoiy City": (40.0844, 65.3792),
            "Karmana": (40.1333, 65.3667),
            "Konimex": (40.3000, 64.9667),
            "Navbahor": (39.9500, 65.4667),
            "Nurota": (40.5667, 65.6833),
            "Qiziltepa": (39.9167, 65.5000),
            "Tomdi": (41.3000, 64.9167),
            "Uchquduq": (42.1500, 63.5500),
            "Zarafshon": (41.5667, 64.1833),
        }
    },
    "Samarkand": {
        "center": (39.6542, 66.9597),
        "districts": {
            "Samarkand City": (39.6542, 66.9597),
            "Bulung'ur": (39.7667, 67.2667),
            "Ishtikhan": (39.9833, 66.5000),
            "Jomboy": (39.7167, 67.1500),
            "Kattaqorgon": (39.9000, 66.2667),
            "Narpay": (39.9833, 66.0500),
            "Nurobod": (39.5333, 67.3500),
            "Oqdaryo": (39.9000, 66.8333),
            "Paxtachi": (39.6500, 66.3667),
            "Payariq": (39.5500, 66.8333),
            "Pastdargom": (39.5333, 66.6000),
            "Samarkand": (39.6833, 66.9167),
            "Toyloq": (39.4833, 67.1500),
            "Urgut": (39.4000, 67.2500),
        }
    },
    "Sirdaryo": {
        "center": (40.8375, 68.6650),
        "districts": {
            "Guliston": (40.4833, 68.7833),
            "Boyovut": (40.2833, 68.5833),
            "Guliston": (40.5000, 68.7833),
            "Mirzaobod": (40.2333, 68.6500),
            "Oqoltin": (40.3833, 68.1500),
            "Sardoba": (40.1667, 68.1167),
            "Saykhunobod": (40.2667, 67.9500),
            "Sirdaryo": (40.8333, 68.6667),
            "Xovos": (40.1167, 68.4000),
            "Yangier": (40.2667, 68.8167),
        }
    },
    "Surkhandarya": {
        "center": (37.2242, 67.2783),
        "districts": {
            "Termez": (37.2242, 67.2783),
            "Angor": (37.5000, 67.0167),
            "Bandixon": (38.1833, 67.4667),
            "Boysun": (38.2167, 67.2000),
            "Denov": (38.2667, 67.8833),
            "Jarqorgon": (37.5000, 67.4167),
            "Kumkurgon": (37.7833, 67.7000),
            "Muzrabot": (37.2833, 66.6500),
            "Oltinsoy": (38.3000, 68.2000),
            "Qiziriq": (37.6333, 67.1833),
            "Sariosiyo": (38.4167, 67.9500),
            "Sherobod": (37.6500, 66.0500),
            "Shurchi": (37.5333, 67.2167),
            "Termez": (37.2333, 67.2833),
            "Uzun": (38.1167, 68.0333),
        }
    },
    "Karakalpakstan": {
        "center": (43.8000, 59.0000),
        "districts": {
            "Nukus": (42.4667, 59.6000),
            "Amudaryo": (42.1000, 59.2167),
            "Beruniy": (41.7000, 60.8167),
            "Chimboy": (42.9333, 59.7833),
            "Ellikqala": (41.9000, 60.0833),
            "Kegeyli": (42.7833, 59.6000),
            "Konlikul": (42.1000, 59.5833),
            "Kungirot": (43.0667, 58.9000),
            "Moynaq": (43.7667, 59.0333),
            "Nukus": (42.4500, 59.6000),
            "Qongirot": (43.0500, 58.9000),
            "Qoraozak": (42.8000, 59.8333),
            "Shumanay": (42.3500, 59.3833),
            "Taxtakopir": (42.4000, 59.0167),
            "Tortkul": (41.5500, 60.8333),
            "Xojeli": (42.4000, 59.4500),
        }
    },
}

def get_all_regions():
    return list(UZBEKISTAN_REGIONS.keys())

def get_districts(region):
    if region in UZBEKISTAN_REGIONS:
        return list(UZBEKISTAN_REGIONS[region]["districts"].keys())
    return []

def get_coordinates(region, district=None):
    if region not in UZBEKISTAN_REGIONS:
        return None
    if district is None:
        return UZBEKISTAN_REGIONS[region]["center"]
    if district in UZBEKISTAN_REGIONS[region]["districts"]:
        return UZBEKISTAN_REGIONS[region]["districts"][district]
    return None

def get_all_locations():
    """Returns list of (region, district, lat, lon) tuples"""
    locations = []
    for region, data in UZBEKISTAN_REGIONS.items():
        for district, coords in data["districts"].items():
            locations.append({
                "region": region,
                "district": district,
                "latitude": coords[0],
                "longitude": coords[1]
            })
    return locations

if __name__ == "__main__":
    locations = get_all_locations()
    print(f"Total locations: {len(locations)}")
    print(f"Regions: {len(UZBEKISTAN_REGIONS)}")
    for region in get_all_regions():
        print(f"  {region}: {len(get_districts(region))} districts")
