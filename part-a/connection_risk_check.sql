-- Early warning: no LOADED event on the booked connecting vessel
-- after that vessel's actual departure from the transshipment port.
--
-- Requires an actual departure event (AIS or terminal). It deliberately
-- does not fall back to the booked ETD, which would false-alert whenever
-- the booked vessel itself sails late.
--
-- Detection only: it flags containers for investigation. A second
-- reconciliation step decides whether the cause was a rollover, data
-- latency, a missing milestone or another exception.
--
-- Assumes bookings are stored per leg (each leg has its own booked
-- vessel, voyage and ETD).

SELECT
    b.container_id,
    b.booked_vessel_imo,
    b.booked_voyage_id,
    b.booked_etd,
    b.transshipment_port,
    m_dep_actual.timestamp AS actual_departure
FROM bookings b
JOIN milestones m_dep_actual
    ON  m_dep_actual.vessel_imo = b.booked_vessel_imo
    AND m_dep_actual.voyage_id  = b.booked_voyage_id   -- voyage key avoids matching later calls
    AND m_dep_actual.event_type = 'DEPARTED'
    AND m_dep_actual.port       = b.transshipment_port
LEFT JOIN milestones m_load                             -- anti-join: no LOADED on the booked vessel
    ON  m_load.container_id = b.container_id
    AND m_load.event_type   = 'LOADED'
    AND m_load.port         = b.transshipment_port
    AND m_load.vessel_imo   = b.booked_vessel_imo
    AND m_load.voyage_id    = b.booked_voyage_id
WHERE m_dep_actual.timestamp < CURRENT_TIMESTAMP - INTERVAL '24 hours'  -- tolerance for data latency
  AND m_load.container_id IS NULL;
