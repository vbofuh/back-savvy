import re
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
from email.utils import parsedate_to_datetime

# ตั้งค่า logging
logger = logging.getLogger(__name__)

class ReceiptExtractor:
    """คลาสสำหรับแยกข้อมูลใบเสร็จจากอีเมลต่างๆ"""
    
    @staticmethod
    def extract_receipt_info(email_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """แยกข้อมูลใบเสร็จจากอีเมล"""
        if not email_data:
            return None
        
        # ข้อมูลพื้นฐาน (จะถูกแทนที่โดยข้อมูลจากผู้ให้บริการเฉพาะ)
        result = {
            "email_id": f"imap_{email_data['message_id']}",
            "email_subject": email_data["subject"],
            "email_from": email_data["from"],
            "email_date": email_data["date"],
            "receipt_date": email_data["date"],  # เริ่มต้นใช้วันที่อีเมลเป็นวันที่ใบเสร็จ
            "vendor_name": ReceiptExtractor.extract_vendor_name(email_data["from"]),
            "amount": 0.0,
            "currency": "THB",  # ค่าเริ่มต้นเป็นบาท
            "receipt_file_path": None  # จะเติมภายหลังเมื่อบันทึกไฟล์
        }
        
        # ตรวจสอบว่าเป็นอีเมลจากผู้ให้บริการใด
        if "apple.com" in email_data["from"].lower():
            logger.info("ตรวจพบว่าเป็นใบเสร็จจาก Apple")
            return ReceiptExtractor.extract_apple_receipt(email_data, result)
        elif "kplus" in email_data["from"].lower() or "kasikornbank" in email_data["from"].lower():
            logger.info("ตรวจพบว่าเป็นใบเสร็จจาก K Plus")
            return ReceiptExtractor.extract_kplus_receipt(email_data, result)
        elif "steam" in email_data["from"].lower() or "steampowered" in email_data["from"].lower():
            logger.info("ตรวจพบว่าเป็นใบเสร็จจาก Steam")
            return ReceiptExtractor.extract_steam_receipt(email_data, result)
        else:
            # พยายามตรวจจับรูปแบบทั่วไป
            logger.info(f"ไม่พบรูปแบบเฉพาะ ใช้การตรวจจับทั่วไป จาก: {result['vendor_name']}")
            result["amount"] = ReceiptExtractor.extract_amount_general(email_data["body"])
            return result if result["amount"] > 0 else None
    
    @staticmethod
    def extract_apple_receipt(email_data: Dict[str, Any], base_result: Dict[str, Any]) -> Dict[str, Any]:
        """แยกข้อมูลใบเสร็จจาก Apple"""
        result = base_result.copy()
        result["vendor_name"] = "Apple"
        
        body = email_data["body"]
        
        # พยายามหาวันที่ใบแจ้งหนี้ (INVOICE DATE)
        invoice_date_match = re.search(r'INVOICE DATE\s*(\d{1,2}\s+\w+\s+\d{4})', body)
        if invoice_date_match:
            date_str = invoice_date_match.group(1)
            try:
                # แปลงวันที่ในรูปแบบ '12 Feb 2025' เป็น datetime
                receipt_date = datetime.strptime(date_str, '%d %b %Y')
                result["receipt_date"] = receipt_date
            except Exception as e:
                logger.warning(f"ไม่สามารถแปลงวันที่ Apple: {date_str}, ข้อผิดพลาด: {str(e)}")
        
        # ลองค้นหาจำนวนเงินในรูปแบบของ Apple (เช่น ฿35.00)
        amount_patterns = [
            r'฿(\d+\.\d{2})',  # ฿35.00
            r'TOTAL\s*฿\s*(\d+\.\d{2})',  # TOTAL ฿35.00
            r'Total:\s*฿\s*(\d+\.\d{2})',  # Total: ฿35.00
            r'ค่าใช้จ่ายรวม\s*฿\s*(\d+\.\d{2})',  # ค่าใช้จ่ายรวม ฿35.00
            r'รวม\s*฿\s*(\d+\.\d{2})',  # รวม ฿35.00
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                try:
                    result["amount"] = float(match.group(1))
                    break
                except ValueError:
                    continue
        
        # ถ้ามี attachments ให้ใช้ไฟล์แรก
        if email_data["attachments"]:
            result["receipt_file_path"] = email_data["attachments"][0]["filename"]
        
        return result
    
    @staticmethod
    def extract_kplus_receipt(email_data: Dict[str, Any], base_result: Dict[str, Any]) -> Dict[str, Any]:
        """แยกข้อมูลใบเสร็จจาก K Plus"""
        result = base_result.copy()
        result["vendor_name"] = "K Plus (Kasikorn Bank)"
        
        body = email_data["body"]
        
        # พยายามหาวันที่ทำรายการ
        date_match = re.search(r'วันที่ทำรายการ:\s*(\d{2}/\d{2}/\d{4})', body)
        if not date_match:
            date_match = re.search(r'วันที่ทำรายการ.*?(\d{2}/\d{2}/\d{4})', body)
        
        if date_match:
            date_str = date_match.group(1)
            try:
                # แปลงวันที่ในรูปแบบ 'DD/MM/YYYY' เป็น datetime
                receipt_date = datetime.strptime(date_str, '%d/%m/%Y')
                result["receipt_date"] = receipt_date
            except Exception as e:
                logger.warning(f"ไม่สามารถแปลงวันที่ K Plus: {date_str}, ข้อผิดพลาด: {str(e)}")
        
        # ลองค้นหาเลขที่รายการ
        transaction_id_match = re.search(r'เลขที่รายการ:?\s*(\w+)', body)
        if transaction_id_match:
            result["transaction_id"] = transaction_id_match.group(1)
        
        # ลองค้นหาจำนวนเงิน
        amount_match = re.search(r'จำนวนเงิน\s*\(บาท\):\s*([\d,]+\.\d{2})', body)
        if not amount_match:
            amount_match = re.search(r'จำนวนเงิน\s*\(บาท\).*?([\d,]+\.\d{2})', body)
        
        if amount_match:
            try:
                amount_str = amount_match.group(1).replace(',', '')
                result["amount"] = float(amount_str)
            except ValueError as e:
                logger.warning(f"ไม่สามารถแปลงจำนวนเงิน K Plus: {amount_match.group(1)}, ข้อผิดพลาด: {str(e)}")
        
        # หาผู้รับเงิน/ร้านค้า
        payee_match = re.search(r'เพื่อเข้าบัญชีบริษัท:\s*(.+?)(?:\r|\n)', body)
        if payee_match:
            result["payee"] = payee_match.group(1).strip()
        
        return result
    
    @staticmethod
    def extract_steam_receipt(email_data: Dict[str, Any], base_result: Dict[str, Any]) -> Dict[str, Any]:
        """แยกข้อมูลใบเสร็จจาก Steam"""
        result = base_result.copy()
        result["vendor_name"] = "Steam"
        result["currency"] = "THB"  # ปรับเป็นบาท (THB) ตามใบเสร็จที่เห็น
        
        body = email_data["body"]
        
        # แยกชื่อเกม/สินค้า
        game_match = re.search(r'ขอขอบคุณสำหรับการสั่งซื้อล่าสุดของคุณสำหรับ\s*(.*?)(?:\n|$)', body)
        if game_match:
            result["product_name"] = game_match.group(1).strip()
        
        # พยายามหาวันที่ดำเนินการ (รูปแบบไทย)
        date_match = re.search(r'วันที่ดำเนินการ:\s*(\d{1,2}\s+\w+\.\s+\d{4}\s+@\s+[\d:]+[ap]m\s+\+\d+)', body)
        if date_match:
            date_str = date_match.group(1).strip()
            logger.info(f"พบวันที่จาก Steam: {date_str}")
            
            try:
                # แปลงเดือนภาษาไทยเป็นอังกฤษ
                thai_month_map = {
                    'ม.ค.': 'Jan', 'ก.พ.': 'Feb', 'มี.ค.': 'Mar', 'เม.ย.': 'Apr', 
                    'พ.ค.': 'May', 'มิ.ย.': 'Jun', 'ก.ค.': 'Jul', 'ส.ค.': 'Aug', 
                    'ก.ย.': 'Sep', 'ต.ค.': 'Oct', 'พ.ย.': 'Nov', 'ธ.ค.': 'Dec'
                }
                
                # แยกส่วนของวันที่
                date_parts = date_str.split('@')
                date_only = date_parts[0].strip()
                
                # แยกวัน เดือน ปี
                for thai_month, eng_month in thai_month_map.items():
                    if thai_month in date_only:
                        date_only = date_only.replace(thai_month, eng_month)
                        break
                
                # พยายามแปลงวันที่หลังจากเปลี่ยนเดือนเป็นภาษาอังกฤษ
                try:
                    from dateutil import parser
                    receipt_date = parser.parse(date_only)
                    result["receipt_date"] = receipt_date
                except:
                    # หากใช้ dateutil ไม่ได้ ให้ลองใช้ datetime
                    date_parts = date_only.split()
                    if len(date_parts) == 3:  # ['23', 'Jan', '2025']
                        day = int(date_parts[0])
                        month = date_parts[1]
                        year = int(date_parts[2])
                        receipt_date = datetime.strptime(f"{day} {month} {year}", "%d %b %Y")
                        result["receipt_date"] = receipt_date
                    
            except Exception as e:
                logger.warning(f"ไม่สามารถแปลงวันที่ Steam: {date_str}, ข้อผิดพลาด: {str(e)}")
        
        # ค้นหาจำนวนเงินทั้งหมด
        # รูปแบบ 1: ฿34.00
        amount_match = re.search(r'รวมทั้งหมด:\s*฿\s*([\d,]+\.\d{2})', body)
        if not amount_match:
            # รูปแบบ 2: รวมทั้งหมด: ฿34.00
            amount_match = re.search(r'รวมทั้งหมด:\s*฿([\d,]+\.\d{2})', body)
        if not amount_match:
            # รูปแบบ 3: เสร็จสมบูรณ์แล้ว และ ฿34.00
            amount_match = re.search(r'เสร็จสมบูรณ์แล้ว และ ฿([\d,]+\.\d{2})', body)
        
        if amount_match:
            try:
                amount_str = amount_match.group(1).replace(',', '')
                result["amount"] = float(amount_str)
            except ValueError as e:
                logger.warning(f"ไม่สามารถแปลงจำนวนเงิน Steam: {amount_match.group(1)}, ข้อผิดพลาด: {str(e)}")
        
        # ค้นหาหมายเลขใบกำกับสินค้า
        invoice_match = re.search(r'ใบกำกับสินค้า:\s*(\d+)', body)
        if invoice_match:
            result["invoice_number"] = invoice_match.group(1).strip()
        
        return result
    
    @staticmethod
    def extract_vendor_name(from_email: str) -> str:
        """แยกชื่อผู้ขายจากอีเมลผู้ส่ง"""
        if not from_email:
            return ""
        
        # ลองค้นหารูปแบบ "Name <email>"
        match = re.match(r'"?([^"<]+)"?\s*<', from_email)
        if match:
            return match.group(1).strip()
        
        # ถ้าไม่พบรูปแบบดังกล่าว ให้ใช้ส่วนก่อน @ ในอีเมล
        match = re.search(r'([^@<\s]+)@', from_email)
        if match:
            vendor_part = match.group(1).strip()
            # ปรับแต่งชื่อให้อ่านง่าย
            vendor_part = vendor_part.replace('.', ' ').title()
            return vendor_part
        
        # ถ้าไม่สามารถแยกได้ ให้ส่งคืนอีเมลเต็ม
        return from_email.strip()
    
    @staticmethod
    def extract_amount_general(body: str) -> float:
        """แยกจำนวนเงินจากเนื้อหาอีเมลแบบทั่วไป"""
        if not body:
            return 0.0
        
        # รูปแบบทั่วไป
        # บาท (THB)
        baht_patterns = [
            r'(?:total|amount|ยอดรวม|จำนวนเงิน|ราคา)(?:\s*:)?\s*฿\s*([\d,]+\.\d{2})',
            r'฿\s*([\d,]+\.\d{2})',
            r'(?:THB|บาท)\s*([\d,]+\.\d{2})',
            r'([\d,]+\.\d{2})\s*(?:THB|บาท)',
        ]
        
        # ดอลลาร์ (USD)
        usd_patterns = [
            r'(?:total|amount)(?:\s*:)?\s*\$\s*([\d,]+\.\d{2})',
            r'\$\s*([\d,]+\.\d{2})',
            r'(?:USD)\s*([\d,]+\.\d{2})',
            r'([\d,]+\.\d{2})\s*(?:USD)',
        ]
        
        # ลองค้นหาทุกรูปแบบ
        for pattern in baht_patterns + usd_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                try:
                    # ลบเครื่องหมายคอมม่า
                    amount_str = match.group(1).replace(',', '')
                    return float(amount_str)
                except ValueError:
                    continue
        
        # ถ้าไม่พบรูปแบบที่ระบุ ให้คืนค่า 0
        return 0.0