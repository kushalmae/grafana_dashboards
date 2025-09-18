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
        self.panel_styles = {}  # Will store panel styles from CSV
    
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
    
    def load_panel_styles(self, styles_file: str):
        """Load panel styles from CSV file"""
        try:
            styles_df = pd.read_csv(styles_file)
            for _, row in styles_df.iterrows():
                panel_title = row['Panel_Template']
                self.panel_styles[panel_title] = {
                    'grid_height': int(row.get('Grid_Height', 5)),
                    'grid_width': int(row.get('Grid_Width', 5)),
                    'mappings': self._parse_mappings(row.get('Mappings', '')),
                    'thresholds': self._parse_thresholds(row.get('Thresholds', ''))
                }
            print(f"Loaded styles for {len(self.panel_styles)} panels")
        except FileNotFoundError:
            print(f"Warning: Styles file {styles_file} not found. Using default styles.")
        except Exception as e:
            print(f"Error loading styles: {e}. Using default styles.")
    
    def _parse_mappings(self, mappings_str: str) -> List[Dict[str, Any]]:
        """Parse mapping string format: 'SAFE:light-green|NOMINAL:orange|FAULT:red'"""
        if not mappings_str or pd.isna(mappings_str):
            # Default mappings
            return [{
                "options": {
                    "0": {"color": "light-green", "index": 0},
                    "1": {"color": "super-light-yellow", "index": 1},
                    "2": {"color": "light-orange", "index": 2},
                    "3": {"color": "light-red", "index": 3},
                    "4": {"color": "dark-red", "index": 4}
                },
                "type": "value"
            }]
        
        # Parse custom mappings
        options = {}
        mappings = mappings_str.split('|')
        for i, mapping in enumerate(mappings):
            if ':' in mapping:
                value, color = mapping.split(':', 1)
                options[value] = {"color": color, "index": i}
        
        return [{
            "options": options,
            "type": "value"
        }]
    
    def _parse_thresholds(self, thresholds_str: str) -> Dict[str, Any]:
        """Parse threshold string format: '0:green|1:#EAB839|2:red'"""
        if not thresholds_str or pd.isna(thresholds_str):
            # Default thresholds
            return {
                "mode": "absolute",
                "steps": [{"color": "transparent", "value": 0}]
            }
        
        # Parse custom thresholds
        steps = []
        thresholds = thresholds_str.split('|')
        for threshold in thresholds:
            if ':' in threshold:
                value_str, color = threshold.split(':', 1)
                try:
                    value = float(value_str)
                    steps.append({"color": color, "value": value})
                except ValueError:
                    continue
        
        # Sort steps by value
        steps.sort(key=lambda x: x['value'])
        
        return {
            "mode": "absolute",
            "steps": steps if steps else [{"color": "transparent", "value": 0}]
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
        panel_title = config.get('Panel_Title', '')
        
        # Get styles for this panel using template name
        panel_template = config.get('Panel_Template', panel_title)
        panel_style = self.panel_styles.get(panel_template, {})
        grid_height = panel_style.get('grid_height', 5)
        grid_width = panel_style.get('grid_width', 5)
        mappings = panel_style.get('mappings', [{
            "options": {
                "0": {"color": "light-green", "index": 0},
                "1": {"color": "super-light-yellow", "index": 1},
                "2": {"color": "light-orange", "index": 2},
                "3": {"color": "light-red", "index": 3},
                "4": {"color": "dark-red", "index": 4}
            },
            "type": "value"
        }])
        thresholds = panel_style.get('thresholds', {
            "mode": "absolute",
            "steps": [{"color": "transparent", "value": 0}]
        })
        
        return {
            "datasource": {"type": "influxdb", "uid": "${DataSource}"},
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "thresholds"},
                    "mappings": mappings,
                    "thresholds": thresholds
                },
                "overrides": []
            },
            "gridPos": {"h": grid_height, "w": grid_width, "x": x_pos, "y": y_pos},
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
            "title": config.get('Panel_Title', config.get('Panel_Template', 'Untitled')),
            "type": config.get('Panel_Type', 'state-timeline')
        }
    
    def _expand_payloads(self, row_data) -> List[Dict[str, Any]]:
        """Expand payload templates into individual panels"""
        expanded_panels = []
        
        for _, row_config in row_data.iterrows():
            payloads_str = row_config.get('Payloads', '')
            panel_template = row_config.get('Panel_Template', '')
            is_additional_target = str(row_config.get('Is_Additional_Target', '')).upper() == 'TRUE'
            
            if payloads_str and not pd.isna(payloads_str) and panel_template and not is_additional_target:
                # Split payloads: "PL1|PL2|PL3|PL4"
                payloads = [p.strip() for p in payloads_str.split('|') if p.strip()]
                
                for payload in payloads:
                    # Create individual panel for each payload
                    new_config = row_config.copy()
                    new_config['Panel_Title'] = f"{panel_template} {payload}"
                    
                    # Replace ${scid} with payload in table names and spacecraft_id
                    for field in ['Table_Name', 'Spacecraft_ID']:
                        field_value = str(row_config.get(field, ''))
                        if '${scid}' in field_value:
                            new_config[field] = field_value.replace('${scid}', payload)
                    
                    expanded_panels.append(new_config.to_dict())
            else:
                # Regular panel (no payload expansion) or additional target
                expanded_panels.append(row_config.to_dict())
        
        return expanded_panels

    def _calculate_layout_positions(self, panel_groups, current_x=0, current_y=0):
        """Calculate panel positions based on layout strategy"""
        positioned_panels = []
        
        # Group panels by template and layout to handle payloads together
        template_groups = {}
        for panel_group in panel_groups:
            panel_config = panel_group['panel_config']
            panel_template = panel_config.get('Panel_Template', '')
            layout_type = panel_config.get('Layout', 'sequential').lower()
            
            # Create key for grouping (template + layout)
            group_key = f"{panel_template}_{layout_type}"
            
            if group_key not in template_groups:
                template_groups[group_key] = {
                    'template': panel_template,
                    'layout': layout_type,
                    'panels': []
                }
            template_groups[group_key]['panels'].append(panel_group)
        
        # Position each template group
        for group_key, template_group in template_groups.items():
            layout_type = template_group['layout']
            template_name = template_group['template']
            panels_in_group = template_group['panels']
            
            # Get panel dimensions
            panel_style = self.panel_styles.get(template_name, {})
            panel_width = panel_style.get('grid_width', 5)
            panel_height = panel_style.get('grid_height', 5)
            
            if layout_type == 'horizontal':
                # For horizontal layout, force new row and place all payloads side by side
                if current_x > 0:
                    current_y += panel_height
                    current_x = 0
                
                # Place all panels of this template horizontally
                for panel_group in panels_in_group:
                    panel_group['x_pos'] = current_x
                    panel_group['y_pos'] = current_y
                    positioned_panels.append(panel_group)
                    current_x += panel_width
                    
                    # Check if we exceed width
                    if current_x >= 24:
                        current_x = 0
                        current_y += panel_height
                
                # Move to next row after horizontal group
                if current_x > 0:
                    current_y += panel_height
                    current_x = 0
                    
            elif layout_type == 'auto':
                # Check if all panels in template group fit on current row
                total_width = len(panels_in_group) * panel_width
                if current_x + total_width > 24:
                    current_y += panel_height
                    current_x = 0
                
                # Place all panels of this template
                for panel_group in panels_in_group:
                    panel_group['x_pos'] = current_x
                    panel_group['y_pos'] = current_y
                    positioned_panels.append(panel_group)
                    current_x += panel_width
                    
            else:  # sequential
                # Continue placing panels sequentially
                for panel_group in panels_in_group:
                    panel_group['x_pos'] = current_x
                    panel_group['y_pos'] = current_y
                    positioned_panels.append(panel_group)
                    current_x += panel_width
                    
                    # Wrap to next row if needed
                    if current_x >= 24:
                        current_x = 0
                        current_y += panel_height
        
        return positioned_panels, current_x, current_y
    
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
            
            # Expand payloads into individual panels
            expanded_row_data = self._expand_payloads(row_data)
            
            # Convert back to DataFrame for processing
            expanded_df = pd.DataFrame(expanded_row_data)
            
            # Group by panels (rows with Panel_Title/Panel_Template) and their additional targets
            panel_groups = []
            current_panel = None
            
            for _, row_config in expanded_df.iterrows():
                is_additional_target = str(row_config.get('Is_Additional_Target', '')).upper() == 'TRUE'
                panel_title = row_config.get('Panel_Title', '')
                panel_template = row_config.get('Panel_Template', '')
                
                if not is_additional_target and (panel_title or panel_template):
                    # This is a new panel
                    if current_panel is not None:
                        panel_groups.append(current_panel)
                    current_panel = {
                        'panel_config': row_config,
                        'targets': [row_config]  # First target
                    }
                elif is_additional_target and current_panel is not None:
                    # This is an additional target for the current panel
                    current_panel['targets'].append(row_config)
            
            # Add the last panel
            if current_panel is not None:
                panel_groups.append(current_panel)
            
            # Calculate layout positions for panels
            positioned_panels, x_pos, current_y = self._calculate_layout_positions(panel_groups, 0, current_y)
            
            # Create panels with their targets
            for panel_group in positioned_panels:
                # Create the panel with calculated position
                panel = self._create_panel(panel_group['panel_config'], panel_id, panel_group['x_pos'], panel_group['y_pos'])
                
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
            
            # Update current_y for next row
            if positioned_panels:
                # Get the maximum y position + height from this row's panels
                max_y = max(p['y_pos'] for p in positioned_panels)
                max_height = max(self.panel_styles.get(p['panel_config'].get('Panel_Template', ''), {}).get('grid_height', 5) 
                               for p in positioned_panels)
                current_y = max_y + max_height
        
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
    
    # Load panel styles
    generator.load_panel_styles('panel_styles.csv')
    
    # Generate dashboard from CSV
    dashboard = generator.generate_dashboard(
        'dashboard_config.csv',
        'Generated THDR FDIR Dashboard'
    )
    
    # Save to file
    generator.save_dashboard(dashboard, 'generated_dashboard.json')


if __name__ == "__main__":
    main()
