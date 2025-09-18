#!/usr/bin/env python3
"""
Grafana Dashboard Generator
Converts Excel/CSV input to Grafana JSON dashboard format
"""

import pandas as pd
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any


class GrafanaDashboardGenerator:
    """Simple generator for Grafana dashboards from Excel/CSV input"""
    
    def __init__(self):
        self.dashboard_template = self._get_base_template()
    
    def _get_base_template(self) -> Dict[str, Any]:
        """Base Grafana dashboard template"""
        return {
            "annotations": {
                "list": [{
                    "builtIn": 1,
                    "datasource": {"type": "grafana", "uid": "-- Grafana --"},
                    "enable": True,
                    "hide": True,
                    "iconColor": "rgba(0, 211, 255, 1)",
                    "name": "Annotations & Alerts",
                    "type": "dashboard"
                }]
            },
            "editable": True,
            "fiscalYearStartMonth": 0,
            "graphTooltip": 0,
            "id": None,
            "links": [],
            "panels": [],
            "preload": False,
            "schemaVersion": 41,
            "tags": [],
            "templating": {
                "list": [
                    {
                        "current": {"text": "TM004DUP", "value": "TM004DUP"},
                        "datasource": {"type": "influxdb", "uid": "${DataSource}"},
                        "definition": "SELECT DISTINCT \"spacecraft_id\" \nFROM \"MDC_ACMODE\"\nWHERE \"spacecraft_id\" IS NOT NULL;",
                        "description": "",
                        "label": "Spacecraft",
                        "name": "scid",
                        "options": [],
                        "query": {
                            "query": "SELECT DISTINCT \"spacecraft_id\" \nFROM \"MDC_ACMODE\"\nWHERE \"spacecraft_id\" IS NOT NULL;",
                            "refId": "InfluxVariableQueryEditor-VariableQuery"
                        },
                        "refresh": 1,
                        "regex": "",
                        "type": "query"
                    },
                    {
                        "current": {"text": "influxdb-sql-thunder-max-telemetry-mr-30-b", "value": "eex74u67acirkd"},
                        "label": "Data Source",
                        "name": "DataSource",
                        "options": [],
                        "query": "influxdb",
                        "refresh": 1,
                        "regex": "",
                        "type": "datasource"
                    }
                ]
            },
            "time": {
                "from": "2025-09-11T02:30:00.000Z",
                "to": "2025-09-11T23:20:00.000Z"
            },
            "timepicker": {},
            "timezone": "utc",
            "title": "Generated Dashboard",
            "uid": str(uuid.uuid4()),
            "version": 1
        }
    
    def _create_row_panel(self, row_name: str, row_id: int, y_pos: int) -> Dict[str, Any]:
        """Create a row panel"""
        return {
            "collapsed": False,
            "gridPos": {"h": 1, "w": 24, "x": 0, "y": y_pos},
            "id": row_id,
            "panels": [],
            "title": row_name,
            "type": "row"
        }
    
    def _build_sql_query(self, config: Dict[str, Any]) -> str:
        """Build SQL query from configuration components"""
        eng_str_field = config.get('Eng_Str_Field', 'eng_str')
        time_field = config.get('Time_Field', 'ert')
        table_name = config.get('Table_Name', 'STATE_MACH_TARGET_STATE')
        spacecraft_id = config.get('Spacecraft_ID', '${scid}')
        
        # Handle NaN values from pandas
        if pd.isna(eng_str_field): eng_str_field = 'eng_str'
        if pd.isna(time_field): time_field = 'ert'
        if pd.isna(table_name): table_name = 'STATE_MACH_TARGET_STATE'
        if pd.isna(spacecraft_id): spacecraft_id = '${scid}'
        
        # Build the SQL query with proper formatting
        sql_query = f"""SELECT\r\n  "{eng_str_field}" AS " ",\r\n  from_unixtime("{time_field}")\r\nFROM\r\n  "{table_name}"\r\nWHERE\r\n  "{time_field}" >= $__timeFrom::bigint\r\n  AND "{time_field}" <= $__timeTo::bigint\r\n  AND "spacecraft_id" = '{spacecraft_id}'\r\nORDER BY "{time_field}" DESC\r\n"""
        
        return sql_query
    
    def _create_target(self, config: Dict[str, Any], ref_id: str) -> Dict[str, Any]:
        """Create a single target from configuration"""
        dataset = config.get('Dataset', 'iox')
        if pd.isna(dataset): dataset = 'iox'
        
        target = {
            "dataset": dataset,
            "editorMode": "code",
            "format": "table",
            "rawQuery": True,
            "rawSql": self._build_sql_query(config),
            "refId": ref_id,
            "sql": {
                "columns": [{"parameters": [], "type": "function"}],
                "groupBy": [{"property": {"type": "string"}, "type": "groupBy"}]
            }
        }
        
        return target
    
    def _create_panel(self, config: Dict[str, Any], panel_id: int, x_pos: int, y_pos: int) -> Dict[str, Any]:
        """Create a panel from configuration"""
        return {
            "datasource": {"type": "influxdb", "uid": "${DataSource}"},
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "thresholds"},
                    "mappings": [{
                        "options": {
                            "0": {"color": "light-green", "index": 0},
                            "1": {"color": "super-light-yellow", "index": 1},
                            "2": {"color": "light-orange", "index": 2},
                            "3": {"color": "light-red", "index": 3},
                            "4": {"color": "dark-red", "index": 4}
                        },
                        "type": "value"
                    }],
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [{"color": "transparent", "value": 0}]
                    }
                },
                "overrides": []
            },
            "gridPos": {"h": 5, "w": 5, "x": x_pos, "y": y_pos},
            "id": panel_id,
            "options": {
                "colorMode": "background",
                "graphMode": "none",
                "justifyMode": "center",
                "orientation": "auto",
                "percentChangeColorMode": "standard",
                "reduceOptions": {"calcs": ["last"], "fields": "", "values": False},
                "showPercentChange": False,
                "text": {"titleSize": 12, "valueSize": 25},
                "textMode": "value_and_name",
                "wideLayout": True
            },
            "pluginVersion": "12.1.0-247000",
            "targets": [],  # Will be populated dynamically
            "title": config['Panel_Title'],
            "type": config.get('Panel_Type', 'state-timeline')
        }
    
    def generate_dashboard(self, csv_file: str, dashboard_title: str = None) -> Dict[str, Any]:
        """Generate Grafana dashboard from CSV input with dynamic targets"""
        # Read CSV
        df = pd.read_csv(csv_file)
        
        # Initialize dashboard
        dashboard = self.dashboard_template.copy()
        if dashboard_title:
            dashboard['title'] = dashboard_title
        
        panels = []
        current_y = 0
        panel_id = 1
        
        # Group by rows
        rows = df['Row'].unique()
        
        for row_name in rows:
            # Add row panel
            row_panel = self._create_row_panel(row_name, panel_id, current_y)
            panels.append(row_panel)
            panel_id += 1
            current_y += 1
            
            # Get all rows for this row name
            row_data = df[df['Row'] == row_name].copy()
            
            # Group by panels (rows with Panel_Title) and their additional targets
            panel_groups = []
            current_panel = None
            
            for _, row_config in row_data.iterrows():
                is_additional_target = str(row_config.get('Is_Additional_Target', '')).upper() == 'TRUE'
                
                if not is_additional_target and not pd.isna(row_config.get('Panel_Title', '')):
                    # This is a new panel
                    if current_panel is not None:
                        panel_groups.append(current_panel)
                    current_panel = {
                        'panel_config': row_config.to_dict(),
                        'targets': [row_config.to_dict()]  # First target
                    }
                elif is_additional_target and current_panel is not None:
                    # This is an additional target for the current panel
                    current_panel['targets'].append(row_config.to_dict())
            
            # Add the last panel
            if current_panel is not None:
                panel_groups.append(current_panel)
            
            # Create panels with their targets
            x_pos = 0
            for panel_group in panel_groups:
                # Create the panel
                panel = self._create_panel(panel_group['panel_config'], panel_id, x_pos, current_y)
                
                # Add all targets to the panel
                targets = []
                ref_ids = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']  # Support up to 8 targets
                
                for i, target_config in enumerate(panel_group['targets']):
                    if i < len(ref_ids):
                        target = self._create_target(target_config, ref_ids[i])
                        targets.append(target)
                
                panel['targets'] = targets
                panels.append(panel)
                panel_id += 1
                x_pos += 5  # Move to next position
                
                # If we exceed width, move to next row
                if x_pos >= 24:
                    x_pos = 0
                    current_y += 5
            
            # Move to next row if we haven't already
            if x_pos > 0:
                current_y += 5
        
        dashboard['panels'] = panels
        return dashboard
    
    def save_dashboard(self, dashboard: Dict[str, Any], output_file: str):
        """Save dashboard to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(dashboard, f, indent=2)
        print(f"Dashboard saved to: {output_file}")


def main():
    """Main function to run the generator"""
    generator = GrafanaDashboardGenerator()
    
    # Generate dashboard from CSV
    dashboard = generator.generate_dashboard(
        'dashboard_config.csv',
        'Generated THDR FDIR Dashboard'
    )
    
    # Save to file
    generator.save_dashboard(dashboard, 'generated_dashboard.json')


if __name__ == "__main__":
    main()
