# Amazon QuickSight Setup

## Calculated Fields

### conversation_phase

    ifelse(
        conversation_status = 'FAILED_IDENTITY_VERIFICATION' OR conversation_status = 'DECLINED_ADDRESS_UPDATE',
        'UPDATE_FAILED',
        ifelse(
            conversation_status = 'WAITING_ON_INITIAL_RESPONSE' OR conversation_status = 'NONE',
            'WAITING_ON_ENGAGEMENT',
            ifelse(
                conversation_status = 'WAITING_FOR_VERIFICATION_FIRST_TIME' OR conversation_status = 'WAITING_FOR_VERIFICATION' OR conversation_status = 'WAITING_FOR_ADDRESS_CHANGE_ANSWER' OR conversation_status = 'WAITING_FOR_ADDRESS' OR conversation_status = 'WAITING_FOR_ADDRESS_CONFIRMATION',
                'UPDATE_IN_PROGRESS',
                ifelse(
                    conversation_status = 'ADDRESS_CONFIRMED' OR conversation_status = 'ADDRESS_UPDATED',
                    'UPDATE_COMPLETE',
                    'UNKNOWN'
                )
            )
        )       
    )

### report_status_success

    ifelse(conversation_status = 'ADDRESS_CONFIRMED' OR conversation_status = 'ADDRESS_UPDATED', 1, 0)

### report_status_fail

    ifelse(conversation_status = 'FAILED_IDENTITY_VERIFICATION' OR conversation_status = 'DECLINED_ADDRESS_UPDATE', 1, 0)

### report_status_has_responded

    ifelse(conversation_status = 'WAITING_ON_INITIAL_RESPONSE' OR conversation_status = 'NONE', 0, 1)

### report_status_in_flight

    ifelse(conversation_status = 'WAITING_FOR_VERIFICATION_FIRST_TIME' OR conversation_status = 'WAITING_FOR_VERIFICATION' OR conversation_status = 'WAITING_FOR_ADDRESS_CHANGE_ANSWER' OR conversation_status = 'WAITING_FOR_ADDRESS' OR conversation_status = 'WAITING_FOR_ADDRESS_CONFIRMATION', 1, 0)

## Visualizations

### Grouped by Conversation Status

- Visual Type: Pie Chart
- Field wells
  - Group/Color: `conversation_phase`
  - Value: `conversation_status (Count)`

### Respondents

- Visual Type: Gauge Chart
- Field wells
  - Value: `report_status_has_responded (Sum)`
  - Target value: `conversation_status (Count)`

### Successful Address Engagements

- Visual Type: Gauge Chart
- Field wells
  - Value: `report_status_has_success (Sum)`
  - Target value: `conversation_status (Count)`

### Group by Engagement Phase

- Visual Type: Horizontal Bar Chart
- Field wells
  - Y Axis: `conversation_phase`

### Contact Table

- Visual Type: Table
- Field wells
  - Value:
    - `pk`
    - `Language`
    - `first_name`
    - `last_name`
    - `conversation_status`
    - `physical_address`
