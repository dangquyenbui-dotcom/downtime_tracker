"""
MRP (Material Requirements Planning) Service
This service contains the core logic for calculating production suggestions.
"""

from .erp_connection import get_erp_service
from .capacity import ProductionCapacityDB
from datetime import datetime

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
        # 1. Fetch all necessary data in bulk
        print("MRP RUN: Fetching data...")
        sales_orders = self.erp.get_open_order_schedule()
        boms = self.erp.get_bom_data()
        purchase_orders = self.erp.get_purchase_order_data()
        component_inventory = self.get_component_inventory()
        finished_good_inventory_data = self.erp.get_on_hand_inventory()
        capacities = {c['line_id']: c['capacity_per_shift'] for c in capacity_db.get_all()}

        # 2. Pre-process and create lookups
        fg_inventory_map = {item['PartNumber']: item['TotalOnHand'] for item in finished_good_inventory_data}
        
        boms_by_parent = {}
        for item in boms:
            parent = item['Parent Part Number']
            if parent not in boms_by_parent:
                boms_by_parent[parent] = []
            boms_by_parent[parent].append(item)

        pos_by_part = {}
        for po in purchase_orders:
            part = po['Part Number']
            open_qty = po.get('OpenPOQuantity', 0)
            if open_qty > 0:
                if part not in pos_by_part:
                    pos_by_part[part] = 0
                pos_by_part[part] += open_qty

        # 3. First, calculate Net Qty for all SOs
        for so in sales_orders:
            part_number = so['Part']
            on_hand_qty = fg_inventory_map.get(part_number, 0)
            ord_qty_curr_level = so.get('Ord Qty - Cur. Level', 0)
            net_qty = ord_qty_curr_level - on_hand_qty
            so['Net Qty'] = net_qty if net_qty > 0 else 0
            so['On Hand Qty'] = on_hand_qty

        # Enhance component demand tracking
        component_demand = {}
        for so in sales_orders:
            if so.get('Net Qty', 0) > 0:
                part_number = so['Part']
                if part_number in boms_by_parent:
                    for component in boms_by_parent[part_number]:
                        comp_part_num = component['Part Number']
                        qty_per_unit = component['Quantity'] * (1 + (component.get('Scrap %', 0) / 100))
                        required_for_so = so['Net Qty'] * qty_per_unit

                        if comp_part_num not in component_demand:
                            component_demand[comp_part_num] = []
                        component_demand[comp_part_num].append({
                            'so': so['SO'],
                            'required': required_for_so
                        })

        # 5. Sort Sales Orders by "Due to Ship" date
        max_date = datetime.max.date()
        def get_sort_date(so):
            due_date_str = so.get('Due to Ship')
            if due_date_str:
                try:
                    return datetime.strptime(due_date_str, '%m/%d/%Y').date()
                except (ValueError, TypeError):
                    return max_date
            return max_date
        sales_orders.sort(key=get_sort_date)

        # 6. Initialize a mutable "live" inventory (for approved stock only)
        live_component_inventory = {
            part: data.get('approved', 0) for part, data in component_inventory.items()
        }
        
        # Log allocations for tooltip
        allocation_log = {}

        print(f"MRP RUN: Sorted {len(sales_orders)} SO lines. Starting allocation...")

        # 7. Process each sales order sequentially
        mrp_results = []
        for so in sales_orders:
            net_production_qty = so['Net Qty']
            gross_order_qty = so.get('Ord Qty - Cur. Level', 0)
            part_number = so['Part']
            
            final_can_produce_qty = float('inf')
            bottleneck = None
            bom_components = boms_by_parent.get(part_number, [])

            # --- PASS 1: DISCOVERY ---
            if net_production_qty > 0 and bom_components:
                for component in bom_components:
                    comp_part_num = component['Part Number']
                    qty_per_unit = component['Quantity'] * (1 + (component.get('Scrap %', 0) / 100))
                    if qty_per_unit <= 0: continue

                    initial_inv = component_inventory.get(comp_part_num, {'approved': 0, 'pending_qc': 0})
                    inventory_before_this_so = live_component_inventory.get(comp_part_num, 0)
                    pending_qc_qty = initial_inv.get('pending_qc', 0)
                    open_po_qty = pos_by_part.get(comp_part_num, 0)
                    
                    available_for_allocation = inventory_before_this_so + pending_qc_qty + open_po_qty
                    max_build_for_comp = available_for_allocation / qty_per_unit

                    if max_build_for_comp < final_can_produce_qty:
                        final_can_produce_qty = max_build_for_comp
                        bottleneck = comp_part_num
            elif not bom_components and net_production_qty > 0:
                final_can_produce_qty = 0
                bottleneck = "No BOM Found"

            if final_can_produce_qty == float('inf'):
                final_can_produce_qty = gross_order_qty

            so_result = {
                'sales_order': so,
                'components': [],
                'bottleneck': bottleneck,
                'can_produce_qty': final_can_produce_qty,
                'shifts_required': 0
            }

            # --- PASS 2: ALLOCATION ---
            if bom_components:
                for component in bom_components:
                    comp_part_num = component['Part Number']
                    qty_per_unit = component['Quantity'] * (1 + (component.get('Scrap %', 0) / 100))
                    if qty_per_unit <= 0: continue
                    
                    initial_inv = component_inventory.get(comp_part_num, {'approved': 0, 'pending_qc': 0})
                    pending_qc_qty = initial_inv.get('pending_qc', 0)
                    open_po_qty = pos_by_part.get(comp_part_num, 0)
                    
                    inventory_before_this_so = live_component_inventory.get(comp_part_num, 0)
                    available_for_allocation = inventory_before_this_so + pending_qc_qty + open_po_qty

                    required_for_constrained_build = final_can_produce_qty * qty_per_unit
                    
                    if net_production_qty > 0:
                        allocated_for_this_so = min(inventory_before_this_so, required_for_constrained_build)
                        
                        # --- BUG FIX: Safely update live inventory ---
                        live_component_inventory[comp_part_num] = inventory_before_this_so - allocated_for_this_so

                        if comp_part_num not in allocation_log:
                            allocation_log[comp_part_num] = []
                        if allocated_for_this_so > 0:
                            allocation_log[comp_part_num].append({
                                'so': so['SO'],
                                'allocated': allocated_for_this_so
                            })
                    else:
                        allocated_for_this_so = 0

                    total_original_need = net_production_qty * qty_per_unit
                    shortfall = max(0, total_original_need - available_for_allocation)
                    
                    shared_with_so_details = []
                    total_allocated_to_others = 0
                    if comp_part_num in allocation_log:
                        for allocation in allocation_log[comp_part_num]:
                            if allocation['so'] != so['SO']:
                                total_allocated_to_others += allocation['allocated']
                        for allocation in allocation_log[comp_part_num]:
                            if allocation['so'] != so['SO']:
                                shared_with_so_details.append(f"  - SO {allocation['so']}: {allocation['allocated']:,.2f}")
                        if total_allocated_to_others > 0:
                            total_string = f"Total Allocated to Others: {total_allocated_to_others:,.2f}"
                            shared_with_so_details.insert(0, total_string)

                    component_details = {
                        'part_number': comp_part_num,
                        'description': component['Description'],
                        'shared_with_so': shared_with_so_details,
                        'total_required': gross_order_qty * qty_per_unit,
                        'on_hand_initial': initial_inv['approved'],
                        'on_hand_pending_qc': initial_inv['pending_qc'],
                        'inventory_before_this_so': inventory_before_this_so,
                        'allocated_for_this_so': allocated_for_this_so,
                        'open_po_qty': open_po_qty,
                        'total_available_for_so': available_for_allocation,
                        'shortfall': shortfall
                    }
                    so_result['components'].append(component_details)

            if capacities:
                line_capacity = next(iter(capacities.values()), 0)
                if line_capacity > 0:
                    so_result['shifts_required'] = (net_production_qty / line_capacity) if line_capacity > 0 else 0

            mrp_results.append(so_result)

        mrp_results.sort(key=lambda r: r['sales_order']['SO'])
        
        print("MRP RUN: Calculation complete.")
        return mrp_results

# Singleton instance
mrp_service = MRPService()