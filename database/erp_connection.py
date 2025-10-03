"""
Dedicated ERP Database Connection Service.
This is separate from the main application's database connection.
"""
import pyodbc
from config import Config

class ERPConnection:
    """Handles a single, persistent connection to the ERP database."""

    def __init__(self):
        self._connection_string = self._build_connection_string()
        self.connection = None
        try:
            self.connection = pyodbc.connect(self._connection_string, autocommit=True)
            print("✅ [ERP_DB] Connection successful.")
        except pyodbc.Error as e:
            print(f"❌ [ERP_DB] FATAL: Connection failed: {e}")

    def _build_connection_string(self):
        """Builds the ERP database connection string from .env config."""
        return (
            f"DRIVER={{{Config.ERP_DB_DRIVER}}};"
            f"SERVER={Config.ERP_DB_SERVER},{Config.ERP_DB_PORT};"
            f"DATABASE={Config.ERP_DB_NAME};"
            f"UID={Config.ERP_DB_USERNAME};"
            f"PWD={Config.ERP_DB_PASSWORD};"
            f"TrustServerCertificate=yes;"
            f"Connection Timeout={Config.ERP_DB_TIMEOUT};"
        )

    def execute_query(self, sql, params=None):
        """Executes a SQL query and returns results as a list of dicts."""
        if not self.connection:
            print("❌ [ERP_DB] Cannot execute query, no active connection.")
            return []
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql, params or [])
            if cursor.description:
                columns = [column[0] for column in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                cursor.close()
                return results
            cursor.close()
            return []
        except pyodbc.Error as e:
            print(f"❌ [ERP_DB] Query Failed: {e}")
            import traceback
            traceback.print_exc()
            return []
        except Exception as e:
            print(f"❌ [ERP_DB] Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return []
            
_erp_db_instance = None

def get_erp_db():
    """Gets the global singleton instance of the ERP connection."""
    global _erp_db_instance
    if _erp_db_instance is None:
        _erp_db_instance = ERPConnection()
    return _erp_db_instance
    
class ErpService:
    """Contains all business logic for querying the ERP database."""
    
    def get_open_jobs_by_line(self, facility, line):
        db = get_erp_db()
        sql = """
            SELECT DISTINCT
                j.jo_jobnum AS JobNumber,
                CASE j.jo_waid
                    WHEN 1 THEN 'IRWINDALE'
                    WHEN 2 THEN 'DUARTE'
                    WHEN 3 THEN 'AREA_3'
                    ELSE 'UNKNOWN'
                END AS Facility,
                ISNULL(p.pr_codenum, 'UNKNOWN') AS PartNumber,
                ISNULL(p.pr_descrip, 'UNKNOWN') AS PartDescription,
                ISNULL(p1.p1_name, 'N/A') AS Customer,
                CASE 
                    WHEN ca.ca_name = 'Stick Pack' THEN 'SP'
                    ELSE 'BPS'
                END AS s_BU,
                ISNULL(line.d3_value, 'N/A') AS ProductionLine,
                CASE 
                    WHEN jl.lj_ordnum IS NOT NULL AND jl.lj_ordnum != 0 
                        THEN CONVERT(VARCHAR, jl.lj_ordnum)
                    WHEN wip_so.d2_value IS NOT NULL AND wip_so.d2_value != '' AND wip_so.d2_value != '0'
                        THEN wip_so.d2_value
                    ELSE ''
                END AS SalesOrder
            FROM dtjob j
            LEFT JOIN dtljob jl ON j.jo_jobnum = jl.lj_jobnum
            LEFT JOIN dmprod p ON jl.lj_prid = p.pr_id
            LEFT JOIN dmpr1 p1 ON p.pr_user5 = p1.p1_id
            LEFT JOIN dmcats ca ON p.pr_caid = ca.ca_id
            LEFT JOIN dtd2 line_link ON j.jo_jobnum = line_link.d2_recid AND line_link.d2_d1id = 5
            LEFT JOIN dmd3 line ON line_link.d2_value = line.d3_id AND line.d3_d1id = 5
            LEFT JOIN dtd2 wip_so ON j.jo_jobnum = wip_so.d2_recid AND wip_so.d2_d1id = 31
            WHERE j.jo_closed IS NULL
              AND j.jo_type = 'a'
              AND UPPER(TRIM(line.d3_value)) = UPPER(?)
              AND UPPER(CASE j.jo_waid
                    WHEN 1 THEN 'IRWINDALE'
                    WHEN 2 THEN 'DUARTE'
                    WHEN 3 THEN 'AREA_3'
                    ELSE 'UNKNOWN'
                  END) = UPPER(?)
            ORDER BY j.jo_jobnum ASC;
        """
        return db.execute_query(sql, (line, facility))

    def get_on_hand_inventory(self):
        """
        Executes a query to get the total on-hand quantity for all 'T%' parts.
        """
        db = get_erp_db()
        sql = """
            SELECT
                p.pr_codenum AS PartNumber,
                SUM(f.fi_balance) AS TotalOnHand
            FROM dtfifo f
            JOIN dmprod p ON f.fi_prid = p.pr_id
            JOIN dmware w ON f.fi_waid = w.wa_id
            WHERE
                f.fi_balance > 0
                AND p.pr_codenum LIKE 'T%'
                AND w.wa_name IN ('DUARTE', 'IRWINDALE')
            GROUP BY
                p.pr_codenum;
        """
        return db.execute_query(sql)

    def get_open_order_schedule(self):
        """Executes the full query to get all open order data for scheduling."""
        db = get_erp_db()
        sql = """
            WITH LatestOrderStatus AS (
                SELECT 
                    to_ordnum, to_billpo, to_ordtype, to_shipped, to_id, to_wanted, to_promise,
                    to_orddate, to_dueship, to_s1id, to_biid, to_notes, to_waid,
                    ROW_NUMBER() OVER (PARTITION BY to_ordnum ORDER BY to_id DESC) as rn
                FROM dttord
                WHERE to_ordtype IN ('s', 'h', 'd', 'm', 'l')
            ),
            OpenOrders AS (
                SELECT 
                    to_ordnum, to_billpo, to_ordtype, to_id as latest_to_id, to_wanted, to_promise,
                    to_orddate, to_dueship, to_s1id, to_biid, to_notes, to_waid
                FROM LatestOrderStatus
                WHERE rn = 1 AND to_ordtype IN ('s', 'h', 'm', 'l') AND to_shipped IS NULL
            ),
            PrimarySalesRep AS (
                SELECT 
                    s2_recid, s2_table,
                    CASE 
                        WHEN COUNT(CASE WHEN sm.sm_lname != 'HOUSE ACCOUNT' THEN 1 END) > 0 
                        THEN MAX(CASE WHEN sm.sm_lname != 'HOUSE ACCOUNT' THEN sm.sm_lname END)
                        ELSE MAX(sm.sm_lname)
                    END as primary_rep
                FROM dmsman2 s2
                INNER JOIN dmsman sm ON s2.s2_smid = sm.sm_id
                WHERE s2_table = 'dmbill'
                GROUP BY s2_recid, s2_table
            ),
            RiskData AS (
                SELECT 
                    d2_recid as to_id,
                    MAX(CASE WHEN d1_field = 'u_No_Risk' THEN d2_value END) AS no_risk_value,
                    MAX(CASE WHEN d1_field = 'u_Low_Risk' THEN d2_value END) AS low_risk_value,
                    MAX(CASE WHEN d1_field = 'u_High_Risk' THEN d2_value END) AS high_risk_value,
                    MAX(CASE WHEN d1_field = 'u_Schedule_Note' THEN d2_value END) AS schedule_note_value
                FROM dtd2
                INNER JOIN dmd1 ON dtd2.d2_d1id = dmd1.d1_id
                WHERE dmd1.d1_table = 'dttord'
                AND dmd1.d1_field IN ('u_No_Risk', 'u_Low_Risk', 'u_High_Risk', 'u_Schedule_Note')
                GROUP BY d2_recid
            ),
            AggregatedOrderData AS (
                SELECT
                    oo.to_ordnum, oo.to_billpo, oo.to_ordtype, oo.to_wanted, oo.to_promise, oo.to_orddate,
                    oo.to_dueship, oo.to_s1id, oo.to_biid, oo.to_notes, oo.latest_to_id, oo.to_waid,
                    p.pr_codenum, p.pr_descrip, p.pr_user5, p.pr_caid, p.pr_unid, p.pr_user3, p.pr_id, o.or_price,
                    SUM(o.or_quant) as total_current_qty,
                    CASE
                        WHEN oo.to_ordnum % 100 = 0 THEN SUM(o.or_quant)
                        ELSE
                            COALESCE(
                                (SELECT TOP 1 orig_o.or_quant
                                FROM dtord orig_o
                                INNER JOIN dmprod orig_p ON orig_o.or_prid = orig_p.pr_id
                                INNER JOIN dttord orig_t ON orig_o.or_ordnum = orig_t.to_ordnum AND orig_o.or_toid = orig_t.to_id
                                WHERE orig_o.or_ordnum = (oo.to_ordnum - (oo.to_ordnum % 100))
                                AND orig_p.pr_codenum = p.pr_codenum
                                ORDER BY orig_t.to_id DESC),
                                SUM(o.or_quant))
                    END AS total_original_qty,
                    ROW_NUMBER() OVER (PARTITION BY oo.to_ordnum ORDER BY p.pr_codenum, o.or_price DESC) as line_sequence
                FROM OpenOrders oo
                INNER JOIN dtord o ON oo.to_ordnum = o.or_ordnum AND o.or_toid = oo.latest_to_id
                INNER JOIN dmprod p ON o.or_prid = p.pr_id
                WHERE p.pr_codenum LIKE 'T%'
                GROUP BY oo.to_ordnum, oo.to_billpo, oo.to_ordtype, oo.to_wanted, oo.to_promise, oo.to_orddate, oo.to_dueship,
                         oo.to_s1id, oo.to_biid, oo.to_notes, oo.latest_to_id, oo.to_waid, p.pr_codenum, p.pr_descrip,
                         p.pr_user5, p.pr_caid, p.pr_unid, p.pr_user3, p.pr_id, o.or_price
            ),
            ProducedQuantities AS (
                SELECT 
                    lj.lj_ordnum as SalesOrder,
                    p.pr_codenum as PartNumber,
                    SUM(COALESCE(j4.j4_quant, 0)) as TotalProducedQty
                FROM dtjob j
                INNER JOIN dtljob lj ON j.jo_jobnum = lj.lj_jobnum
                INNER JOIN dmprod p ON lj.lj_prid = p.pr_id
                LEFT JOIN dtjob4 j4 ON j.jo_jobnum = j4.j4_jobnum AND lj.lj_id = j4.j4_ljid
                WHERE p.pr_codenum LIKE 'T%'
                GROUP BY lj.lj_ordnum, p.pr_codenum
            ),
            TotalShippedQuantities AS (
                SELECT 
                    FLOOR(ord.to_ordnum / 100) * 100 AS original_so_num,
                    prod.pr_codenum,
                    SUM(det.or_shipquant) AS total_shipped
                FROM dttord ord
                INNER JOIN dtord det ON ord.to_id = det.or_toid
                INNER JOIN dmprod prod ON det.or_prid = prod.pr_id
                WHERE ord.to_shipped IS NOT NULL 
                AND ord.to_status = 'c'
                AND ord.to_ordtype IN ('s', 'm')
                GROUP BY FLOOR(ord.to_ordnum / 100) * 100, prod.pr_codenum
            )
            SELECT
                aod.latest_to_id,
                COALESCE(wa.wa_name, 'N/A') AS [Facility],
                CASE WHEN ca.ca_name = 'Stick Pack' THEN 'SP' ELSE 'BPS' END AS [BU],
                aod.to_ordnum AS [SO],
                aod.to_billpo AS [Bill to PO],
                CASE
                    WHEN aod.to_ordtype = 's' THEN 'Sales Order'
                    WHEN aod.to_ordtype = 'h' THEN 'Credit Hold'
                    WHEN aod.to_ordtype = 'm' THEN 'ICT Order'
                    WHEN aod.to_ordtype = 'l' THEN 'On Hold Order'
                    ELSE 'Other'
                END AS [SO Type],
                aod.pr_codenum AS [Part],
                COALESCE(p1.p1_name, 'N/A') AS [Customer Name],
                aod.pr_descrip AS [Description],
                aod.total_original_qty AS [Ord Qty - (00) Level],
                COALESCE(tsq.total_shipped, 0) AS [Total Shipped Qty],
                aod.total_current_qty AS [Ord Qty - Cur. Level],
                COALESCE(pq.TotalProducedQty, 0) AS [Produced Qty],
                
                CASE
                    WHEN (aod.total_original_qty - COALESCE(pq.TotalProducedQty, 0)) < 0 THEN 0
                    ELSE (aod.total_original_qty - COALESCE(pq.TotalProducedQty, 0))
                END AS [Net Qty],
                
                CASE 
                    WHEN aod.line_sequence = 1 AND rd.no_risk_value IS NOT NULL AND ISNUMERIC(rd.no_risk_value) = 1 
                    THEN CAST(rd.no_risk_value AS NUMERIC(18,2))
                    ELSE 0
                END AS [Can Make - No Risk],
                CASE 
                    WHEN aod.line_sequence = 1 AND rd.low_risk_value IS NOT NULL AND ISNUMERIC(rd.low_risk_value) = 1 
                    THEN CAST(rd.low_risk_value AS NUMERIC(18,2))
                    ELSE 0
                END AS [Low Risk],
                CASE 
                    WHEN aod.line_sequence = 1 AND rd.high_risk_value IS NOT NULL AND ISNUMERIC(rd.high_risk_value) = 1 
                    THEN CAST(rd.high_risk_value AS NUMERIC(18,2))
                    ELSE 0
                END AS [High Risk],
                COALESCE(un.un_name, 'N/A') AS [UoM],
                COALESCE(aod.pr_user3, '') AS [Qty Per UoM],
                CASE 
                    WHEN ISNUMERIC(aod.pr_user3) = 1 AND aod.pr_user3 <> '' 
                    THEN aod.total_current_qty * CAST(aod.pr_user3 AS NUMERIC(18,2))
                    ELSE aod.total_current_qty
                END AS [Ext Qty (Current x per UoM)],
                aod.or_price AS [Unit Price],
                aod.total_current_qty * aod.or_price AS [Ext $ (Current x Price)],
                (aod.total_original_qty - COALESCE(pq.TotalProducedQty, 0)) * aod.or_price AS [Ext $ (Net Qty x Price)],
                CASE 
                    WHEN aod.line_sequence = 1 AND rd.no_risk_value IS NOT NULL AND ISNUMERIC(rd.no_risk_value) = 1 
                    THEN CAST(rd.no_risk_value AS NUMERIC(18,2)) * aod.or_price
                    ELSE 0
                END AS [$ Can Make - No Risk],
                CASE 
                    WHEN aod.line_sequence = 1 AND rd.low_risk_value IS NOT NULL AND ISNUMERIC(rd.low_risk_value) = 1 
                    THEN CAST(rd.low_risk_value AS NUMERIC(18,2)) * aod.or_price
                    ELSE 0
                END AS [$ Low Risk],
                CASE 
                    WHEN aod.line_sequence = 1 AND rd.high_risk_value IS NOT NULL AND ISNUMERIC(rd.high_risk_value) = 1 
                    THEN CAST(rd.high_risk_value AS NUMERIC(18,2)) * aod.or_price
                    ELSE 0
                END AS [$ High Risk],
                CONVERT(VARCHAR, aod.to_dueship, 101) AS [Due to Ship],
                CONVERT(VARCHAR, aod.to_wanted, 101) AS [Requested Date],
                CONVERT(VARCHAR, aod.to_promise, 101) AS [Comp Arrived Date],
                CONVERT(VARCHAR, aod.to_orddate, 101) AS [Ordered Date],
                COALESCE(psr.primary_rep, sm_order.sm_lname, 'N/A') AS [Sales Rep],
                COALESCE(rd.schedule_note_value, '') AS [Schedule Note]
            FROM AggregatedOrderData aod
            LEFT JOIN dmpr1 p1 ON aod.pr_user5 = p1.p1_id
            LEFT JOIN dmcats ca ON aod.pr_caid = ca.ca_id
            LEFT JOIN dmunit un ON aod.pr_unid = un.un_id
            LEFT JOIN dmware wa ON aod.to_waid = wa.wa_id
            LEFT JOIN dmsman sm_order ON aod.to_s1id = sm_order.sm_id
            LEFT JOIN PrimarySalesRep psr ON aod.to_biid = psr.s2_recid AND psr.s2_table = 'dmbill'
            LEFT JOIN RiskData rd ON aod.latest_to_id = rd.to_id
            LEFT JOIN ProducedQuantities pq ON CAST(aod.to_ordnum AS VARCHAR) = pq.SalesOrder AND aod.pr_codenum = pq.PartNumber
            LEFT JOIN TotalShippedQuantities tsq ON (FLOOR(aod.to_ordnum / 100) * 100) = tsq.original_so_num AND aod.pr_codenum = tsq.pr_codenum
            ORDER BY aod.to_ordnum DESC, aod.pr_codenum;
        """
        return db.execute_query(sql)

_erp_service_instance = None
def get_erp_service():
    global _erp_service_instance
    if _erp_service_instance is None:
        _erp_service_instance = ErpService()
    return _erp_service_instance