import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "krrsoftwaresolutions11@gmail.com"
SENDER_PASSWORD = "qztq jibj mlqv owkz"

def send_feedback_notification(feedback):
    """Send email notification when new feedback is received"""
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"New {feedback.feedback_type.upper()} Feedback - Coupons Cover"
        msg['From'] = SENDER_EMAIL
        msg['To'] = SENDER_EMAIL
        
        # Create HTML body
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f9f9f9;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 5px 5px 0 0;
                    text-align: center;
                }}
                .content {{
                    background: white;
                    padding: 20px;
                    border-radius: 0 0 5px 5px;
                }}
                .feedback-type {{
                    display: inline-block;
                    padding: 5px 15px;
                    border-radius: 20px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                .bug {{ background-color: #fee; color: #c00; }}
                .feature {{ background-color: #efe; color: #0a0; }}
                .general {{ background-color: #eef; color: #00a; }}
                .complaint {{ background-color: #ffe; color: #a50; }}
                .appreciation {{ background-color: #fef; color: #a0a; }}
                .info-row {{
                    margin: 10px 0;
                    padding: 10px;
                    background: #f5f5f5;
                    border-left: 3px solid #667eea;
                }}
                .label {{
                    font-weight: bold;
                    color: #667eea;
                }}
                .message-box {{
                    background: #f9f9f9;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 15px 0;
                    border-left: 4px solid #667eea;
                }}
                .rating {{
                    color: #ffc107;
                    font-size: 20px;
                }}
                .footer {{
                    text-align: center;
                    padding: 15px;
                    color: #666;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📝 New User Feedback Received</h1>
                </div>
                <div class="content">
                    <p><span class="feedback-type {feedback.feedback_type}">{feedback.feedback_type.upper()}</span></p>
                    
                    <div class="info-row">
                        <span class="label">📅 Date:</span> {feedback.created_at.strftime('%B %d, %Y at %I:%M %p') if feedback.created_at else 'N/A'}
                    </div>
                    
                    {f'<div class="info-row"><span class="label">👤 Name:</span> {feedback.name}</div>' if feedback.name else ''}
                    
                    {f'<div class="info-row"><span class="label">📧 Email:</span> {feedback.email}</div>' if feedback.email else ''}
                    
                    <div class="info-row">
                        <span class="label">🔗 Page:</span> {feedback.page_url}
                    </div>
                    
                    {f'''<div class="info-row">
                        <span class="label">⭐ Rating:</span> 
                        <span class="rating">{"★" * feedback.rating}{"☆" * (5 - feedback.rating)}</span> 
                        ({feedback.rating}/5)
                    </div>''' if feedback.rating else ''}
                    
                    <div class="message-box">
                        <strong>💬 Message:</strong><br><br>
                        {feedback.message.replace(chr(10), '<br>')}
                    </div>
                    
                    {f'<div class="info-row"><span class="label">🌐 Browser:</span> <small>{feedback.browser_info}</small></div>' if feedback.browser_info else ''}
                    
                    <div style="margin-top: 20px; padding: 15px; background: #e8f4ff; border-radius: 5px;">
                        <strong>🔗 Quick Actions:</strong><br>
                        <a href="http://localhost:8000/admin/feedback" style="color: #667eea; text-decoration: none;">View in Admin Panel →</a>
                    </div>
                </div>
                <div class="footer">
                    <p>This is an automated message from Coupons Cover Feedback System</p>
                    <p>Feedback ID: #{feedback.id}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Attach HTML body
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Feedback notification email sent successfully for feedback ID: {feedback.id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send feedback notification email: {e}")
        return False

def send_feedback_response(to_email, feedback_id, admin_response):
    """Send response to user who submitted feedback"""
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Response to Your Feedback - Coupons Cover"
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        
        # Create HTML body
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f9f9f9;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 5px 5px 0 0;
                    text-align: center;
                }}
                .content {{
                    background: white;
                    padding: 20px;
                    border-radius: 0 0 5px 5px;
                }}
                .response-box {{
                    background: #f0f7ff;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 15px 0;
                    border-left: 4px solid #667eea;
                }}
                .footer {{
                    text-align: center;
                    padding: 15px;
                    color: #666;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>💌 Thank You for Your Feedback!</h1>
                </div>
                <div class="content">
                    <p>Dear User,</p>
                    
                    <p>Thank you for taking the time to share your feedback with us. We appreciate your input and take all feedback seriously.</p>
                    
                    <div class="response-box">
                        <strong>Our Response:</strong><br><br>
                        {admin_response.replace(chr(10), '<br>')}
                    </div>
                    
                    <p>If you have any additional questions or concerns, please don't hesitate to reach out to us.</p>
                    
                    <p>Best regards,<br>
                    <strong>Coupons Cover Team</strong></p>
                </div>
                <div class="footer">
                    <p>Feedback Reference: #{feedback_id}</p>
                    <p>&copy; 2025 Coupons Cover. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Attach HTML body
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Feedback response email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send feedback response email: {e}")
        return False
