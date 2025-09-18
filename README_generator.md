# Grafana Dashboard Generator

A simple MVP tool to dynamically generate Grafana dashboards from Excel/CSV input.

## Files

- `dashboard_config.csv` - Excel/CSV template for dashboard configuration
- `grafana_generator.py` - Python script to convert CSV to Grafana JSON
- `requirements.txt` - Python dependencies
- `generated_dashboard.json` - Output Grafana dashboard JSON

## How to Use

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Your Dashboard
Edit `dashboard_config.csv` with your dashboard configuration:

| Column | Description |
|--------|-------------|
| Row | Row name (e.g., "Row1", "Row2") |
| Panel_Title | Title for the panel (leave empty for additional targets) |
| Panel_Type | Grafana panel type (e.g., "state-timeline") |
| Eng_Str_Field | Field name for engineering string (e.g., "eng_str") |
| Time_Field | Field name for timestamp (e.g., "ert") |
| Table_Name | Database table name (e.g., "STATE_MACH_TARGET_STATE") |
| Spacecraft_ID | Spacecraft ID value (e.g., "${scid}") |
| Dataset | Dataset name (e.g., "iox") |
| Is_Additional_Target | Set to "TRUE" for additional targets, leave empty for new panels |

**Dynamic Multi-Target Support:**
- Each row with a `Panel_Title` creates a new panel
- Subsequent rows with `Is_Additional_Target=TRUE` add more targets to the previous panel
- Supports unlimited targets (A, B, C, D, E, F, G, H...)

### 3. Generate Dashboard
```bash
python grafana_generator.py
```

This creates `generated_dashboard.json` that can be imported into Grafana.

## Example CSV Format
```csv
Row,Panel_Title,Panel_Type,Eng_Str_Field,Time_Field,Table_Name,Spacecraft_ID,Dataset,Is_Additional_Target
Row1,Test Panel 1,state-timeline,eng_str,ert,STATE_MACH_TARGET_STATE,${scid},iox,
Row1,Test Panel 2,state-timeline,eng_str,ert,STATE_MACH_TARGET_STATE,${scid},iox,
Row1,,,status_field,timestamp,SYSTEM_STATUS,${scid},iox,TRUE
Row1,,,health_str,ert,HEALTH_CHECK,${scid},iox,TRUE
Row1,,,mode_str,ert,OPERATION_MODE,${scid},iox,TRUE
```

This example creates:
- **Panel 1**: Single target (refId A) from STATE_MACH_TARGET_STATE
- **Panel 2**: Four targets (refId A,B,C,D) from different tables:
  - Target A: STATE_MACH_TARGET_STATE.eng_str
  - Target B: SYSTEM_STATUS.status_field  
  - Target C: HEALTH_CHECK.health_str
  - Target D: OPERATION_MODE.mode_str

## Features

- **Modular Design**: Easy to extend and modify
- **Excel Compatible**: Use CSV files that open in Excel
- **Template Variables**: Supports Grafana template variables like `${scid}` and `${DataSource}`
- **Automatic Layout**: Panels are automatically positioned in rows
- **Simple Configuration**: Minimal required fields

## Customization

The script maintains the same structure as your original dashboard including:
- Template variables (spacecraft ID, datasource)
- Color mappings for state-timeline panels
- Time range filters
- InfluxDB datasource configuration

To modify the dashboard template, edit the `_get_base_template()` method in `grafana_generator.py`.
