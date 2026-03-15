
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple


@dataclass
class Alert:
    severity: str 
    title: str
    body: str
    emoji: str
    category: str 
    

class AlertAnalyzer:

    # ==========================================================================
    # TEMPERATURE THRESHOLDS (°C) - These are AIR temperatures, not wind chill
    # IMPORTANT: No wind sensor available. Wind significantly increases cold risk.
    # Source: Princeton Outdoor Action, PMC research on hypothermia
    # ==========================================================================
    TEMP_SEVERE_COLD = -10     # Severe cold, frostbite likely even with minimal wind
    TEMP_FREEZING = 0          # Ice on trail, frostbite risk increases with wind
    TEMP_HYPOTHERMIA_WET = 10  # Hypothermia possible when wet (scientifically validated)
    TEMP_HEAT_MONITOR = 25     # Monitor for heat exhaustion in strenuous activity
    TEMP_HEAT_WARNING = 30     # Heat exhaustion risk increases
    TEMP_HEAT_DANGER = 35      # Heat stroke risk, especially with humidity

    # ==========================================================================
    # MESSAGE TEMPLATES - All user-facing messages in one place
    # Keys match hazard types returned by detection helpers
    # ==========================================================================
    ALERT_MESSAGES = {
        # Thermal - cold
        'severe_cold': {
            'title': '🥶 SEVERE COLD',
            'body': '{station}: {temp}°C. Frostbite likely. Cover all exposed skin. Wind increases risk.',
            'emoji': '🥶',
        },
        'freezing': {
            'title': '❄️ Freezing Conditions',
            'body': '{station}: {temp}°C. Ice on trail likely. Use traction devices. Wind increases risk.',
            'emoji': '❄️',
        },
        'hypothermia_wet': {
            'title': '🥶 Hypothermia Risk',
            'body': '{station}: {temp}°C + wet conditions. Hypothermia can occur rapidly. Stay dry or turn back.',
            'emoji': '🥶',
        },
        'cold_dry': {
            'title': '❄️ Cold Conditions',
            'body': '{station}: {temp}°C. Dress in layers. Risk increases if wet or windy.',
            'emoji': '❄️',
        },
        # Thermal - heat
        'heat_stroke': {
            'title': '🔥 Heat Stroke Risk',
            'body': '{station}: {temp}°C. Stop if dizzy or nauseous. Seek shade and water immediately.',
            'emoji': '🔥',
        },
        'heat_warning': {
            'title': '☀️ Heat Warning',
            'body': '{station}: {temp}°C. Heat exhaustion risk. Take breaks in shade, drink frequently.',
            'emoji': '☀️',
        },
        'heat_monitor': {
            'title': '☀️ Warm Conditions',
            'body': '{station}: {temp}°C. Stay hydrated during strenuous activity.',
            'emoji': '☀️',
        },
        # Pressure
        'pressure_severe': {
            'title': '⛈️ Severe Weather Warning',
            'body': '{station}: Pressure at {pressure} hPa. Severe weather likely. Descend or seek shelter.',
            'emoji': '⛈️',
        },
        'pressure_low': {
            'title': '🌧️ Storm Watch',
            'body': '{station}: Low pressure ({pressure} hPa). Weather may deteriorate. Monitor conditions.',
            'emoji': '🌧️',
        },
        'pressure_dropping_fast': {
            'title': '⛈️ Storm Incoming',
            'body': '{station}: Pressure dropping {rate} hPa/hr. Storm likely within hours. Plan descent.',
            'emoji': '⛈️',
        },
        'pressure_dropping_very_fast': {
            'title': '⛈️ SEVERE WEATHER IMMINENT',
            'body': '{station}: Pressure dropping {rate} hPa/hr. Severe weather imminent. Seek shelter now.',
            'emoji': '⛈️',
        },
        # Rain
        'rain_active': {
            'title': '🌧️ Active Rainfall',
            'body': '{station}: Rain detected. Trail may be slippery. Watch footing on rocks and roots.',
            'emoji': '🌧️',
        },
        # UV
        'uv_extreme': {
            'title': '☀️ EXTREME UV',
            'body': '{station}: UV {uv}. Sunburn in 10-15 minutes. Wear protection, limit exposure.',
            'emoji': '☀️',
        },
        'uv_very_high': {
            'title': '☀️ Very High UV',
            'body': '{station}: UV {uv}. Apply sunscreen (SPF 30+). Wear hat and sunglasses.',
            'emoji': '☀️',
        },
        'uv_high': {
            'title': '☀️ High UV',
            'body': '{station}: UV {uv}. Sun protection recommended.',
            'emoji': '☀️',
        },
        # Visibility
        'visibility_poor': {
            'title': '🌫️ Poor Visibility',
            'body': '{station}: Low light + fog/rain. Visibility reduced. Use headlamp and stay on marked trail.',
            'emoji': '🌫️',
        },
        'visibility_dark': {
            'title': '🌙 Low Light',
            'body': '{station}: Limited daylight. Headlamp recommended.',
            'emoji': '🌙',
        },
        # Air quality (CO2)
        'co2_idlh': {
            'title': '💨 EVACUATE NOW',
            'body': '{station}: CO2 {co2} ppm. Immediately dangerous to life. Leave area now.',
            'emoji': '💨',
        },
        'co2_evacuate': {
            'title': '💨 EVACUATE',
            'body': '{station}: CO2 {co2} ppm. Maximum 15-minute exposure. Open doors/windows or leave.',
            'emoji': '💨',
        },
        'co2_dangerous': {
            'title': '💨 Dangerous CO2',
            'body': '{station}: CO2 {co2} ppm. OSHA limit exceeded. Ventilate immediately.',
            'emoji': '💨',
        },
        'co2_impairment': {
            'title': '💨 High CO2',
            'body': '{station}: CO2 {co2} ppm. May cause headaches, reduced concentration. Improve ventilation.',
            'emoji': '💨',
        },
        'co2_poor': {
            'title': '💨 Poor Air',
            'body': '{station}: CO2 {co2} ppm. Stuffy air. Open windows if possible.',
            'emoji': '💨',
        },
        'co2_stuffy': {
            'title': '💨 Stuffy Air',
            'body': '{station}: CO2 {co2} ppm. Ventilation recommended.',
            'emoji': '💨',
        },
        # Trail
        'traffic_high': {
            'title': '👥 High Trail Traffic',
            'body': '{station}: {motion} hikers detected in last hour. Expect crowds and delays.',
            'emoji': '👥',
        },
        'traffic_moderate': {
            'title': '👥 Moderate Traffic',
            'body': '{station}: {motion} hikers in last hour. Trail moderately busy.',
            'emoji': '👥',
        },
        'slippery': {
            'title': '⚠️ Slippery Trail',
            'body': '{station}: Recent rain + cold temps. Ice or mud likely. Use caution.',
            'emoji': '⚠️',
        },
        # Soil moisture
        'soil_saturated': {
            'title': '🌊 Trail Flooded/Muddy',
            'body': '{station}: Soil saturated ({moisture}%). Expect deep mud or standing water. Consider alternate route.',
            'emoji': '🌊',
        },
        'soil_wet': {
            'title': '💧 Muddy Conditions',
            'body': '{station}: Wet soil ({moisture}%). Mud likely in low-lying areas. Wear waterproof boots.',
            'emoji': '💧',
        },
    }
    
    # ==========================================================================
    # PRESSURE THRESHOLDS (hPa) - Altitude-adjusted for ~1250m elevation
    # Normal pressure at 1250m is ~870 hPa (not sea-level 1013 hPa)
    # Weather alerts trigger on deviation from normal, not absolute values
    # ==========================================================================
    PRESSURE_BASELINE_1250M = 870   # Expected pressure at 1250m altitude
    PRESSURE_STORM_DROP = 15        # 15 hPa below baseline = storm watch
    PRESSURE_SEVERE_DROP = 25       # 25 hPa below baseline = severe weather

    # Rate of change thresholds (hPa per hour)
    PRESSURE_RAPID_DROP = 3         # 3+ hPa/hour = storm incoming
    PRESSURE_VERY_RAPID_DROP = 6    # 6+ hPa/hour = severe weather imminent
    
    # Humidity  (%) - Fog typically forms at 90%+ humidity
    HUMIDITY_VERY_HIGH = 90
    
    # ==========================================================================
    # CO2 THRESHOLDS (ppm) - For mountain shelters/huts
    # Source: ASHRAE, OSHA Technical Manual, NIOSH
    # ==========================================================================
    CO2_STUFFY = 1000           # Stuffy air, ventilate
    CO2_POOR = 1500             # Poor air quality
    CO2_IMPAIRMENT = 2500       # Cognitive effects (precautionary)
    CO2_DANGEROUS = 5000        # OSHA occupational limit
    CO2_EVACUATE = 30000        # 15-minute exposure limit
    CO2_IDLH = 40000            # Immediately dangerous to life/health
    
    # UV  (index)
    UV_HIGH = 6
    UV_VERY_HIGH = 8
    UV_EXTREME = 11
    
    # Light (lux)
    LUX_DARK = 100 #130
    LUX_VERY_DARK = 10
    
    # Traffic thresholds (people/hour)
    TRAFFIC_MODERATE = 15
    TRAFFIC_HIGH = 30

    # ==========================================================================
    # SOIL MOISTURE THRESHOLDS (%) - For trail condition assessment
    # Note: Thresholds are approximate, may need calibration per sensor/soil type
    # ==========================================================================
    SOIL_SATURATED = 80         # Trail likely flooded or very muddy
    SOIL_WET = 60               # Expect mud in low-lying areas

    def __init__(self):
        # Pressure history per station: {station_id: (pressure, timestamp)}
        self._pressure_history: Dict[str, Tuple[float, datetime]] = {}

    def _get_pressure_rate(self, station_id: str, current_pressure: float,
                            current_time: datetime) -> Optional[float]:
        """
        Calculate pressure rate of change in hPa/hour.

        Returns negative values for dropping pressure, positive for rising.
        Returns None if no previous reading or reading too old (>2 hours).
        """
        if station_id not in self._pressure_history:
            self._pressure_history[station_id] = (current_pressure, current_time)
            return None

        prev_pressure, prev_time = self._pressure_history[station_id]
        time_diff = current_time - prev_time

        # Ignore readings older than 2 hours
        if time_diff > timedelta(hours=2):
            self._pressure_history[station_id] = (current_pressure, current_time)
            return None

        # Need at least 10 minutes between readings for meaningful rate
        if time_diff < timedelta(minutes=10):
            return None

        # Calculate rate in hPa per hour
        hours = time_diff.total_seconds() / 3600
        rate = (current_pressure - prev_pressure) / hours

        # Update history
        self._pressure_history[station_id] = (current_pressure, current_time)

        return rate

    def analyze(self, data: dict, station_name: str = "this trail",
                station_id: str = None, timestamp: datetime = None) -> List[Alert]:
        """
        Analyze sensor data and return list of alerts.

        Args:
            data: Dict with sensor readings
            station_name: Human-readable name for messages
            station_id: Unique station ID for tracking pressure history
            timestamp: Reading timestamp for rate-of-change calculations
        """
        sensors = self._extract_sensor_data(data)

        hazards = []
        hazards.extend(self._check_thermal_hazards(
            sensors['temp'], sensors['humidity'], sensors['is_raining']
        ))
        hazards.extend(self._check_pressure_hazards(sensors['pressure']))

        if station_id and timestamp and sensors['pressure'] is not None:
            hazards.extend(self._check_pressure_rate(
                station_id, sensors['pressure'], timestamp
            ))

        hazards.extend(self._check_rain(sensors['is_raining']))
        hazards.extend(self._check_uv_exposure(sensors['uv']))
        hazards.extend(self._check_visibility(
            sensors['lux'], sensors['humidity'], sensors['is_raining']
        ))
        hazards.extend(self._check_air_quality(sensors['co2']))
        hazards.extend(self._check_trail_traffic(sensors['motion']))
        hazards.extend(self._check_soil_moisture(sensors['soil_moisture']))
        hazards.extend(self._check_slippery_conditions(
            sensors['rained_recently'], sensors['temp']
        ))

        alerts = [self._build_alert(h, station_name) for h in hazards]
        
        return alerts
    
    def _extract_sensor_data(self, data: dict) -> dict:
        atmo = data.get('atmospheric', {})
        light = data.get('light', {})
        precip = data.get('precipitation', {})
        air = data.get('air_quality', {})
        activity = data.get('trail_activity', {})
        soil = data.get('soil', {})

        return {
            'temp': atmo.get('temperature'),
            'humidity': atmo.get('humidity'),
            'pressure': atmo.get('pressure'),
            'uv': light.get('uv_index'),
            'lux': light.get('lux'),
            'is_raining': precip.get('is_raining', False),
            'rained_recently': precip.get('rain_detected_last_hour', False),
            'co2': air.get('co2_ppm'),
            'motion': activity.get('motion_count', 0),
            'soil_moisture': soil.get('moisture_percent'),
        }

    def _build_alert(self, hazard: dict, station: str) -> Alert:
        """
        Build an Alert from hazard data using message templates.

        Args:
            hazard: {'type': str, 'severity': str, 'category': str, 'values': dict}
            station: Station name for message formatting
        """
        template = self.ALERT_MESSAGES[hazard['type']]
        values = {'station': station, **hazard.get('values', {})}

        return Alert(
            severity=hazard['severity'],
            title=template['title'],
            body=template['body'].format(**values),
            emoji=template['emoji'],
            category=hazard['category']
        )
    
    def _check_thermal_hazards(self, temp: Optional[float], humidity: Optional[float],
                                 is_raining: bool) -> List[dict]:
        """
        Detect cold hazards (frostbite, hypothermia) and heat hazards (exhaustion, stroke).

        Returns list of hazard dicts, not Alert objects. Message building is separate.
        """
        if temp is None:
            return []

        hazards = []
        is_wet = is_raining or (humidity and humidity > self.HUMIDITY_VERY_HIGH)

        # === COLD HAZARDS ===
        if temp < self.TEMP_SEVERE_COLD:
            hazards.append({
                'type': 'severe_cold',
                'severity': 'danger',
                'category': 'temperature',
                'values': {'temp': temp}
            })
        elif temp < self.TEMP_FREEZING:
            hazards.append({
                'type': 'freezing',
                'severity': 'warning',
                'category': 'temperature',
                'values': {'temp': temp}
            })
        elif temp < self.TEMP_HYPOTHERMIA_WET:
            if is_wet:
                hazards.append({
                    'type': 'hypothermia_wet',
                    'severity': 'danger',
                    'category': 'temperature',
                    'values': {'temp': temp}
                })
            else:
                hazards.append({
                    'type': 'cold_dry',
                    'severity': 'info',
                    'category': 'temperature',
                    'values': {'temp': temp}
                })

        # === HEAT HAZARDS ===
        elif temp > self.TEMP_HEAT_DANGER:
            hazards.append({
                'type': 'heat_stroke',
                'severity': 'danger',
                'category': 'temperature',
                'values': {'temp': temp}
            })
        elif temp > self.TEMP_HEAT_WARNING:
            hazards.append({
                'type': 'heat_warning',
                'severity': 'warning',
                'category': 'temperature',
                'values': {'temp': temp}
            })
        elif temp > self.TEMP_HEAT_MONITOR:
            hazards.append({
                'type': 'heat_monitor',
                'severity': 'info',
                'category': 'temperature',
                'values': {'temp': temp}
            })

        return hazards
    
    def _check_pressure_hazards(self, pressure: Optional[float]) -> List[dict]:
        """
        Detect pressure-related weather hazards.

        Uses altitude-adjusted baseline. At 1250m, normal is ~870 hPa.
        Alerts trigger on deviation from baseline, not absolute values.
        """
        if pressure is None:
            return []

        hazards = []
        baseline = self.PRESSURE_BASELINE_1250M
        severe_threshold = baseline - self.PRESSURE_SEVERE_DROP  # ~845 hPa
        storm_threshold = baseline - self.PRESSURE_STORM_DROP    # ~855 hPa

        if pressure < severe_threshold:
            hazards.append({
                'type': 'pressure_severe',
                'severity': 'danger',
                'category': 'weather',
                'values': {'pressure': pressure}
            })
        elif pressure < storm_threshold:
            hazards.append({
                'type': 'pressure_low',
                'severity': 'warning',
                'category': 'weather',
                'values': {'pressure': pressure}
            })

        return hazards

    def _check_pressure_rate(self, station_id: str, pressure: float,
                              timestamp: datetime) -> List[dict]:
        """
        Detect rapid pressure changes indicating incoming weather.

        A dropping pressure indicates incoming storm/bad weather.
        Rate thresholds: 3 hPa/hr = storm, 6 hPa/hr = severe.
        """
        rate = self._get_pressure_rate(station_id, pressure, timestamp)

        if rate is None:
            return []

        hazards = []

        # Negative rate = pressure dropping
        if rate <= -self.PRESSURE_VERY_RAPID_DROP:
            hazards.append({
                'type': 'pressure_dropping_very_fast',
                'severity': 'danger',
                'category': 'weather',
                'values': {'rate': abs(round(rate, 1))}
            })
        elif rate <= -self.PRESSURE_RAPID_DROP:
            hazards.append({
                'type': 'pressure_dropping_fast',
                'severity': 'warning',
                'category': 'weather',
                'values': {'rate': abs(round(rate, 1))}
            })

        return hazards

    def _check_rain(self, is_raining: bool) -> List[dict]:
        """Detect active rainfall."""
        if not is_raining:
            return []

        return [{
            'type': 'rain_active',
            'severity': 'warning',
            'category': 'weather',
            'values': {}
        }]
    
    def _check_uv_exposure(self, uv: Optional[float]) -> List[dict]:
        """Detect UV exposure hazards."""
        if uv is None:
            return []

        hazards = []

        if uv >= self.UV_EXTREME:
            hazards.append({
                'type': 'uv_extreme',
                'severity': 'danger',
                'category': 'weather',
                'values': {'uv': uv}
            })
        elif uv >= self.UV_VERY_HIGH:
            hazards.append({
                'type': 'uv_very_high',
                'severity': 'warning',
                'category': 'weather',
                'values': {'uv': uv}
            })
        elif uv >= self.UV_HIGH:
            hazards.append({
                'type': 'uv_high',
                'severity': 'info',
                'category': 'weather',
                'values': {'uv': uv}
            })

        return hazards
    
    def _check_visibility(self, lux: Optional[float], humidity: Optional[float],
                          is_raining: bool) -> List[dict]:
        """Detect visibility hazards (low light, fog)."""
        if lux is None:
            return []

        hazards = []

        if lux < self.LUX_DARK:
            if is_raining or (humidity and humidity > self.HUMIDITY_VERY_HIGH):
                hazards.append({
                    'type': 'visibility_poor',
                    'severity': 'warning',
                    'category': 'weather',
                    'values': {}
                })
            elif lux < self.LUX_VERY_DARK:
                hazards.append({
                    'type': 'visibility_dark',
                    'severity': 'info',
                    'category': 'weather',
                    'values': {}
                })

        return hazards
    
    def _check_air_quality(self, co2: Optional[float]) -> List[dict]:
        """
        Detect air quality hazards (CO2 levels).

        Thresholds per OSHA/NIOSH:
        - 1000 ppm: Stuffy, ventilate
        - 1500 ppm: Poor air quality
        - 2500 ppm: Cognitive effects possible (precautionary)
        - 5000 ppm: OSHA occupational limit
        - 30000 ppm: 15-min exposure limit
        - 40000 ppm: IDLH (immediately dangerous)
        """
        if co2 is None:
            return []

        hazards = []

        if co2 >= self.CO2_IDLH:
            hazards.append({
                'type': 'co2_idlh',
                'severity': 'danger',
                'category': 'air_quality',
                'values': {'co2': co2}
            })
        elif co2 >= self.CO2_EVACUATE:
            hazards.append({
                'type': 'co2_evacuate',
                'severity': 'danger',
                'category': 'air_quality',
                'values': {'co2': co2}
            })
        elif co2 >= self.CO2_DANGEROUS:
            hazards.append({
                'type': 'co2_dangerous',
                'severity': 'danger',
                'category': 'air_quality',
                'values': {'co2': co2}
            })
        elif co2 >= self.CO2_IMPAIRMENT:
            hazards.append({
                'type': 'co2_impairment',
                'severity': 'warning',
                'category': 'air_quality',
                'values': {'co2': co2}
            })
        elif co2 >= self.CO2_POOR:
            hazards.append({
                'type': 'co2_poor',
                'severity': 'warning',
                'category': 'air_quality',
                'values': {'co2': co2}
            })
        elif co2 >= self.CO2_STUFFY:
            hazards.append({
                'type': 'co2_stuffy',
                'severity': 'info',
                'category': 'air_quality',
                'values': {'co2': co2}
            })

        return hazards
    
    def _check_trail_traffic(self, motion: int) -> List[dict]:
        """Detect trail traffic levels."""
        hazards = []

        if motion > self.TRAFFIC_HIGH:
            hazards.append({
                'type': 'traffic_high',
                'severity': 'info',
                'category': 'trail',
                'values': {'motion': motion}
            })
        elif motion > self.TRAFFIC_MODERATE:
            hazards.append({
                'type': 'traffic_moderate',
                'severity': 'info',
                'category': 'trail',
                'values': {'motion': motion}
            })

        return hazards

    def _check_soil_moisture(self, moisture: Optional[float]) -> List[dict]:
        """Detect trail conditions based on soil moisture."""
        if moisture is None:
            return []

        hazards = []

        if moisture >= self.SOIL_SATURATED:
            hazards.append({
                'type': 'soil_saturated',
                'severity': 'warning',
                'category': 'trail',
                'values': {'moisture': moisture}
            })
        elif moisture >= self.SOIL_WET:
            hazards.append({
                'type': 'soil_wet',
                'severity': 'info',
                'category': 'trail',
                'values': {'moisture': moisture}
            })

        return hazards

    def _check_slippery_conditions(self, rained_recently: bool, temp: Optional[float]) -> List[dict]:
        """Detect slippery trail conditions (rain + cold)."""
        if not rained_recently or temp is None or temp >= 5:
            return []

        return [{
            'type': 'slippery',
            'severity': 'warning',
            'category': 'trail',
            'values': {}
        }]
    
    def get_is_dangerous_flags(self, data: dict) -> dict:
        """
        Return dict of is_dangerous flags for each sensor value.

        A value is "dangerous" if it triggers a danger or warning level alert.
        Uses the same thresholds as alert detection for consistency.

        Returns dict matching the API response structure with _is_dangerous suffixes.
        """
        sensors = self._extract_sensor_data(data)

        temp = sensors['temp']
        humidity = sensors['humidity']
        pressure = sensors['pressure']
        is_raining = sensors['is_raining']
        uv = sensors['uv']
        lux = sensors['lux']
        co2 = sensors['co2']
        soil_moisture = sensors['soil_moisture']
        motion = sensors['motion']
        rained_recently = sensors['rained_recently']

        # Temperature: dangerous if triggers danger/warning (not info)
        temp_dangerous = False
        if temp is not None:
            is_wet = is_raining or (humidity and humidity > self.HUMIDITY_VERY_HIGH)
            if temp < self.TEMP_FREEZING:  # Freezing or below
                temp_dangerous = True
            elif temp < self.TEMP_HYPOTHERMIA_WET and is_wet:  # Hypothermia risk when wet
                temp_dangerous = True
            elif temp > self.TEMP_HEAT_WARNING:  # Heat warning or danger
                temp_dangerous = True

        # Humidity: dangerous if contributing to hypothermia risk or fog
        humidity_dangerous = False
        if humidity is not None:
            if humidity > self.HUMIDITY_VERY_HIGH:
                # High humidity + cold = hypothermia risk
                if temp is not None and temp < self.TEMP_HYPOTHERMIA_WET:
                    humidity_dangerous = True

        # Pressure: dangerous if below storm threshold
        pressure_dangerous = False
        if pressure is not None:
            storm_threshold = self.PRESSURE_BASELINE_1250M - self.PRESSURE_STORM_DROP
            if pressure < storm_threshold:
                pressure_dangerous = True

        # UV: dangerous if high or above (warning/danger level)
        uv_dangerous = False
        if uv is not None and uv >= self.UV_VERY_HIGH:
            uv_dangerous = True

        # Lux: dangerous if very dark with poor visibility conditions
        lux_dangerous = False
        if lux is not None and lux < self.LUX_DARK:
            if is_raining or (humidity and humidity > self.HUMIDITY_VERY_HIGH):
                lux_dangerous = True

        # CO2: dangerous if at impairment level or above
        co2_dangerous = False
        if co2 is not None and co2 >= self.CO2_IMPAIRMENT:
            co2_dangerous = True

        # Soil moisture: dangerous if saturated (muddy/flooded)
        soil_dangerous = False
        if soil_moisture is not None and soil_moisture >= self.SOIL_SATURATED:
            soil_dangerous = True

        # Rain: flagged as dangerous (warning level)
        rain_dangerous = is_raining

        # Recent rain: dangerous if combined with cold (slippery)
        rain_recent_dangerous = False
        if rained_recently and temp is not None and temp < 5:
            rain_recent_dangerous = True

        # Motion: not really "dangerous", just informational
        motion_dangerous = False

        return {
            'temperature_is_dangerous': temp_dangerous,
            'humidity_is_dangerous': humidity_dangerous,
            'pressure_is_dangerous': pressure_dangerous,
            'uv_index_is_dangerous': uv_dangerous,
            'lux_is_dangerous': lux_dangerous,
            'co2_ppm_is_dangerous': co2_dangerous,
            'moisture_percent_is_dangerous': soil_dangerous,
            'is_raining_is_dangerous': rain_dangerous,
            'rain_detected_last_hour_is_dangerous': rain_recent_dangerous,
            'motion_count_is_dangerous': motion_dangerous,
        }

    def get_highest_severity_alert(self, alerts: List[Alert]) -> Optional[Alert]:
        if not alerts:
            return None

        severity_order = {'danger': 0, 'warning': 1, 'info': 2}
        return min(alerts, key=lambda a: severity_order.get(a.severity, 999))



alert_analyzer = AlertAnalyzer()
