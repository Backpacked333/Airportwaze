from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import httpx
import random
import math
import numpy as np
from scipy import stats
import logging

# Database imports
from app.database import SessionLocal, init_db, get_db
from app.models import Airport as DBAirport, Checkpoint as DBCheckpoint
from app.db_helpers import airport_to_api_model, checkpoint_to_api_model, get_wait_time_distribution

# Data source imports
from app.data_sources.tsa_api import TSAWaitTimeAPI
from app.data_sources.cbp_api import CBPWaitTimeAPI
from app.data_sources.flight_data import FlightDataAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Airport Waze API", description="Real-time airport wait times and journey planning")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize data source APIs on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and data source APIs on application startup."""
    logger.info("🚀 Starting AirportWaze API...")

    # Initialize database schema
    logger.info("📊 Initializing database...")
    init_db()
    logger.info("✅ Database initialized")

    # Initialize data source APIs
    logger.info("🔌 Initializing data source APIs...")
    app.state.tsa_api = TSAWaitTimeAPI()
    app.state.cbp_api = CBPWaitTimeAPI()
    app.state.flight_api = FlightDataAPI()
    logger.info("✅ Data sources initialized")

    logger.info("✅ AirportWaze API started successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("👋 Shutting down AirportWaze API...")

# ============== DATA MODELS ==============

class Checkpoint(BaseModel):
    id: str
    name: str
    type: str
    terminal: str
    lat: float
    lng: float
    current_wait_minutes: int
    historical_avg_minutes: int
    status: str
    last_updated: str

class Airport(BaseModel):
    code: str
    name: str
    city: str
    lat: float
    lng: float
    terminals: list[str]
    checkpoints: list[Checkpoint]

class JourneyRequest(BaseModel):
    airport_code: str
    terminal: str
    gate: str
    has_tsa_precheck: bool = False
    has_global_entry: bool = False
    has_checked_bags: bool = True
    mobility_factor: float = 1.0
    departure_time: Optional[str] = None
    user_lat: Optional[float] = None
    user_lng: Optional[float] = None

class JourneyStep(BaseModel):
    step_name: str
    location: str
    lat: float
    lng: float
    estimated_wait_minutes: int
    estimated_walk_minutes: int
    distance_meters: int
    checkpoint_id: Optional[str] = None

class JourneyPlan(BaseModel):
    total_time_minutes: int
    total_distance_meters: int
    recommended_arrival_time: str
    steps: list[JourneyStep]
    buffer_minutes: int

class WaitTimeReport(BaseModel):
    airport_code: str
    checkpoint_id: str
    reported_wait_minutes: int
    reporter_id: Optional[str] = None
    user_lat: Optional[float] = None
    user_lng: Optional[float] = None

# ============== NEW MVP DATA MODELS ==============

class WaitTimeDistribution(BaseModel):
    """Probabilistic wait time using log-normal distribution"""
    p50: int  # median (50th percentile)
    p80: int  # 80th percentile
    p90: int  # 90th percentile
    p95: int  # 95th percentile
    mu: float  # log-normal mu parameter
    sigma: float  # log-normal sigma parameter
    sample_size: int  # number of observations
    confidence: str  # "high", "medium", "low" based on data quality

class Flight(BaseModel):
    """User's flight information"""
    flight_number: Optional[str] = None
    airline: Optional[str] = None
    departure_time: str  # ISO format
    terminal: str
    gate: str
    airport_code: str

class WillIMakeItRequest(BaseModel):
    """Request for 'Will I make it?' probability calculation"""
    flight: Flight
    has_tsa_precheck: bool = False
    has_global_entry: bool = False
    has_checked_bags: bool = True
    mobility_factor: float = 1.0
    current_time: Optional[str] = None  # ISO format, defaults to now
    user_lat: Optional[float] = None
    user_lng: Optional[float] = None

class SegmentDistribution(BaseModel):
    """Time distribution for a journey segment"""
    step_name: str
    location: str
    lat: float
    lng: float
    wait_distribution: Optional[WaitTimeDistribution] = None
    walk_minutes: int
    walk_distance_meters: int
    checkpoint_id: Optional[str] = None

class WillIMakeItResponse(BaseModel):
    """Response with probability of making flight"""
    probability_of_making_it: float  # 0.0 to 1.0
    probability_percentage: int  # 0 to 100
    status: str  # "safe", "risky", "unlikely", "very_unlikely"
    status_message: str
    total_time_p50: int  # median total time
    total_time_p80: int  # 80th percentile
    total_time_p90: int  # 90th percentile
    total_time_p95: int  # 95th percentile
    time_until_boarding: int  # minutes until boarding closes
    buffer_minutes: int  # recommended buffer
    leave_by_80: str  # ISO time to leave for 80% confidence
    leave_by_90: str  # ISO time to leave for 90% confidence
    leave_by_95: str  # ISO time to leave for 95% confidence
    segments: List[SegmentDistribution]
    simulation_runs: int  # number of Monte Carlo simulations
    boarding_cutoff_minutes: int  # minutes before departure when boarding closes

# ============== AIRPORT DATA WITH REAL GPS COORDINATES ==============

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

crowdsourced_reports: list[dict] = []

def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def get_time_multiplier() -> float:
    now = datetime.utcnow()
    hour = now.hour
    day = now.weekday()
    if 6 <= hour <= 9 or 16 <= hour <= 20:
        multiplier = 1.4
    elif 22 <= hour or hour <= 5:
        multiplier = 0.6
    else:
        multiplier = 1.0
    if day in [4, 5, 6]:
        multiplier *= 1.2
    return multiplier

def calculate_current_wait(base_wait: int) -> int:
    multiplier = get_time_multiplier()
    variation = random.uniform(0.8, 1.2)
    return max(2, min(int(base_wait * multiplier * variation), 90))

def get_checkpoint_status(wait_minutes: int) -> str:
    if wait_minutes <= 10:
        return "low"
    elif wait_minutes <= 25:
        return "moderate"
    elif wait_minutes <= 40:
        return "high"
    return "very_high"

def calculate_walking_time(lat1: float, lng1: float, lat2: float, lng2: float, mobility_factor: float = 1.0) -> tuple[int, int]:
    distance = haversine_distance(lat1, lng1, lat2, lng2)
    walking_speed = 1.4 / mobility_factor
    time_seconds = distance / walking_speed
    return int(time_seconds / 60) + 1, int(distance)

def get_gate_position(airport_code: str, terminal: str, gate: str) -> tuple[float, float]:
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

# ============== PROBABILISTIC HELPER FUNCTIONS ==============

def get_wait_time_distribution(base_wait: int, checkpoint_type: str) -> WaitTimeDistribution:
    """
    Generate a log-normal wait time distribution for a checkpoint.
    Uses the base wait time and applies time-of-day multiplier.
    Sigma varies by checkpoint type (bag check has more variance than TSA PreCheck).
    """
    multiplier = get_time_multiplier()
    median_wait = max(2, base_wait * multiplier)
    
    # Sigma (variance) depends on checkpoint type
    # Bag check has highest variance, TSA PreCheck has lowest
    sigma_map = {
        "bag_check": 0.5,      # High variance - depends on airline, time, etc.
        "tsa": 0.4,            # Moderate variance
        "tsa_precheck": 0.25,  # Low variance - more predictable
        "passport_control": 0.45,  # Moderate-high variance
    }
    sigma = sigma_map.get(checkpoint_type, 0.4)
    
    # For log-normal: if we want median = m, then mu = ln(m)
    mu = np.log(median_wait)
    
    # Calculate percentiles using log-normal distribution
    p50 = int(np.exp(mu))  # median
    p80 = int(np.exp(mu + sigma * stats.norm.ppf(0.80)))
    p90 = int(np.exp(mu + sigma * stats.norm.ppf(0.90)))
    p95 = int(np.exp(mu + sigma * stats.norm.ppf(0.95)))
    
    # Determine confidence based on data quality (simulated for now)
    # In production, this would be based on actual sample size
    sample_size = random.randint(50, 500)
    if sample_size >= 200:
        confidence = "high"
    elif sample_size >= 100:
        confidence = "medium"
    else:
        confidence = "low"
    
    return WaitTimeDistribution(
        p50=max(1, p50),
        p80=max(1, p80),
        p90=max(1, p90),
        p95=max(1, p95),
        mu=round(mu, 4),
        sigma=round(sigma, 4),
        sample_size=sample_size,
        confidence=confidence
    )

def sample_wait_time(distribution: WaitTimeDistribution) -> float:
    """Sample a single wait time from the distribution for Monte Carlo simulation."""
    return max(1, np.random.lognormal(distribution.mu, distribution.sigma))

def sample_walking_time(base_minutes: int, mobility_factor: float = 1.0) -> float:
    """
    Sample walking time with some variance.
    Walking time is more predictable than wait times, so use smaller sigma.
    """
    # Walking time has low variance (sigma = 0.15)
    mu = np.log(max(1, base_minutes))
    sigma = 0.15 * mobility_factor  # Slower walkers have more variance
    return max(0.5, np.random.lognormal(mu, sigma))

def run_monte_carlo_simulation(
    segments: list[dict],
    num_simulations: int = 10000
) -> tuple[np.ndarray, list[np.ndarray]]:
    """
    Run Monte Carlo simulation to get distribution of total journey times.
    Returns array of total times and list of arrays for each segment.
    """
    total_times = np.zeros(num_simulations)
    segment_times = [np.zeros(num_simulations) for _ in segments]
    
    for i in range(num_simulations):
        total = 0
        for j, seg in enumerate(segments):
            # Sample wait time if there's a distribution
            if seg.get("wait_distribution"):
                wait = sample_wait_time(seg["wait_distribution"])
            else:
                wait = 0
            
            # Sample walking time
            walk = sample_walking_time(seg["walk_minutes"], seg.get("mobility_factor", 1.0))
            
            segment_time = wait + walk
            segment_times[j][i] = segment_time
            total += segment_time
        
        total_times[i] = total
    
    return total_times, segment_times

def calculate_probability_of_making_it(
    total_times: np.ndarray,
    time_available: float
) -> float:
    """Calculate probability of making it given simulated total times and available time."""
    return float(np.mean(total_times <= time_available))

def get_status_from_probability(prob: float) -> tuple[str, str]:
    """Get status label and message from probability."""
    if prob >= 0.95:
        return "safe", "You're in great shape! Plenty of time to spare."
    elif prob >= 0.80:
        return "good", "You should make it comfortably."
    elif prob >= 0.60:
        return "risky", "It's going to be close. Consider leaving soon."
    elif prob >= 0.40:
        return "unlikely", "High risk of missing your flight. Leave immediately!"
    else:
        return "very_unlikely", "Very high risk of missing your flight. You may need to rebook."

@app.get("/healthz")
async def healthz():
    return {"status": "healthy"}

@app.get("/api/airports")
async def get_airports(db: Session = Depends(get_db)):
    """Get list of all airports from database."""
    airports = db.query(DBAirport).all()
    return {
        "airports": [
            airport_to_api_model(db, airport, include_checkpoints=False)
            for airport in airports
        ]
    }

@app.get("/api/airports/{airport_code}")
async def get_airport(airport_code: str, db: Session = Depends(get_db)):
    """
    Get airport details with current checkpoint wait times from database.
    Optionally integrates TSA/CBP real-time data if available.
    """
    airport_code = airport_code.upper()

    # Query airport from database
    airport = db.query(DBAirport).filter(DBAirport.code == airport_code).first()

    if not airport:
        raise HTTPException(status_code=404, detail="Airport not found")

    # Try to get TSA wait times for this airport
    try:
        tsa_waits = await app.state.tsa_api.get_wait_times(airport_code)
        if tsa_waits:
            logger.info(f"📡 Got TSA data for {airport_code}: {len(tsa_waits)} checkpoints")
            # TSA data will be used in checkpoint_to_api_model via database observations
    except Exception as e:
        logger.warning(f"TSA API error for {airport_code}: {e}")

    # Try to get CBP wait times
    try:
        cbp_waits = await app.state.cbp_api.get_wait_times(airport_code)
        if cbp_waits:
            logger.info(f"📡 Got CBP data for {airport_code}: {len(cbp_waits)} checkpoints")
    except Exception as e:
        logger.warning(f"CBP API error for {airport_code}: {e}")

    # Convert to API model (includes all checkpoints with current wait times)
    return Airport(**airport_to_api_model(db, airport, include_checkpoints=True))

@app.get("/api/airports/{airport_code}/terminals/{terminal}/gates")
async def get_terminal_gates(airport_code: str, terminal: str):
    airport_code = airport_code.upper()
    if airport_code not in AIRPORTS_DATA:
        raise HTTPException(status_code=404, detail="Airport not found")
    airport_data = AIRPORTS_DATA[airport_code]
    gates_data = airport_data.get("gates", {}).get(terminal, {})
    gates = [{"name": name, "lat": coords["lat"], "lng": coords["lng"]} for name, coords in gates_data.items()]
    return {"terminal": terminal, "gates": gates}

@app.post("/api/journey/plan")
async def plan_journey(request: JourneyRequest):
    airport_code = request.airport_code.upper()
    if airport_code not in AIRPORTS_DATA:
        raise HTTPException(status_code=404, detail="Airport not found")
    airport_data = AIRPORTS_DATA[airport_code]
    steps = []
    total_time = 0
    total_distance = 0
    if request.user_lat and request.user_lng:
        current_lat, current_lng = request.user_lat, request.user_lng
    else:
        current_lat, current_lng = airport_data["lat"], airport_data["lng"]
    if request.has_checked_bags:
        bag_checkpoints = [cp for cp in airport_data["checkpoints"] if cp["type"] == "bag_check" and cp["terminal"] == request.terminal]
        if bag_checkpoints:
            cp = bag_checkpoints[0]
            walk_time, walk_dist = calculate_walking_time(current_lat, current_lng, cp["lat"], cp["lng"], request.mobility_factor)
            wait_time = calculate_current_wait(cp["base_wait"])
            steps.append(JourneyStep(
                step_name="Bag Check-In",
                location=cp["name"],
                lat=cp["lat"],
                lng=cp["lng"],
                estimated_wait_minutes=wait_time,
                estimated_walk_minutes=walk_time,
                distance_meters=walk_dist,
                checkpoint_id=cp["id"]
            ))
            total_time += walk_time + wait_time
            total_distance += walk_dist
            current_lat, current_lng = cp["lat"], cp["lng"]
    if request.has_tsa_precheck:
        security_checkpoints = [cp for cp in airport_data["checkpoints"] if cp["type"] == "tsa_precheck" and cp["terminal"] == request.terminal]
    else:
        security_checkpoints = [cp for cp in airport_data["checkpoints"] if cp["type"] == "tsa" and cp["terminal"] == request.terminal]
    if not security_checkpoints:
        security_checkpoints = [cp for cp in airport_data["checkpoints"] if cp["type"] in ["tsa", "tsa_precheck"] and cp["terminal"] == request.terminal]
    if security_checkpoints:
        cp = min(security_checkpoints, key=lambda x: calculate_current_wait(x["base_wait"]))
        walk_time, walk_dist = calculate_walking_time(current_lat, current_lng, cp["lat"], cp["lng"], request.mobility_factor)
        wait_time = calculate_current_wait(cp["base_wait"])
        steps.append(JourneyStep(
            step_name="Security Screening" + (" (PreCheck)" if request.has_tsa_precheck else ""),
            location=cp["name"],
            lat=cp["lat"],
            lng=cp["lng"],
            estimated_wait_minutes=wait_time,
            estimated_walk_minutes=walk_time,
            distance_meters=walk_dist,
            checkpoint_id=cp["id"]
        ))
        total_time += walk_time + wait_time
        total_distance += walk_dist
        current_lat, current_lng = cp["lat"], cp["lng"]
    gate_lat, gate_lng = get_gate_position(airport_code, request.terminal, request.gate)
    walk_time, walk_dist = calculate_walking_time(current_lat, current_lng, gate_lat, gate_lng, request.mobility_factor)
    steps.append(JourneyStep(
        step_name="Walk to Gate",
        location=f"Gate {request.gate}",
        lat=gate_lat,
        lng=gate_lng,
        estimated_wait_minutes=0,
        estimated_walk_minutes=walk_time,
        distance_meters=walk_dist,
        checkpoint_id=None
    ))
    total_time += walk_time
    total_distance += walk_dist
    buffer = 30 if any(cp["type"] == "passport_control" for cp in airport_data["checkpoints"] if cp["terminal"] == request.terminal) else 15
    if request.departure_time:
        try:
            departure = datetime.fromisoformat(request.departure_time.replace('Z', '+00:00'))
        except ValueError:
            departure = datetime.utcnow() + timedelta(hours=3)
    else:
        departure = datetime.utcnow() + timedelta(hours=3)
    recommended_arrival = departure - timedelta(minutes=total_time + buffer)
    return JourneyPlan(
        total_time_minutes=total_time,
        total_distance_meters=total_distance,
        recommended_arrival_time=recommended_arrival.isoformat(),
        steps=steps,
        buffer_minutes=buffer
    )

@app.post("/api/wait-times/report")
async def report_wait_time(report: WaitTimeReport):
    report_data = {
        "airport_code": report.airport_code.upper(),
        "checkpoint_id": report.checkpoint_id,
        "reported_wait_minutes": report.reported_wait_minutes,
        "timestamp": datetime.utcnow().isoformat(),
        "reporter_id": report.reporter_id,
        "user_lat": report.user_lat,
        "user_lng": report.user_lng
    }
    crowdsourced_reports.append(report_data)
    if len(crowdsourced_reports) > 1000:
        crowdsourced_reports.pop(0)
    return {"status": "success", "message": "Wait time reported successfully"}

@app.get("/api/wait-times/reports/{airport_code}")
async def get_recent_reports(airport_code: str, limit: int = 20):
    airport_code = airport_code.upper()
    reports = [r for r in crowdsourced_reports if r["airport_code"] == airport_code]
    return {"reports": reports[-limit:]}

@app.get("/api/predictions/{airport_code}")
async def get_predictions(airport_code: str, hours_ahead: int = 24):
    airport_code = airport_code.upper()
    if airport_code not in AIRPORTS_DATA:
        raise HTTPException(status_code=404, detail="Airport not found")
    airport_data = AIRPORTS_DATA[airport_code]
    predictions = []
    now = datetime.utcnow()
    for hour_offset in range(0, min(hours_ahead, 48), 2):
        future_time = now + timedelta(hours=hour_offset)
        hour = future_time.hour
        day = future_time.weekday()
        if 6 <= hour <= 9 or 16 <= hour <= 20:
            mult = 1.4
        elif 22 <= hour or hour <= 5:
            mult = 0.6
        else:
            mult = 1.0
        if day in [4, 5, 6]:
            mult *= 1.2
        checkpoint_predictions = []
        for cp in airport_data["checkpoints"]:
            predicted_wait = int(cp["base_wait"] * mult)
            checkpoint_predictions.append({
                "checkpoint_id": cp["id"],
                "checkpoint_name": cp["name"],
                "lat": cp["lat"],
                "lng": cp["lng"],
                "predicted_wait_minutes": max(2, min(predicted_wait, 90))
            })
        predictions.append({
            "time": future_time.isoformat(),
            "checkpoints": checkpoint_predictions
        })
    return {"airport_code": airport_code, "predictions": predictions}

@app.get("/api/tsa/live")
async def get_live_tsa_data():
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("https://www.tsa.gov/data/apcp.xml")
            if response.status_code == 200:
                return {"source": "tsa_live", "status": "available", "note": "Live TSA data available"}
    except Exception:
        pass
    return {
        "source": "simulated",
        "status": "fallback",
        "note": "Using simulated data based on historical patterns",
        "data_quality": "high",
        "last_model_update": datetime.utcnow().isoformat()
    }

# ============== WILL I MAKE IT? ENDPOINT ==============

@app.post("/api/will-i-make-it", response_model=WillIMakeItResponse)
async def will_i_make_it(request: WillIMakeItRequest):
    """
    Calculate the probability of making your flight using Monte Carlo simulation.
    Returns probability, confidence bands, and leave-by times.
    """
    airport_code = request.flight.airport_code.upper()
    if airport_code not in AIRPORTS_DATA:
        raise HTTPException(status_code=404, detail="Airport not found")
    
    airport_data = AIRPORTS_DATA[airport_code]
    
    # Parse departure time
    try:
        departure_time = datetime.fromisoformat(request.flight.departure_time.replace('Z', '+00:00'))
        if departure_time.tzinfo:
            departure_time = departure_time.replace(tzinfo=None)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid departure time format")
    
    # Parse current time (or use now)
    if request.current_time:
        try:
            current_time = datetime.fromisoformat(request.current_time.replace('Z', '+00:00'))
            if current_time.tzinfo:
                current_time = current_time.replace(tzinfo=None)
        except ValueError:
            current_time = datetime.utcnow()
    else:
        current_time = datetime.utcnow()
    
    # Boarding cutoff: typically 15-30 minutes before departure
    # International flights have longer cutoffs
    has_passport_control = any(
        cp["type"] == "passport_control" 
        for cp in airport_data["checkpoints"] 
        if cp["terminal"] == request.flight.terminal
    )
    boarding_cutoff_minutes = 30 if has_passport_control else 15
    
    # Calculate time until boarding closes
    boarding_time = departure_time - timedelta(minutes=boarding_cutoff_minutes)
    time_until_boarding = (boarding_time - current_time).total_seconds() / 60
    
    # Build journey segments with distributions
    segments = []
    if request.user_lat and request.user_lng:
        current_lat, current_lng = request.user_lat, request.user_lng
    else:
        current_lat, current_lng = airport_data["lat"], airport_data["lng"]
    
    # Bag check segment (if applicable)
    if request.has_checked_bags:
        bag_checkpoints = [
            cp for cp in airport_data["checkpoints"] 
            if cp["type"] == "bag_check" and cp["terminal"] == request.flight.terminal
        ]
        if bag_checkpoints:
            cp = bag_checkpoints[0]
            walk_time, walk_dist = calculate_walking_time(
                current_lat, current_lng, cp["lat"], cp["lng"], request.mobility_factor
            )
            wait_dist = get_wait_time_distribution(cp["base_wait"], cp["type"])
            
            segments.append({
                "step_name": "Bag Check-In",
                "location": cp["name"],
                "lat": cp["lat"],
                "lng": cp["lng"],
                "wait_distribution": wait_dist,
                "walk_minutes": walk_time,
                "walk_distance_meters": walk_dist,
                "checkpoint_id": cp["id"],
                "mobility_factor": request.mobility_factor
            })
            current_lat, current_lng = cp["lat"], cp["lng"]
    
    # Security segment
    if request.has_tsa_precheck:
        security_checkpoints = [
            cp for cp in airport_data["checkpoints"] 
            if cp["type"] == "tsa_precheck" and cp["terminal"] == request.flight.terminal
        ]
    else:
        security_checkpoints = [
            cp for cp in airport_data["checkpoints"] 
            if cp["type"] == "tsa" and cp["terminal"] == request.flight.terminal
        ]
    
    if not security_checkpoints:
        security_checkpoints = [
            cp for cp in airport_data["checkpoints"] 
            if cp["type"] in ["tsa", "tsa_precheck"] and cp["terminal"] == request.flight.terminal
        ]
    
    if security_checkpoints:
        # Choose checkpoint with lowest current wait
        cp = min(security_checkpoints, key=lambda x: x["base_wait"])
        walk_time, walk_dist = calculate_walking_time(
            current_lat, current_lng, cp["lat"], cp["lng"], request.mobility_factor
        )
        wait_dist = get_wait_time_distribution(cp["base_wait"], cp["type"])
        
        step_name = "Security (PreCheck)" if request.has_tsa_precheck else "Security Screening"
        segments.append({
            "step_name": step_name,
            "location": cp["name"],
            "lat": cp["lat"],
            "lng": cp["lng"],
            "wait_distribution": wait_dist,
            "walk_minutes": walk_time,
            "walk_distance_meters": walk_dist,
            "checkpoint_id": cp["id"],
            "mobility_factor": request.mobility_factor
        })
        current_lat, current_lng = cp["lat"], cp["lng"]
    
    # Walk to gate segment
    gate_lat, gate_lng = get_gate_position(airport_code, request.flight.terminal, request.flight.gate)
    walk_time, walk_dist = calculate_walking_time(
        current_lat, current_lng, gate_lat, gate_lng, request.mobility_factor
    )
    
    segments.append({
        "step_name": "Walk to Gate",
        "location": f"Gate {request.flight.gate}",
        "lat": gate_lat,
        "lng": gate_lng,
        "wait_distribution": None,
        "walk_minutes": walk_time,
        "walk_distance_meters": walk_dist,
        "checkpoint_id": None,
        "mobility_factor": request.mobility_factor
    })
    
    # Run Monte Carlo simulation
    num_simulations = 10000
    total_times, _ = run_monte_carlo_simulation(segments, num_simulations)
    
    # Calculate percentiles
    p50 = int(np.percentile(total_times, 50))
    p80 = int(np.percentile(total_times, 80))
    p90 = int(np.percentile(total_times, 90))
    p95 = int(np.percentile(total_times, 95))
    
    # Calculate probability of making it
    probability = calculate_probability_of_making_it(total_times, time_until_boarding)
    status, status_message = get_status_from_probability(probability)
    
    # Calculate leave-by times for different confidence levels
    leave_by_80 = boarding_time - timedelta(minutes=p80)
    leave_by_90 = boarding_time - timedelta(minutes=p90)
    leave_by_95 = boarding_time - timedelta(minutes=p95)
    
    # Build segment distributions for response
    response_segments = []
    for seg in segments:
        wait_dist = seg.get("wait_distribution")
        response_segments.append(SegmentDistribution(
            step_name=seg["step_name"],
            location=seg["location"],
            lat=seg["lat"],
            lng=seg["lng"],
            wait_distribution=wait_dist,
            walk_minutes=seg["walk_minutes"],
            walk_distance_meters=seg["walk_distance_meters"],
            checkpoint_id=seg.get("checkpoint_id")
        ))
    
    return WillIMakeItResponse(
        probability_of_making_it=round(probability, 4),
        probability_percentage=int(probability * 100),
        status=status,
        status_message=status_message,
        total_time_p50=p50,
        total_time_p80=p80,
        total_time_p90=p90,
        total_time_p95=p95,
        time_until_boarding=max(0, int(time_until_boarding)),
        buffer_minutes=boarding_cutoff_minutes,
        leave_by_80=leave_by_80.isoformat(),
        leave_by_90=leave_by_90.isoformat(),
        leave_by_95=leave_by_95.isoformat(),
        segments=response_segments,
        simulation_runs=num_simulations,
        boarding_cutoff_minutes=boarding_cutoff_minutes
    )

@app.post("/api/flight/import")
async def import_flight(flight: Flight):
    """
    Import flight details. For MVP, this just validates and returns the flight info.
    In production, this would look up flight details from an API.
    """
    airport_code = flight.airport_code.upper()
    if airport_code not in AIRPORTS_DATA:
        raise HTTPException(status_code=404, detail="Airport not found")
    
    airport_data = AIRPORTS_DATA[airport_code]
    
    # Validate terminal
    if flight.terminal not in airport_data["terminals"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Terminal '{flight.terminal}' not found. Available: {airport_data['terminals']}"
        )
    
    # Validate gate exists (or use default)
    gates = airport_data.get("gates", {}).get(flight.terminal, {})
    if flight.gate not in gates and gates:
        # Use first available gate as fallback
        flight.gate = list(gates.keys())[0]
    
    return {
        "status": "success",
        "flight": {
            "flight_number": flight.flight_number,
            "airline": flight.airline,
            "departure_time": flight.departure_time,
            "terminal": flight.terminal,
            "gate": flight.gate,
            "airport_code": airport_code
        },
        "airport": {
            "name": airport_data["name"],
            "city": airport_data["city"]
        }
    }

@app.get("/api/checkpoints/{checkpoint_id}/distribution")
async def get_checkpoint_distribution(checkpoint_id: str):
    """
    Get the wait time distribution for a specific checkpoint.
    """
    # Find checkpoint across all airports
    for airport_code, airport_data in AIRPORTS_DATA.items():
        for cp in airport_data["checkpoints"]:
            if cp["id"] == checkpoint_id:
                distribution = get_wait_time_distribution(cp["base_wait"], cp["type"])
                return {
                    "checkpoint_id": checkpoint_id,
                    "checkpoint_name": cp["name"],
                    "checkpoint_type": cp["type"],
                    "terminal": cp["terminal"],
                    "airport_code": airport_code,
                    "distribution": distribution
                }
    
    raise HTTPException(status_code=404, detail="Checkpoint not found")
