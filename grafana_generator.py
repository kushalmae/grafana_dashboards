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
    """
    Grafana Dashboard Generator
    
    Generates Grafana dashboards from CSV configuration with support for:
    - Flexible layout strategies (horizontal, sequential, auto)
    - Custom panel styles and mappings
    - Multiple targets per panel
    """
    
    # Grid system constants
    GRAFANA_GRID_WIDTH = 24
    DEFAULT_PANEL_WIDTH = 5
    DEFAULT_PANEL_HEIGHT = 5
    
    # Supported reference IDs for targets (up to 8 targets per panel)
    TARGET_REF_IDS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    
    # Layout types
    LAYOUT_HORIZONTAL = 'horizontal'
    LAYOUT_SEQUENTIAL = 'sequential'
    LAYOUT_AUTO = 'auto'
    
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
    
    # ============================================================================
    # CONFIGURATION AND STYLES MANAGEMENT
    # ============================================================================
    
    def _load_panel_styles_from_config(self, config_df: pd.DataFrame):
        """
        Load panel styles from the main configuration DataFrame.
        
        Extracts style information from rows that have Panel_Template and style columns.
        
        Args:
            config_df: Main configuration DataFrame containing style columns
        """
        # Filter rows that have panel templates and style information
        style_rows = config_df[
            (config_df['Panel_Template'].notna()) & 
            (config_df['Panel_Template'] != '') &
            (config_df['Grid_Height'].notna() | config_df['Grid_Width'].notna())
        ]
        
        for _, row in style_rows.iterrows():
            panel_template = row['Panel_Template']
            if panel_template not in self.panel_styles:
                self.panel_styles[panel_template] = {
                    'grid_height': int(row.get('Grid_Height', self.DEFAULT_PANEL_HEIGHT)) if pd.notna(row.get('Grid_Height')) else self.DEFAULT_PANEL_HEIGHT,
                    'grid_width': int(row.get('Grid_Width', self.DEFAULT_PANEL_WIDTH)) if pd.notna(row.get('Grid_Width')) else self.DEFAULT_PANEL_WIDTH,
                    'mappings': self._parse_mappings(row.get('Mappings', '')),
                    'thresholds': self._parse_thresholds(row.get('Thresholds', ''))
                }
        
        print(f"Loaded styles for {len(self.panel_styles)} panels from configuration")
    
    def _parse_mappings(self, mappings_str: str) -> List[Dict[str, Any]]:
        """Parse mapping string format: 'SAFE:light-green:Payload Safe|NOMINAL:orange:Nominal State|FAULT:red:Fault State'"""
        if not mappings_str or pd.isna(mappings_str):
            # Empty mappings by default
            return []
        
        # Parse custom mappings
        options = {}
        mappings = mappings_str.split('|')
        
        for i, mapping in enumerate(mappings):
            if ':' in mapping:
                parts = mapping.split(':', 2)  # Split into max 3 parts: value:color:text
                value = parts[0]
                color = parts[1] if len(parts) > 1 else "green"
                text = parts[2] if len(parts) > 2 else value  # Use value as text if not specified
                
                options[value] = {
                    "color": color, 
                    "index": i,
                    "text": text
                }
        
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
    
    def _build_state_timeline_query(self, config: Dict[str, Any]) -> str:
        """Build SQL query specifically for state-timeline panels"""
        eng_str_field = config.get('Eng_Str_Field', 'eng_str')
        time_field = config.get('Time_Field', 'ert')
        table_name = config.get('Table_Name', 'STATE_MACH_TARGET_STATE')
        spacecraft_id = config.get('Spacecraft_ID', '${scid}')
        column_alias = config.get('Column_Alias', '')
        
        # Handle NaN values from pandas
        if pd.isna(eng_str_field): eng_str_field = 'eng_str'
        if pd.isna(time_field): time_field = 'ert'
        if pd.isna(table_name): table_name = 'STATE_MACH_TARGET_STATE'
        if pd.isna(spacecraft_id): spacecraft_id = '${scid}'
        if pd.isna(column_alias): column_alias = ''
        
        # Use column alias if provided, otherwise use empty string (default behavior)
        alias_part = f'"{column_alias}"' if column_alias else '" "'
        
        # State-timeline specific query: includes both eng_str and from_unixtime
        sql_query = f"""SELECT\r\n  "{eng_str_field}" AS {alias_part},\r\n  from_unixtime("{time_field}") AS "time"\r\nFROM\r\n  "{table_name}"\r\nWHERE\r\n  "{time_field}" >= $__timeFrom::bigint\r\n  AND "{time_field}" <= $__timeTo::bigint\r\n  AND "spacecraft_id" = '{spacecraft_id}'\r\nORDER BY "{time_field}" ASC\r\n"""
        
        return sql_query
    
    def _build_standard_query(self, config: Dict[str, Any]) -> str:
        """Build SQL query for standard panels (stat, gauge, etc.)"""
        eng_str_field = config.get('Eng_Str_Field', 'eng_str')
        time_field = config.get('Time_Field', 'ert')
        table_name = config.get('Table_Name', 'STATE_MACH_TARGET_STATE')
        spacecraft_id = config.get('Spacecraft_ID', '${scid}')
        column_alias = config.get('Column_Alias', '')
        
        # Handle NaN values from pandas
        if pd.isna(eng_str_field): eng_str_field = 'eng_str'
        if pd.isna(time_field): time_field = 'ert'
        if pd.isna(table_name): table_name = 'STATE_MACH_TARGET_STATE'
        if pd.isna(spacecraft_id): spacecraft_id = '${scid}'
        if pd.isna(column_alias): column_alias = ''
        
        # Use column alias if provided, otherwise use empty string (default behavior)
        alias_part = f'"{column_alias}"' if column_alias else '" "'
        
        # Standard query: just the field with alias
        sql_query = f"""SELECT\r\n  "{eng_str_field}" AS {alias_part}\r\nFROM\r\n  "{table_name}"\r\nWHERE\r\n  "{time_field}" >= $__timeFrom::bigint\r\n  AND "{time_field}" <= $__timeTo::bigint\r\n  AND "spacecraft_id" = '{spacecraft_id}'\r\nORDER BY "{time_field}" DESC\r\n"""
        
        return sql_query
    
    def _build_sql_query(self, config: Dict[str, Any]) -> str:
        """Build SQL query from configuration components - routes to appropriate builder"""
        panel_type = config.get('Panel_Type', 'stat')
        
        # Handle NaN values from pandas
        if pd.isna(panel_type): panel_type = 'stat'
        
        # Route to appropriate query builder based on panel type
        if panel_type == 'state-timeline':
            return self._build_state_timeline_query(config)
        else:
            return self._build_standard_query(config)
    
    def _create_target(self, config: Dict[str, Any], ref_id: str) -> Dict[str, Any]:
        """Create a single target from configuration"""
        # dataset = config.get('Dataset', 'iox')
        # if pd.isna(dataset): dataset = 'iox'
        
        target = {
            "dataset": "iox",
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
        mappings = panel_style.get('mappings', [])
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
                "justifyMode": "auto",
                "orientation": "auto",
                "percentChangeColorMode": "standard",
                "reduceOptions": {"calcs": ["last"], "fields": "", "values": False},
                "showPercentChange": False,
                "textMode": "value_and_name",
                "wideLayout": True
            },
            "pluginVersion": "12.1.0-247000",
            "targets": [],  # Will be populated dynamically
            "title": config.get('Panel_Title', config.get('Panel_Template', 'Untitled')),
            "type": config.get('Panel_Type', 'state-timeline')
        }
    

    # ============================================================================
    # LAYOUT AND POSITIONING LOGIC  
    # ============================================================================

    def _calculate_layout_positions(self, panel_groups, current_x=0, current_y=0):
        """
        Calculate panel positions based on layout strategy.
        
        Layout Types:
        - horizontal: All panels of same template on same row
        - sequential: Continue from current position, wrap when needed  
        - auto: Smart grouping - new row if template group doesn't fit
        
        Args:
            panel_groups: List of panel group configurations
            current_x: Starting X position (0-23)
            current_y: Starting Y position  
            
        Returns:
            Tuple of (positioned_panels, final_x, final_y)
        """
        positioned_panels = []
        
        # Group panels by template and layout to handle them together
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
            
            if layout_type == self.LAYOUT_HORIZONTAL:
                # For horizontal layout, force new row and place all panels side by side
                if current_x > 0:
                    current_y += panel_height
                    current_x = 0
                
                # Place all panels of this template horizontally
                for panel_group in panels_in_group:
                    panel_group['x_pos'] = current_x
                    panel_group['y_pos'] = current_y
                    positioned_panels.append(panel_group)
                    current_x += panel_width
                    
                    # Check if we exceed Grafana grid width
                    if current_x >= self.GRAFANA_GRID_WIDTH:
                        current_x = 0
                        current_y += panel_height
                
                # Move to next row after horizontal group
                if current_x > 0:
                    current_y += panel_height
                    current_x = 0
                    
            elif layout_type == self.LAYOUT_AUTO:
                # Check if all panels in template group fit on current row
                total_width = len(panels_in_group) * panel_width
                if current_x + total_width > self.GRAFANA_GRID_WIDTH:
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
                    if current_x >= self.GRAFANA_GRID_WIDTH:
                        current_x = 0
                        current_y += panel_height
        
        return positioned_panels, current_x, current_y
    
    # ============================================================================
    # DASHBOARD GENERATION
    # ============================================================================
    
    def generate_dashboard(self, csv_file: str, dashboard_title: str = None) -> Dict[str, Any]:
        """Generate Grafana dashboard from CSV input with dynamic targets"""
        # Read CSV configuration
        config_dataframe = pd.read_csv(csv_file)
        
        # Load panel styles from the configuration
        self._load_panel_styles_from_config(config_dataframe)
        
        # Initialize dashboard
        dashboard = self.dashboard_template.copy()
        if dashboard_title:
            dashboard['title'] = dashboard_title
        
        panels = []
        current_y = 0
        panel_id = 1
        
        # Group by rows
        rows = config_dataframe['Row'].unique()
        
        for row_name in rows:
            # Add row panel
            row_panel = self._create_row_panel(row_name, panel_id, current_y)
            panels.append(row_panel)
            panel_id += 1
            current_y += 1
            
            # Get all rows for this row name
            row_data = config_dataframe[config_dataframe['Row'] == row_name].copy()
            
            # Group by Panel_Template - same templates become one panel with multiple targets
            panel_groups = {}  # Dictionary to group by panel template
            
            for _, row_config in row_data.iterrows():
                panel_template = row_config.get('Panel_Template', '')
                
                # Handle NaN values from pandas
                if pd.isna(panel_template): panel_template = ''
                panel_template = panel_template.strip()
                
                if panel_template:
                    # This row has a panel template - either start new panel or add to existing
                    if panel_template not in panel_groups:
                        # First occurrence of this panel template
                        panel_groups[panel_template] = {
                            'panel_config': row_config,
                            'targets': [row_config]
                        }
                    else:
                        # Additional occurrence of same panel template - add as target
                        panel_groups[panel_template]['targets'].append(row_config)
                else:
                    # This is an additional target (no Panel_Template) - add to the last panel
                    if panel_groups:
                        # Get the last panel group added
                        last_panel_template = list(panel_groups.keys())[-1]
                        panel_groups[last_panel_template]['targets'].append(row_config)
            
            # Convert dictionary to list for processing
            panel_groups = list(panel_groups.values())
            
            # Calculate layout positions for panels
            positioned_panels, x_pos, current_y = self._calculate_layout_positions(panel_groups, 0, current_y)
            
            # Create panels with their targets
            for panel_group in positioned_panels:
                # Create the panel with calculated position
                panel = self._create_panel(panel_group['panel_config'], panel_id, panel_group['x_pos'], panel_group['y_pos'])
                
                # Add all targets to the panel
                targets = []
                
                for i, target_config in enumerate(panel_group['targets']):
                    if i < len(self.TARGET_REF_IDS):
                        target = self._create_target(target_config, self.TARGET_REF_IDS[i])
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
    
    # Generate dashboard from CSV (styles are now loaded from the same CSV)
    dashboard = generator.generate_dashboard(
        'dashboard_config.csv',
        'Generated Dashboard'
    )
    
    # Save to file
    generator.save_dashboard(dashboard, 'generated_dashboard.json')


if __name__ == "__main__":
    main()
