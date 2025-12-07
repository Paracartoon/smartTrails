
from dataclasses import dataclass

from typing import Optional, List


@dataclass
class Alert:
    severity: str 
    title: str
    body: str
    emoji: str
    category: str 
    

class AlertAnalyzer:
    
    # Temperature in (°C)
    TEMP_EXTREME_COLD = -15
    TEMP_VERY_COLD = -10
    TEMP_COLD = 0
    TEMP_HOT = 30
    TEMP_EXTREME_HEAT = 35
    
    # Pressure  (hPa)
    PRESSURE_VERY_LOW = 920
    PRESSURE_LOW = 950
    
    # Humidity  (%)
    HUMIDITY_VERY_HIGH = 90
    HUMIDITY_HIGH = 85
    
    # CO2 (ppm)
    CO2_POOR = 1000
    CO2_BAD = 2000
    CO2_DANGEROUS = 5000
    
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
    
    def analyze(self, data: dict, station_name: str = "this trail") -> List[Alert]:
        """
        Analyze sensor data and return list of alerts
        
        Args:
            data: Dict with sensor readings
            station_name: Name of the station for personalized messages
        """
        alerts = []
        
        sensors = self._extract_sensor_data(data)
        
        alerts.extend(self._check_temperature(sensors['temp'], station_name))
        alerts.extend(self._check_hypothermia_risk(
            sensors['temp'], 
            sensors['humidity'], 
            sensors['is_raining'], 
            station_name
        ))
        alerts.extend(self._check_weather(sensors['pressure'], station_name))
        alerts.extend(self._check_rain(sensors['is_raining'], station_name))
        alerts.extend(self._check_uv(sensors['uv'], station_name))
        alerts.extend(self._check_visibility(
            sensors['lux'], 
            sensors['humidity'], 
            sensors['is_raining'], 
            station_name
        ))
        alerts.extend(self._check_air_quality(sensors['co2'], station_name))
        alerts.extend(self._check_trail_traffic(sensors['motion'], station_name))
        alerts.extend(self._check_slippery_conditions(
            sensors['rained_recently'], 
            sensors['temp'], 
            station_name
        ))
        
        return alerts
    
    def _extract_sensor_data(self, data: dict) -> dict:
        atmo = data.get('atmospheric', {})
        light = data.get('light', {})
        precip = data.get('precipitation', {})
        air = data.get('air_quality', {})
        activity = data.get('trail_activity', {})
        
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
        }
    
    def _check_temperature(self, temp: Optional[float], station: str) -> List[Alert]:
        if temp is None:
            return []
        
        alerts = []
        
        if temp < self.TEMP_EXTREME_COLD:
            alerts.append(Alert(
                severity='danger',
                title='🥶 EXTREME COLD WARNING',
                body=f'{station}: {temp}°C. Frostbite possible in minutes. Exposed skin at risk.',
                emoji='🥶',
                category='temperature'
            ))
        elif temp < self.TEMP_VERY_COLD:
            alerts.append(Alert(
                severity='danger',
                title='❄️ Severe Cold Alert',
                body=f'{station}: {temp}°C. Frostbite risk. Ensure proper clothing and limit exposure.',
                emoji='❄️',
                category='temperature'
            ))
        elif temp < self.TEMP_COLD:
            alerts.append(Alert(
                severity='warning',
                title='❄️ Freezing Conditions',
                body=f'{station}: {temp}°C. Ice likely on trail. Use traction devices if available.',
                emoji='❄️',
                category='temperature'
            ))
        elif temp > self.TEMP_EXTREME_HEAT:
            alerts.append(Alert(
                severity='danger',
                title='🔥 Extreme Heat Warning',
                body=f'{station}: {temp}°C. Heat exhaustion risk. Carry extra water, take frequent breaks.',
                emoji='🔥',
                category='temperature'
            ))
        elif temp > self.TEMP_HOT:
            alerts.append(Alert(
                severity='warning',
                title='☀️ Hot Conditions',
                body=f'{station}: {temp}°C. Stay hydrated. Seek shade during midday.',
                emoji='☀️',
                category='temperature'
            ))
        
        return alerts
    
    def _check_hypothermia_risk(self, temp: Optional[float], humidity: Optional[float],
                                  is_raining: bool, station: str) -> List[Alert]:
        if temp is None or temp >= 10:
            return []
        
        is_wet = is_raining or (humidity and humidity > self.HUMIDITY_VERY_HIGH)
        
        if is_wet:
            return [Alert(
                severity='danger',
                title='🥶 Hypothermia Risk',
                body=f'{station}: Cold ({temp}°C) + wet conditions. Hypothermia can occur quickly. Stay dry or turn back.',
                emoji='🥶',
                category='weather'
            )]
        
        return []
    
    def _check_weather(self, pressure: Optional[float], station: str) -> List[Alert]:
        if pressure is None:
            return []
        
        alerts = []
        
        if pressure < self.PRESSURE_VERY_LOW:
            alerts.append(Alert(
                severity='danger',
                title='⛈️ Severe Weather Warning',
                body=f'{station}: Pressure at {pressure} hPa. Severe weather likely. Descend or seek shelter.',
                emoji='⛈️',
                category='weather'
            ))
        elif pressure < self.PRESSURE_LOW:
            alerts.append(Alert(
                severity='warning',
                title='🌧️ Storm Watch',
                body=f'{station}: Low pressure ({pressure} hPa). Weather may deteriorate. Monitor conditions.',
                emoji='🌧️',
                category='weather'
            ))
        
        return alerts
    
    def _check_rain(self, is_raining: bool, station: str) -> List[Alert]:
        if not is_raining:
            return []
        
        return [Alert(
            severity='warning',
            title='🌧️ Active Rainfall',
            body=f'{station}: Rain detected. Trail may be slippery. Watch footing on rocks and roots.',
            emoji='🌧️',
            category='weather'
        )]
    
    def _check_uv(self, uv: Optional[float], station: str) -> List[Alert]:
        if uv is None:
            return []
        
        alerts = []
        
        if uv >= self.UV_EXTREME:
            alerts.append(Alert(
                severity='danger',
                title='☀️ EXTREME UV',
                body=f'{station}: UV {uv}. Sunburn in 10-15 minutes. Wear protection, limit exposure.',
                emoji='☀️',
                category='weather'
            ))
        elif uv >= self.UV_VERY_HIGH:
            alerts.append(Alert(
                severity='warning',
                title='☀️ Very High UV',
                body=f'{station}: UV {uv}. Apply sunscreen (SPF 30+). Wear hat and sunglasses.',
                emoji='☀️',
                category='weather'
            ))
        elif uv >= self.UV_HIGH:
            alerts.append(Alert(
                severity='info',
                title='☀️ High UV',
                body=f'{station}: UV {uv}. Sun protection recommended.',
                emoji='☀️',
                category='weather'
            ))
        
        return alerts
    
    def _check_visibility(self, lux: Optional[float], humidity: Optional[float],
                          is_raining: bool, station: str) -> List[Alert]:
        if lux is None:
            return []
        
        alerts = []
        
        if lux < self.LUX_DARK:
            if is_raining or (humidity and humidity > 85):
                alerts.append(Alert(
                    severity='warning',
                    title='🌫️ Poor Visibility',
                    body=f'{station}: Low light + fog/rain. Visibility reduced. Use headlamp and stay on marked trail.',
                    emoji='🌫️',
                    category='weather'
                ))
            elif lux < self.LUX_VERY_DARK:
                alerts.append(Alert(
                    severity='info',
                    title='🌙 Low Light',
                    body=f'{station}: Limited daylight. Headlamp recommended.',
                    emoji='🌙',
                    category='weather'
                ))
        
        return alerts
    
    def _check_air_quality(self, co2: Optional[float], station: str) -> List[Alert]:
        if co2 is None:
            return []
        
        alerts = []
        
        if co2 > self.CO2_DANGEROUS:
            alerts.append(Alert(
                severity='danger',
                title='💨 DANGEROUS AIR QUALITY',
                body=f'{station}: CO2 {co2} ppm. Exit immediately if breathing difficulty or dizziness.',
                emoji='💨',
                category='air_quality'
            ))
        elif co2 > self.CO2_BAD:
            alerts.append(Alert(
                severity='warning',
                title='💨 Poor Air Quality',
                body=f'{station}: CO2 {co2} ppm. Headache or drowsiness possible. Improve ventilation.',
                emoji='💨',
                category='air_quality'
            ))
        elif co2 > self.CO2_POOR:
            alerts.append(Alert(
                severity='info',
                title='💨 Stuffy Air',
                body=f'{station}: CO2 {co2} ppm. Ventilation limited. Open window if possible.',
                emoji='💨',
                category='air_quality'
            ))
        
        return alerts
    
    def _check_trail_traffic(self, motion: int, station: str) -> List[Alert]:
        alerts = []
        
        if motion > self.TRAFFIC_HIGH:
            alerts.append(Alert(
                severity='info',
                title='👥 High Trail Traffic',
                body=f'{station}: {motion} hikers detected in last hour. Expect crowds and delays.',
                emoji='👥',
                category='trail'
            ))
        elif motion > self.TRAFFIC_MODERATE:
            alerts.append(Alert(
                severity='info',
                title='👥 Moderate Traffic',
                body=f'{station}: {motion} hikers in last hour. Trail moderately busy.',
                emoji='👥',
                category='trail'
            ))
        
        return alerts
    
    def _check_slippery_conditions(self, rained_recently: bool, temp: Optional[float],
                                    station: str) -> List[Alert]:
        if not rained_recently or temp is None or temp >= 5:
            return []
        
        return [Alert(
            severity='warning',
            title='⚠️ Slippery Trail',
            body=f'{station}: Recent rain + cold temps. Ice or mud likely. Use caution.',
            emoji='⚠️',
            category='trail'
        )]
    
    def get_highest_severity_alert(self, alerts: List[Alert]) -> Optional[Alert]:
        if not alerts:
            return None
        
        severity_order = {'danger': 0, 'warning': 1, 'info': 2}
        return min(alerts, key=lambda a: severity_order.get(a.severity, 999))



alert_analyzer = AlertAnalyzer()
