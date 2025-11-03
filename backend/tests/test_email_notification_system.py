"""
Unit tests for email notification system and HTML report generation.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import json
import sys

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.reporting.email_notification_service import EmailNotificationService
    from multi_instance_arxiv_system.reporting.email_template_manager import EmailTemplateManager
    from multi_instance_arxiv_system.reporting.html_report_generator import HTMLReportGenerator
    from multi_instance_arxiv_system.models.reporting_models import EmailReport, UpdateReport
except ImportError as e:
    pytest.skip(f"Required modules not available: {e}", allow_module_level=True)


class TestEmailNotificationService:
    """Test cases for EmailNotificationService."""
    
    @pytest.fixture
    def email_config(self):
        """Create email configuration."""
        return {
            'smtp_server': 'smtp.example.com',
            'smtp_port': 587,
            'username': 'test@example.com',
            'password': 'test_password',
            'use_tls': True,
            'from_address': 'arxiv-system@example.com',
            'from_name': 'ArXiv Multi-Instance System'
        }
    
    @pytest.fixture
    def email_service(self, email_config):
        """Create EmailNotificationService instance."""
        return EmailNotificationService(email_config)
    
    def test_initialization(self, email_service, email_config):
        """Test email service initialization."""
        assert email_service.smtp_server == email_config['smtp_server']
        assert email_service.smtp_port == email_config['smtp_port']
        assert email_service.username == email_config['username']
        assert email_service.from_address == email_config['from_address']
        assert email_service.use_tls == email_config['use_tls']
    
    @pytest.mark.asyncio
    async def test_send_simple_email(self, email_service):
        """Test sending simple text email."""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            
            result = await email_service.send_email(
                recipients=['test@example.com'],
                subject='Test Subject',
                body='Test message body',
                is_html=False
            )
            
            assert result == True
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once()
            mock_server.send_message.assert_called_once()
            mock_server.quit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_html_email(self, email_service):
        """Test sending HTML email."""
        html_content = """
        <html>
            <body>
                <h1>Test HTML Email</h1>
                <p>This is a test HTML email.</p>
            </body>
        </html>
        """
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            
            result = await email_service.send_email(
                recipients=['test@example.com'],
                subject='HTML Test',
                body=html_content,
                is_html=True
            )
            
            assert result == True
            mock_server.send_message.assert_called_once()
            
            # Verify HTML content was included
            sent_message = mock_server.send_message.call_args[0][0]
            assert 'text/html' in str(sent_message)
    
    @pytest.mark.asyncio
    async def test_send_email_with_attachments(self, email_service):
        """Test sending email with attachments."""
        # Create temporary file for attachment
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write('Test attachment content')
            temp_file_path = temp_file.name
        
        try:
            with patch('smtplib.SMTP') as mock_smtp:
                mock_server = Mock()
                mock_smtp.return_value = mock_server
                
                result = await email_service.send_email(
                    recipients=['test@example.com'],
                    subject='Email with Attachment',
                    body='This email has an attachment.',
                    attachments=[temp_file_path]
                )
                
                assert result == True
                mock_server.send_message.assert_called_once()
        
        finally:
            Path(temp_file_path).unlink()  # Clean up
    
    @pytest.mark.asyncio
    async def test_send_email_smtp_error(self, email_service):
        """Test email sending with SMTP error."""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_smtp.side_effect = Exception("SMTP connection failed")
            
            result = await email_service.send_email(
                recipients=['test@example.com'],
                subject='Test Subject',
                body='Test body'
            )
            
            assert result == False
    
    @pytest.mark.asyncio
    async def test_send_notification_with_priority(self, email_service):
        """Test sending notification with priority levels."""
        with patch.object(email_service, 'send_email') as mock_send:
            mock_send.return_value = True
            
            # High priority notification
            result = await email_service.send_notification(
                recipients=['admin@example.com'],
                subject='Critical Alert',
                message='System critical error detected',
                priority='high'
            )
            
            assert result == True
            mock_send.assert_called_once()
            
            # Check that priority was reflected in subject
            call_args = mock_send.call_args
            assert 'URGENT' in call_args[1]['subject'] or 'CRITICAL' in call_args[1]['subject']
    
    @pytest.mark.asyncio
    async def test_batch_send_emails(self, email_service):
        """Test sending multiple emails in batch."""
        email_list = [
            {
                'recipients': ['user1@example.com'],
                'subject': 'Update 1',
                'body': 'Update message 1'
            },
            {
                'recipients': ['user2@example.com'],
                'subject': 'Update 2',
                'body': 'Update message 2'
            }
        ]
        
        with patch.object(email_service, 'send_email') as mock_send:
            mock_send.return_value = True
            
            results = await email_service.send_batch_emails(email_list)
            
            assert len(results) == 2
            assert all(results)
            assert mock_send.call_count == 2
    
    def test_validate_email_addresses(self, email_service):
        """Test email address validation."""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'admin+alerts@company.org'
        ]
        
        invalid_emails = [
            'invalid-email',
            '@domain.com',
            'user@',
            'user space@domain.com'
        ]
        
        for email in valid_emails:
            assert email_service._validate_email_address(email) == True
        
        for email in invalid_emails:
            assert email_service._validate_email_address(email) == False
    
    @pytest.mark.asyncio
    async def test_email_rate_limiting(self, email_service):
        """Test email rate limiting functionality."""
        # Configure rate limiting (e.g., max 5 emails per minute)
        email_service.rate_limit_per_minute = 5
        
        with patch.object(email_service, 'send_email') as mock_send:
            mock_send.return_value = True
            
            # Send emails rapidly
            results = []
            for i in range(10):
                result = await email_service.send_email(
                    recipients=[f'user{i}@example.com'],
                    subject=f'Test {i}',
                    body=f'Message {i}'
                )
                results.append(result)
            
            # Should have rate limiting in effect
            successful_sends = sum(results)
            assert successful_sends <= 5  # Rate limit should prevent more than 5


class TestEmailTemplateManager:
    """Test cases for EmailTemplateManager."""
    
    @pytest.fixture
    def template_manager(self):
        """Create EmailTemplateManager instance."""
        return EmailTemplateManager()
    
    def test_initialization(self, template_manager):
        """Test template manager initialization."""
        assert hasattr(template_manager, 'templates')
        assert isinstance(template_manager.templates, dict)
    
    def test_load_default_templates(self, template_manager):
        """Test loading default email templates."""
        template_manager.load_default_templates()
        
        expected_templates = [
            'update_notification',
            'error_alert',
            'system_status',
            'monthly_report'
        ]
        
        for template_name in expected_templates:
            assert template_name in template_manager.templates
    
    def test_render_update_notification_template(self, template_manager):
        """Test rendering update notification template."""
        template_manager.load_default_templates()
        
        template_data = {
            'instance_name': 'ai_scholar',
            'update_date': datetime.now().strftime('%Y-%m-%d'),
            'papers_downloaded': 150,
            'papers_processed': 145,
            'errors_count': 2,
            'processing_time': '2.5 hours'
        }
        
        rendered = template_manager.render_template('update_notification', template_data)
        
        assert 'ai_scholar' in rendered
        assert '150' in rendered
        assert '145' in rendered
        assert 'Update completed' in rendered or 'update' in rendered.lower()
    
    def test_render_error_alert_template(self, template_manager):
        """Test rendering error alert template."""
        template_manager.load_default_templates()
        
        template_data = {
            'instance_name': 'quant_scholar',
            'error_count': 5,
            'critical_errors': 2,
            'error_summary': 'Network connectivity issues detected',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        rendered = template_manager.render_template('error_alert', template_data)
        
        assert 'quant_scholar' in rendered
        assert '5' in rendered
        assert '2' in rendered
        assert 'Network connectivity' in rendered
    
    def test_custom_template_registration(self, template_manager):
        """Test registering custom email templates."""
        custom_template = """
        <html>
            <body>
                <h1>Custom Template</h1>
                <p>Hello {{name}}, this is a custom template.</p>
                <p>Value: {{value}}</p>
            </body>
        </html>
        """
        
        template_manager.register_template('custom_test', custom_template)
        
        assert 'custom_test' in template_manager.templates
        
        rendered = template_manager.render_template('custom_test', {
            'name': 'John',
            'value': '42'
        })
        
        assert 'John' in rendered
        assert '42' in rendered
        assert 'Custom Template' in rendered
    
    def test_template_validation(self, template_manager):
        """Test template validation."""
        # Valid template
        valid_template = "<html><body>Hello {{name}}</body></html>"
        assert template_manager._validate_template(valid_template) == True
        
        # Invalid template (malformed HTML)
        invalid_template = "<html><body>Hello {{name}</body>"  # Missing closing tag
        assert template_manager._validate_template(invalid_template) == False
        
        # Template with invalid syntax
        syntax_error_template = "<html><body>Hello {{name</body></html>"  # Missing }}
        assert template_manager._validate_template(syntax_error_template) == False


class TestHTMLReportGenerator:
    """Test cases for HTMLReportGenerator."""
    
    @pytest.fixture
    def report_generator(self):
        """Create HTMLReportGenerator instance."""
        return HTMLReportGenerator()
    
    @pytest.fixture
    def sample_update_report(self):
        """Create sample update report data."""
        return UpdateReport(
            instance_name='ai_scholar',
            update_date=datetime.now(),
            papers_downloaded=150,
            papers_processed=145,
            processing_errors=2,
            processing_time_minutes=150,
            storage_used_gb=25.5,
            vector_store_documents=1450
        )
    
    def test_initialization(self, report_generator):
        """Test report generator initialization."""
        assert hasattr(report_generator, 'chart_generator')
        assert hasattr(report_generator, 'template_engine')
    
    def test_generate_update_report_html(self, report_generator, sample_update_report):
        """Test generating HTML update report."""
        html_content = report_generator.generate_update_report(sample_update_report)
        
        assert isinstance(html_content, str)
        assert '<html>' in html_content
        assert 'ai_scholar' in html_content
        assert '150' in html_content  # papers_downloaded
        assert '145' in html_content  # papers_processed
        assert '25.5' in html_content  # storage_used_gb
    
    def test_generate_error_summary_html(self, report_generator):
        """Test generating HTML error summary."""
        error_data = {
            'instance_name': 'quant_scholar',
            'total_errors': 10,
            'critical_errors': 2,
            'error_categories': {
                'network': 5,
                'pdf_processing': 3,
                'storage': 2
            },
            'recent_errors': [
                {
                    'timestamp': datetime.now().isoformat(),
                    'category': 'network',
                    'message': 'Connection timeout',
                    'severity': 'medium'
                }
            ]
        }
        
        html_content = report_generator.generate_error_summary(error_data)
        
        assert isinstance(html_content, str)
        assert '<html>' in html_content
        assert 'quant_scholar' in html_content
        assert '10' in html_content  # total_errors
        assert 'Connection timeout' in html_content
    
    def test_generate_chart_html(self, report_generator):
        """Test generating chart HTML."""
        chart_data = {
            'labels': ['January', 'February', 'March'],
            'datasets': [{
                'label': 'Papers Downloaded',
                'data': [100, 150, 200],
                'backgroundColor': 'rgba(54, 162, 235, 0.2)'
            }]
        }
        
        chart_html = report_generator.generate_chart('line', chart_data, 'Monthly Downloads')
        
        assert isinstance(chart_html, str)
        assert 'canvas' in chart_html
        assert 'Chart.js' in chart_html or 'chart' in chart_html.lower()
        assert 'Monthly Downloads' in chart_html
    
    def test_add_css_styling(self, report_generator):
        """Test adding CSS styling to HTML reports."""
        basic_html = "<html><body><h1>Test Report</h1></body></html>"
        
        styled_html = report_generator._add_css_styling(basic_html)
        
        assert '<style>' in styled_html
        assert 'font-family' in styled_html
        assert 'color' in styled_html
        assert basic_html in styled_html
    
    def test_responsive_design_elements(self, report_generator):
        """Test responsive design elements in generated HTML."""
        sample_data = {
            'title': 'Test Report',
            'content': 'Test content'
        }
        
        html_content = report_generator._generate_responsive_html(sample_data)
        
        assert 'viewport' in html_content
        assert 'media' in html_content  # CSS media queries
        assert 'responsive' in html_content or '@media' in html_content


class TestEmailReportModel:
    """Test cases for EmailReport model."""
    
    def test_email_report_creation(self):
        """Test creating EmailReport instance."""
        report = EmailReport(
            report_id='test_report_001',
            instance_name='ai_scholar',
            report_type='update_notification',
            recipients=['admin@example.com'],
            subject='AI Scholar Update Complete',
            generated_at=datetime.now()
        )
        
        assert report.report_id == 'test_report_001'
        assert report.instance_name == 'ai_scholar'
        assert report.report_type == 'update_notification'
        assert 'admin@example.com' in report.recipients
    
    def test_email_report_validation(self):
        """Test EmailReport validation."""
        # Valid report
        valid_report = EmailReport(
            report_id='valid_report',
            instance_name='test_instance',
            report_type='test_type',
            recipients=['test@example.com'],
            subject='Test Subject',
            generated_at=datetime.now()
        )
        
        assert valid_report.validate() == True
        
        # Invalid report (empty recipients)
        with pytest.raises(ValueError):
            EmailReport(
                report_id='invalid_report',
                instance_name='test_instance',
                report_type='test_type',
                recipients=[],  # Empty recipients should raise error
                subject='Test Subject',
                generated_at=datetime.now()
            )
    
    def test_email_report_serialization(self):
        """Test EmailReport serialization."""
        report = EmailReport(
            report_id='serialize_test',
            instance_name='test_instance',
            report_type='test_type',
            recipients=['test@example.com'],
            subject='Test Subject',
            generated_at=datetime.now()
        )
        
        report_dict = report.to_dict()
        
        assert report_dict['report_id'] == 'serialize_test'
        assert report_dict['instance_name'] == 'test_instance'
        assert report_dict['recipients'] == ['test@example.com']
        assert 'generated_at' in report_dict


class TestEmailSystemIntegration:
    """Integration tests for email notification system."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_email_workflow(self):
        """Test complete email notification workflow."""
        # Mock email configuration
        email_config = {
            'smtp_server': 'smtp.example.com',
            'smtp_port': 587,
            'username': 'test@example.com',
            'password': 'test_password',
            'from_address': 'system@example.com'
        }
        
        # Create services
        email_service = EmailNotificationService(email_config)
        template_manager = EmailTemplateManager()
        report_generator = HTMLReportGenerator()
        
        # Load templates
        template_manager.load_default_templates()
        
        # Create sample report data
        update_data = {
            'instance_name': 'ai_scholar',
            'update_date': datetime.now().strftime('%Y-%m-%d'),
            'papers_downloaded': 100,
            'papers_processed': 95,
            'errors_count': 1
        }
        
        with patch.object(email_service, 'send_email') as mock_send:
            mock_send.return_value = True
            
            # Generate HTML report
            html_content = template_manager.render_template('update_notification', update_data)
            
            # Send email
            result = await email_service.send_email(
                recipients=['admin@example.com'],
                subject='AI Scholar Update Complete',
                body=html_content,
                is_html=True
            )
            
            assert result == True
            mock_send.assert_called_once()
            
            # Verify email content
            call_args = mock_send.call_args
            assert 'ai_scholar' in call_args[1]['body']
            assert '100' in call_args[1]['body']
    
    @pytest.mark.asyncio
    async def test_error_notification_workflow(self):
        """Test error notification workflow."""
        email_service = EmailNotificationService({
            'smtp_server': 'smtp.example.com',
            'from_address': 'system@example.com'
        })
        
        template_manager = EmailTemplateManager()
        template_manager.load_default_templates()
        
        error_data = {
            'instance_name': 'quant_scholar',
            'error_count': 5,
            'critical_errors': 1,
            'error_summary': 'Critical processing error detected'
        }
        
        with patch.object(email_service, 'send_email') as mock_send:
            mock_send.return_value = True
            
            # Generate error alert
            alert_content = template_manager.render_template('error_alert', error_data)
            
            # Send critical alert
            result = await email_service.send_notification(
                recipients=['admin@example.com'],
                subject='CRITICAL: Quant Scholar Error Alert',
                message=alert_content,
                priority='critical'
            )
            
            assert result == True
            mock_send.assert_called_once()
            
            # Verify alert was marked as critical
            call_args = mock_send.call_args
            subject = call_args[1]['subject']
            assert 'CRITICAL' in subject or 'URGENT' in subject