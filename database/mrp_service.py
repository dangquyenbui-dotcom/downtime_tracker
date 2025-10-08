# dangquyenbui-dotcom/downtime_tracker/downtime_tracker-5bb4163f1c166071f5c302dee6ed03e0344576eb/database/mrp_service.py
"""
MRP (Material Requirements Planning) Service
This service contains the core logic for calculating production suggestions.
"""

from .erp_connection import get_erp_service
from .capacity import ProductionCapacityDB

# Create an instance of the capacity DB directly
capacity_db = ProductionCapacityDB()

class MRPService:
    def __init__(self):
        self.erp = get_erp_service()

    def get_component_inventory(self):
        """
        Fetches and processes raw material/component inventory from the ERP.
        Returns a dictionary mapping part numbers to their available quantities.
        """
        inventory_data = self.erp.get_raw_material_inventory()
        inventory = {}
        for row in inventory_data:
            part_number = row['PartNumber']
            inventory[part_number] = {
                'approved': row.get('on_hand_approved', 0),
                'pending_qc': row.get('on_hand_pending_qc', 0),
                'quarantine': row.get('on_hand_quarantine', 0),
                'issued_to_job': row.get('issued_to_job', 0),
                'staged': row.get('staged', 0)
            }
        return inventory

    def calculate_mrp_suggestions(self):
        """
        The main MRP engine. Calculates production suggestions for all open sales orders.
        """
        # 1. Fetch all necessary data in bulk to minimize DB calls
        print("MRP RUN: Fetching data...")
        sales_orders = self.erp.get_open_order_schedule()
        boms = self.erp.get_bom_data()
        purchase_orders = self.erp.get_purchase_order_data()
        component_inventory = self.get_component_inventory()
        
        # --- FIX: Fetch Finished Good Inventory to calculate Net Qty ---
        finished_good_inventory_data = self.erp.get_on_hand_inventory()
        fg_inventory_map = {item['PartNumber']: item['TotalOnHand'] for item in finished_good_inventory_data}
        
        capacities = {c['line_id']: c['capacity_per_shift'] for c in capacity_db.get_all()}
        print(f"MRP RUN: Found {len(sales_orders)} SO lines, {len(boms)} BOM lines, {len(purchase_orders)} PO lines.")

        # 2. Pre-process data into lookup dictionaries for performance
        boms_by_parent = {}
        for item in boms:
            parent = item['Parent Part Number']
            if parent not in boms_by_parent:
                boms_by_parent[parent] = []
            boms_by_parent[parent].append(item)

        pos_by_part = {}
        for po in purchase_orders:
            part = po['Part Number']
            if po.get('Open Quantity', 0) > 0:
                if part not in pos_by_part:
                    pos_by_part[part] = 0
                pos_by_part[part] += po['Open Quantity']

        # 3. Process each sales order
        mrp_results = []
        for so in sales_orders:
            part_number = so['Part']
            
            # --- FIX: Calculate Net Qty here ---
            on_hand_qty = fg_inventory_map.get(part_number, 0)
            ord_qty_curr_level = so.get('Ord Qty - Cur. Level', 0)
            net_qty = ord_qty_curr_level - on_hand_qty
            
            # Store the calculated Net Qty back into the sales order object for display
            so['Net Qty'] = net_qty if net_qty > 0 else 0
            
            required_qty = so['Net Qty'] # Use the newly calculated value
            
            if required_qty <= 0:
                continue 

            so_result = {
                'sales_order': so,
                'components': [],
                'bottleneck': None,
                'can_produce_qty': float('inf'),
                'shifts_required': 0
            }

            # 4. BOM Explosion and Material Calculation
            if part_number in boms_by_parent:
                for component in boms_by_parent[part_number]:
                    comp_part_num = component['Part Number']
                    qty_per_unit = component['Quantity'] * (1 + (component.get('Scrap %', 0) / 100))
                    
                    if qty_per_unit <= 0: continue

                    comp_inv = component_inventory.get(comp_part_num, {'approved': 0, 'pending_qc': 0, 'quarantine': 0})
                    open_po_qty = pos_by_part.get(comp_part_num, 0)
                    
                    # AVAILABILITY CALCULATION
                    available_qty = comp_inv['approved'] + open_po_qty

                    component_details = {
                        'part_number': comp_part_num,
                        'description': component['Description'],
                        'required_per_unit': qty_per_unit,
                        'total_required': required_qty * qty_per_unit,
                        'on_hand_approved': comp_inv['approved'],
                        'on_hand_pending_qc': comp_inv['pending_qc'],
                        'on_hand_quarantine': comp_inv['quarantine'],
                        'open_po_qty': open_po_qty,
                        'total_available': available_qty,
                        'shortfall': max(0, (required_qty * qty_per_unit) - available_qty)
                    }

                    so_result['components'].append(component_details)

                    # Determine max buildable quantity for this component
                    max_build_for_comp = available_qty / qty_per_unit
                    
                    if max_build_for_comp < so_result['can_produce_qty']:
                        so_result['can_produce_qty'] = max_build_for_comp
                        so_result['bottleneck'] = comp_part_num

            # If no BOM found, can't produce anything
            if not so_result['components']:
                so_result['can_produce_qty'] = 0
                so_result['bottleneck'] = "No BOM Found"

            # 5. Capacity Calculation
            # This is a placeholder for matching SO to a line. For now, we'll find any capacity.
            # A more advanced version would match the SO to a specific production line.
            if capacities:
                # Find a relevant capacity - for now, just take the first one found for stick packs
                # This logic can be greatly improved later.
                line_capacity = next(iter(capacities.values()), 0)
                if line_capacity > 0:
                    so_result['shifts_required'] = (required_qty / line_capacity) if line_capacity > 0 else 0

            mrp_results.append(so_result)
        
        print("MRP RUN: Calculation complete.")
        return mrp_results

# Singleton instance
mrp_service = MRPService()