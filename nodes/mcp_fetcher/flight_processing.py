import asyncio
from core.config import allowedAirlines

def extract_essential_flight_data(offer: dict) -> dict:
    """Strips down the Duffel Offer JSON object into a lightweight dictionary."""
    try:
        slices = offer.get("slices", [])
        if not slices:
            return {}

        outbound_slice = slices[0]
        outbound_segments = outbound_slice.get("segments", [])
        if not outbound_segments:
            return {}
            
        # Ensure non-stop only for outbound
        if len(outbound_segments) > 1:
            return {}

        departure_leg = outbound_segments[0]
        arrival_leg = outbound_segments[-1]

        extracted_airlines = set()
        extracted_codes = []
        
        # outbound airlines
        for seg in outbound_segments:
            carrier = seg.get("operating_carrier", {})
            if carrier:
                extracted_airlines.add(carrier.get("name", ""))
            
            flight_number = seg.get("operating_carrier_flight_number", "")
            if carrier and flight_number:
                extracted_codes.append(f"{carrier.get('iata_code', '')}{flight_number}")
                
        is_round_trip = len(slices) > 1
        
        if is_round_trip:
            return_slice = slices[1]
            return_segments = return_slice.get("segments", [])
            if not return_segments:
                return {}
                
            # Ensure non-stop only for return
            if len(return_segments) > 1:
                return {}
                
            for seg in return_segments:
                carrier = seg.get("operating_carrier", {})
                if carrier:
                    extracted_airlines.add(carrier.get("name", ""))
                
                flight_number = seg.get("operating_carrier_flight_number", "")
                if carrier and flight_number:
                    extracted_codes.append(f"{carrier.get('iata_code', '')}{flight_number}")

        carriers = set()
        for s in slices:
            for seg in s.get("segments", []):
                carrier = seg.get("operating_carrier", {})
                if carrier:
                    carriers.add(carrier.get("iata_code", ""))
                
        if not any(c in allowedAirlines for c in carriers):
            return {}

        price_str = offer.get("total_amount", "0")
        
        cabin_class = "N/A"
        try:
            cabin_class = outbound_segments[0]["passengers"][0]["cabin_class"]
            cabin_class = cabin_class.replace("_", " ").title()
        except:
            pass

        flight_information = {
            "airlines": ",".join(filter(None, extracted_airlines)),
            "airline_codes": ",".join(filter(None, extracted_codes)),
            "departure_time": departure_leg.get("departing_at", "N/A"),
            "departure_airport": departure_leg.get("origin", {}).get("name", "N/A"),
            "arrival_airport": arrival_leg.get("destination", {}).get("name", "N/A"),
            "flight_class": cabin_class,
            "price": price_str,
        }

        if is_round_trip:
            return_arrival_leg = return_segments[-1]
            flight_information.update({
                "return_time": return_arrival_leg.get("arriving_at", "N/A"),
                "return_airport": return_arrival_leg.get("destination", {}).get("name", "N/A"),
            })

        return flight_information
    except Exception as e:
        print(f"Error extracting flight data: {e}")
        return {}

async def execute_single_flight_search(client, headers, payload, semaphore: asyncio.Semaphore) -> list:
    """Executes Duffel Offer Request."""
    try:
        async with semaphore:
            response = await client.post(
                "https://api.duffel.com/air/offer_requests",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
        data = response.json()
        offers = data.get("data", {}).get("offers", [])
        
        results = []
        for offer in offers:
            extracted = extract_essential_flight_data(offer)
            if extracted:
                results.append(extracted)
                
        return results

    except Exception as e:
        print(f"Query Failed for {payload.get('data', {}).get('slices', [])}: {e}")
        return []