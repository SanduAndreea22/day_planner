from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings
from sib_api_v3_sdk import ApiClient, Configuration, TransactionalEmailsApi
from sib_api_v3_sdk.models import SendSmtpEmail

class BrevoBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        configuration = Configuration()
        configuration.api_key['api-key'] = settings.BREVO_API_KEY
        api_instance = TransactionalEmailsApi(ApiClient(configuration))

        sent_count = 0

        for message in email_messages:
            html_body = message.body
            for content, mimetype in getattr(message, "alternatives", []):
                if mimetype == "text/html":
                    html_body = content
                    break
            try:
                email = SendSmtpEmail(
                    to=[{"email": recipient} for recipient in message.to],
                    sender={"email": settings.DEFAULT_FROM_EMAIL.split("<")[-1].replace(">", "").strip(),
                            "name": settings.DEFAULT_FROM_EMAIL.split("<")[0].strip()},
                    subject=message.subject,
                    html_content=html_body
                )
                api_instance.send_transac_email(email)
                sent_count += 1
            except Exception:
                if not self.fail_silently:
                    raise
        return sent_count
