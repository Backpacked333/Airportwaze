"""Airport service for airport data operations."""
import logging
from typing import List, Dict, Optional
from datetime import datetime

from app.data import AIRPORTS_DATA
from app.schemas.airport import Airport
from app.schemas.checkpoint import Checkpoint
from app.utils.calculations import calculate_current_wait, get_checkpoint_status

logger = logging.getLogger(__name__)


class AirportService:
    """Service for airport-related operations."""

    @staticmethod
    def get_all_airports() -> List[Dict]:
        """Get list of all airports."""
        airports = []
        for code, data in AIRPORTS_DATA.items():
            airports.append({
                "code": code,
                "name": data["name"],
                "city": data["city"],
                "lat": data["lat"],
                "lng": data["lng"],
                "terminals": data["terminals"]
            })
        return airports

    @staticmethod
    def get_airport(airport_code: str) -> Optional[Airport]:
        """Get airport details with current wait times."""
        airport_code = airport_code.upper()
        airport_data = AIRPORTS_DATA.get(airport_code)

        if not airport_data:
            logger.warning(f"Airport not found: {airport_code}")
            return None

        checkpoints = []
        for cp in airport_data["checkpoints"]:
            current_wait = calculate_current_wait(cp["base_wait"])
            checkpoints.append(Checkpoint(
                id=cp["id"],
                name=cp["name"],
                type=cp["type"],
                terminal=cp["terminal"],
                lat=cp["lat"],
                lng=cp["lng"],
                current_wait_minutes=current_wait,
                historical_avg_minutes=cp["base_wait"],
                status=get_checkpoint_status(current_wait),
                last_updated=datetime.utcnow().isoformat()
            ))

        return Airport(
            code=airport_data["code"],
            name=airport_data["name"],
            city=airport_data["city"],
            lat=airport_data["lat"],
            lng=airport_data["lng"],
            terminals=airport_data["terminals"],
            checkpoints=checkpoints
        )

    @staticmethod
    def get_terminal_gates(airport_code: str, terminal: str) -> Optional[Dict]:
        """Get gates for a specific terminal."""
        airport_code = airport_code.upper()
        airport_data = AIRPORTS_DATA.get(airport_code)

        if not airport_data:
            return None

        gates_data = airport_data.get("gates", {}).get(terminal, {})
        gates = [
            {"name": name, "lat": coords["lat"], "lng": coords["lng"]}
            for name, coords in gates_data.items()
        ]

        return {"terminal": terminal, "gates": gates}
