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

    def disconnect(self):
        """ยกเลิกการเชื่อมต่อ"""
        if self.connection:
            try:
                self.connection.logout()
            except:
                pass

    def search_emails(self, days: int = 30, search_criteria: str = None) -> List[int]:
        """ค้นหาอีเมลตามเงื่อนไข"""
        try:
            # เลือกโฟลเดอร์
            self.connection.select(self.imap_setting.folder)

            # ถ้าไม่ได้ระบุเงื่อนไขการค้นหา ให้ใช้การค้นหาอีเมลจาก Apple เกี่ยวกับใบเสร็จ
            if search_criteria is None:
                search_criteria = '(FROM "apple.com" SUBJECT "invoice")'
                logger.info(f"ค้นหาอีเมลด้วยเงื่อนไข: {search_criteria}")

            # ค้นหาอีเมล
            status, data = self.connection.search(None, search_criteria)
            if status != "OK":
                logger.error(f"เกิดข้อผิดพลาดในการค้นหาอีเมล: {status}")
                return []

            # แปลงข้อมูลเป็นรายการ message IDs
            message_ids = data[0].split()
            logger.info(f"พบอีเมลทั้งหมด {len(message_ids)} รายการที่ตรงกับเงื่อนไข")

            # จำกัดจำนวนอีเมลสำหรับการทดสอบ (แค่ 10 ฉบับล่าสุด)
            if len(message_ids) > 10:
                message_ids = message_ids[-10:]
                logger.info("จำกัดการประมวลผลเพียง 10 ฉบับล่าสุด")

            return [int(id) for id in message_ids]

        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการค้นหาอีเมล: {str(e)}")
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

    result = {
        "email_id": f"imap_{email_data['message_id']}",
        "email_subject": email_data["subject"],
        "email_from": email_data["from"],
        "email_date": email_data["date"],
        "receipt_date": email_data["date"],
        "vendor_name": "Apple",
        "amount": extract_amount(email_data["body"]),
        "receipt_file_path": None
    }

    # ค้นหาวันที่ใบแจ้งหนี้
    invoice_date_match = re.search(r'INVOICE DATE\s*(\d{1,2}\s+\w+\s+\d{4})', email_data["body"])
    if invoice_date_match:
        date_str = invoice_date_match.group(1)
        try:
            receipt_date = datetime.strptime(date_str, '%d %b %Y')
            result["receipt_date"] = receipt_date
        except:
            pass

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