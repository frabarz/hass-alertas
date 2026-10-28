# Dashboards and automations

## Card

```yaml
type: entities
title: Alertas Chile
entities:
  - entity: binary_sensor.csn
  - entity: binary_sensor.sismo_detector
  - entity: binary_sensor.senapred_sae
  - entity: binary_sensor.tsunami
  - entity: sensor.active_alerts
  - entity: sensor.last_alert
  - entity: binary_sensor.connection
```

The connection sensor is diagnostic but can still be shown explicitly.

## Notify on any new active alert

```yaml
alias: Alertas Chile — notify active emergency
triggers:
  - trigger: state
    entity_id:
      - binary_sensor.csn
      - binary_sensor.sismo_detector
      - binary_sensor.senapred_sae
      - binary_sensor.tsunami
    from: "off"
    to: "on"
actions:
  - action: notify.mobile_app_phone
    data:
      title: "{{ trigger.to_state.attributes.source_name }}"
      message: >-
        {% if trigger.to_state.attributes.magnitude is defined %}
        M{{ trigger.to_state.attributes.magnitude }} —
        {{ trigger.to_state.attributes.place }}
        {% elif trigger.to_state.attributes.message is defined %}
        {{ trigger.to_state.attributes.message }}
        {% elif trigger.to_state.attributes.text is defined %}
        {{ trigger.to_state.attributes.text }}
        {% else %}
        Active alert
        {% endif %}
```

## React to the event entity

```yaml
alias: Alertas Chile — log every relay message
triggers:
  - trigger: state
    entity_id: event.alert
actions:
  - action: logbook.log
    data:
      name: "{{ trigger.to_state.attributes.event_type }}"
      message: "{{ trigger.to_state.attributes }}"
```

## Tsunami evacuation aid

```yaml
alias: Alertas Chile — tsunami alert
triggers:
  - trigger: state
    entity_id: binary_sensor.tsunami
    to: "on"
actions:
  - action: notify.mobile_app_phone
    data:
      title: Tsunami — {{ state_attr('binary_sensor.tsunami', 'state') }}
      message: >-
        Zonas: {{ state_attr('binary_sensor.tsunami', 'zones') | join(', ') }}.
        Siga las instrucciones oficiales de SENAPRED/SHOA.
      data:
        channel: alarm_stream
        ttl: 0
        priority: high
```

Use critical/alarm notification channels where available, but always keep
official SAE alerts enabled on your phone.
