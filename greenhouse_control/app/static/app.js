document.addEventListener('DOMContentLoaded', () => {
  async function refreshTelemetry() {
    try {
      const res = await fetch('api/status');
      if (!res.ok) return;
      const data = await res.json();

      if (data.vpd) {
        document.getElementById('leafVpdValue').textContent = data.vpd.leaf_vpd_kpa.toFixed(2);
        document.getElementById('airVpdValue').textContent = `${data.vpd.air_vpd_kpa.toFixed(2)} kPa`;
        
        const needlePercent = Math.min(100, Math.max(0, (data.vpd.leaf_vpd_kpa / 2.0) * 100));
        document.getElementById('vpdNeedle').style.left = `${needlePercent}%`;
      }

      if (data.climate) {
        document.getElementById('airTempValue').textContent = `${data.climate.air_temp.toFixed(1)} °C`;
        document.getElementById('humidityValue').textContent = `${data.climate.humidity.toFixed(1)} %`;
        document.getElementById('leafTempValue').textContent = `${data.vpd.effective_leaf_temp_c.toFixed(1)} °C`;
        document.getElementById('dewPointValue').textContent = `${data.vpd.dew_point_c.toFixed(1)} °C`;
      }

      if (data.irrigation) {
        document.getElementById('soilMoistureValue').textContent = data.irrigation.soil_moisture.toFixed(1);
        const valveStatusEl = document.getElementById('valveStatus');
        if (data.irrigation.valve_open) {
          valveStatusEl.textContent = 'ON';
          valveStatusEl.classList.add('on');
        } else {
          valveStatusEl.textContent = 'OFF';
          valveStatusEl.classList.remove('on');
        }
      }

      const haIndicator = document.getElementById('haStatusIndicator');
      const haText = document.getElementById('haStatusText');
      if (data.ha_connected) {
        haIndicator.classList.add('active');
        haText.textContent = 'HA Connected';
      } else {
        haIndicator.classList.remove('active');
        haText.textContent = 'Standalone Mode';
      }

      if (data.actions) {
        updateActuator('exhaustStatus', data.actions.exhaust_fan);
        updateActuator('humidifierStatus', data.actions.humidifier);
        updateActuator('heaterStatus', data.actions.heater);
        
        const badge = document.getElementById('vpdStatusBadge');
        badge.textContent = data.actions.status || 'Optimal';
      }

    } catch (e) {
      console.warn('Telemetry polling error:', e);
    }
  }

  function updateActuator(elementId, isOn) {
    const el = document.getElementById(elementId);
    if (!el) return;
    if (isOn) {
      el.textContent = 'ON';
      el.classList.add('on');
    } else {
      el.textContent = 'OFF';
      el.classList.remove('on');
    }
  }

  refreshTelemetry();
  setInterval(refreshTelemetry, 5000);
});
