# dangquyenbui-dotcom/production_portal_dev/production_portal_DEV-35c5b2d7d65c0b0de1b2129d9ecd46a5ad103507/database/mrp_service.py
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
        fg_inventory_map = {
            item['PartNumber'].strip(): {
                'approved': item.get('on_hand_approved', 0),
                'pending_qc': item.get('on_hand_pending_qc', 0),
                'total': item.get('TotalOnHand', 0)
            } for item in finished_good_inventory_data
        }
        
        boms_by_parent = {}
        for item in boms:
            parent = item['Parent Part Number'].strip()
            if parent not in boms_by_parent:
                boms_by_parent[parent] = []
            boms_by_parent[parent].append(item)

        pos_by_part = {}
        for po in purchase_orders:
            part = po['Part Number'].strip()
            open_qty = po.get('OpenPOQuantity', 0)
            if open_qty > 0:
                if part not in pos_by_part:
                    pos_by_part[part] = 0
                pos_by_part[part] += open_qty

        # 3. Initialize mutable "live" inventories for sequential allocation
        live_fg_approved = {part.strip(): data.get('approved', 0) for part, data in fg_inventory_map.items()}
        live_fg_qc = {part.strip(): data.get('pending_qc', 0) for part, data in fg_inventory_map.items()}

        # 4. Sort Sales Orders by "Due to Ship" date to process them in priority order
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

        # 5. Initialize component inventory and allocation log
        live_component_inventory = {
            part.strip(): data.get('approved', 0) for part, data in component_inventory.items()
        }
        allocation_log = {}

        print(f"MRP RUN: Sorted {len(sales_orders)} SO lines. Starting allocation...")

        # 6. Process each sales order sequentially
        mrp_results = []
        for so in sales_orders:
            part_number = so['Part'].strip()
            ord_qty_curr_level = so.get('Ord Qty - Cur. Level', 0)

            fg_inv_static = fg_inventory_map.get(part_number, {'approved': 0, 'pending_qc': 0})
            so['On Hand Qty Approved'] = fg_inv_static.get('approved', 0)
            so['On Hand Qty Pending QC'] = fg_inv_static.get('pending_qc', 0)
            
            needed = ord_qty_curr_level
            
            # Step 1: Fulfill from available APPROVED stock
            available_approved = live_fg_approved.get(part_number, 0)
            fulfilled_from_approved = min(needed, available_approved)
            
            if part_number in live_fg_approved:
                live_fg_approved[part_number] -= fulfilled_from_approved
            
            needed -= fulfilled_from_approved

            # Set Net Qty for all cases so the frontend filter works correctly.
            so['Net Qty'] = needed if needed > 0 else 0

            if needed <= 0:
                mrp_results.append({'sales_order': so, 'components': [], 'bottleneck': 'None', 'can_produce_qty': ord_qty_curr_level, 'status': 'ready-to-ship', 'shifts_required': 0})
                continue

            # Step 2: Check if remainder can be covered by PENDING QC stock
            available_qc = live_fg_qc.get(part_number, 0)
            if needed <= available_qc:
                if part_number in live_fg_qc:
                    live_fg_qc[part_number] -= needed
                
                status = 'pending-qc'
                bottleneck_text = f"Pending QC (Approved: {fulfilled_from_approved:,.0f}, QC: {so['On Hand Qty Pending QC']:,.0f})"
                if fulfilled_from_approved > 0:
                    status = 'partial-ship-pending-qc'
                    bottleneck_text = f"Partial Ship (On-Hand: {fulfilled_from_approved:,.0f}) / QC Hold"

                mrp_results.append({'sales_order': so, 'components': [], 'bottleneck': bottleneck_text, 'can_produce_qty': fulfilled_from_approved, 'status': status, 'shifts_required': 0})
                continue

            # Step 3: If we reach here, production is required
            net_production_qty = needed
            
            final_can_produce_qty = float('inf')
            bottleneck = None
            bom_components = boms_by_parent.get(part_number, [])

            # --- PASS 1: DISCOVERY ---
            if bom_components:
                for component in bom_components:
                    comp_part_num = component['Part Number'].strip()
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
            elif not bom_components:
                final_can_produce_qty = 0
                bottleneck = "No BOM Found"
            
            if final_can_produce_qty == float('inf'):
                final_can_produce_qty = net_production_qty
            final_can_produce_qty = min(final_can_produce_qty, net_production_qty)

            # Determine production status
            prod_status = 'ok'
            if final_can_produce_qty < net_production_qty:
                prod_status = 'partial' if final_can_produce_qty > 0 else 'critical'
            
            component_details = []

            # --- PASS 2: ALLOCATION ---
            if bom_components:
                for component in bom_components:
                    comp_part_num = component['Part Number'].strip()
                    qty_per_unit = component['Quantity'] * (1 + (component.get('Scrap %', 0) / 100))
                    if qty_per_unit <= 0: continue
                    
                    initial_inv = component_inventory.get(comp_part_num, {'approved': 0, 'pending_qc': 0})
                    inventory_before_this_so = live_component_inventory.get(comp_part_num, 0)
                    open_po_qty = pos_by_part.get(comp_part_num, 0)

                    required_for_constrained_build = final_can_produce_qty * qty_per_unit
                    allocated_for_this_so = min(inventory_before_this_so, required_for_constrained_build)
                    if comp_part_num in live_component_inventory:
                        live_component_inventory[comp_part_num] -= allocated_for_this_so

                    if comp_part_num not in allocation_log:
                        allocation_log[comp_part_num] = []
                    if allocated_for_this_so > 0:
                        allocation_log[comp_part_num].append({ 'so': so['SO'], 'allocated': allocated_for_this_so })

                    total_original_need = net_production_qty * qty_per_unit
                    available_for_allocation = inventory_before_this_so + initial_inv.get('pending_qc', 0) + open_po_qty
                    shortfall = max(0, total_original_need - available_for_allocation)
                    
                    shared_with_so_details = []
                    total_allocated_to_others = 0
                    if comp_part_num in allocation_log:
                        for allocation in allocation_log[comp_part_num]:
                            if allocation['so'] != so['SO']:
                                total_allocated_to_others += allocation['allocated']
                        if total_allocated_to_others > 0:
                            shared_with_so_details.insert(0, f"Total Allocated to Prior SOs: {total_allocated_to_others:,.2f}")
                            for allocation in allocation_log[comp_part_num]:
                                if allocation['so'] != so['SO']:
                                    shared_with_so_details.append(f"  - SO {allocation['so']}: {allocation['allocated']:,.2f}")

                    component_details.append({
                        'part_number': comp_part_num, 'description': component['Description'],
                        'shared_with_so': shared_with_so_details, 'total_required': ord_qty_curr_level * qty_per_unit,
                        'on_hand_initial': initial_inv['approved'], 'inventory_before_this_so': inventory_before_this_so,
                        'allocated_for_this_so': allocated_for_this_so, 'open_po_qty': open_po_qty,
                        'shortfall': shortfall
                    })
            
            so_result = {
                'sales_order': so, 'components': component_details, 'bottleneck': bottleneck,
                'can_produce_qty': fulfilled_from_approved + final_can_produce_qty,
                'shifts_required': 0, 'status': prod_status
            }

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