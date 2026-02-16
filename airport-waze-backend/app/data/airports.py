"""Airport data with real GPS coordinates."""

AIRPORTS_DATA = {
    "JFK": {
        "code": "JFK",
        "name": "John F. Kennedy International Airport",
        "city": "New York",
        "lat": 40.6413,
        "lng": -73.7781,
        "terminals": ["Terminal 1", "Terminal 4", "Terminal 5", "Terminal 7", "Terminal 8"],
        "checkpoints": [
            {"id": "jfk-t1-tsa-1", "name": "Terminal 1 Security", "type": "tsa", "terminal": "Terminal 1", "lat": 40.6428, "lng": -73.7889, "base_wait": 25},
            {"id": "jfk-t1-tsa-pre", "name": "Terminal 1 TSA PreCheck", "type": "tsa_precheck", "terminal": "Terminal 1", "lat": 40.6429, "lng": -73.7887, "base_wait": 8},
            {"id": "jfk-t1-bag", "name": "Terminal 1 Bag Check", "type": "bag_check", "terminal": "Terminal 1", "lat": 40.6425, "lng": -73.7892, "base_wait": 12},
            {"id": "jfk-t4-tsa-1", "name": "Terminal 4 Security A", "type": "tsa", "terminal": "Terminal 4", "lat": 40.6437, "lng": -73.7820, "base_wait": 30},
            {"id": "jfk-t4-tsa-2", "name": "Terminal 4 Security B", "type": "tsa", "terminal": "Terminal 4", "lat": 40.6435, "lng": -73.7815, "base_wait": 28},
            {"id": "jfk-t4-tsa-pre", "name": "Terminal 4 TSA PreCheck", "type": "tsa_precheck", "terminal": "Terminal 4", "lat": 40.6436, "lng": -73.7818, "base_wait": 10},
            {"id": "jfk-t4-bag", "name": "Terminal 4 Bag Check", "type": "bag_check", "terminal": "Terminal 4", "lat": 40.6440, "lng": -73.7825, "base_wait": 15},
            {"id": "jfk-t4-passport", "name": "Terminal 4 Passport Control", "type": "passport_control", "terminal": "Terminal 4", "lat": 40.6432, "lng": -73.7810, "base_wait": 20},
            {"id": "jfk-t5-tsa-1", "name": "Terminal 5 Security", "type": "tsa", "terminal": "Terminal 5", "lat": 40.6453, "lng": -73.7762, "base_wait": 22},
            {"id": "jfk-t5-tsa-pre", "name": "Terminal 5 TSA PreCheck", "type": "tsa_precheck", "terminal": "Terminal 5", "lat": 40.6454, "lng": -73.7760, "base_wait": 7},
            {"id": "jfk-t5-bag", "name": "Terminal 5 Bag Check", "type": "bag_check", "terminal": "Terminal 5", "lat": 40.6456, "lng": -73.7765, "base_wait": 10},
            {"id": "jfk-t7-tsa-1", "name": "Terminal 7 Security", "type": "tsa", "terminal": "Terminal 7", "lat": 40.6480, "lng": -73.7755, "base_wait": 26},
            {"id": "jfk-t7-tsa-pre", "name": "Terminal 7 TSA PreCheck", "type": "tsa_precheck", "terminal": "Terminal 7", "lat": 40.6481, "lng": -73.7753, "base_wait": 9},
            {"id": "jfk-t7-bag", "name": "Terminal 7 Bag Check", "type": "bag_check", "terminal": "Terminal 7", "lat": 40.6483, "lng": -73.7758, "base_wait": 14},
            {"id": "jfk-t8-tsa-1", "name": "Terminal 8 Security", "type": "tsa", "terminal": "Terminal 8", "lat": 40.6455, "lng": -73.7850, "base_wait": 24},
            {"id": "jfk-t8-tsa-pre", "name": "Terminal 8 TSA PreCheck", "type": "tsa_precheck", "terminal": "Terminal 8", "lat": 40.6456, "lng": -73.7848, "base_wait": 8},
            {"id": "jfk-t8-bag", "name": "Terminal 8 Bag Check", "type": "bag_check", "terminal": "Terminal 8", "lat": 40.6458, "lng": -73.7855, "base_wait": 13},
        ],
        "gates": {
            "Terminal 1": {
                "1A": {"lat": 40.6420, "lng": -73.7895}, "1B": {"lat": 40.6418, "lng": -73.7893}, 
                "1C": {"lat": 40.6416, "lng": -73.7891}, "1D": {"lat": 40.6414, "lng": -73.7889},
            },
            "Terminal 4": {
                "A1": {"lat": 40.6425, "lng": -73.7805}, "A2": {"lat": 40.6423, "lng": -73.7803},
                "B20": {"lat": 40.6430, "lng": -73.7795}, "B21": {"lat": 40.6428, "lng": -73.7793},
            },
            "Terminal 5": {
                "1": {"lat": 40.6445, "lng": -73.7755}, "2": {"lat": 40.6443, "lng": -73.7753},
                "3": {"lat": 40.6441, "lng": -73.7751}, "4": {"lat": 40.6439, "lng": -73.7749},
            },
            "Terminal 7": {
                "1": {"lat": 40.6472, "lng": -73.7748}, "2": {"lat": 40.6470, "lng": -73.7746},
            },
            "Terminal 8": {
                "1": {"lat": 40.6447, "lng": -73.7858}, "2": {"lat": 40.6445, "lng": -73.7856},
            },
        }
    },
    "LAX": {
        "code": "LAX",
        "name": "Los Angeles International Airport",
        "city": "Los Angeles",
        "lat": 33.9425,
        "lng": -118.4081,
        "terminals": ["Terminal 1", "Terminal 2", "Terminal 3", "Terminal 4", "Terminal 5", "Terminal 6", "Terminal 7", "Terminal 8", "Tom Bradley International"],
        "checkpoints": [
            {"id": "lax-t1-tsa", "name": "Terminal 1 Security", "type": "tsa", "terminal": "Terminal 1", "lat": 33.9462, "lng": -118.4015, "base_wait": 20},
            {"id": "lax-t1-tsa-pre", "name": "Terminal 1 TSA PreCheck", "type": "tsa_precheck", "terminal": "Terminal 1", "lat": 33.9463, "lng": -118.4013, "base_wait": 6},
            {"id": "lax-t1-bag", "name": "Terminal 1 Bag Check", "type": "bag_check", "terminal": "Terminal 1", "lat": 33.9465, "lng": -118.4018, "base_wait": 10},
            {"id": "lax-t2-tsa", "name": "Terminal 2 Security", "type": "tsa", "terminal": "Terminal 2", "lat": 33.9455, "lng": -118.4005, "base_wait": 22},
            {"id": "lax-t2-tsa-pre", "name": "Terminal 2 TSA PreCheck", "type": "tsa_precheck", "terminal": "Terminal 2", "lat": 33.9456, "lng": -118.4003, "base_wait": 7},
            {"id": "lax-t3-tsa", "name": "Terminal 3 Security", "type": "tsa", "terminal": "Terminal 3", "lat": 33.9448, "lng": -118.3995, "base_wait": 25},
            {"id": "lax-t3-tsa-pre", "name": "Terminal 3 TSA PreCheck", "type": "tsa_precheck", "terminal": "Terminal 3", "lat": 33.9449, "lng": -118.3993, "base_wait": 8},
            {"id": "lax-t4-tsa", "name": "Terminal 4 Security", "type": "tsa", "terminal": "Terminal 4", "lat": 33.9432, "lng": -118.4060, "base_wait": 23},
            {"id": "lax-t5-tsa", "name": "Terminal 5 Security", "type": "tsa", "terminal": "Terminal 5", "lat": 33.9438, "lng": -118.4045, "base_wait": 21},
            {"id": "lax-t6-tsa", "name": "Terminal 6 Security", "type": "tsa", "terminal": "Terminal 6", "lat": 33.9445, "lng": -118.4030, "base_wait": 24},
            {"id": "lax-t7-tsa", "name": "Terminal 7 Security", "type": "tsa", "terminal": "Terminal 7", "lat": 33.9452, "lng": -118.4020, "base_wait": 26},
            {"id": "lax-t8-tsa", "name": "Terminal 8 Security", "type": "tsa", "terminal": "Terminal 8", "lat": 33.9458, "lng": -118.4010, "base_wait": 22},
            {"id": "lax-tbit-tsa", "name": "TBIT Security", "type": "tsa", "terminal": "Tom Bradley International", "lat": 33.9425, "lng": -118.4081, "base_wait": 35},
            {"id": "lax-tbit-tsa-pre", "name": "TBIT TSA PreCheck", "type": "tsa_precheck", "terminal": "Tom Bradley International", "lat": 33.9426, "lng": -118.4079, "base_wait": 12},
            {"id": "lax-tbit-passport", "name": "TBIT Passport Control", "type": "passport_control", "terminal": "Tom Bradley International", "lat": 33.9420, "lng": -118.4085, "base_wait": 25},
        ],
        "gates": {
            "Terminal 1": {"1": {"lat": 33.9455, "lng": -118.4010}, "2": {"lat": 33.9453, "lng": -118.4008}},
            "Terminal 2": {"21": {"lat": 33.9448, "lng": -118.4000}, "22": {"lat": 33.9446, "lng": -118.3998}},
            "Terminal 3": {"31": {"lat": 33.9441, "lng": -118.3990}, "32": {"lat": 33.9439, "lng": -118.3988}},
            "Terminal 4": {"41": {"lat": 33.9425, "lng": -118.4055}, "42": {"lat": 33.9423, "lng": -118.4053}},
            "Terminal 5": {"51": {"lat": 33.9431, "lng": -118.4040}, "52": {"lat": 33.9429, "lng": -118.4038}},
            "Terminal 6": {"61": {"lat": 33.9438, "lng": -118.4025}, "62": {"lat": 33.9436, "lng": -118.4023}},
            "Terminal 7": {"71": {"lat": 33.9445, "lng": -118.4015}, "72": {"lat": 33.9443, "lng": -118.4013}},
            "Terminal 8": {"81": {"lat": 33.9451, "lng": -118.4005}, "82": {"lat": 33.9449, "lng": -118.4003}},
            "Tom Bradley International": {"101": {"lat": 33.9418, "lng": -118.4090}, "102": {"lat": 33.9416, "lng": -118.4088}},
        }
    },
    "ORD": {
        "code": "ORD",
        "name": "O'Hare International Airport",
        "city": "Chicago",
        "lat": 41.9742,
        "lng": -87.9073,
        "terminals": ["Terminal 1", "Terminal 2", "Terminal 3", "Terminal 5"],
        "checkpoints": [
            {"id": "ord-t1-tsa-1", "name": "Terminal 1 Security L", "type": "tsa", "terminal": "Terminal 1", "lat": 41.9785, "lng": -87.9045, "base_wait": 28},
            {"id": "ord-t1-tsa-2", "name": "Terminal 1 Security C", "type": "tsa", "terminal": "Terminal 1", "lat": 41.9783, "lng": -87.9040, "base_wait": 25},
            {"id": "ord-t1-tsa-pre", "name": "Terminal 1 TSA PreCheck", "type": "tsa_precheck", "terminal": "Terminal 1", "lat": 41.9784, "lng": -87.9043, "base_wait": 9},
            {"id": "ord-t1-bag", "name": "Terminal 1 Bag Check", "type": "bag_check", "terminal": "Terminal 1", "lat": 41.9788, "lng": -87.9050, "base_wait": 15},
            {"id": "ord-t2-tsa", "name": "Terminal 2 Security", "type": "tsa", "terminal": "Terminal 2", "lat": 41.9765, "lng": -87.9085, "base_wait": 22},
            {"id": "ord-t2-tsa-pre", "name": "Terminal 2 TSA PreCheck", "type": "tsa_precheck", "terminal": "Terminal 2", "lat": 41.9766, "lng": -87.9083, "base_wait": 7},
            {"id": "ord-t3-tsa-h", "name": "Terminal 3 Security H", "type": "tsa", "terminal": "Terminal 3", "lat": 41.9745, "lng": -87.9100, "base_wait": 30},
            {"id": "ord-t3-tsa-k", "name": "Terminal 3 Security K", "type": "tsa", "terminal": "Terminal 3", "lat": 41.9743, "lng": -87.9095, "base_wait": 27},
            {"id": "ord-t3-tsa-pre", "name": "Terminal 3 TSA PreCheck", "type": "tsa_precheck", "terminal": "Terminal 3", "lat": 41.9744, "lng": -87.9098, "base_wait": 10},
            {"id": "ord-t5-tsa", "name": "Terminal 5 Security", "type": "tsa", "terminal": "Terminal 5", "lat": 41.9720, "lng": -87.9150, "base_wait": 35},
            {"id": "ord-t5-tsa-pre", "name": "Terminal 5 TSA PreCheck", "type": "tsa_precheck", "terminal": "Terminal 5", "lat": 41.9721, "lng": -87.9148, "base_wait": 12},
            {"id": "ord-t5-passport", "name": "Terminal 5 Passport Control", "type": "passport_control", "terminal": "Terminal 5", "lat": 41.9715, "lng": -87.9155, "base_wait": 22},
        ],
        "gates": {
            "Terminal 1": {"B1": {"lat": 41.9778, "lng": -87.9035}, "C1": {"lat": 41.9780, "lng": -87.9030}},
            "Terminal 2": {"E1": {"lat": 41.9758, "lng": -87.9080}, "F1": {"lat": 41.9760, "lng": -87.9075}},
            "Terminal 3": {"G1": {"lat": 41.9738, "lng": -87.9095}, "H1": {"lat": 41.9740, "lng": -87.9090}},
            "Terminal 5": {"M1": {"lat": 41.9713, "lng": -87.9145}, "M2": {"lat": 41.9711, "lng": -87.9143}},
        }
    },
    "ATL": {
        "code": "ATL",
        "name": "Hartsfield-Jackson Atlanta International Airport",
        "city": "Atlanta",
        "lat": 33.6407,
        "lng": -84.4277,
        "terminals": ["Domestic Terminal North", "Domestic Terminal South", "International Terminal"],
        "checkpoints": [
            {"id": "atl-north-tsa", "name": "North Security", "type": "tsa", "terminal": "Domestic Terminal North", "lat": 33.6405, "lng": -84.4265, "base_wait": 25},
            {"id": "atl-north-tsa-pre", "name": "North TSA PreCheck", "type": "tsa_precheck", "terminal": "Domestic Terminal North", "lat": 33.6406, "lng": -84.4263, "base_wait": 8},
            {"id": "atl-north-bag", "name": "North Bag Check", "type": "bag_check", "terminal": "Domestic Terminal North", "lat": 33.6408, "lng": -84.4270, "base_wait": 12},
            {"id": "atl-south-tsa", "name": "South Security", "type": "tsa", "terminal": "Domestic Terminal South", "lat": 33.6395, "lng": -84.4265, "base_wait": 28},
            {"id": "atl-south-tsa-pre", "name": "South TSA PreCheck", "type": "tsa_precheck", "terminal": "Domestic Terminal South", "lat": 33.6396, "lng": -84.4263, "base_wait": 9},
            {"id": "atl-south-bag", "name": "South Bag Check", "type": "bag_check", "terminal": "Domestic Terminal South", "lat": 33.6398, "lng": -84.4270, "base_wait": 14},
            {"id": "atl-intl-tsa", "name": "International Security", "type": "tsa", "terminal": "International Terminal", "lat": 33.6365, "lng": -84.4350, "base_wait": 30},
            {"id": "atl-intl-tsa-pre", "name": "International TSA PreCheck", "type": "tsa_precheck", "terminal": "International Terminal", "lat": 33.6366, "lng": -84.4348, "base_wait": 10},
            {"id": "atl-intl-passport", "name": "International Passport Control", "type": "passport_control", "terminal": "International Terminal", "lat": 33.6360, "lng": -84.4355, "base_wait": 20},
        ],
        "gates": {
            "Domestic Terminal North": {"A1": {"lat": 33.6398, "lng": -84.4255}, "A2": {"lat": 33.6396, "lng": -84.4253}},
            "Domestic Terminal South": {"T1": {"lat": 33.6388, "lng": -84.4255}, "T2": {"lat": 33.6386, "lng": -84.4253}},
            "International Terminal": {"E1": {"lat": 33.6358, "lng": -84.4345}, "E2": {"lat": 33.6356, "lng": -84.4343}},
        }
    },
    "DFW": {
        "code": "DFW",
        "name": "Dallas/Fort Worth International Airport",
        "city": "Dallas",
        "lat": 32.8998,
        "lng": -97.0403,
        "terminals": ["Terminal A", "Terminal B", "Terminal C", "Terminal D", "Terminal E"],
        "checkpoints": [
            {"id": "dfw-a-tsa", "name": "Terminal A Security", "type": "tsa", "terminal": "Terminal A", "lat": 32.8985, "lng": -97.0380, "base_wait": 22},
            {"id": "dfw-a-tsa-pre", "name": "Terminal A TSA PreCheck", "type": "tsa_precheck", "terminal": "Terminal A", "lat": 32.8986, "lng": -97.0378, "base_wait": 7},
            {"id": "dfw-b-tsa", "name": "Terminal B Security", "type": "tsa", "terminal": "Terminal B", "lat": 32.8995, "lng": -97.0400, "base_wait": 25},
            {"id": "dfw-b-tsa-pre", "name": "Terminal B TSA PreCheck", "type": "tsa_precheck", "terminal": "Terminal B", "lat": 32.8996, "lng": -97.0398, "base_wait": 8},
            {"id": "dfw-c-tsa", "name": "Terminal C Security", "type": "tsa", "terminal": "Terminal C", "lat": 32.9005, "lng": -97.0420, "base_wait": 28},
            {"id": "dfw-c-tsa-pre", "name": "Terminal C TSA PreCheck", "type": "tsa_precheck", "terminal": "Terminal C", "lat": 32.9006, "lng": -97.0418, "base_wait": 9},
            {"id": "dfw-d-tsa", "name": "Terminal D Security", "type": "tsa", "terminal": "Terminal D", "lat": 32.9015, "lng": -97.0440, "base_wait": 30},
            {"id": "dfw-d-tsa-pre", "name": "Terminal D TSA PreCheck", "type": "tsa_precheck", "terminal": "Terminal D", "lat": 32.9016, "lng": -97.0438, "base_wait": 10},
            {"id": "dfw-d-passport", "name": "Terminal D Passport Control", "type": "passport_control", "terminal": "Terminal D", "lat": 32.9010, "lng": -97.0445, "base_wait": 18},
            {"id": "dfw-e-tsa", "name": "Terminal E Security", "type": "tsa", "terminal": "Terminal E", "lat": 32.9025, "lng": -97.0460, "base_wait": 24},
            {"id": "dfw-e-tsa-pre", "name": "Terminal E TSA PreCheck", "type": "tsa_precheck", "terminal": "Terminal E", "lat": 32.9026, "lng": -97.0458, "base_wait": 8},
        ],
        "gates": {
            "Terminal A": {"A1": {"lat": 32.8978, "lng": -97.0375}, "A2": {"lat": 32.8976, "lng": -97.0373}},
            "Terminal B": {"B1": {"lat": 32.8988, "lng": -97.0395}, "B2": {"lat": 32.8986, "lng": -97.0393}},
            "Terminal C": {"C1": {"lat": 32.8998, "lng": -97.0415}, "C2": {"lat": 32.8996, "lng": -97.0413}},
            "Terminal D": {"D1": {"lat": 32.9008, "lng": -97.0435}, "D2": {"lat": 32.9006, "lng": -97.0433}},
            "Terminal E": {"E1": {"lat": 32.9018, "lng": -97.0455}, "E2": {"lat": 32.9016, "lng": -97.0453}},
        }
    },
    "SFO": {
        "code": "SFO",
        "name": "San Francisco International Airport",
        "city": "San Francisco",
        "lat": 37.6213,
        "lng": -122.3790,
        "terminals": ["Terminal 1", "Terminal 2", "Terminal 3", "International Terminal"],
        "checkpoints": [
            {"id": "sfo-t1-tsa", "name": "Terminal 1 Security", "type": "tsa", "terminal": "Terminal 1", "lat": 37.6165, "lng": -122.3855, "base_wait": 22},
            {"id": "sfo-t1-tsa-pre", "name": "Terminal 1 TSA PreCheck", "type": "tsa_precheck", "terminal": "Terminal 1", "lat": 37.6166, "lng": -122.3853, "base_wait": 7},
            {"id": "sfo-t2-tsa", "name": "Terminal 2 Security", "type": "tsa", "terminal": "Terminal 2", "lat": 37.6175, "lng": -122.3835, "base_wait": 20},
            {"id": "sfo-t2-tsa-pre", "name": "Terminal 2 TSA PreCheck", "type": "tsa_precheck", "terminal": "Terminal 2", "lat": 37.6176, "lng": -122.3833, "base_wait": 6},
            {"id": "sfo-t3-tsa", "name": "Terminal 3 Security", "type": "tsa", "terminal": "Terminal 3", "lat": 37.6185, "lng": -122.3815, "base_wait": 25},
            {"id": "sfo-t3-tsa-pre", "name": "Terminal 3 TSA PreCheck", "type": "tsa_precheck", "terminal": "Terminal 3", "lat": 37.6186, "lng": -122.3813, "base_wait": 8},
            {"id": "sfo-intl-tsa", "name": "International Security", "type": "tsa", "terminal": "International Terminal", "lat": 37.6155, "lng": -122.3900, "base_wait": 30},
            {"id": "sfo-intl-tsa-pre", "name": "International TSA PreCheck", "type": "tsa_precheck", "terminal": "International Terminal", "lat": 37.6156, "lng": -122.3898, "base_wait": 10},
            {"id": "sfo-intl-passport", "name": "International Passport Control", "type": "passport_control", "terminal": "International Terminal", "lat": 37.6150, "lng": -122.3905, "base_wait": 22},
        ],
        "gates": {
            "Terminal 1": {"B1": {"lat": 37.6158, "lng": -122.3850}, "B2": {"lat": 37.6156, "lng": -122.3848}},
            "Terminal 2": {"D1": {"lat": 37.6168, "lng": -122.3830}, "D2": {"lat": 37.6166, "lng": -122.3828}},
            "Terminal 3": {"E1": {"lat": 37.6178, "lng": -122.3810}, "E2": {"lat": 37.6176, "lng": -122.3808}},
            "International Terminal": {"A1": {"lat": 37.6148, "lng": -122.3895}, "G1": {"lat": 37.6145, "lng": -122.3910}},
        }
    },
    "MIA": {
        "code": "MIA",
        "name": "Miami International Airport",
        "city": "Miami",
        "lat": 25.7959,
        "lng": -80.2870,
        "terminals": ["North Terminal", "Central Terminal", "South Terminal"],
        "checkpoints": [
            {"id": "mia-north-tsa", "name": "North Terminal Security", "type": "tsa", "terminal": "North Terminal", "lat": 25.7975, "lng": -80.2855, "base_wait": 28},
            {"id": "mia-north-tsa-pre", "name": "North Terminal TSA PreCheck", "type": "tsa_precheck", "terminal": "North Terminal", "lat": 25.7976, "lng": -80.2853, "base_wait": 9},
            {"id": "mia-central-tsa", "name": "Central Terminal Security", "type": "tsa", "terminal": "Central Terminal", "lat": 25.7960, "lng": -80.2870, "base_wait": 25},
            {"id": "mia-central-tsa-pre", "name": "Central Terminal TSA PreCheck", "type": "tsa_precheck", "terminal": "Central Terminal", "lat": 25.7961, "lng": -80.2868, "base_wait": 8},
            {"id": "mia-south-tsa", "name": "South Terminal Security", "type": "tsa", "terminal": "South Terminal", "lat": 25.7945, "lng": -80.2885, "base_wait": 30},
            {"id": "mia-south-tsa-pre", "name": "South Terminal TSA PreCheck", "type": "tsa_precheck", "terminal": "South Terminal", "lat": 25.7946, "lng": -80.2883, "base_wait": 10},
            {"id": "mia-south-passport", "name": "South Terminal Passport Control", "type": "passport_control", "terminal": "South Terminal", "lat": 25.7940, "lng": -80.2890, "base_wait": 22},
        ],
        "gates": {
            "North Terminal": {"D1": {"lat": 25.7968, "lng": -80.2850}, "D2": {"lat": 25.7966, "lng": -80.2848}},
            "Central Terminal": {"E1": {"lat": 25.7953, "lng": -80.2865}, "E2": {"lat": 25.7951, "lng": -80.2863}},
            "South Terminal": {"J1": {"lat": 25.7938, "lng": -80.2880}, "J2": {"lat": 25.7936, "lng": -80.2878}},
        }
    },
    "DEN": {
        "code": "DEN",
        "name": "Denver International Airport",
        "city": "Denver",
        "lat": 39.8561,
        "lng": -104.6737,
        "terminals": ["Jeppesen Terminal", "Concourse A", "Concourse B", "Concourse C"],
        "checkpoints": [
            {"id": "den-main-tsa-n", "name": "North Security", "type": "tsa", "terminal": "Jeppesen Terminal", "lat": 39.8575, "lng": -104.6730, "base_wait": 25},
            {"id": "den-main-tsa-s", "name": "South Security", "type": "tsa", "terminal": "Jeppesen Terminal", "lat": 39.8565, "lng": -104.6730, "base_wait": 28},
            {"id": "den-main-tsa-pre", "name": "TSA PreCheck", "type": "tsa_precheck", "terminal": "Jeppesen Terminal", "lat": 39.8570, "lng": -104.6728, "base_wait": 8},
            {"id": "den-main-bag", "name": "Main Bag Check", "type": "bag_check", "terminal": "Jeppesen Terminal", "lat": 39.8580, "lng": -104.6735, "base_wait": 12},
            {"id": "den-a-tsa", "name": "Concourse A Security", "type": "tsa", "terminal": "Concourse A", "lat": 39.8520, "lng": -104.6700, "base_wait": 20},
            {"id": "den-a-passport", "name": "Concourse A Passport Control", "type": "passport_control", "terminal": "Concourse A", "lat": 39.8515, "lng": -104.6705, "base_wait": 18},
        ],
        "gates": {
            "Jeppesen Terminal": {"Main": {"lat": 39.8570, "lng": -104.6725}},
            "Concourse A": {"A1": {"lat": 39.8513, "lng": -104.6695}, "A2": {"lat": 39.8511, "lng": -104.6693}},
            "Concourse B": {"B1": {"lat": 39.8545, "lng": -104.6680}, "B2": {"lat": 39.8543, "lng": -104.6678}},
            "Concourse C": {"C1": {"lat": 39.8530, "lng": -104.6660}, "C2": {"lat": 39.8528, "lng": -104.6658}},
        }
    },
    "SEA": {
        "code": "SEA",
        "name": "Seattle-Tacoma International Airport",
        "city": "Seattle",
        "lat": 47.4502,
        "lng": -122.3088,
        "terminals": ["Main Terminal", "North Satellite", "South Satellite"],
        "checkpoints": [
            {"id": "sea-main-tsa-1", "name": "Checkpoint 1", "type": "tsa", "terminal": "Main Terminal", "lat": 47.4495, "lng": -122.3085, "base_wait": 22},
            {"id": "sea-main-tsa-2", "name": "Checkpoint 2", "type": "tsa", "terminal": "Main Terminal", "lat": 47.4498, "lng": -122.3080, "base_wait": 25},
            {"id": "sea-main-tsa-3", "name": "Checkpoint 3", "type": "tsa", "terminal": "Main Terminal", "lat": 47.4492, "lng": -122.3090, "base_wait": 28},
            {"id": "sea-main-tsa-pre", "name": "TSA PreCheck", "type": "tsa_precheck", "terminal": "Main Terminal", "lat": 47.4496, "lng": -122.3083, "base_wait": 8},
            {"id": "sea-main-bag", "name": "Main Bag Check", "type": "bag_check", "terminal": "Main Terminal", "lat": 47.4500, "lng": -122.3095, "base_wait": 12},
            {"id": "sea-south-passport", "name": "South Satellite Passport Control", "type": "passport_control", "terminal": "South Satellite", "lat": 47.4450, "lng": -122.3050, "base_wait": 20},
        ],
        "gates": {
            "Main Terminal": {"A1": {"lat": 47.4488, "lng": -122.3080}, "A2": {"lat": 47.4486, "lng": -122.3078}},
            "North Satellite": {"N1": {"lat": 47.4520, "lng": -122.3060}, "N2": {"lat": 47.4518, "lng": -122.3058}},
            "South Satellite": {"S1": {"lat": 47.4445, "lng": -122.3045}, "S2": {"lat": 47.4443, "lng": -122.3043}},
        }
    },
}


def get_gate_position(airport_code: str, terminal: str, gate: str) -> tuple[float, float]:
    """Get the GPS coordinates for a specific gate."""
    airport_data = AIRPORTS_DATA.get(airport_code)
    if not airport_data:
        return 0.0, 0.0
    gates = airport_data.get("gates", {}).get(terminal, {})
    if gate in gates:
        return gates[gate]["lat"], gates[gate]["lng"]
    if gates:
        first_gate = list(gates.values())[0]
        return first_gate["lat"], first_gate["lng"]
    return airport_data["lat"], airport_data["lng"]
