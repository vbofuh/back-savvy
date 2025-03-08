import imaplib
import email
import re
import logging
from email.header import decode_header
from email.utils import parsedate_to_datetime
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..models.imap_setting import ImapSetting
from ..services.encryption_service import decrypt_password

# ตั้งค่า logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IMAPClient:
    def __init__(self, imap_setting: ImapSetting):
        self.imap_setting = imap_setting
        self.connection = None

    def connect(self) -> bool:
        """เชื่อมต่อกับเซิร์ฟเวอร์ IMAP"""
        try:
            # ถอดรหัสรหัสผ่าน
            decrypted_password = decrypt_password(self.imap_setting.password_encrypted)
            
            # เชื่อมต่อกับเซิร์ฟเวอร์
            if self.imap_setting.use_ssl:
                self.connection = imaplib.IMAP4_SSL(self.imap_setting.server, self.imap_setting.port)
            else:
                self.connection = imaplib.IMAP4(self.imap_setting.server, self.imap_setting.port)
            
            # ล็อกอิน
            self.connection.login(self.imap_setting.username, decrypted_password)
            logger.info(f"เชื่อมต่อกับ IMAP สำเร็จ: {self.imap_setting.email}")
            return True

        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อกับ IMAP: {str(e)}")
            return False
            import traceback
            logger.error(f"รายละเอียดข้อผิดพลาด: {traceback.format_exc()}")
            return False

    def disconnect(self):
        """ยกเลิกการเชื่อมต่อ"""
        if self.connection:
            try:
                self.connection.logout()
            except:
                pass

    def search_emails(self, days: int = 30, limit: int = 50, search_criteria: str = None) -> List[int]:
        """ค้นหาอีเมลตามเงื่อนไข โดยสามารถระบุจำนวนวันย้อนหลังและจำนวนจำกัดได้"""
        try:
            # เลือกโฟลเดอร์
            self.connection.select(self.imap_setting.folder)
            
            # คำนวณวันที่ย้อนหลัง (ถ้ากำหนด days > 0)
            date_criteria = None
            if days > 0:
                from datetime import datetime, timedelta
                since_date = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
                date_criteria = f'SINCE "{since_date}"'
                logger.info(f"ค้นหาอีเมลตั้งแต่วันที่: {since_date}")
            
            # สร้างตัวแปรสำหรับเก็บ message IDs
            all_message_ids = []
            
            # ค้นหาแยกตามผู้ให้บริการและรวมผล
            sources = [
                # [ชื่อแหล่ง, เงื่อนไขการค้นหา]
                # ["Apple", '(FROM "apple.com" SUBJECT "invoice")'],
                ["Steam", '(FROM "steampowered.com")'],
                ["Steam Support", '(SUBJECT "Steam Support")'],
                ["Kasikornbank", '(FROM "kasikornbank.com")'],
                ["Spotify", '(FROM "spotify.com")'],
                ["Spotify Premium", '(FROM "spotify.com" SUBJECT "Premium")']
                
            ]
            
            for source_name, source_criteria in sources:
                # รวมเงื่อนไขวันที่ (ถ้ามี)
                if date_criteria:
                    combined_criteria = f'({source_criteria} {date_criteria})'
                else:
                    combined_criteria = source_criteria
                
                logger.info(f"ค้นหาอีเมลจาก {source_name} ด้วยเงื่อนไข: {combined_criteria}")
                status, data = self.connection.search(None, combined_criteria)
                
                if status == "OK" and data[0]:
                    ids = data[0].split()
                    all_message_ids.extend(ids)
                    logger.info(f"พบอีเมลจาก {source_name} {len(ids)} รายการ")
            
            # ตรวจสอบว่ามีข้อมูลหรือไม่
            if not all_message_ids:
                logger.warning("ไม่พบอีเมลที่ตรงกับเงื่อนไขทั้งหมด")
                return []
            
            # เรียงลำดับและตัดซ้ำ (เรียงจากใหม่ไปเก่า)
            unique_ids = sorted(set(all_message_ids), key=int, reverse=True)
            
            # จำกัดจำนวนตามที่กำหนด
            if limit > 0 and len(unique_ids) > limit:
                unique_ids = unique_ids[:limit]
                logger.info(f"จำกัดการประมวลผลเพียง {limit} ฉบับล่าสุด")
            
            logger.info(f"รวมพบอีเมลทั้งหมด {len(unique_ids)} รายการหลังจากตัดซ้ำและจำกัดจำนวน")
            return [int(id) for id in unique_ids]
        
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการค้นหาอีเมล: {str(e)}")
            import traceback
            logger.error(f"รายละเอียดข้อผิดพลาด: {traceback.format_exc()}")
            return []
    
    

    def get_email(self, message_id: int) -> Optional[Dict[str, Any]]:
        """ดึงข้อมูลอีเมล"""
        try:
            status, data = self.connection.fetch(str(message_id), "(RFC822)")
            if status != "OK":
                logger.error(f"เกิดข้อผิดพลาดในการดึงอีเมล {message_id}: {status}")
                return None

            msg = email.message_from_bytes(data[0][1])
            
            # แยกข้อมูลพื้นฐาน
            subject = self._decode_header(msg["Subject"]) if msg["Subject"] else ""
            from_email = self._decode_header(msg["From"]) if msg["From"] else ""
            date_str = msg["Date"] if msg["Date"] else ""
            date = self._parse_date(date_str)
            
            # ดึงเนื้อหาและไฟล์แนบ
            body = self._get_email_body(msg)
            attachments = self._get_attachments(msg)

            return {
                "message_id": message_id,
                "subject": subject,
                "from": from_email,
                "date": date,
                "body": body,
                "attachments": attachments
            }

        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการดึงอีเมล {message_id}: {str(e)}")
            return None

    def _decode_header(self, header: str) -> str:
        """ถอดรหัสหัวข้ออีเมล"""
        try:
            decoded_headers = decode_header(header)
            header_parts = []
            for decoded_text, charset in decoded_headers:
                if isinstance(decoded_text, bytes):
                    charset = charset or 'utf-8'
                    decoded_text = decoded_text.decode(charset, errors='replace')
                header_parts.append(decoded_text)
            return ''.join(header_parts)

        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการถอดรหัสหัวข้อ: {str(e)}")
            return header

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """แปลงสตริงวันที่เป็น datetime"""
        try:
            if not date_str:
                return None
            return parsedate_to_datetime(date_str)

        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการแปลงวันที่ {date_str}: {str(e)}")
            return None

    def _get_email_body(self, msg) -> str:
        """ดึงเนื้อหาข้อความ"""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                    
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                if "attachment" in content_disposition:
                    continue

                if content_type in ["text/plain", "text/html"]:
                    try:
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        body += payload.decode(charset, errors='replace')
                    except Exception as e:
                        logger.error(f"เกิดข้อผิดพลาดในการอ่านเนื้อหาอีเมล: {str(e)}")
        else:
            content_type = msg.get_content_type()
            if content_type in ["text/plain", "text/html"]:
                try:
                    payload = msg.get_payload(decode=True)
                    charset = msg.get_content_charset() or 'utf-8'
                    body = payload.decode(charset, errors='replace')
                except Exception as e:
                    logger.error(f"เกิดข้อผิดพลาดในการอ่านเนื้อหาอีเมล: {str(e)}")

        return body

    def _get_attachments(self, msg) -> List[Dict[str, Any]]:
        """ดึงไฟล์แนบ"""
        attachments = []
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue

            filename = part.get_filename()
            if not filename:
                continue

            filename = self._decode_header(filename)
            content_type = part.get_content_type()

            if (content_type.startswith('image/') or 
                content_type == 'application/pdf' or 
                filename.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png'))):

                attachments.append({
                    "filename": filename,
                    "content_type": content_type,
                    "content": part.get_payload(decode=True)
                })

        return attachments


def extract_receipt_info(email_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """แยกข้อมูลใบเสร็จจากอีเมล"""
    if not email_data:
        return None

    # ข้อมูลพื้นฐาน
    result = {
        "email_id": f"imap_{email_data['message_id']}",
        "email_subject": email_data["subject"],
        "email_from": email_data["from"],
        "email_date": email_data["date"],
        "receipt_date": email_data["date"],
        "vendor_name": extract_vendor_name(email_data["from"]),
        "amount": 0.0,
        "currency": "THB",  # ค่าเริ่มต้น
        "receipt_file_path": None
    }

    # ตรวจสอบว่าเป็นอีเมลจากผู้ให้บริการใด
    from_email = email_data["from"].lower()
    
    if "apple.com" in from_email:
        # ใบเสร็จ Apple
        logger.info("ตรวจพบว่าเป็นใบเสร็จจาก Apple")
        result["vendor_name"] = "Apple"
        result["amount"] = extract_amount(email_data["body"])
        
        # ค้นหาวันที่ใบแจ้งหนี้
        invoice_date_match = re.search(r'INVOICE DATE\s*(\d{1,2}\s+\w+\s+\d{4})', email_data["body"])
        if invoice_date_match:
            date_str = invoice_date_match.group(1)
            try:
                receipt_date = datetime.strptime(date_str, '%d %b %Y')
                result["receipt_date"] = receipt_date
            except:
                pass
    
    if "kplus" in from_email or "kasikornbank" in from_email:
        # ใบเสร็จ K Plus
        logger.info("ตรวจพบว่าเป็นใบเสร็จจาก K Plus")
        result["vendor_name"] = "K Plus (Kasikorn Bank)"
        
        body = email_data["body"]
        
        # ค้นหาจำนวนเงิน
        amount_match = re.search(r'จำนวนเงิน\s*\(บาท\):\s*([\d,]+\.\d{2})', body)
        if amount_match:
            try:
                amount_str = amount_match.group(1).replace(',', '')
                result["amount"] = float(amount_str)
            except ValueError:
                pass
        
        # ค้นหาวันที่ทำรายการ
        date_match = re.search(r'วันที่ทำรายการ:\s*(\d{2}/\d{2}/\d{4})', body)
        if date_match:
            date_str = date_match.group(1)
            try:
                receipt_date = datetime.strptime(date_str, '%d/%m/%Y')
                result["receipt_date"] = receipt_date
            except:
                pass
    
    elif "steam" in from_email or "steampowered" in from_email:
        # ใบเสร็จ Steam
        logger.info("ตรวจพบว่าเป็นใบเสร็จจาก Steam")
        result["vendor_name"] = "Steam"

        body = email_data["body"]
        
        # ค้นหาจำนวนเงิน
        logger.info(f"ตรวจพบว่าเป็นใบเสร็จจาก Steam: {email_data['subject']}")

        # บันทึกส่วนแรกของเนื้อหาเพื่อตรวจสอบรูปแบบ
        logger.info(f"ตัวอย่างเนื้อหา: {body[:500]}")

        # บันทึกผลการค้นหาแต่ละส่วน
        baht_match = re.search(r'(?:Total|รวม):\s*฿\s*([\d,]+\.\d{2})', body, re.IGNORECASE)
        logger.info(f"ผลการค้นหาจำนวนเงินแบบที่ 1: {baht_match}")

        if not baht_match:
            baht_match = re.search(r'฿\s*([\d,]+\.\d{2})', body, re.IGNORECASE)
            logger.info(f"ผลการค้นหาจำนวนเงินแบบที่ 2: {baht_match}")
        if baht_match:
            try:
                amount_str = baht_match.group(1).replace(',', '')
                result["amount"] = float(amount_str)
            except ValueError:
                pass
        
        # ค้นหาวันที่
        date_match = re.search(r'Date issued:\s*(.+?)\s*(?:\r|\n|<br>)', body)
        if date_match:
            date_str = date_match.group(1).strip()
            # ลองแปลงวันที่ในรูปแบบต่างๆ
            try:
                if '@' in date_str:  # รูปแบบ "23 Jan, 2021 @ 7:40pm"
                    date_only = date_str.split('@')[0].strip()
                    receipt_date = datetime.strptime(date_only, '%d %b, %Y')
                    result["receipt_date"] = receipt_date
            except:
                pass
    
    elif "spotify.com" in from_email:
        # ใบเสร็จ Spotify
        logger.info("ตรวจพบว่าเป็นใบเสร็จจาก Spotify")
        result["vendor_name"] = "Spotify"
        
        body = email_data["body"]
        logger.info(f"เนื้อหาอีเมล Spotify: {body[:1000]}")  # บันทึกเนื้อหาเพื่อการดีบัก
        
        # ค้นหาจำนวนเงินในหลายรูปแบบ
        amount = 0.0
        
        # รูปแบบที่ 1: รูปแบบทั้งหมด
        amount_match = re.search(r'ทั้งหมด\s*฿\s*([\d,]+\.\d{2})', body)
        if amount_match:
            try:
                amount_str = amount_match.group(1).replace(',', '')
                amount = float(amount_str)
                logger.info(f"พบจำนวนเงินรูปแบบที่ 1: {amount}")
            except ValueError:
                pass
        
        # รูปแบบที่ 2: รูปแบบ Premium
        if amount == 0:
            premium_match = re.search(r'Premium\s*฿\s*([\d,]+\.\d{2})', body)
            if premium_match:
                try:
                    amount_str = premium_match.group(1).replace(',', '')
                    amount = float(amount_str)
                    logger.info(f"พบจำนวนเงินรูปแบบที่ 2: {amount}")
                except ValueError:
                    pass
        
        # รูปแบบที่ 3: ค้นหาแบบทั่วไป
        if amount == 0:
            general_match = re.search(r'฿\s*([\d,]+\.\d{2})', body)
            if general_match:
                try:
                    amount_str = general_match.group(1).replace(',', '')
                    amount = float(amount_str)
                    logger.info(f"พบจำนวนเงินรูปแบบที่ 3: {amount}")
                except ValueError:
                    pass
        
        # รูปแบบที่ 4: ค้นหาตัวเลขที่ตามด้วย THB หรือ บาท
        if amount == 0:
            thb_match = re.search(r'([\d,]+\.\d{2})\s*(?:THB|บาท)', body)
            if thb_match:
                try:
                    amount_str = thb_match.group(1).replace(',', '')
                    amount = float(amount_str)
                    logger.info(f"พบจำนวนเงินรูปแบบที่ 4: {amount}")
                except ValueError:
                    pass
        
        # กำหนดค่าจำนวนเงินที่ค้นพบ
        result["amount"] = amount
        
        # ค้นหาวันที่ในหลายรูปแบบ
        # รูปแบบที่ 1: เดือนไทย วันที่ ปี
        date_match = re.search(r'(มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม)\s+(\d{1,2}),?\s+(\d{4})', body)
        if date_match:
            try:
                # แปลงเดือนภาษาไทยเป็นตัวเลข
                thai_month_map = {
                    'มกราคม': 1, 'กุมภาพันธ์': 2, 'มีนาคม': 3, 'เมษายน': 4,
                    'พฤษภาคม': 5, 'มิถุนายน': 6, 'กรกฎาคม': 7, 'สิงหาคม': 8,
                    'กันยายน': 9, 'ตุลาคม': 10, 'พฤศจิกายน': 11, 'ธันวาคม': 12
                }
                
                month_name = date_match.group(1)
                day = int(date_match.group(2))
                year = int(date_match.group(3))
                
                month_num = thai_month_map.get(month_name, 1)
                result["receipt_date"] = datetime(year, month_num, day)
                logger.info(f"พบวันที่รูปแบบที่ 1: {result['receipt_date']}")
            except (ValueError, KeyError) as e:
                logger.error(f"ข้อผิดพลาดในการแปลงวันที่: {str(e)}")
        
        # รูปแบบที่ 2: วันที่ เดือนไทย ปี
        if "receipt_date" not in result or result["receipt_date"] is None:
            date_match2 = re.search(r'(\d{1,2})\s+(มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม)\s+(\d{4})', body)
            if date_match2:
                try:
                    thai_month_map = {
                        'มกราคม': 1, 'กุมภาพันธ์': 2, 'มีนาคม': 3, 'เมษายน': 4,
                        'พฤษภาคม': 5, 'มิถุนายน': 6, 'กรกฎาคม': 7, 'สิงหาคม': 8,
                        'กันยายน': 9, 'ตุลาคม': 10, 'พฤศจิกายน': 11, 'ธันวาคม': 12
                    }
                    
                    day = int(date_match2.group(1))
                    month_name = date_match2.group(2)
                    year = int(date_match2.group(3))
                    
                    month_num = thai_month_map.get(month_name, 1)
                    result["receipt_date"] = datetime(year, month_num, day)
                    logger.info(f"พบวันที่รูปแบบที่ 2: {result['receipt_date']}")
                except (ValueError, KeyError) as e:
                    logger.error(f"ข้อผิดพลาดในการแปลงวันที่: {str(e)}")
        
        # ค้นหารหัสคำสั่งซื้อ
        order_id_match = re.search(r'รหัสคำสั่งซื้อ\s*:\s*(\d+)', body)
        if order_id_match:
            result["receipt_number"] = order_id_match.group(1)
            logger.info(f"พบรหัสคำสั่งซื้อ: {result['receipt_number']}")
        
        # ในกรณีที่ไม่พบรหัสคำสั่งซื้อในรูปแบบแรก ลองรูปแบบอื่น
        if "receipt_number" not in result or not result["receipt_number"]:
            alt_order_id_match = re.search(r'Order\s*#?:?\s*(\d+)', body, re.IGNORECASE)
            if alt_order_id_match:
                result["receipt_number"] = alt_order_id_match.group(1)
                logger.info(f"พบรหัสคำสั่งซื้อรูปแบบที่ 2: {result['receipt_number']}")
        
        # บันทึกข้อมูลที่แยกได้ทั้งหมด
        logger.info(f"ข้อมูลใบเสร็จ Spotify ที่สกัดได้: {result}")
    else:
        # กรณีทั่วไป
        logger.info(f"ไม่พบรูปแบบเฉพาะ ใช้การตรวจจับทั่วไป จาก: {result['vendor_name']}")
        result["amount"] = extract_amount(email_data["body"])

    # ตรวจสอบไฟล์แนบ
    if email_data["attachments"]:
        result["receipt_file_path"] = email_data["attachments"][0]["filename"]

    return result


def extract_vendor_name(from_email: str) -> str:
    """แยกชื่อผู้ขายจากอีเมลผู้ส่ง"""
    if not from_email:
        return ""

    match = re.match(r'"?([^"<]+)"?\s*<', from_email)
    if match:
        return match.group(1).strip()

    match = re.search(r'([^@<\s]+)@', from_email)
    if match:
        return match.group(1).strip()

    return from_email.strip()


def extract_amount(body: str) -> float:
    """แยกจำนวนเงินจากเนื้อหาอีเมล"""
    if not body:
        return 0.0

    amount_patterns = [
        r'฿(\d+\.\d{2})',
        r'TOTAL\s*฿\s*(\d+\.\d{2})',
        r'Total:\s*฿\s*(\d+\.\d{2})',
        r'ค่าใช้จ่ายรวม\s*฿\s*(\d+\.\d{2})',
        r'รวม\s*฿\s*(\d+\.\d{2})',
    ]

    for pattern in amount_patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue

    general_patterns = [
        r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)(?:\s*฿)',
        r'฿\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
    ]

    for pattern in general_patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except ValueError:
                continue

    return 0.0